"""
Clean and validate ExtractedVoter records → NormalizedVoter ready for DB.
"""
from __future__ import annotations

import re
import unicodedata

from app.voter_roll_ingestion.models import ExtractedVoter, NormalizedVoter

# Serilingampally EPIC prefix is SWO (3 letters) + 7 digits = 10 chars
# Generic ECI pattern: 2-3 uppercase letters + 6-8 digits
EPIC_RE = re.compile(r"^[A-Z]{2,3}[0-9]{6,8}$")
MIN_AGE, MAX_AGE = 18, 120

_GENDER_MAP: dict[str, str] = {
    "male": "M", "m": "M",
    "female": "F", "f": "F",
    "other": "O", "o": "O", "others": "O",
    # Telugu OCR variants
    "పురుషుడు": "M", "మహిళ": "F",
}


def _clean(raw: str | None) -> str | None:
    if not raw:
        return None
    s = unicodedata.normalize("NFC", raw)
    s = " ".join(s.split())
    s = "".join(ch for ch in s if unicodedata.category(ch) not in ("Cc", "Cf"))
    return s.strip() or None


def _normalize_epic(raw: str | None) -> str | None:
    if not raw:
        return None
    candidate = raw.strip().upper().replace(" ", "").replace("-", "")
    # OCR sometimes reads 'O' as '0' in prefix — fix common SWO→SW0 issue
    if candidate.startswith("SW0") and len(candidate) == 10:
        candidate = "SWO" + candidate[3:]
    if EPIC_RE.match(candidate):
        return candidate
    return None


def _normalize_gender(raw: str | None) -> str | None:
    if not raw:
        return None
    key = raw.strip().lower()
    result = _GENDER_MAP.get(key) or _GENDER_MAP.get(key[:1])
    # Handle Telugu-script gender markers from OCR noise
    if not result:
        if "male" in key or key == "m":
            return "M"
        if "female" in key or key == "f":
            return "F"
    return result


def _normalize_age(raw: str | int | None) -> int | None:
    if raw is None:
        return None
    try:
        val = int(str(raw).strip().split(".")[0])
        return val if MIN_AGE <= val <= MAX_AGE else None
    except (ValueError, TypeError):
        return None


def normalize_voter(raw: ExtractedVoter) -> NormalizedVoter | None:
    epic = _normalize_epic(raw.ec_voter_id)
    name = _clean(raw.name)
    if not epic and not name:
        return None
    addr_parts = filter(None, [_clean(raw.house_no), _clean(raw.address)])
    address = ", ".join(addr_parts) or None
    return NormalizedVoter(
        ec_voter_id=epic or f"UNKNOWN-{name}",
        name=(name or "UNKNOWN").upper(),
        father_or_husband_name=(_clean(raw.father_or_husband_name) or "").upper() or None,
        age=_normalize_age(raw.age),
        gender=_normalize_gender(raw.gender),
        address=address,
        serial_number=raw.serial_number,
    )


def normalize_batch(voters: list[ExtractedVoter]) -> tuple[list[NormalizedVoter], int]:
    seen: set[str] = set()
    valid: list[NormalizedVoter] = []
    invalid = 0
    for raw in voters:
        result = normalize_voter(raw)
        if result is None:
            invalid += 1
            continue
        if result.ec_voter_id in seen:
            invalid += 1
            continue
        seen.add(result.ec_voter_id)
        valid.append(result)
    return valid, invalid
