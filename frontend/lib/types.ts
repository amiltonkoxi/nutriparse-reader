// frontend/lib/types.ts
export type AllergenStatus = "contains" | "traces" | "absent" | "unknown";

export interface AllergenEntry {
  status: AllergenStatus;
  evidence: string | null;
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
  pages_scanned?: number | null;
  raw_text_preview?: string | null;
  nutrition_evidence?: Record<string, string | null>;
  notes?: string[] | null;
}

export interface Meta {
  product_name: string | null;
  source_file: string;
  extraction_mode: "text" | "ocr";
  serving_basis: "per 100g" | "unknown";
  languages: string[];
  confidence: number;
}

export interface ApiResponse {
  meta: Meta;
  allergens: {
    gluten: AllergenEntry;
    egg: AllergenEntry;
    crustaceans: AllergenEntry;
    fish: AllergenEntry;
    peanut: AllergenEntry;
    soy: AllergenEntry;
    milk: AllergenEntry;
    tree_nuts: AllergenEntry;
    celery: AllergenEntry;
    mustard: AllergenEntry;
  };
  nutrition_per_100g: NutritionPer100g;
  diagnostics: Diagnostics;
  extras?: Record<string, unknown>;
}
