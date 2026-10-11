"""Forecast accuracy metrics, always reported against simple baselines."""

import numpy as np
import pandas as pd
from scipy import stats


def mape(actual, forecast) -> float:
    a, f = np.asarray(actual, float), np.asarray(forecast, float)
    return float(np.mean(np.abs(f / a - 1)) * 100)


def diebold_mariano(e_model, e_ref, h: int = 1) -> tuple[float, float]:
    """Diebold-Mariano test on absolute errors with the Harvey-Leybourne-Newbold correction.

    Returns (statistic, two-sided p-value). Negative statistic = model more accurate than reference.
    Errors are pooled across companies, so treat the p-value as indicative, not exact.
    """
    d = np.abs(np.asarray(e_model, float)) - np.abs(np.asarray(e_ref, float))
    n = len(d)
    if n < 5 or np.allclose(d, 0):
        return 0.0, 1.0
    gamma0 = np.var(d, ddof=0)
    var = (gamma0 + 2 * sum(np.cov(d[k:], d[:-k], ddof=0)[0, 1] for k in range(1, h))) / n
    dm = d.mean() / np.sqrt(var)
    dm *= np.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    return float(dm), float(2 * stats.t.sf(abs(dm), df=n - 1))


def summarize(preds: pd.DataFrame, reference: str, scale_by: str) -> pd.DataFrame:
    """One row per model on identical rows.

    reference: model used for the Diebold-Mariano comparison (the best simple rule).
    scale_by:  model whose MAE scales the relative MAE (< 1 means better than that rule).
    """
    piv = preds.pivot_table(index=['company', 'target_t'], columns='model', values='forecast')
    actual = preds.drop_duplicates(['company', 'target_t']).set_index(['company', 'target_t'])['actual'].loc[piv.index]
    family = preds.drop_duplicates('model').set_index('model')['family']
    ref_err, scale_mae = actual - piv[reference], (actual - piv[scale_by]).abs().mean()
    rows = []
    for m in piv.columns:
        err = actual - piv[m]
        dm, p = diebold_mariano(err, ref_err) if m != reference else (np.nan, np.nan)
        rows.append({'model': m, 'family': family[m], 'MAPE %': mape(actual, piv[m]), 'MAE (Cr)': err.abs().mean(),
                     'RMSE (Cr)': np.sqrt((err ** 2).mean()), 'Rel. MAE': err.abs().mean() / scale_mae,
                     'DM stat vs best rule': dm, 'DM p-value': p, 'n': len(err)})
    return pd.DataFrame(rows).sort_values('MAPE %').reset_index(drop=True)


def per_company(preds: pd.DataFrame) -> pd.DataFrame:
    return (preds.groupby(['model', 'company'])
            .apply(lambda g: mape(g['actual'], g['forecast']), include_groups=False)
            .unstack('company').round(2))


def interval_report(preds: pd.DataFrame) -> pd.DataFrame:
    g = preds.dropna(subset=['lower'])
    return (g.groupby('model')
            .apply(lambda d: pd.Series({'coverage %': d['covered'].astype(float).mean() * 100,
                                        'avg width %': ((d['upper'] - d['lower']) / d['forecast']).mean() * 100,
                                        'n': len(d)}), include_groups=False)
            .round(1))
