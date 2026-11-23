// frontend/lib/types.ts — mirrors backend/nutriparse/schemas.py (schema v1.0)
export type AllergenStatus = "contains" | "traces" | "absent" | "unknown";

export type AllergenBasis =
  | "ingredients"
  | "statement"
  | "table_flags"
  | "checkbox"
  | "grid"
  | "layout_table"
  | "global_statement"
  | "implicit_declaration"
  | "not_food";

export interface AllergenEntry {
  status: AllergenStatus;
  evidence: string | null;
  basis: AllergenBasis | null;
  page: number | null;
  conflict: boolean;
}

export type NutrientValue = number | string | null;

export interface NutritionPer100g {
  energy_kJ: NutrientValue;
  energy_kcal: NutrientValue;
  fat_g: NutrientValue;
  saturated_fat_g: NutrientValue;
  carbohydrate_g: NutrientValue;
  sugars_g: NutrientValue;
  protein_g: NutrientValue;
  salt_g: NutrientValue;
  sodium_mg: NutrientValue;
  collagen_g?: NutrientValue;
  water_g?: NutrientValue;
}

export interface Diagnostics {
  warnings: string[];
  pages_scanned: number;
  raw_text_preview: string;
  nutrition_evidence: Record<string, string | null>;
  serving_basis_evidence: string | null;
  notes?: string[] | null;
  timings_ms: Record<string, number>;
}

export interface Meta {
  schema_version: string;
  engine_version: string;
  product_name: string | null;
  source_file: string | null;
  extraction_mode: "text" | "ocr" | "mixed";
  pages: number;
  ocr_pages: number[];
  languages: string[];
  serving_basis: string;
  serving_basis_inferred: boolean;
  /** Share of the 14 EU allergens with a status backed by evidence (0..1). */
  allergen_coverage: number;
  /** True when an allergen is unknown or in conflict. */
  needs_review: boolean;
}

/** The 14 allergens of Regulation (EU) No 1169/2011, Annex II. */
export const ALLERGEN_KEYS = [
  "gluten", "crustaceans", "egg", "fish", "peanut", "soy", "milk",
  "tree_nuts", "celery", "mustard", "sesame", "sulphites", "lupin", "molluscs",
] as const;
export type AllergenKey = (typeof ALLERGEN_KEYS)[number];

export interface ApiResponse {
  meta: Meta;
  allergens: Record<AllergenKey, AllergenEntry>;
  nutrition_per_100g: NutritionPer100g;
  diagnostics: Diagnostics;
  extras?: Record<string, unknown>;
}
