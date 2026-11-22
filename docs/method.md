# Method and evaluation

This document describes how NutriParse decides the allergen status of a food
product from its specification sheet, how that decision was evaluated, and
what the results do and do not show.

## 1. Problem

Retailers and distributors receive specification sheets (PDF) from suppliers
and must check the 14 allergens of Regulation (EU) No 1169/2011, Annex II,
before a product is listed. Sheets differ in language (here Hungarian,
English, Polish), in layout, and in quality: some are digital, many are
scans.

For each allergen the system returns one of four states:

| status | meaning |
|---|---|
| `contains` | named as an ingredient or declared as contained |
| `traces` | declared as "may contain" or cross-contamination |
| `absent` | the sheet explicitly declares the product free of it |
| `unknown` | the sheet gives no evidence either way |

### Cost asymmetry

The errors are not equally bad. Reporting an allergen as `absent` when the
product contains it can reach a consumer with an allergy. Reporting
`contains` or `unknown` when it is absent costs a few minutes of manual
checking. The design and the evaluation are built around this asymmetry.

The previous version (v0.3) reported `absent` for every allergen it did not
find. On a plain yoghurt sheet it returned "milk: absent".

## 2. Design

```
PDF ─► pages ─► words + boxes ─► evidence rules ─► fusion ─► status + evidence + page
        │            ▲
        │  scan? ────┘ Tesseract (hun+pol+eng), per page
        └─► page image ─► visual cell readers (tick boxes, table flags)
```

**Unified document model.** The PDF text layer and OCR both produce words
with bounding boxes. Only pages with almost no text are sent to OCR, so mixed
documents (digital pages plus scanned annexes) are handled page by page.

**Evidence rules.** Each rule recognises one way real sheets declare
allergens (all were observed in the real set, section 3.1):

| rule | example |
|---|---|
| ingredients | "Összetevők: búzaliszt, tyúktojás, ivóvíz" |
| statement | "Nyomokban tejet, zellert, szóját tartalmazhat." |
| global statement | "ALLERGÉN ANYAGOKAT NEM TARTALMAZ." |
| table flags | "Tej és származékai I N" (I/N, Y/N, two columns) |
| tick boxes | "mentes ☐ tartalmaz ☒ előfordulhat ☐" |
| +/- grid | "01 + milk protein   15 - Cocoa" |
| layout table | X marks under Igen / Nem / Kereszt columns |
| implicit declaration | "Allergén információ: hal." (others not listed) |

A multilingual lexicon maps words to the 14 allergens. It handles
Hungarian case endings (tej → tejet) and known traps: cocoa butter,
coconut milk, "kén-dioxid" (contains "dio", nut), a "Tejüzem" (dairy plant)
in a page header.

**Visual cell readers.** General OCR reads paragraphs well but drops what
matters in tables: a lone "N" in a cell, or which box is ticked. Two small
readers look at a known region of the page image, located from the OCR word
boxes:

* *tick boxes*: measures the ink inside the box right of each status label
  (inside the outline, with an adaptive threshold) and accepts the box with
  clearly more ink than the others in the same row;
* *row tails*: re-reads the right end of each allergen row with single-line
  OCR. A row is only accepted when the number of flags read equals the
  number of flag columns in the table, because reading "N" from "N I" would
  turn `traces` into `absent`.

The tick-box reader also runs on digital pages, where boxes are often drawn
as vector shapes and leave no text.

**Fusion (safety first).**

1. `unknown` is the default. Nothing becomes `absent` without evidence.
2. Direct evidence (ingredients, statements, tables, ticks) beats
   document-wide statements. Among direct evidence the most severe status
   wins: contains > traces > absent.
3. When direct sources disagree, the severe status is kept and the allergen
   is flagged as a conflict for human review.
4. A global "no allergens" statement, and then an allergen declaration that
   lists other allergens, only fill gaps.

Every non-`unknown` result carries the text that supports it and its page.

## 3. Data

### 3.1 Real-world set (development set)

Eleven supplier specification sheets (Hungarian and Polish suppliers): six
digital, four scanned, one non-food (excluded from allergen scoring). They
declare allergens in eight different ways, and one has no allergen
declaration at all. The sheets are confidential and are not in
the repository; `evaluation/real_labels.json` holds the gold labels keyed by
the SHA-256 of each PDF, so anyone with the same files can reproduce the
numbers. Scanned pages were labelled by looking at the page image.

This set was used to design the rules. Its results are therefore optimistic
and are reported only as a sanity check.

### 3.2 Synthetic benchmark (development and test splits)

`evaluation/synth/generate.py` writes one-page A4 sheets with a known ground
truth: 16 product archetypes, 3 languages, 10 declaration formats, random
"may contain" lists, distractor sentences ("free from foreign odours"),
random layout offsets and font sizes, and a nutrition panel. A share of the
documents is also "scanned": rendered at 200 or 150 dpi, rotated, blurred,
noised and JPEG-compressed (`scan_good`, `scan_poor`).

The vocabulary of the generator was written separately from the engine's
lexicon. Protocol:

* **dev split** (seed 1, 60 documents, 112 PDFs): used for error analysis.
  Fixes made from it: multi-word status labels ("nie zawiera", "may
  contain"), Polish grid legend, fish species names, Polish nutrition
  labels, tick-box ink measurement, the column-count check above;
* **test split** (seed 2, 120 documents, 212 PDFs): run once the engine was
  frozen. All headline numbers below come from it.

### 3.3 Label guide

* `contains`: in the ingredient list, or declared as contained.
* `traces`: declared as may contain or cross-contamination.
* `absent`: declared free (table, global statement), or not listed in an
  explicit allergen declaration.
* `unknown`: the sheet says nothing (for example, an ingredient list with no
  allergen section: an allergen not in the list may still be present as
  traces).

## 4. Metrics

Computed over all (document, allergen) pairs.

| metric | definition | why |
|---|---|---|
| accuracy | predicted status = gold status | overall quality |
| **unsafe miss rate** | P(pred = absent \| gold ∈ {contains, traces}) | the error that can harm a consumer |
| false absent rate | P(pred = absent \| gold ≠ absent) | any unjustified "absent" |
| positive recall | P(pred ∈ {contains, traces} \| gold ∈ {contains, traces}) | are allergens found |
| abstention rate | P(pred = unknown \| gold ≠ unknown) | how much is left to a human |

95% intervals come from a bootstrap over documents (1000 resamples),
because the 14 decisions of one document are correlated.

The baseline is the v0.3 parser run on **the same extracted text**, so the
comparison isolates the decision logic, not the OCR.

## 5. Results (test split, 212 PDFs)

| system | accuracy | unsafe miss rate | false absent | positive recall | abstention |
|---|---|---|---|---|---|
| **v1** | **92.5%** [89.5, 95.3] | **0.0%** [0.0, 0.0] | 0.0% | 97.4% | 7.6% |
| v0.3 | 53.9% [51.0, 56.6] | 51.0% [44.5, 57.5] | 59.4% | 23.2% | 28.4% |

By input quality (v1):

| input | accuracy | unsafe miss | abstention |
|---|---|---|---|
| digital | 99.7% | 0.0% | 0.3% |
| scan, good | 90.2% | 0.0% | 9.4% |
| scan, poor | 76.2% | 0.0% | 24.8% |

As the scan gets worse, accuracy falls but the errors stay on the safe side:
the system says `unknown` instead of guessing. Of the 2,359 truly absent
decisions, 12 were reported as `contains` (0.5%) and 196 as `unknown`.

**Ablation: visual cell readers.**

| input | without readers | with readers |
|---|---|---|
| digital | 91.1% | 99.7% |
| scan, good | 61.2% | 90.2% |
| scan, poor | 61.0% | 76.2% |

The unsafe miss rate is 0.0% in both configurations: the readers add
coverage without adding risk.

**Hardest formats.** X-mark tables on scans (70.6%, mostly abstentions:
Tesseract rarely finds the column headings) and I/N/X tables (80.5%).

**Nutrition** (value within 1% or 0.05 g): 100% on digital sheets for every
field except salt (95.8%); 63–100% on scans depending on the field.

**Real-world development set** (10 food sheets, 140 decisions): v1 140/140
correct; v0.3 62.9% accuracy and 44.4% unsafe miss rate. Optimistic, see
3.1.

**Latency** (2 vCPU): median 0.03 s per digital PDF, 1.7 s per scanned page.

## 6. Limitations

* The synthetic generator and the engine were written by the same author.
  They share assumptions about what sheets look like, so synthetic results
  are an upper bound for unseen layouts. A larger, independently annotated
  real set is the most important next step.
* The real set is small (10 food sheets) and was used for development.
* Only Hungarian, English and Polish are covered.
* The nutrition parser is the v0.3 parser with small fixes; it is evaluated
  but was not redesigned.
* "May contain" wording that implies no allergen name (for example "made in
  a factory that handles nuts" with a brand-specific term) is not covered.

## 7. Next steps

1. Annotate 50+ real sheets with a second annotator and report agreement
   (Cohen's kappa).
2. Use a layout model or a small vision-language model only as a fallback
   for rows that stay `unknown`, and measure whether it lowers abstention
   without raising the unsafe miss rate.
3. Calibrate a per-allergen confidence score on the annotated set
   (reliability diagram), instead of a fixed formula.
