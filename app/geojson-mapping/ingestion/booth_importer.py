"""
Booth CSV Importer.
Accepts ECI booth list CSV and upserts into booths table.
Validates: booth_number uniqueness, coordinate range, voter counts,
           required columns, zone mapping.
"""
import csv
import io
import uuid
from typing import Optional
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_design.models import Booth, CampaignZone, BoothWardMapping
from app.geojson_mapping.schemas import IngestionReport

REQUIRED_COLUMNS = {"booth_number", "booth_name", "total_voters", "female_voters", "male_voters"}
OPTIONAL_COLUMNS = {"address", "latitude", "longitude", "ward_id", "ward_name"}

# Serilingampally AC-52 coordinate bounds
LAT_MIN, LAT_MAX = 17.40, 17.55
LNG_MIN, LNG_MAX = 78.26, 78.42


class BoothImporter:
    def __init__(self, db: AsyncSession, constituency_id: UUID, dry_run: bool = False):
        self.db = db
        self.constituency_id = constituency_id
        self.dry_run = dry_run

    async def import_csv(self, csv_text: str) -> IngestionReport:
        reader = csv.DictReader(io.StringIO(csv_text))
        fieldnames = set(reader.fieldnames or [])
        fieldnames_lower = {f.strip().lower() for f in fieldnames}

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

        # Normalize header names
        col_map = {f.strip().lower(): f.strip() for f in (reader.fieldnames or [])}

        rows = list(reader)
        report = IngestionReport(
            status="success",
            total_rows=len(rows),
            inserted=0,
            updated=0,
            skipped=0,
        )

        # Build existing booth_number map to detect updates
        existing = await self._fetch_existing_booth_numbers()
        seen_numbers: set[str] = set()

        zone_map = await self._build_zone_map()

        for idx, raw_row in enumerate(rows, start=2):  # row 1 = header
            row = {k.strip().lower(): v.strip() for k, v in raw_row.items() if v}
            booth_num = row.get("booth_number", "").strip()
            if not booth_num:
                report.errors.append({"row": idx, "error": "Empty booth_number"})
                report.skipped += 1
                continue

            # Duplicate within upload
            if booth_num in seen_numbers:
                report.duplicate_booth_numbers.append(booth_num)
                report.warnings.append(f"Row {idx}: duplicate booth_number {booth_num} in upload — skipped")
                report.skipped += 1
                continue
            seen_numbers.add(booth_num)

            # Validate voter counts
            try:
                total_v = int(row.get("total_voters", 0))
                female_v = int(row.get("female_voters", 0))
                male_v = int(row.get("male_voters", 0))
            except ValueError:
                report.errors.append({"row": idx, "error": f"Non-integer voter counts for booth {booth_num}"})
                report.skipped += 1
                continue

            if total_v <= 0:
                report.warnings.append(f"Row {idx}: booth {booth_num} has total_voters={total_v}")

            # Validate coordinates
            lat = self._parse_float(row.get("latitude"))
            lng = self._parse_float(row.get("longitude"))
            geom = None

            if lat is not None and lng is not None:
                if not (LAT_MIN <= lat <= LAT_MAX and LNG_MIN <= lng <= LNG_MAX):
                    report.invalid_coordinates.append(booth_num)
                    report.warnings.append(
                        f"Row {idx}: booth {booth_num} coordinates ({lat},{lng}) outside constituency bounds — stored without location"
                    )
                    lat, lng = None, None
                else:
                    geom = f"SRID=4326;POINT({lng} {lat})"

            # Zone lookup
            ward_id = row.get("ward_id")
            zone_id = zone_map.get(ward_id) if ward_id else None

            if not self.dry_run:
                if booth_num in existing:
                    await self._update_booth(existing[booth_num], row, total_v, female_v, male_v, geom, zone_id)
                    report.updated += 1
                else:
                    await self._insert_booth(row, booth_num, total_v, female_v, male_v, geom, zone_id, ward_id)
                    report.inserted += 1
            else:
                # Dry run: just count what would happen
                if booth_num in existing:
                    report.updated += 1
                else:
                    report.inserted += 1

        if report.errors:
            report.status = "partial"
        if not self.dry_run:
            await self.db.flush()

        return report

    async def _insert_booth(
        self,
        row: dict,
        booth_num: str,
        total_v: int,
        female_v: int,
        male_v: int,
        geom: Optional[str],
        zone_id: Optional[UUID],
        ward_id: Optional[str],
    ) -> None:
        booth = Booth(
            id=uuid.uuid4(),
            constituency_id=self.constituency_id,
            zone_id=zone_id,
            booth_number=booth_num,
            booth_name=row.get("booth_name"),
            address=row.get("address"),
            total_voters=total_v,
            female_voters=female_v,
            male_voters=male_v,
        )
        if geom:
            booth.location = text(f"ST_GeogFromText('{geom}')")

        self.db.add(booth)
        await self.db.flush()

        if ward_id:
            mapping = BoothWardMapping(
                id=uuid.uuid4(),
                booth_id=booth.id,
                ward_id=ward_id,
                ward_name=row.get("ward_name"),
            )
            self.db.add(mapping)

    async def _update_booth(
        self,
        booth_id: UUID,
        row: dict,
        total_v: int,
        female_v: int,
        male_v: int,
        geom: Optional[str],
        zone_id: Optional[UUID],
    ) -> None:
        result = await self.db.execute(select(Booth).where(Booth.id == booth_id))
        booth = result.scalar_one_or_none()
        if not booth:
            return

        booth.booth_name = row.get("booth_name") or booth.booth_name
        booth.address = row.get("address") or booth.address
        booth.total_voters = total_v
        booth.female_voters = female_v
        booth.male_voters = male_v
        if zone_id:
            booth.zone_id = zone_id
        if geom:
            booth.location = text(f"ST_GeogFromText('{geom}')")

    async def _fetch_existing_booth_numbers(self) -> dict[str, UUID]:
        result = await self.db.execute(
            select(Booth.booth_number, Booth.id).where(Booth.constituency_id == self.constituency_id)
        )
        return {row.booth_number: row.id for row in result.all()}

    async def _build_zone_map(self) -> dict[str, UUID]:
        """Map zone_code → zone UUID for the constituency."""
        result = await self.db.execute(
            select(CampaignZone.zone_code, CampaignZone.id).where(
                CampaignZone.constituency_id == self.constituency_id
            )
        )
        return {row.zone_code: row.id for row in result.all()}

    @staticmethod
    def _parse_float(val: Optional[str]) -> Optional[float]:
        if not val:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None
