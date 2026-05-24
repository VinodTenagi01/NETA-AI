"""
End-to-end voter roll PDF ingestion pipeline.

Flow:
  PDF → OCR pages → parse pages → normalize voters → bulk insert to DB
  Supports dry_run mode for validation without DB writes.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.voter_roll_ingestion.extractor_ocr import extract_pages_ocr
from app.voter_roll_ingestion.models import NormalizedVoter, PipelineResult
from app.voter_roll_ingestion.normalizer import normalize_batch
from app.voter_roll_ingestion.parser import parse_document

BATCH_SIZE = 500
# AC-52 Serilingampally constituency UUID (from seed data)
AC52_CONSTITUENCY_ID = uuid.UUID("11111111-0052-4000-8000-000000000001")


# ─── Booth resolution ─────────────────────────────────────────────────────────


async def _resolve_booth(
    session: AsyncSession,
    constituency_id: uuid.UUID,
    part_number: int | None,
    booth_name: str | None,
) -> uuid.UUID | None:
    """
    Find or create a Booth row for the given part number.
    Returns the booth UUID, or None on failure.
    """
    from app.database_design.models import Booth

    if part_number is not None:
        # Match by booth_number = zero-padded part number (e.g. "001")
        booth_code = str(part_number).zfill(3)
        result = await session.scalar(
            select(Booth.id).where(
                Booth.constituency_id == constituency_id,
                Booth.booth_number == booth_code,
            )
        )
        if result:
            return result

    # Auto-create booth for this part
    new_id = uuid.uuid4()
    code = str(part_number).zfill(3) if part_number else uuid.uuid4().hex[:6].upper()
    stmt = text(
        """
        INSERT INTO booths (id, constituency_id, booth_number, booth_name, created_at, updated_at)
        VALUES (:id, :cid, :code, :name, NOW(), NOW())
        ON CONFLICT (constituency_id, booth_number) DO UPDATE SET booth_name = EXCLUDED.booth_name
        RETURNING id
        """
    )
    row = await session.execute(
        stmt,
        {
            "id": str(new_id),
            "cid": str(constituency_id),
            "code": code,
            "name": booth_name or f"Part {part_number}",
        },
    )
    returned_id = row.scalar_one_or_none()
    await session.flush()
    return uuid.UUID(str(returned_id)) if returned_id else new_id


# ─── Bulk voter insert ────────────────────────────────────────────────────────


async def _bulk_insert_voters(
    session: AsyncSession,
    voters: list[NormalizedVoter],
    booth_id: uuid.UUID,
) -> tuple[int, int, int]:
    """Returns (inserted, skipped, errors)."""
    inserted = skipped = errors = 0

    for start in range(0, len(voters), BATCH_SIZE):
        batch = voters[start : start + BATCH_SIZE]
        epic_ids = [v.ec_voter_id for v in batch]

        existing: set[str] = set(
            await session.scalars(
                select(text("voter_id")).select_from(text("voters")).where(
                    text("voter_id = ANY(:ids)")
                ).params(ids=epic_ids)
            )
        )

        new_voters = [v for v in batch if v.ec_voter_id not in existing]
        skipped += len(batch) - len(new_voters)
        if not new_voters:
            continue

        rows = [
            {
                "id": str(uuid.uuid4()),
                "booth_id": str(booth_id),
                "voter_id": v.ec_voter_id,
                "full_name": v.name,
                "father_name": v.father_or_husband_name,
                "gender": v.gender,
                "age": v.age,
                "serial_number": v.serial_number,
                "is_contacted": False,
            }
            for v in new_voters
        ]

        try:
            await session.execute(
                text(
                    """
                    INSERT INTO voters
                        (id, booth_id, voter_id, full_name, father_name, gender, age,
                         serial_number, is_contacted, created_at)
                    VALUES
                        (:id, :booth_id, :voter_id, :full_name, :father_name, :gender,
                         :age, :serial_number, :is_contacted, NOW())
                    """
                ),
                rows,
            )
            inserted += len(rows)
        except Exception as exc:
            errors += len(rows)
            await session.rollback()
            # Retry individually to minimize loss
            for row in rows:
                try:
                    await session.execute(
                        text(
                            """
                            INSERT INTO voters
                                (id, booth_id, voter_id, full_name, father_name, gender, age,
                                 serial_number, is_contacted, created_at)
                            VALUES
                                (:id, :booth_id, :voter_id, :full_name, :father_name, :gender,
                                 :age, :serial_number, :is_contacted, NOW())
                            """
                        ),
                        row,
                    )
                    inserted += 1
                    errors -= 1
                except Exception:
                    await session.rollback()

    return inserted, skipped, errors


# ─── Pipeline entry point ─────────────────────────────────────────────────────


async def process_pdf(
    pdf_path: Path,
    session: Optional[AsyncSession] = None,
    constituency_id: uuid.UUID = AC52_CONSTITUENCY_ID,
    dry_run: bool = False,
    cache_ocr: bool = True,
) -> PipelineResult:
    """
    Full pipeline: OCR → parse → normalize → insert.
    If dry_run=True, skips DB insert and returns stats only.
    If cache_ocr=True, saves/reloads OCR JSON to avoid re-running Tesseract.
    """
    result = PipelineResult(file_name=pdf_path.name)

    # ── 1. OCR (with optional cache) ──────────────────────────────────────
    cache_path = pdf_path.parent / (pdf_path.stem + "_ocr_cache.json")

    if cache_ocr and cache_path.exists():
        with open(cache_path, encoding="utf-8") as f:
            pages_raw = json.load(f)
        pages = [(item[0], item[1]) for item in pages_raw]
    else:
        pages = extract_pages_ocr(pdf_path)
        if cache_ocr:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(pages, f, ensure_ascii=False, indent=2)

    # ── 2. Parse ──────────────────────────────────────────────────────────
    doc = parse_document(pages)
    result.part_number = doc.header.part_number if doc.header else None
    result.booth_name = doc.header.booth_name if doc.header else None

    # ── 3. Normalize ──────────────────────────────────────────────────────
    valid_voters, invalid_count = normalize_batch(doc.voters)
    result.invalid = invalid_count + len(doc.parse_errors)
    result.errors.extend(doc.parse_errors[:10])

    if dry_run or not valid_voters:
        result.status = "completed" if not doc.parse_errors else "partial"
        result.skipped = len(doc.voters) - len(valid_voters)
        return result

    # ── 4. Insert ─────────────────────────────────────────────────────────
    if session is None:
        result.status = "failed"
        result.errors.append("No DB session provided and dry_run=False")
        return result

    try:
        booth_id = await _resolve_booth(
            session,
            constituency_id,
            result.part_number,
            result.booth_name,
        )
        if booth_id is None:
            result.status = "failed"
            result.errors.append("Could not resolve or create booth")
            return result

        inserted, skipped, errors = await _bulk_insert_voters(
            session, valid_voters, booth_id
        )
        await session.commit()

        result.inserted = inserted
        result.skipped = skipped + (len(doc.voters) - len(valid_voters))
        result.errors.extend([f"bulk_error:{errors}"] if errors else [])
        result.status = "completed" if errors == 0 else "partial"

    except Exception as exc:
        await session.rollback()
        result.status = "failed"
        result.errors.append(f"DB error: {exc}")

    return result
