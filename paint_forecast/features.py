"""Leakage-safe features and targets for one-step-ahead forecasting.

Every row describes a forecast made at the end of period t for period t+1:

* features use data from periods <= t only (row shifts within a company);
* the target is the year-on-year log growth of period t+1,
      y = log(revenue[t+1]) - log(revenue[t+1-m]),   m = 4 (quarterly) or 1 (annual),
  so a forecast of y converts back to revenue as revenue[t+1-m] * exp(y_hat).

Predicting growth instead of the revenue level stops models from scoring well just by
knowing that Asian Paints is 20x bigger than Indigo, and lets one model serve all companies.
"""

import numpy as np
import pandas as pd

from .config import LOCKDOWN, SEASON
from .data import period_label

SEQ_LEN = 4        # quarters of history the GRU sees
GROWTH_CAP = 0.35  # log points


def _lag(df: pd.DataFrame, col: str, k: int) -> pd.Series:
    return df.groupby('company')[col].shift(k)


def build_features(panel: pd.DataFrame, freq: str = 'Q') -> pd.DataFrame:
    m = SEASON[freq]
    df = panel.copy()

    # current-period year-on-year signals. Growth inputs are capped at +/-GROWTH_CAP: the largest
    # non-COVID quarter is 0.31, lockdown quarters reach -0.90 / +0.78 and would dominate linear models.
    df['yoy_0'] = (df['log_revenue'] - _lag(df, 'log_revenue', m)).clip(-GROWTH_CAP, GROWTH_CAP)
    df['gm_chg'] = df['gross_margin'] - _lag(df, 'gross_margin', m)
    df['em_chg'] = df['ebitda_margin'] - _lag(df, 'ebitda_margin', m)

    # industry signals: the average across companies that reported period t
    for col in ['yoy_0', 'gm_chg']:
        df[f'industry_{col}'] = df.groupby('t')[col].transform('mean')
    df = df.rename(columns={'industry_yoy_0': 'industry_yoy'})

    n_lags = 4 if freq == 'Q' else 2
    for k in range(1, n_lags):
        df[f'yoy_{k}'] = _lag(df, 'yoy_0', k)
    df['accel'] = df['yoy_0'] - df['yoy_1']

    if freq == 'Q':
        df['yoy_mean4'] = df[['yoy_0', 'yoy_1', 'yoy_2', 'yoy_3']].mean(axis=1, skipna=False)
        for col in ['gm_chg', 'em_chg', 'industry_yoy']:
            for k in range(1, SEQ_LEN):
                df[f'{col}_{k}'] = _lag(df, col, k)
        next_q = (df['t'] + 1) % 4 + 1
        for q in range(1, 5):
            df[f'target_q{q}'] = (next_q == q).astype(float)

        df = add_level_features(df)

    for c in sorted(df['company'].unique()):
        df[f'comp_{c.split()[0].lower()}'] = (df['company'] == c).astype(float)

    # target: YoY log growth of period t+1, and the base revenue it applies to
    df['target_t'] = df['t'] + 1
    df['target_period'] = [period_label(t, freq) for t in df['target_t']]
    df['target_revenue'] = _lag(df, 'revenue', -1)
    df['base_revenue'] = _lag(df, 'revenue', m - 1)            # revenue[t+1-m]
    df['y'] = np.log(df['target_revenue']) - np.log(df['base_revenue'])
    # the target row must really be the next period (guards against gaps at series ends)
    df.loc[_lag(df, 't', -1) != df['target_t'], ['target_revenue', 'y']] = np.nan

    lock = LOCKDOWN[freq]
    touched = [df['period'], df['target_period']]
    touched += [pd.Series([period_label(t - m, freq) for t in df['t']], index=df.index),
                pd.Series([period_label(t + 1 - m, freq) for t in df['t']], index=df.index)]
    df['covid_affected'] = np.logical_or.reduce([s.isin(lock) for s in touched])
    return df


def feature_sets(freq: str = 'Q') -> dict:
    """Column groups used by the models."""
    comp = ['comp_asian', 'comp_berger', 'comp_indigo', 'comp_kansai']
    if freq == 'Q':
        # yoy_3 is the growth of the target's base quarter: a weak base usually means stronger growth next
        tabular = ['yoy_0', 'yoy_1', 'yoy_2', 'yoy_3', 'yoy_mean4', 'accel',
                   'gm_chg', 'em_chg', 'industry_yoy', 'industry_gm_chg']
        seasonal = ['target_q1', 'target_q2', 'target_q3', 'target_q4']
        lagged = lambda name, k: name if k == 0 else f'{name}_{k}'
        # oldest step first: [yoy, gross-margin change, EBITDA-margin change, industry yoy] per quarter
        seq = [[f'yoy_{k}', lagged('gm_chg', k), lagged('em_chg', k), lagged('industry_yoy', k)]
               for k in range(SEQ_LEN - 1, -1, -1)]
        return {'tabular': tabular + seasonal + comp, 'sequence': seq, 'static': seasonal + comp,
                'level': ['revenue', 'rev_lag1', 'rev_lag2', 'rev_lag4', 'rev_roll4'] + seasonal + comp}
    tabular = ['yoy_0', 'yoy_1', 'accel', 'gm_chg', 'em_chg', 'industry_yoy']
    return {'tabular': tabular + comp, 'sequence': None, 'static': None, 'level': None}


def add_level_features(df: pd.DataFrame) -> pd.DataFrame:
    """Revenue-level inputs used only to reproduce the v1 framing in the ablation study."""
    out = df.copy()
    for k in (1, 2, 4):
        out[f'rev_lag{k}'] = _lag(out, 'revenue', k)
    out['rev_roll4'] = out.groupby('company')['revenue'].transform(lambda s: s.rolling(4).mean())
    return out


def model_ready(df: pd.DataFrame, freq: str = 'Q') -> pd.Series:
    """Rows where every model's inputs exist (all models are judged on the same rows)."""
    fs = feature_sets(freq)
    cols = list(fs['tabular'])
    if fs['sequence']:
        cols += [c for step in fs['sequence'] for c in step]
    if fs['level']:
        cols += fs['level']
    cols = [c for c in dict.fromkeys(cols) if c in df.columns]
    return df[cols].notna().all(axis=1) & df['base_revenue'].notna()
