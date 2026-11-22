"""Public API contract (response schema v1.0)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

AllergenStatus = Literal["contains", "traces", "absent", "unknown"]
Basis = Literal[
    "ingredients", "statement", "table_flags", "checkbox", "grid", "layout_table",
    "global_statement", "implicit_declaration", "not_food",
]


class AllergenResult(BaseModel):
    status: AllergenStatus
    evidence: str | None = Field(None, description="Text from the document that supports the status")
    basis: Basis | None = Field(None, description="Which rule produced the status")
    page: int | None = None
    conflict: bool = Field(False, description="Sources in the document disagree; needs human review")


class Meta(BaseModel):
    schema_version: str
    engine_version: str
    product_name: str | None
    source_file: str | None
    extraction_mode: Literal["text", "ocr", "mixed"]
    pages: int
    ocr_pages: list[int]
    languages: list[str]
    serving_basis: str
    serving_basis_inferred: bool
    allergen_coverage: float = Field(
        description="Share of the 14 EU allergens with a status backed by evidence (0..1)"
    )
    needs_review: bool = Field(description="True when an allergen is unknown or in conflict")


class Diagnostics(BaseModel):
    warnings: list[str]
    pages_scanned: int
    raw_text_preview: str
    nutrition_evidence: dict[str, str | None]
    serving_basis_evidence: str | None
    notes: list[str] | None = None
    timings_ms: dict[str, float]


class ExtractionResult(BaseModel):
    meta: Meta
    allergens: dict[str, AllergenResult]
    nutrition_per_100g: dict[str, float | str | None]
    extras: dict[str, dict]
    diagnostics: Diagnostics


class ErrorResponse(BaseModel):
    detail: str
