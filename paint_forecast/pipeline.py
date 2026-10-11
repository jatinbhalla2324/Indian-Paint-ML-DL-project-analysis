"""End-to-end run: walk-forward backtests, summaries, next-period forecasts and the guidance check."""

import json
import platform
import time

import numpy as np
import pandas as pd

from . import metrics
from .backtest import add_intervals, walk_forward
from .config import BACKTEST_START, CALIBRATION_WINDOW, INTERVAL_LEVEL, MIN_CALIBRATION_ERRORS, RESULTS_DIR, TEST_WINDOW
from .data import label_to_t, load_panel
from .deep import dl_models
from .features import build_features, feature_sets, model_ready
from .guidance import add_guidance_forecasts, load_actuals, load_guidance, score_against_actuals
from .models import GrowthRegressor, _lgbm, _ridge, ablation_models, baselines, ml_models

BEST_RULE = {'Q': 'Same quarter last year x latest YoY growth', 'A': 'Last year x latest growth'}
SCALE_RULE = {'Q': 'Same quarter last year', 'A': 'Same as last year'}


def forecast_next(feat: pd.DataFrame, models: dict, freq: str, preds: pd.DataFrame | None = None) -> pd.DataFrame:
    """Fit every model on all published data and forecast the first unpublished period.

    If backtest predictions are given, attach an interval from each model's out-of-sample errors.
    """
    data = feat[model_ready(feat, freq)]
    T = int(data['t'].max())
    train = data[(data['target_t'] <= T) & data['y'].notna() & ~data['covid_affected']]
    rows = data[data['t'] == T]
    out = []
    for name, factory in models.items():
        m = factory().fit(train)
        rec = rows[['company', 'period', 'target_period', 'base_revenue']].copy()
        rec['model'], rec['family'] = m.name, m.family
        rec['y_hat'] = m.predict_growth(rows)
        rec['forecast'] = rec['base_revenue'] * np.exp(rec['y_hat'])
        if preds is not None:
            err = (preds.loc[(preds['model'] == m.name) & ~preds['covid_affected']]
                   .sort_values('origin')['log_error'].tail(CALIBRATION_WINDOW))
            if len(err) >= MIN_CALIBRATION_ERRORS:
                lo, hi = np.quantile(err, [(1 - INTERVAL_LEVEL) / 2, 1 - (1 - INTERVAL_LEVEL) / 2])
                rec['lower'], rec['upper'] = rec['forecast'] * np.exp(lo), rec['forecast'] * np.exp(hi)
        out.append(rec)
    return pd.concat(out, ignore_index=True)


def feature_effects(feat: pd.DataFrame, freq: str = 'Q') -> pd.DataFrame:
    """What the ML correction learned on all data: Ridge standardised coefficients and LightGBM gain."""
    data = feat[model_ready(feat, freq) & feat['y'].notna() & ~feat['covid_affected']]
    cols = feature_sets(freq)['tabular']
    ridge = GrowthRegressor('Ridge', _ridge(), cols).fit(data)
    lgbm = GrowthRegressor('LightGBM', _lgbm(), cols).fit(data)
    gain = lgbm.estimator.booster_.feature_importance('gain')
    return (pd.DataFrame({'feature': cols, 'ridge_coef_std': ridge.estimator[-1].coef_,
                          'lightgbm_gain_share': gain / gain.sum()})
            .sort_values('lightgbm_gain_share', ascending=False).reset_index(drop=True))


def _window(preds, freq, which):
    t0, t1 = (label_to_t(x, freq) for x in TEST_WINDOW[freq])
    if which == 'test':
        return preds[(preds['target_t'] >= t0) & (preds['target_t'] <= t1)]
    return preds[(preds['target_t'] < t0) & ~preds['covid_affected']]


def run(freq: str = 'Q', seeds: int = 5, device: str = 'cpu', verbose: bool = True) -> dict:
    tic = time.time()
    feat = build_features(load_panel(freq), freq)
    main = {**baselines(freq), **ml_models(freq), **dl_models(freq, seeds, device)}
    ablation = ablation_models(freq)
    if verbose:
        print(f'[{freq}] walk-forward backtest, targets {BACKTEST_START[freq]} .. {TEST_WINDOW[freq][1]}')
    preds = add_intervals(walk_forward(feat, {**main, **ablation}, freq, BACKTEST_START[freq], TEST_WINDOW[freq][1], verbose=verbose))

    test, pretest = _window(preds, freq, 'test'), _window(preds, freq, 'pretest')
    main_names = [m for m in preds['model'].unique() if preds.loc[preds['model'] == m, 'family'].iloc[0] != 'Ablation']
    res = {
        'predictions': preds,
        'summary_test': metrics.summarize(test[test['model'].isin(main_names)], BEST_RULE[freq], SCALE_RULE[freq]),
        'summary_pretest': metrics.summarize(pretest[pretest['model'].isin(main_names)], BEST_RULE[freq], SCALE_RULE[freq]),
        'per_company_test': metrics.per_company(test),
    }
    if freq == 'Q':
        abl = test[test['family'].eq('Ablation') | test['model'].isin([BEST_RULE[freq], SCALE_RULE[freq]])]
        res['ablation_test'] = metrics.summarize(abl, BEST_RULE[freq], SCALE_RULE[freq])
        res['intervals_test'] = metrics.interval_report(test[test['model'].isin(main_names)])
        res['feature_effects'] = feature_effects(feat, freq)

    # next unpublished period, plus the management-guidance check for the quarterly horizon
    forward = forecast_next(feat, main, freq, preds)
    if freq == 'Q':
        ranked = res['summary_test']
        best_model = ranked.loc[ranked['family'] != 'Baseline', 'model'].iloc[0]
        forward = add_guidance_forecasts(forward, best_model, load_guidance())
        forward = score_against_actuals(forward, load_actuals())
        res['forward_scores'] = (forward.groupby('model')
                                 .agg(family=('family', 'first'), mean_abs_error_pct=('error %', lambda s: s.abs().mean()))
                                 .sort_values('mean_abs_error_pct').reset_index())
    res['forward'] = forward
    res['meta'] = {'freq': freq, 'seeds': seeds, 'device': device, 'runtime_s': round(time.time() - tic, 1),
                   'python': platform.python_version(), 'test_window': TEST_WINDOW[freq],
                   'n_test_rows': int(res['summary_test']['n'].iloc[0])}
    return res


def save(res: dict, out_dir=RESULTS_DIR) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = 'quarterly' if res['meta']['freq'] == 'Q' else 'annual'
    for key, val in res.items():
        if isinstance(val, pd.DataFrame):
            val.round(4).to_csv(out_dir / f'{tag}_{key}.csv', index=key in ('per_company_test', 'intervals_test'))
    (out_dir / f'{tag}_meta.json').write_text(json.dumps(res['meta'], indent=2))
