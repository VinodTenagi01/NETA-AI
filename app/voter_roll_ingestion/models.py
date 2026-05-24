"""
Pydantic models for voter roll OCR extraction and normalization pipeline.
"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class PageHeader(BaseModel):
    part_number: Optional[int] = None
    ac_number: Optional[int] = None
    ac_name: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    booth_name: Optional[str] = None
    booth_address: Optional[str] = None
    mandal: Optional[str] = None
    total_voters: Optional[int] = None
    male_voters: Optional[int] = None
    female_voters: Optional[int] = None


class ExtractedVoter(BaseModel):
    serial_number: Optional[int] = None
    ec_voter_id: Optional[str] = None      # EPIC number e.g. SWO5869530
    name: Optional[str] = None
    father_or_husband_name: Optional[str] = None
    house_no: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None           # M / F / O raw from OCR
    address: Optional[str] = None          # free text address if present


class ParsedPage(BaseModel):
    page_number: int
    header: Optional[PageHeader] = None
    voters: list[ExtractedVoter] = []
    raw_text: str = ""
    is_header_page: bool = False


class ParsedDocument(BaseModel):
    source_file: str
    total_pages: int
    header: Optional[PageHeader] = None
    voters: list[ExtractedVoter] = []
    parse_errors: list[str] = []


class NormalizedVoter(BaseModel):
    ec_voter_id: str
    serial_number: Optional[int] = None
    name: str
    father_or_husband_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None           # M / F / O
    address: Optional[str] = None


class PipelineResult(BaseModel):
    file_name: str
    status: str                            # completed | failed | partial
    inserted: int = 0
    skipped: int = 0
    invalid: int = 0
    errors: list[str] = []
    booth_name: Optional[str] = None
    part_number: Optional[int] = None
