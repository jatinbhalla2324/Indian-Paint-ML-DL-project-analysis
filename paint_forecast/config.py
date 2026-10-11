"""Paths, periods and constants shared by the whole pipeline."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data' / 'processed'
EXTERNAL_DIR = ROOT / 'data' / 'external'
RESULTS_DIR = ROOT / 'reports' / 'results'
FIGURES_DIR = ROOT / 'reports' / 'figures'

COMPANIES = ['Asian Paints', 'Berger Paints', 'Kansai Nerolac', 'Indigo Paints']
BASIS = 'Standalone'          # standalone exists for every period; never mix bases in one series
FIRST_FY = 2015               # period index t = 0 is FY2015 (Q1 for quarterly data)

# Season length: the target is always compared with the same period one year earlier.
SEASON = {'Q': 4, 'A': 1}

# Quarters distorted by COVID lockdowns. Training rows that touch them (as the feature period,
# the target period or either base period) are dropped; they are never used to judge a model.
# Annual totals smooth the lockdown quarters out (FY2021 growth was -5% to +16%), so none are dropped.
LOCKDOWN = {
    'Q': {'FY2020 Q4', 'FY2021 Q1', 'FY2022 Q1'},
    'A': set(),
}
MIN_TRAIN_ROWS = 12   # forecast origins with fewer training rows are skipped for every model

# Evaluation windows, expressed as the first and last *target* period.
TEST_WINDOW = {'Q': ('FY2024 Q1', 'FY2026 Q4'), 'A': ('FY2024', 'FY2026')}
BACKTEST_START = {'Q': 'FY2019 Q1', 'A': 'FY2019'}   # earlier targets feed intervals and robustness checks

INTERVAL_LEVEL = 0.80
MIN_CALIBRATION_ERRORS = 16
CALIBRATION_WINDOW = 32     # most recent errors used for an interval (about 8 quarters x 4 companies)
SEED = 42
