# Data quality report

_Generated from the files in data/processed/ when the dataset was built (2026-09-26)._

## 1. Coverage

Source documents: 211 official filings (166 Quarterly Results, 42 Annual Report, 3 Audited Financial Statements).

| company | basis | annual rows | years | quarterly rows | quarters |
|---|---|---|---|---|---|
| Asian Paints | Standalone | 12 | FY2015-FY2026 | 48 | FY2015 Q1 - FY2026 Q4 |
| Asian Paints | Consolidated | 12 | FY2015-FY2026 | 48 | FY2015 Q1 - FY2026 Q4 |
| Berger Paints | Standalone | 12 | FY2015-FY2026 | 48 | FY2015 Q1 - FY2026 Q4 |
| Berger Paints | Consolidated | 12 | FY2015-FY2026 | 47 | FY2015 Q1 - FY2026 Q4 |
| Kansai Nerolac | Standalone | 12 | FY2015-FY2026 | 48 | FY2015 Q1 - FY2026 Q4 |
| Kansai Nerolac | Consolidated | 12 | FY2015-FY2026 | 32 | FY2019 Q1 - FY2026 Q4 |
| Indigo Paints | Standalone | 9 | FY2018-FY2026 | 25 | FY2020 Q4 - FY2026 Q4 |
| Indigo Paints | Consolidated | 4 | FY2023-FY2026 | 16 | FY2023 Q1 - FY2026 Q4 |

Periods with no published figures are not written. They are Indigo Paints before its listing (annual statements start FY2018, quarterly results Q4 FY2020) and consolidated statements that were not published (consolidated quarterly results were optional before FY2020; Indigo had no subsidiary before FY2024).

## 2. Validation checks

| check | result | flagged rows | what is checked |
|---|---|---|---|
| duplicate_periods | PASS | 0 | no duplicate company + basis + period in any file |
| units | PASS | 0 | units are INR crore / INR per share; annual revenue within 10-100,000 crore; four quarters add up to 90-110% of annual revenue (catches lakh/crore or period mix-ups) |
| impossible_values | PASS | 0 | revenue, assets > 0; cash, debt, capex >= 0; material cost, EBITDA, PAT <= revenue; equity, cash, debt <= total assets |
| pnl_identity | PASS | 0 | revenue - material cost >= EBITDA (material cost and EBITDA are consistent) |
| feature_recalculation | PASS | 0 | every growth rate, margin, margin change and ratio recomputed independently from the reported files |
| balance_sheet | PASS | 0 | net debt = debt - cash; FCF = OCF - capex; total assets = equity + liabilities (checked on the statement during extraction) |
| source_traceability | PASS | 0 | every reported value has a source document, page and URL; every document is in the document index |
| quarters_vs_annual | WARN | 4 | Q1+Q2+Q3+Q4 within 1% of the annual figure (differences = restatements in the Q4 filing; quarters are kept as first reported) |
| standalone_vs_consolidated | PASS | 0 | consolidated revenue >= standalone revenue |
| eps_sign | PASS | 0 | EPS has the same sign as PAT |
| share_count_change | INFO | 4 | PAT / EPS (implied share count) changes by more than 3% year on year: bonus issue or split, EPS not comparable across the change |
| large_moves | INFO | 25 | revenue growth above +/-40% (review aid; most are COVID base effects) |

## 3. Missing values

Annual (`annual_reported.csv`):

| column | standalone missing | consolidated missing |
|---|---|---|
| revenue | 1 / 45 (2%) | 0 / 40 (0%) |
| raw_material_cost | 1 / 45 (2%) | 0 / 40 (0%) |
| ebitda | 2 / 45 (4%) | 0 / 40 (0%) |
| depreciation | 1 / 45 (2%) | 0 / 40 (0%) |
| exceptional_items | 7 / 45 (16%) | 14 / 40 (35%) |
| pat | 0 / 45 (0%) | 0 / 40 (0%) |
| total_assets | 1 / 45 (2%) | 1 / 40 (2%) |
| net_worth | 3 / 45 (7%) | 1 / 40 (2%) |
| total_debt | 3 / 45 (7%) | 3 / 40 (8%) |
| cash | 3 / 45 (7%) | 3 / 40 (8%) |
| operating_cash_flow | 4 / 45 (9%) | 4 / 40 (10%) |
| capex | 4 / 45 (9%) | 3 / 40 (8%) |
| eps_basic | 2 / 45 (4%) | 0 / 40 (0%) |

Quarterly (`quarterly_reported.csv`; balance sheet and cash flow are annual only):

| column | standalone missing | consolidated missing |
|---|---|---|
| revenue | 0 / 169 (0%) | 1 / 143 (1%) |
| raw_material_cost | 1 / 169 (1%) | 4 / 143 (3%) |
| ebitda | 1 / 169 (1%) | 0 / 143 (0%) |
| depreciation | 1 / 169 (1%) | 0 / 143 (0%) |
| exceptional_items | 55 / 169 (33%) | 76 / 143 (53%) |
| pat | 0 / 169 (0%) | 0 / 143 (0%) |
| eps_basic | 3 / 169 (2%) | 4 / 143 (3%) |

Why values are missing: the line was not published (e.g. no cash-flow statement in older quarterly filings), the filing is an unreadable scan (Indigo Paints FY2018 audited statements), or the candidate figures could not be verified and were left out rather than guessed.

## 4. Flagged rows

**quarters_vs_annual** (WARN, 4 rows)

| company | basis | financial_year | quarter | metric | value | expected | detail |
|---|---|---|---|---|---|---|---|
| Asian Paints | Consolidated | FY2017 | FY | ebitda | 2,986.42 | 3,017.39 | sum of quarters differs by +1.04% |
| Berger Paints | Consolidated | FY2019 | FY | ebitda | 881.57 | 893.92 | sum of quarters differs by +1.40% |
| Berger Paints | Standalone | FY2019 | FY | ebitda | 810.19 | 850.59 | sum of quarters differs by +4.99% |
| Berger Paints | Standalone | FY2018 | FY | pat | 431.84 | 438.65 | sum of quarters differs by +1.58% |

**share_count_change** (INFO, 4 rows)

| company | basis | financial_year | quarter | metric | value | expected | detail |
|---|---|---|---|---|---|---|---|
| Berger Paints | Standalone | FY2016 | FY | eps_basic | 3.67 |  | implied shares 69.28 -> 96.69 crore |
| Berger Paints | Standalone | FY2024 | FY | eps_basic | 8.71 |  | implied shares 97.11 -> 116.54 crore |
| Indigo Paints | Standalone | FY2022 | FY | eps_basic | 17.67 |  | implied shares 4.56 -> 4.76 crore |
| Kansai Nerolac | Standalone | FY2024 | FY | eps_basic | 14.63 |  | implied shares 53.87 -> 80.85 crore |

**large_moves** (INFO, 25 rows)

| company | basis | financial_year | quarter | metric | value | expected | detail |
|---|---|---|---|---|---|---|---|
| Asian Paints | Standalone | FY2021 | Q1 | revenue_growth | -44.14 |  | review aid |
| Asian Paints | Standalone | FY2021 | Q4 | revenue_growth | 46.19 |  | review aid |
| Asian Paints | Standalone | FY2022 | Q1 | revenue_growth | 95.62 |  | review aid |
| Asian Paints | Standalone | FY2023 | Q1 | revenue_growth | 58.51 |  | review aid |
| Asian Paints | Consolidated | FY2021 | Q1 | revenue_growth | -43.04 |  | review aid |
| Asian Paints | Consolidated | FY2021 | Q4 | revenue_growth | 43.49 |  | review aid |
| Asian Paints | Consolidated | FY2022 | Q1 | revenue_growth | 91.11 |  | review aid |
| Asian Paints | Consolidated | FY2023 | Q1 | revenue_growth | 54.10 |  | review aid |
| Berger Paints | Standalone | FY2021 | Q1 | revenue_growth | -47.88 |  | review aid |
| Berger Paints | Standalone | FY2021 | Q4 | revenue_growth | 52.96 |  | review aid |
| Berger Paints | Standalone | FY2022 | Q1 | revenue_growth | 96.00 |  | review aid |
| Berger Paints | Standalone | FY2023 | Q1 | revenue_growth | 53.70 |  | review aid |
| Berger Paints | Consolidated | FY2021 | Q1 | revenue_growth | -45.78 |  | review aid |
| Berger Paints | Consolidated | FY2021 | Q4 | revenue_growth | 49.54 |  | review aid |
| Berger Paints | Consolidated | FY2022 | Q1 | revenue_growth | 93.23 |  | review aid |
| Berger Paints | Consolidated | FY2023 | Q1 | revenue_growth | 53.45 |  | review aid |
| Kansai Nerolac | Standalone | FY2021 | Q1 | revenue_growth | -59.13 |  | review aid |
| Kansai Nerolac | Standalone | FY2022 | Q1 | revenue_growth | 117.57 |  | review aid |
| Kansai Nerolac | Standalone | FY2023 | Q1 | revenue_growth | 49.45 |  | review aid |
| Kansai Nerolac | Consolidated | FY2021 | Q1 | revenue_growth | -58.58 |  | review aid |
| Kansai Nerolac | Consolidated | FY2022 | Q1 | revenue_growth | 119.55 |  | review aid |
| Kansai Nerolac | Consolidated | FY2023 | Q1 | revenue_growth | 46.24 |  | review aid |
| Indigo Paints | Standalone | FY2021 | Q4 | revenue_growth | 40.84 |  | review aid |
| Indigo Paints | Standalone | FY2022 | Q1 | revenue_growth | 49.19 |  | review aid |
| Indigo Paints | Standalone | FY2023 | Q1 | revenue_growth | 43.56 |  | review aid |

## 5. How the values were verified

* Each statement column is checked with accounting identities (total income, sum of expenses, profit before tax, tax, PAT, EBITDA computed two ways, assets = equity + liabilities).
* The same period appears in several filings (current, comparative and year-to-date columns); a value is accepted when the identities hold or independent filings agree, and annual/YTD figures must equal the sum of their quarters.
* Verification status of the 3082 reported values: VERIFIED 3032, SINGLE_SOURCE 50.
* Extraction method: ocr 2760, text 322 (scanned filings are read with OCR; values from them pass the same checks).

* Values are **as first reported** in the period's own filing. 1362 cases where a later filing prints a different verified figure for the same period were found (Ind AS transition, reclassifications, mergers); the dataset keeps the first-reported figure. Exception: in 195 cases the own filing's figure could not be verified and two or more later filings agree on another figure; the later figure is used and the rejected one is quoted in `notes` (mostly OCR misreads; a few are genuine restatements).

## 6. Comparability breaks (`comparability_flags`)

| flag | periods | effect |
|---|---|---|
| accounting_standard = Indian GAAP | FY2015-FY2016 (Indigo to FY2019) | older framework; Ind AS revenue is net of some discounts that were expenses under Indian GAAP |
| IND_AS_TRANSITION | FY2017 | growth vs FY2016 compares Ind AS with Indian GAAP |
| PRE_GST_EXCISE | FY2017, Q1 FY2018 | revenue printed gross of excise; the dataset subtracts excise duty |
| IND_AS_116_LEASES | FY2020 | leases capitalised: EBITDA up, D&A and finance costs up vs FY2019 |
| TAX_RATE_CHANGE | Q2 FY2020, FY2020 | deferred-tax re-measurement lowers tax |
| COVID_LOCKDOWN | Q4 FY2020, Q1 FY2021 | lockdown periods; growth in FY2022 Q1 is a base effect |
| IPO_FEB_2021 | Indigo Q4 FY2021 | IPO proceeds raise cash and equity |

EPS is as printed: bonus issues change the share count (see `share_count_change` above), so compare EPS only within periods with the same share base.
