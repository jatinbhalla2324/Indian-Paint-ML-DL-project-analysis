"""Forecast next quarter's revenue for every company, with an 80% range.

    python scripts/predict.py                         # recommended model, GRU and the simple rule
    python scripts/predict.py --models ensemble       # one model only
    python scripts/predict.py --markdown              # print a Markdown table

Models are trained on every quarter in data/processed and forecast the first quarter after it.
The 80% range comes from each model's own recent walk-forward errors. If the actual result for
that quarter is listed in data/external/actuals_q1fy27.csv, it is shown next to the forecast.
"""

import argparse
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings('ignore', category=UserWarning)

import pandas as pd
import torch

from paint_forecast.backtest import walk_forward
from paint_forecast.config import BACKTEST_START, COMPANIES, RESULTS_DIR, TEST_WINDOW
from paint_forecast.data import load_panel
from paint_forecast.deep import dl_models
from paint_forecast.features import build_features
from paint_forecast.guidance import load_actuals
from paint_forecast.models import baselines, ml_models
from paint_forecast.pipeline import forecast_next

RULE = 'Same quarter last year x latest YoY growth'
ENSEMBLE = 'Ensemble (Ridge + RF + LightGBM)'


def available_models(seeds: int) -> dict:
    gru = next(k for k in dl_models('Q', seeds) if k.startswith('GRU'))
    return {
        'ensemble': (ENSEMBLE, ml_models('Q')[ENSEMBLE]),
        'gru': (gru, dl_models('Q', seeds)[gru]),
        'ridge': ('Ridge', ml_models('Q')['Ridge']),
        'rule': (RULE, baselines('Q')[RULE]),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--models', nargs='+', default=['ensemble', 'gru', 'rule'], choices=['ensemble', 'gru', 'ridge', 'rule'])
    ap.add_argument('--seeds', type=int, default=5, help='random seeds for the GRU ensemble')
    ap.add_argument('--markdown', action='store_true', help='print a Markdown table')
    args = ap.parse_args()
    torch.set_num_threads(2)

    panel = load_panel('Q')
    feat = build_features(panel, 'Q')
    pool = available_models(args.seeds)
    chosen = dict(pool[m] for m in args.models)

    # walk-forward errors give each model's 80% range; then fit on everything and forecast ahead
    errors = walk_forward(feat, chosen, 'Q', BACKTEST_START['Q'], TEST_WINDOW['Q'][1], verbose=False)
    fc = forecast_next(feat, chosen, 'Q', errors)

    actual = load_actuals().set_index('company')
    fc['actual'] = fc['company'].map(actual['revenue']) if (actual['period'] == fc['target_period'].iloc[0]).all() else float('nan')
    fc['growth %'] = (fc['forecast'] / fc['base_revenue'] - 1) * 100
    fc['error %'] = (fc['forecast'] / fc['actual'] - 1) * 100
    fc['company'] = pd.Categorical(fc['company'], COMPANIES, ordered=True)
    fc['model'] = pd.Categorical(fc['model'], [pool[m][0] for m in args.models], ordered=True)
    fc = fc.sort_values(['company', 'model']).reset_index(drop=True)

    last, nxt = fc['period'].iloc[0], fc['target_period'].iloc[0]
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = fc[['company', 'model', 'target_period', 'base_revenue', 'forecast', 'lower', 'upper', 'growth %', 'actual', 'error %']]
    out.round(2).to_csv(RESULTS_DIR / 'next_quarter_forecast.csv', index=False)

    if args.markdown:
        print(f'Forecast for **{nxt}** (standalone revenue, INR crore; data through {last}).\n')
        print('| Company | Model | Forecast | 80% range | YoY growth | Actual | Error |')
        print('|---|---|---:|---:|---:|---:|---:|')
        for _, r in fc.iterrows():
            act = '' if pd.isna(r['actual']) else f"{r['actual']:,.0f}"
            err = '' if pd.isna(r['error %']) else f"{r['error %']:+.1f}%"
            print(f"| {r['company']} | {r['model']} | {r['forecast']:,.0f} | {r['lower']:,.0f} - {r['upper']:,.0f} | "
                  f"{r['growth %']:+.1f}% | {act} | {err} |")
        return

    print(f'\nForecast for {nxt}  (standalone revenue, INR crore; models trained on data through {last})\n')
    for c, g in fc.groupby('company', observed=True):
        base = g['base_revenue'].iloc[0]
        act = '' if pd.isna(g['actual'].iloc[0]) else f"   actual {g['actual'].iloc[0]:,.0f}"
        print(f'{c}  (same quarter last year: {base:,.0f}){act}')
        for _, r in g.iterrows():
            err = '' if pd.isna(r['error %']) else f"   error {r['error %']:+.1f}%"
            print(f"  {r['model']:44s} {r['forecast']:>9,.0f}   80% range {r['lower']:>7,.0f} - {r['upper']:<7,.0f}"
                  f"  YoY {r['growth %']:+5.1f}%{err}")
        print()
    print(f'Saved to {RESULTS_DIR / "next_quarter_forecast.csv"}')


if __name__ == '__main__':
    main()
