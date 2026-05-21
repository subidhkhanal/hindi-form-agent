# Train/Val/Test Distribution Comparison

## Top-level metrics

| Metric | Train | Val | Test |
|---|---|---|---|
| N | 2270 | 290 | 290 |
| Avg fields filled | 5.22 | 5.20 | 5.23 |
| Unique states | 31 | 24 | 21 |

## Source composition

| Source | Train | Val | Test |
|---|---|---|---|
| handcrafted_seed | 10 | 0 | 0 |
| hiner | 1600 | 200 | 200 |
| synthetic_dense | 640 | 80 | 80 |
| hardcases | 20 | 10 | 10 |

## Fields-filled distribution

| Fields | Train | Val | Test |
|---|---|---|---|
| 2 | 1578 | 198 | 200 |
| 3 | 22 | 2 | 0 |
| 4 | 2 | 1 | 0 |
| 5 | 6 | 2 | 4 |
| 6 | 9 | 2 | 2 |
| 7 | 5 | 5 | 3 |
| 8 | 1 | 0 | 1 |
| 9 | 2 | 0 | 0 |
| 10 | 2 | 0 | 0 |
| 11 | 42 | 7 | 5 |
| 12 | 130 | 22 | 18 |
| 13 | 232 | 20 | 24 |
| 14 | 200 | 26 | 26 |
| 15 | 4 | 1 | 2 |
| 16 | 33 | 4 | 5 |
| 17 | 2 | 0 | 0 |

## Caste distribution (where present)

| Caste | Train | Val | Test |
|---|---|---|---|
| general | 193 | 22 | 24 |
| obc | 261 | 34 | 31 |
| sc | 91 | 10 | 15 |
| st | 68 | 7 | 8 |

## Religion (top 5 across splits)

| Religion | Train | Val | Test |
|---|---|---|---|
| इस्लाम | 74 | 9 | 5 |
| ईसाई | 28 | 1 | 2 |
| जैन | 7 | 2 | 0 |
| बौद्ध | 0 | 0 | 1 |
| सिख | 21 | 2 | 2 |
| हिंदू | 505 | 66 | 70 |

## Hard-case category coverage (must be 2/1/1 per category)

| Category | Train | Val | Test |
|---|---|---|---|
| approximation | 2 | 1 | 1 |
| conflicting_info | 2 | 1 | 1 |
| implicit_info | 2 | 1 | 1 |
| indirect_self_reference | 2 | 1 | 1 |
| mixed_scripts | 2 | 1 | 1 |
| multiple_persons | 2 | 1 | 1 |
| negation | 2 | 1 | 1 |
| place_name_variant | 2 | 1 | 1 |
| self_correction | 2 | 1 | 1 |
| trailing_info | 2 | 1 | 1 |
