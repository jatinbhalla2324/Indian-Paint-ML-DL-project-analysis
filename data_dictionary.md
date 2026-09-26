# Data dictionary

All money values are in **INR crore** (1 crore = 10 million). Percentages are in percent (12.5 = 12.5%). Missing values are `NA`: the figure was not published for that period/basis or could not be verified from the filings; nothing is estimated.

## Keys (all files)

| column | definition |
|---|---|
| `company` | Company name |
| `basis` | Standalone or Consolidated financial statements |
| `financial_year` | Indian fiscal year April-March; FY2024 = 1 Apr 2023 - 31 Mar 2024 |
| `quarter` | Fiscal quarter Q1 (Apr-Jun) ... Q4 (Jan-Mar); three-month figures, never year-to-date |
| `period_end` | Last day of the period (balance-sheet date for stock items) |

## Reported values — `annual_reported.csv`, `quarterly_reported.csv`

Taken from the financial statements in the company's own filings (quarterly results, annual reports). `calculated from statement lines` means the value is the sum/difference of lines printed in the same statement column (e.g. EBITDA); `sources.csv` gives the document, page and formula of every value. Balance-sheet and cash-flow values are annual only.

| column | unit | files | definition |
|---|---|---|---|
| `revenue` | INR crore | annual, quarterly | Revenue from operations, net of excise duty (pre-GST Ind AS periods: printed revenue minus excise duty; Indian GAAP periods: net revenue as printed) |
| `raw_material_cost` | INR crore | annual, quarterly | Cost of materials consumed + purchases of stock-in-trade + changes in inventories |
| `ebitda` | INR crore | annual, quarterly | Revenue - (total expenses - finance costs - depreciation & amortisation); excludes other income and exceptional items. Computed from the lines of one statement column |
| `depreciation` | INR crore | annual, quarterly | Depreciation and amortisation expense |
| `exceptional_items` | INR crore | annual, quarterly | Exceptional items included in profit before tax (gain +, loss -); NA when the statement has no exceptional-items line |
| `pat` | INR crore | annual, quarterly | Net profit for the period (consolidated: incl. non-controlling interests and share of associates/JVs); includes exceptional items |
| `eps_basic` | INR per share | annual, quarterly | Basic EPS as printed, after exceptional items, taken from the same statement column as `pat` (not adjusted for later bonus issues or splits) |
| `total_assets` | INR crore | annual | Total assets at period end |
| `net_worth` | INR crore | annual | Equity attributable to owners = equity share capital + other equity |
| `total_debt` | INR crore | annual | Non-current + current borrowings (incl. current maturities); lease liabilities excluded. 0 when none of the balance sheets for that date (two or more filings) has a borrowings line |
| `cash` | INR crore | annual | Cash and cash equivalents + other bank balances (current investments excluded) |
| `operating_cash_flow` | INR crore | annual | Net cash from operating activities |
| `capex` | INR crore | annual | Payments for property, plant & equipment and intangible assets (gross, positive number) |
| `accounting_standard` |  | annual, quarterly | Indian GAAP (FY2015-FY2016 as first reported; Indigo pre-IPO statements) or Ind AS |
| `comparability_flags` |  | annual, quarterly | Known breaks in comparability for this period (see data_quality_report.md) |

## Derived features — `annual_features.csv`, `quarterly_features.csv`

Computed only from the reported files. A feature is `NA` when an input is missing, when a growth base is zero or negative, or when a ratio denominator is zero or negative. Growth compares with the previous fiscal year (quarterly: the same quarter of the previous fiscal year) of the same company and basis.

| column | unit | files | formula |
|---|---|---|---|
| `ebit` | INR crore | annual, quarterly | operating profit = ebitda - depreciation (excludes other income) |
| `gross_margin` | % | annual, quarterly | (revenue - raw_material_cost) / revenue x 100 |
| `ebitda_margin` | % | annual, quarterly | ebitda / revenue x 100 |
| `ebit_margin` | % | annual, quarterly | ebit / revenue x 100 (operating margin) |
| `net_margin` | % | annual, quarterly | pat / revenue x 100 |
| `revenue_growth` | % | annual, quarterly | revenue_t / revenue_(t-1) - 1, x 100; NA if revenue_(t-1) <= 0 |
| `ebitda_growth` | % | annual, quarterly | ebitda_t / ebitda_(t-1) - 1, x 100; NA if ebitda_(t-1) <= 0 |
| `pat_growth` | % | annual, quarterly | pat_t / pat_(t-1) - 1, x 100; NA if pat_(t-1) <= 0 |
| `gross_margin_change` | pp | annual, quarterly | gross_margin_t - gross_margin_(t-1), percentage points |
| `ebitda_margin_change` | pp | annual, quarterly | ebitda_margin_t - ebitda_margin_(t-1), percentage points |
| `net_margin_change` | pp | annual, quarterly | net_margin_t - net_margin_(t-1), percentage points |
| `net_debt` | INR crore | annual | total_debt - cash (negative = net cash) |
| `free_cash_flow` | INR crore | annual | operating_cash_flow - capex |
| `debt_to_equity` | x | annual | total_debt / net_worth |
| `net_debt_to_ebitda` | x | annual | net_debt / ebitda; NA if ebitda <= 0 |
| `equity_to_assets` | % | annual | net_worth / total_assets x 100 |
| `return_on_equity` | % | annual | pat / net_worth (closing) x 100 |
| `return_on_assets` | % | annual | pat / total_assets (closing) x 100 |

## `sources.csv`

| column | definition |
|---|---|
| `metric`, `value`, `unit` | the reported value (column name in the reported file) |
| `source_document` | name of the filing; its official URL and SHA-256 are in `document_index.csv` |
| `document_type` | Quarterly Results, Annual Report or Audited Financial Statements |
| `page` | 1-based PDF page of the statement |
| `table` | statement, basis and column the value was read from |
| `value_type` | `reported` (single printed line) or `calculated from statement lines` |
| `formula` | how the value is built from the printed lines |
| `source_url` | official URL the document was downloaded from |
| `extraction_method` | `text` (PDF text layer) or `ocr` (scanned page) |
| `verification_status` | `VERIFIED` (arithmetic identities hold and/or the same figure appears in several filings), `SINGLE_SOURCE` (one filing, no check available), `CALCULATED` (quarter derived as YTD minus previous YTD) |
| `notes` | why the value was accepted (checks passed, corroborating filings, rejected alternatives) |
