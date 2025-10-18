export type AllergenStatus = "contains" | "traces" | "absent" | "unknown";
export interface AllergenEntry { status: AllergenStatus; evidence: string | null; }
export interface Energy { kJ: number | null; kcal: number | null; }
export interface Nutrition {
  energy: Energy; fat_g: number | null; carbohydrate_g: number | null;
  sugar_g: number | null; protein_g: number | null; salt_g: number | null;
  sodium_g: number | null; notes?: string | null;
}
export interface Extras { saturated_fat_g?: number | null; water_g?: number | null; collagen_g?: number | null; }
export interface Diagnostics { warnings: string[]; pages_scanned?: number | null; raw_text_preview?: string | null; }
export interface Meta {
  product_name: string | null; source_file: string; extraction_mode: "text" | "ocr";
  serving_basis: "per 100g" | "unknown"; languages: string[]; confidence: number;
}
export interface ApiResponse {
  meta: Meta;
  allergens: {
    gluten: AllergenEntry; egg: AllergenEntry; crustaceans: AllergenEntry; fish: AllergenEntry;
    peanut: AllergenEntry; soy: AllergenEntry; milk: AllergenEntry; tree_nuts: AllergenEntry;
    celery: AllergenEntry; mustard: AllergenEntry;
  };
  nutrition: Nutrition; extras?: Extras; diagnostics: Diagnostics;
}
