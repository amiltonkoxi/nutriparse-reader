# Synthetic benchmark

Documents: 212 (each scored on 14 allergens). 95% intervals: document bootstrap, 1000 resamples.

## Headline

| System | Accuracy | Unsafe miss rate | False absent rate | Positive recall | Abstention |
|---|---|---|---|---|---|
| v1 | 78.1% [73.1, 82.8] | 0.0% [0.0, 0.0] | 0.0% | 90.0% | 23.6% |
| legacy | 53.9% [51.0, 56.6] | 51.0% [44.5, 57.5] | 59.4% | 23.2% | 28.4% |

## By input quality

| Group | n | v1 accuracy | v1 unsafe miss | v1 abstention | legacy accuracy | legacy unsafe miss |
|---|---|---|---|---|---|---|
| digital | 120 | 91.1% | 0.0% | 9.8% | 52.4% | 49.8% |
| scan_good | 46 | 61.2% | 0.0% | 41.4% | 56.5% | 53.5% |
| scan_poor | 46 | 61.0% | 0.0% | 41.9% | 55.3% | 52.1% |

## By declaration format

| Group | n | v1 accuracy | v1 unsafe miss | v1 abstention | legacy accuracy | legacy unsafe miss |
|---|---|---|---|---|---|---|
| checkbox_glyph | 18 | 73.0% | 0.0% | 26.6% | 36.9% | 53.8% |
| checkbox_vector | 18 | 14.3% | 0.0% | 82.5% | 43.6% | 50.0% |
| global | 22 | 100.0% | n/a | 0.0% | 71.4% | n/a |
| grid | 26 | 98.1% | 0.0% | 0.8% | 61.5% | 1.8% |
| none | 22 | 99.4% | 0.0% | 5.0% | 26.0% | 80.0% |
| statement | 22 | 100.0% | 0.0% | 0.0% | 62.3% | 56.5% |
| table_flags | 22 | 87.0% | 0.0% | 13.0% | 63.0% | 78.3% |
| table_inx | 26 | 50.0% | 0.0% | 50.0% | 53.6% | 57.9% |
| table_two_col | 18 | 75.4% | 0.0% | 24.6% | 58.7% | 47.1% |
| xmark | 18 | 70.6% | 0.0% | 29.0% | 57.5% | 78.3% |

## Per allergen (v1)

| Allergen | Accuracy | Unsafe miss | Positive recall | Abstention |
|---|---|---|---|---|
| gluten | 81.1% | 0.0% | 98.1% | 18.9% |
| crustaceans | 80.2% | 0.0% | 95.0% | 21.2% |
| egg | 76.4% | 0.0% | 85.7% | 25.8% |
| fish | 76.9% | 0.0% | 76.5% | 25.3% |
| peanut | 76.4% | 0.0% | 92.0% | 25.4% |
| soy | 76.9% | 0.0% | 76.2% | 24.9% |
| milk | 79.2% | 0.0% | 93.6% | 21.7% |
| tree_nuts | 80.7% | 0.0% | 100.0% | 20.6% |
| celery | 77.4% | 0.0% | 94.1% | 25.1% |
| mustard | 76.4% | 0.0% | 88.2% | 25.8% |
| sesame | 77.4% | 0.0% | 90.0% | 24.1% |
| sulphites | 76.4% | 0.0% | 76.5% | 25.8% |
| lupin | 75.9% | 0.0% | 75.0% | 26.3% |
| molluscs | 81.6% | 0.0% | 95.2% | 19.7% |

## Confusion matrix (v1, all)

| gold \ predicted | contains | traces | absent | unknown |
|---|---|---|---|---|
| contains | 239 | 4 | 0 | 7 |
| traces | 0 | 64 | 0 | 27 |
| absent | 10 | 0 | 1746 | 603 |
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
- ocr: 1.67
- all_median: 0.05

## v1 errors (first 40)

```
s2_0003 scan_good table_inx        en gluten       gold=absent   pred=unknown
s2_0003 scan_good table_inx        en crustaceans  gold=absent   pred=unknown
s2_0003 scan_good table_inx        en egg          gold=absent   pred=unknown
s2_0003 scan_good table_inx        en fish         gold=absent   pred=unknown
s2_0003 scan_good table_inx        en soy          gold=absent   pred=unknown
s2_0003 scan_good table_inx        en milk         gold=absent   pred=unknown
s2_0003 scan_good table_inx        en tree_nuts    gold=absent   pred=unknown
s2_0003 scan_good table_inx        en celery       gold=absent   pred=unknown
s2_0003 scan_good table_inx        en mustard      gold=absent   pred=unknown
s2_0003 scan_good table_inx        en sesame       gold=absent   pred=unknown
s2_0003 scan_good table_inx        en sulphites    gold=traces   pred=unknown
s2_0003 scan_good table_inx        en lupin        gold=absent   pred=unknown
s2_0003 scan_good table_inx        en molluscs     gold=absent   pred=unknown
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
s2_0004 scan_good table_two_col    pl crustaceans  gold=absent   pred=unknown
s2_0004 scan_good table_two_col    pl egg          gold=absent   pred=unknown
s2_0004 scan_good table_two_col    pl fish         gold=absent   pred=unknown
s2_0004 scan_good table_two_col    pl peanut       gold=absent   pred=unknown
s2_0004 scan_good table_two_col    pl soy          gold=absent   pred=unknown
s2_0004 scan_good table_two_col    pl milk         gold=absent   pred=unknown
s2_0004 scan_good table_two_col    pl tree_nuts    gold=absent   pred=unknown
s2_0004 scan_good table_two_col    pl celery       gold=absent   pred=unknown
s2_0004 scan_good table_two_col    pl mustard      gold=absent   pred=unknown
s2_0004 scan_good table_two_col    pl sesame       gold=absent   pred=unknown
s2_0004 scan_good table_two_col    pl sulphites    gold=contains pred=unknown
s2_0004 scan_good table_two_col    pl lupin        gold=absent   pred=unknown
s2_0004 scan_good table_two_col    pl molluscs     gold=absent   pred=unknown
s2_0004 scan_poor table_two_col    pl crustaceans  gold=absent   pred=unknown
```
