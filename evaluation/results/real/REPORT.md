# Real-world set (private PDFs)

Documents: 10 (each scored on 14 allergens). 95% intervals: document bootstrap, 1000 resamples.

## Headline

| System | Accuracy | Unsafe miss rate | False absent rate | Positive recall | Abstention |
|---|---|---|---|---|---|
| v1 | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 0.0% | 100.0% | 0.0% |
| legacy | 62.9% [53.6, 69.3] | 44.4% [0.0, 100.0] | 60.9% | 55.6% | 28.6% |

## By input quality

| Group | n | v1 accuracy | v1 unsafe miss | v1 abstention | legacy accuracy | legacy unsafe miss |
|---|---|---|---|---|---|---|
| digital | 6 | 100.0% | 0.0% | 0.0% | 67.9% | 16.7% |
| scanned | 4 | 100.0% | 0.0% | 0.0% | 55.4% | 100.0% |

## By declaration format

| Group | n | v1 accuracy | v1 unsafe miss | v1 abstention | legacy accuracy | legacy unsafe miss |
|---|---|---|---|---|---|---|
| declaration (fish only) | 1 | 100.0% | 0.0% | 0.0% | 71.4% | 0.0% |
| global_statement | 2 | 100.0% | n/a | 0.0% | 71.4% | n/a |
| no allergen declaration | 1 | 100.0% | n/a | n/a | 28.6% | n/a |
| statement + 2-column table | 1 | 100.0% | 0.0% | 0.0% | 64.3% | 100.0% |
| statement + X-mark table | 1 | 100.0% | 0.0% | 0.0% | 57.1% | 100.0% |
| statement + grid | 1 | 100.0% | 0.0% | 0.0% | 57.1% | 0.0% |
| table I/N/X | 1 | 100.0% | n/a | 0.0% | 71.4% | n/a |
| table Y/N | 1 | 100.0% | n/a | 0.0% | 71.4% | n/a |
| tick-box table | 1 | 100.0% | 0.0% | 0.0% | 64.3% | 100.0% |

## Per allergen (v1)

| Allergen | Accuracy | Unsafe miss | Positive recall | Abstention |
|---|---|---|---|---|
| gluten | 100.0% | 0.0% | 100.0% | 0.0% |
| crustaceans | 100.0% | n/a | n/a | 0.0% |
| egg | 100.0% | 0.0% | 100.0% | 0.0% |
| fish | 100.0% | 0.0% | 100.0% | 0.0% |
| peanut | 100.0% | n/a | n/a | 0.0% |
| soy | 100.0% | 0.0% | 100.0% | 0.0% |
| milk | 100.0% | 0.0% | 100.0% | 0.0% |
| tree_nuts | 100.0% | n/a | n/a | 0.0% |
| celery | 100.0% | 0.0% | 100.0% | 0.0% |
| mustard | 100.0% | n/a | n/a | 0.0% |
| sesame | 100.0% | n/a | n/a | 0.0% |
| sulphites | 100.0% | n/a | n/a | 0.0% |
| lupin | 100.0% | n/a | n/a | 0.0% |
| molluscs | 100.0% | n/a | n/a | 0.0% |

## Confusion matrix (v1, all)

| gold \ predicted | contains | traces | absent | unknown |
|---|---|---|---|---|
| contains | 6 | 0 | 0 | 0 |
| traces | 0 | 3 | 0 | 0 |
| absent | 0 | 0 | 117 | 0 |
| unknown | 0 | 0 | 0 | 14 |

## Latency (median seconds per document, v1)

- text: 0.66
- ocr: 16.48
- all_median: 1.06
