# Synthetic benchmark

Documents: 212 (each scored on 14 allergens). 95% intervals: document bootstrap, 1000 resamples.

## Headline

| System | Accuracy | Unsafe miss rate | False absent rate | Positive recall | Abstention |
|---|---|---|---|---|---|
| v1 | 92.5% [89.5, 95.3] | 0.0% [0.0, 0.0] | 0.0% | 97.4% | 7.6% |
| legacy | 53.9% [51.0, 56.6] | 51.0% [44.5, 57.5] | 59.4% | 23.2% | 28.4% |

## By input quality

| Group | n | v1 accuracy | v1 unsafe miss | v1 abstention | legacy accuracy | legacy unsafe miss |
|---|---|---|---|---|---|---|
| digital | 120 | 99.7% | 0.0% | 0.3% | 52.4% | 49.8% |
| scan_good | 46 | 90.2% | 0.0% | 9.4% | 56.5% | 53.5% |
| scan_poor | 46 | 76.2% | 0.0% | 24.8% | 55.3% | 52.1% |

## By declaration format

| Group | n | v1 accuracy | v1 unsafe miss | v1 abstention | legacy accuracy | legacy unsafe miss |
|---|---|---|---|---|---|---|
| checkbox_glyph | 18 | 94.8% | 0.0% | 4.8% | 36.9% | 53.8% |
| checkbox_vector | 18 | 93.7% | 0.0% | 3.2% | 43.6% | 50.0% |
| global | 22 | 100.0% | n/a | 0.0% | 71.4% | n/a |
| grid | 26 | 98.1% | 0.0% | 0.8% | 61.5% | 1.8% |
| none | 22 | 99.4% | 0.0% | 5.0% | 26.0% | 80.0% |
| statement | 22 | 100.0% | 0.0% | 0.0% | 62.3% | 56.5% |
| table_flags | 22 | 96.4% | 0.0% | 3.2% | 63.0% | 78.3% |
| table_inx | 26 | 80.5% | 0.0% | 19.2% | 53.6% | 57.9% |
| table_two_col | 18 | 89.3% | 0.0% | 10.7% | 58.7% | 47.1% |
| xmark | 18 | 70.6% | 0.0% | 29.0% | 57.5% | 78.3% |

## Per allergen (v1)

| Allergen | Accuracy | Unsafe miss | Positive recall | Abstention |
|---|---|---|---|---|
| gluten | 90.1% | 0.0% | 100.0% | 9.2% |
| crustaceans | 94.3% | 0.0% | 100.0% | 5.7% |
| egg | 92.5% | 0.0% | 92.9% | 7.9% |
| fish | 92.9% | 0.0% | 94.1% | 7.7% |
| peanut | 92.5% | 0.0% | 92.0% | 7.2% |
| soy | 91.0% | 0.0% | 90.5% | 9.3% |
| milk | 88.2% | 0.0% | 100.0% | 11.6% |
| tree_nuts | 92.0% | 0.0% | 100.0% | 8.2% |
| celery | 94.3% | 0.0% | 100.0% | 6.3% |
| mustard | 92.9% | 0.0% | 100.0% | 7.4% |
| sesame | 93.9% | 0.0% | 100.0% | 5.8% |
| sulphites | 92.9% | 0.0% | 82.3% | 7.4% |
| lupin | 92.9% | 0.0% | 100.0% | 7.7% |
| molluscs | 95.3% | 0.0% | 100.0% | 4.7% |

## Confusion matrix (v1, all)

| gold \ predicted | contains | traces | absent | unknown |
|---|---|---|---|---|
| contains | 242 | 4 | 0 | 4 |
| traces | 0 | 86 | 0 | 5 |
| absent | 12 | 0 | 2151 | 196 |
| unknown | 0 | 0 | 0 | 268 |

## Nutrition (share of values within 1% or 0.05 g)

| Nutrient | digital | scan_good | scan_poor |
|---|---|---|---|
| energy_kJ | 100.0% | 100.0% | 100.0% |
| energy_kcal | 100.0% | 100.0% | 100.0% |
| fat_g | 100.0% | 87.0% | 84.8% |
| saturated_fat_g | 100.0% | 76.1% | 63.0% |
| carbohydrate_g | 100.0% | 76.1% | 87.0% |
| sugars_g | 100.0% | 63.0% | 76.1% |
| protein_g | 100.0% | 71.7% | 73.9% |
| salt_g | 95.8% | 87.0% | 91.3% |

## Latency (median seconds per document, v1)

- text: 0.03
- ocr: 1.72
- all_median: 0.07

## v1 errors (first 40)

```
s2_0003 scan_good table_inx        en soy          gold=absent   pred=unknown
s2_0003 scan_poor table_inx        en gluten       gold=absent   pred=unknown
s2_0003 scan_poor table_inx        en crustaceans  gold=absent   pred=unknown
s2_0003 scan_poor table_inx        en egg          gold=absent   pred=unknown
s2_0003 scan_poor table_inx        en fish         gold=absent   pred=unknown
s2_0003 scan_poor table_inx        en soy          gold=absent   pred=unknown
s2_0003 scan_poor table_inx        en milk         gold=absent   pred=unknown
s2_0003 scan_poor table_inx        en tree_nuts    gold=absent   pred=unknown
s2_0003 scan_poor table_inx        en celery       gold=absent   pred=unknown
s2_0003 scan_poor table_inx        en mustard      gold=absent   pred=unknown
s2_0003 scan_poor table_inx        en sesame       gold=absent   pred=unknown
s2_0003 scan_poor table_inx        en sulphites    gold=traces   pred=unknown
s2_0003 scan_poor table_inx        en lupin        gold=absent   pred=unknown
s2_0003 scan_poor table_inx        en molluscs     gold=absent   pred=unknown
s2_0004 scan_good table_two_col    pl egg          gold=absent   pred=unknown
s2_0004 scan_good table_two_col    pl soy          gold=absent   pred=unknown
s2_0004 scan_good table_two_col    pl tree_nuts    gold=absent   pred=unknown
s2_0004 scan_good table_two_col    pl sulphites    gold=contains pred=unknown
s2_0004 scan_poor table_two_col    pl milk         gold=absent   pred=unknown
s2_0004 scan_poor table_two_col    pl tree_nuts    gold=absent   pred=unknown
s2_0004 scan_poor table_two_col    pl sulphites    gold=contains pred=unknown
s2_0004 scan_poor table_two_col    pl lupin        gold=absent   pred=unknown
s2_0005 scan_poor checkbox_glyph   en gluten       gold=absent   pred=contains
s2_0007 scan_good xmark            hu crustaceans  gold=absent   pred=unknown
s2_0007 scan_good xmark            hu egg          gold=absent   pred=unknown
s2_0007 scan_good xmark            hu fish         gold=absent   pred=unknown
s2_0007 scan_good xmark            hu peanut       gold=absent   pred=unknown
s2_0007 scan_good xmark            hu soy          gold=absent   pred=unknown
s2_0007 scan_good xmark            hu sulphites    gold=absent   pred=unknown
s2_0007 scan_good xmark            hu lupin        gold=absent   pred=unknown
s2_0007 scan_poor xmark            hu crustaceans  gold=absent   pred=unknown
s2_0007 scan_poor xmark            hu egg          gold=absent   pred=unknown
s2_0007 scan_poor xmark            hu fish         gold=absent   pred=unknown
s2_0007 scan_poor xmark            hu peanut       gold=absent   pred=unknown
s2_0007 scan_poor xmark            hu soy          gold=absent   pred=unknown
s2_0007 scan_poor xmark            hu milk         gold=absent   pred=unknown
s2_0007 scan_poor xmark            hu tree_nuts    gold=absent   pred=unknown
s2_0007 scan_poor xmark            hu celery       gold=absent   pred=unknown
s2_0007 scan_poor xmark            hu mustard      gold=absent   pred=unknown
s2_0007 scan_poor xmark            hu sulphites    gold=absent   pred=unknown
```
