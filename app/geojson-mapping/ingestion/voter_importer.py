"""
Voter Roll CSV Importer.
Accepts ECI voter roll CSV, encrypts PII, and upserts into voters table.
Validates: voter_id uniqueness, booth_number lookup, gender codes,
           age range, required columns.
"""
import csv
import io
import os
import uuid
from base64 import b64encode
from typing import Optional
from uuid import UUID

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_design.models import Booth, Voter
from app.geojson_mapping.schemas import IngestionReport

REQUIRED_COLUMNS = {"booth_number", "voter_id", "full_name", "gender", "age"}
GENDER_MAP = {"M": "M", "F": "F", "O": "O", "MALE": "M", "FEMALE": "F", "OTHER": "O"}


def _encrypt_pii(plaintext: str, key: bytes) -> bytes:
    """AES-256-GCM encrypt PII field. Returns nonce+ciphertext."""
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return nonce + ct


class VoterImporter:
    def __init__(self, db: AsyncSession, constituency_id: UUID, dry_run: bool = False):
        self.db = db
        self.constituency_id = constituency_id
        self.dry_run = dry_run
        # In production this key comes from environment / KMS
        self._enc_key = os.environ.get("PII_ENCRYPTION_KEY", "").encode("utf-8")
        if len(self._enc_key) < 32:
            self._enc_key = self._enc_key.ljust(32, b"0")[:32]

    async def import_csv(self, csv_text: str) -> IngestionReport:
        reader = csv.DictReader(io.StringIO(csv_text))
        fieldnames_lower = {f.strip().lower() for f in (reader.fieldnames or [])}

        missing = REQUIRED_COLUMNS - fieldnames_lower
        if missing:
            return IngestionReport(
                status="failed",
                total_rows=0,
                inserted=0,
                updated=0,
                skipped=0,
                errors=[{"row": 0, "error": f"Missing required columns: {missing}"}],
            )

        rows = list(reader)
        report = IngestionReport(
            status="success",
            total_rows=len(rows),
            inserted=0,
            updated=0,
            skipped=0,
        )

        # Prefetch booth_number → booth_id map
        booth_map = await self._fetch_booth_map()
        # Prefetch existing voter_ids to detect updates
        existing_voters = await self._fetch_existing_voter_ids()

        seen_voter_ids: set[str] = set()
        batch: list[Voter] = []
        BATCH_SIZE = 500

        for idx, raw_row in enumerate(rows, start=2):
            row = {k.strip().lower(): (v.strip() if v else "") for k, v in raw_row.items()}

            voter_id = row.get("voter_id", "").strip().upper()
            booth_num = row.get("booth_number", "").strip()
            full_name = row.get("full_name", "").strip()

            if not voter_id or not full_name:
                report.errors.append({"row": idx, "error": "voter_id or full_name is empty"})
                report.skipped += 1
                continue

            if voter_id in seen_voter_ids:
                report.warnings.append(f"Row {idx}: duplicate voter_id {voter_id} in upload — skipped")
                report.skipped += 1
                continue
            seen_voter_ids.add(voter_id)

            booth_id = booth_map.get(booth_num)
            if not booth_id:
                report.errors.append({"row": idx, "error": f"Booth {booth_num} not found in constituency"})
                report.skipped += 1
                continue

            gender_raw = row.get("gender", "").upper()
            gender = GENDER_MAP.get(gender_raw)
            if not gender:
                report.warnings.append(f"Row {idx}: unrecognized gender '{gender_raw}' for {voter_id}")
                gender = None

            age_val = self._parse_int(row.get("age"))
            if age_val is not None and not (18 <= age_val <= 120):
                report.warnings.append(f"Row {idx}: age {age_val} out of valid range for {voter_id}")
                age_val = None

            phone_enc = None
            if row.get("phone"):
                phone_clean = "".join(c for c in row["phone"] if c.isdigit())
                if phone_clean:
                    phone_enc = _encrypt_pii(phone_clean, self._enc_key)

            address_enc = None
            if row.get("address"):
                address_enc = _encrypt_pii(row["address"], self._enc_key)

            if not self.dry_run:
                if voter_id in existing_voters:
                    # Update existing
                    result = await self.db.execute(
                        select(Voter).where(Voter.voter_id == voter_id)
                    )
                    voter = result.scalar_one_or_none()
                    if voter:
                        voter.full_name = full_name
                        voter.gender = gender
                        voter.age = age_val
                        voter.booth_id = booth_id
                        if phone_enc:
                            voter.phone_encrypted = phone_enc
                        if address_enc:
                            voter.address_encrypted = address_enc
                    report.updated += 1
                else:
                    voter = Voter(
                        id=uuid.uuid4(),
                        booth_id=booth_id,
                        voter_id=voter_id,
                        full_name=full_name,
                        gender=gender,
                        age=age_val,
                        phone_encrypted=phone_enc,
                        address_encrypted=address_enc,
                    )
                    self.db.add(voter)
                    report.inserted += 1
                    batch.append(voter)

                if len(batch) >= BATCH_SIZE:
                    await self.db.flush()
                    batch.clear()
            else:
                if voter_id in existing_voters:
                    report.updated += 1
                else:
                    report.inserted += 1

        if not self.dry_run and batch:
            await self.db.flush()

        if report.errors:
            report.status = "partial"

        return report

    async def _fetch_booth_map(self) -> dict[str, UUID]:
        result = await self.db.execute(
            select(Booth.booth_number, Booth.id).where(
                Booth.constituency_id == self.constituency_id
            )
        )
        return {row.booth_number: row.id for row in result.all()}

    async def _fetch_existing_voter_ids(self) -> set[str]:
        result = await self.db.execute(
            select(Voter.voter_id).where(Voter.voter_id.isnot(None))
        )
        return {row[0] for row in result.all()}

    @staticmethod
    def _parse_int(val: Optional[str]) -> Optional[int]:
        if not val:
            return None
        try:
            return int(val)
        except (ValueError, TypeError):
            return None
