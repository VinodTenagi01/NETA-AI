"""
CLI entry point: run voter roll PDF ingestion.

Usage (from D:\\NETA.AI root):
    python -m app.voter_roll_ingestion.cli --file data/imports/part1.pdf
    python -m app.voter_roll_ingestion.cli --dir  data/imports/ --dry-run
    python -m app.voter_roll_ingestion.cli --file data/imports/part1.pdf --no-cache

Requires PostgreSQL running and DATABASE_URL in .env.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Allow running as `python -m app.voter_roll_ingestion.cli`
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="NETA AI — Voter Roll PDF Ingestion (OCR pipeline)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (OCR + parse, no DB write)
  python -m app.voter_roll_ingestion.cli --file data/imports/AC52_Part001.pdf --dry-run

  # Import single part
  python -m app.voter_roll_ingestion.cli --file data/imports/AC52_Part001.pdf

  # Import all PDFs in directory
  python -m app.voter_roll_ingestion.cli --dir data/imports/

  # Skip OCR cache (re-run Tesseract)
  python -m app.voter_roll_ingestion.cli --file data/imports/part1.pdf --no-cache
""",
    )
    parser.add_argument("--file", type=Path, default=None, help="Path to a single PDF")
    parser.add_argument("--dir", type=Path, default=None, help="Directory of PDFs to process")
    parser.add_argument("--dry-run", action="store_true", help="Parse only, skip DB writes")
    parser.add_argument("--no-cache", action="store_true", help="Ignore OCR cache, re-run Tesseract")
    parser.add_argument(
        "--constituency-id",
        default="11111111-0052-4000-8000-000000000001",
        help="UUID of target constituency (default: AC-52 Serilingampally)",
    )
    return parser.parse_args()


async def _run_one(pdf_path: Path, args: argparse.Namespace, session=None) -> None:
    import uuid
    from app.voter_roll_ingestion.pipeline import process_pdf

    result = await process_pdf(
        pdf_path=pdf_path,
        session=session,
        constituency_id=uuid.UUID(args.constituency_id),
        dry_run=args.dry_run,
        cache_ocr=not args.no_cache,
    )

    status_icon = {"completed": "[OK]", "partial": "[WARN]", "failed": "[FAIL]"}.get(
        result.status, "[?]"
    )
    print(
        f"{status_icon}  {pdf_path.name:40s}  "
        f"Part={result.part_number or '?':>3}  "
        f"Inserted={result.inserted:>6}  "
        f"Skipped={result.skipped:>6}  "
        f"Invalid={result.invalid:>6}"
    )
    if result.errors:
        for err in result.errors[:3]:
            print(f"       => {err[:100]}")


async def main(args: argparse.Namespace) -> int:
    pdfs: list[Path] = []

    if args.file:
        if not args.file.exists():
            print(f"ERROR: File not found: {args.file}", file=sys.stderr)
            return 1
        pdfs = [args.file]
    elif args.dir:
        if not args.dir.exists():
            print(f"ERROR: Directory not found: {args.dir}", file=sys.stderr)
            return 1
        pdfs = sorted(args.dir.glob("*.pdf"))
        if not pdfs:
            print(f"No PDFs found in {args.dir}", file=sys.stderr)
            return 1
    else:
        print("ERROR: Provide --file or --dir", file=sys.stderr)
        return 1

    print(f"\nNETA AI Voter Roll Ingestion")
    print(f"Mode: {'DRY-RUN' if args.dry_run else 'LIVE'} | PDFs: {len(pdfs)}")
    print("-" * 80)

    session = None
    if not args.dry_run:
        try:
            from app.database_design.database import AsyncSessionFactory
            session = AsyncSessionFactory()
        except Exception as exc:
            print(f"WARNING: Could not open DB session: {exc}")
            print("Falling back to dry-run mode.")
            args.dry_run = True

    try:
        for pdf in pdfs:
            await _run_one(pdf, args, session)
    finally:
        if session is not None:
            try:
                await session.close()
            except Exception as e:
                print(f"WARNING: Error closing session: {e}")

    print("-" * 80)
    print("Done.")
    return 0


if __name__ == "__main__":
    args = _parse_args()
    sys.exit(asyncio.run(main(args)))
