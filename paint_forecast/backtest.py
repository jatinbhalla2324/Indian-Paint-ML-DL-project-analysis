"""Walk-forward (expanding-window) evaluation and empirical prediction intervals.

At each forecast origin T (the last period whose results are published):
  1. train on every row whose *target* period is <= T, so no future revenue is ever seen,
  2. forecast period T+1 for each company,
  3. move T forward one period and repeat.
This mimics how the model would have been used in real time.
"""

import time

import numpy as np
import pandas as pd

from .config import CALIBRATION_WINDOW, INTERVAL_LEVEL, MIN_CALIBRATION_ERRORS, MIN_TRAIN_ROWS
from .data import label_to_t
from .features import model_ready


def walk_forward(feat: pd.DataFrame, models: dict, freq: str, start_target: str, end_target: str,
                 refit_every: int | dict = 1, verbose: bool = True) -> pd.DataFrame:
    data = feat[model_ready(feat, freq)]
    known = lambda T: data[(data['target_t'] <= T) & data['y'].notna() & ~data['covid_affected']]
    origins = [T for T in range(label_to_t(start_target, freq) - 1, label_to_t(end_target, freq))
               if len(known(T)) >= MIN_TRAIN_ROWS]
    out = []
    for name, factory in models.items():
        every = refit_every.get(name, 1) if isinstance(refit_every, dict) else refit_every
        fitted, tic = None, time.time()
        for i, T in enumerate(origins):
            test = data[(data['t'] == T) & data['y'].notna()]
            if test.empty:
                continue
            if fitted is None or i % every == 0:
                fitted = factory().fit(known(T))
            g = fitted.predict_growth(test)
            rec = test[['company', 't', 'period', 'target_t', 'target_period', 'base_revenue', 'target_revenue',
                        'y', 'covid_affected']].copy()
            rec['model'], rec['family'] = fitted.name, fitted.family
            rec['y_hat'] = g
            rec['forecast'] = test['base_revenue'].to_numpy() * np.exp(g)
            out.append(rec)
        if verbose:
            print(f'  {name:48s} {time.time() - tic:6.1f}s')
    preds = pd.concat(out, ignore_index=True).rename(columns={'target_revenue': 'actual', 't': 'origin'})
    preds['ape'] = (preds['forecast'] / preds['actual'] - 1).abs() * 100
    preds['log_error'] = preds['y'] - preds['y_hat']
    return preds


def add_intervals(preds: pd.DataFrame, level: float = INTERVAL_LEVEL) -> pd.DataFrame:
    """Rolling empirical intervals: quantiles of the model's most recent out-of-sample errors.

    For a forecast made at origin T only errors whose target period is <= T are used, so the
    interval is something the model could have published at the time.
    """
    lo_q, hi_q = (1 - level) / 2, 1 - (1 - level) / 2
    out = []
    for _, g in preds.groupby('model'):
        g = g.sort_values('origin').copy()
        lo, hi = np.full(len(g), np.nan), np.full(len(g), np.nan)
        clean = g[~g['covid_affected']]
        for i, T in enumerate(g['origin'].to_numpy()):
            pool = clean.loc[clean['target_t'] <= T, 'log_error'].to_numpy()[-CALIBRATION_WINDOW:]
            if len(pool) >= MIN_CALIBRATION_ERRORS:
                lo[i], hi[i] = np.quantile(pool, [lo_q, hi_q])
        g['lower'] = g['base_revenue'] * np.exp(g['y_hat'] + lo)
        g['upper'] = g['base_revenue'] * np.exp(g['y_hat'] + hi)
        out.append(g)
    res = pd.concat(out).sort_index()
    res['covered'] = ((res['actual'] >= res['lower']) & (res['actual'] <= res['upper'])).astype(float)
    res.loc[res['lower'].isna(), 'covered'] = np.nan
    return res
