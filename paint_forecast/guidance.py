"""Management guidance as a forecast, and a hybrid of guidance with the best data-driven model.

Indian paint companies rarely publish a revenue number; they guide on volume growth, margin
bands and price actions. `management_guidance_may2026.csv` turns the May 2026 calls into one
implied growth rate per company. It is a scenario input: edit the CSV to test other readings.
"""

import numpy as np
import pandas as pd

from .config import EXTERNAL_DIR


def load_guidance(path=EXTERNAL_DIR / 'management_guidance_may2026.csv') -> pd.DataFrame:
    return pd.read_csv(path)


def load_actuals(path=EXTERNAL_DIR / 'actuals_q1fy27.csv') -> pd.DataFrame:
    return pd.read_csv(path)


def add_guidance_forecasts(forward: pd.DataFrame, best_model: str, guidance: pd.DataFrame) -> pd.DataFrame:
    """Append two forecasts per company to the model forecasts for the next period.

    * Management guidance: base revenue x (1 + implied growth).
    * Hybrid: equal-weight average (in log growth) of the best model and the guidance.
    """
    g = guidance.set_index('company')['implied_growth']
    base = forward.drop_duplicates('company').set_index('company')
    best = forward[forward['model'] == best_model].set_index('company')
    rows = []
    for c in base.index:
        g_log = np.log1p(g[c])
        for name, y_hat in [('Management guidance', g_log), (f'Hybrid: {best_model} + guidance', 0.5 * (best.loc[c, 'y_hat'] + g_log))]:
            rows.append({'company': c, 'model': name, 'family': 'Guidance', 'base_revenue': base.loc[c, 'base_revenue'],
                         'y_hat': y_hat, 'forecast': base.loc[c, 'base_revenue'] * np.exp(y_hat)})
    return pd.concat([forward, pd.DataFrame(rows)], ignore_index=True)


def score_against_actuals(forward: pd.DataFrame, actuals: pd.DataFrame) -> pd.DataFrame:
    out = forward.merge(actuals[['company', 'revenue']].rename(columns={'revenue': 'actual'}), on='company', how='left')
    out['error %'] = (out['forecast'] / out['actual'] - 1) * 100
    out['actual YoY %'] = (out['actual'] / out['base_revenue'] - 1) * 100
    out['forecast YoY %'] = (out['forecast'] / out['base_revenue'] - 1) * 100
    return out
