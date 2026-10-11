# Indian paint companies – financial dataset (FY2015–FY2026)

Clean annual and quarterly financials for **Asian Paints, Berger Paints, Kansai Nerolac and Indigo Paints**,
extracted from the companies' official filings, with a source for every value. Ready for ML / DL work. This page documents the dataset; the forecasting project is in the [main README](../README.md).

## Files

```
data/processed/
  annual_reported.csv      85 rows   company x basis x fiscal year - values from the financial statements
  quarterly_reported.csv   312 rows  company x basis x quarter - P&L values (three-month figures, never year-to-date)
  annual_features.csv      85 rows   derived features (margins, growth, net debt, FCF, ratios)
  quarterly_features.csv   312 rows  derived features (margins, year-on-year growth, margin changes)
  sources.csv              3,082 rows  document, page, statement column, formula, URL and check status of every value
  document_index.csv       211 rows  the official filings used: URL, type, period, SHA-256
docs/data_dictionary.md     definition and unit of every column
docs/data_quality_report.md coverage, missing values, validation results, known issues
```

* **Reported values:** revenue, material cost, EBITDA, D&A, exceptional items, PAT and EPS (annual and quarterly), plus
  total assets, equity, debt, cash, operating cash flow and capex (annual only).
* **Features:** EBIT; gross, EBITDA, EBIT and net margins; revenue, EBITDA and PAT growth; margin changes; net debt;
  free cash flow; debt/equity; net debt/EBITDA; equity/assets; ROE and ROA.
* **Keys:** reported and feature files share the same keys (`company, basis, financial_year[, quarter]`). Join them
  on those columns.
* **Basis:** `basis` is `Standalone` or `Consolidated`. **Filter on one basis** and never mix the two in a series.
  Standalone exists for every period.
* **Units:** money is in **INR crore**, EPS in INR and percentages in percent. Missing values are `NA` and are never
  estimated.

Coverage: FY2015–FY2026 (April–March years) for Asian Paints, Berger and Nerolac. Indigo Paints starts in FY2018
(annual) and Q4 FY2020 (quarterly) because it listed in 2021.

## Sources and checks

* **Sources:** 211 official filings — 166 quarterly results, 42 annual reports and 3 audited statements. They come
  from the company investor-relations sites, or from BSE where the site copy was missing or wrong. No third-party data
  was used.
* **Traceability:** every value can be checked through the URL and page number in `sources.csv`.
* **Verification:** every value passed arithmetic identities checks or agreement between several filings. Quarters had
  to add up to the year-to-date and annual figures. EPS had to match PAT at the company's share count.
* **As first reported:** values are as printed in the period's own filing.
* **Report:** full results are in [`data_quality_report.md`](data_quality_report.md). No check fails; four year totals differ from the sum of
  their quarters because of later restatements.

## Limitations

* **Small panel:** 4 companies, about 168 standalone quarters and 43 standalone years with complete core data.
* **Accounting breaks:** Ind AS from FY2017; GST from Q1 FY2018 (pre-GST revenue is shown net of excise); Ind AS 116
  leases from FY2020; COVID quarters. See `comparability_flags`.
* **EPS:** as printed, not adjusted for share splits or bonus issues (Nerolac FY2015 and FY2024, Berger FY2016 and
  FY2024).
* **Exceptional items:** `exceptional_items` is `NA` when a statement has no exceptional-items line.
* **No build code:** the extraction pipeline and source PDFs were removed to keep the folder small. The dataset
  cannot be regenerated from this folder; re-download a filing from its URL to check a value.
