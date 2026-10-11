"""Baselines and machine-learning forecasters behind one interface.

Every forecaster has `fit(train_rows)` and `predict(rows)`, where `predict` returns revenue in
INR crore and `predict_growth` returns the forecast YoY log growth of the target period.

The ML models learn a *correction to the best simple rule*: their target is
    y - yoy_0     (next period's growth minus the latest growth),
so a model that finds no signal falls back to "same period last year x latest growth"
instead of drifting towards the training-period average.
"""

import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import HuberRegressor, RidgeCV
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .config import SEED
from .features import feature_sets


class Forecaster:
    name = 'forecaster'
    family = 'Baseline'

    def fit(self, train: pd.DataFrame) -> 'Forecaster':
        return self

    def predict_growth(self, rows: pd.DataFrame) -> np.ndarray:
        raise NotImplementedError

    def predict(self, rows: pd.DataFrame) -> np.ndarray:
        return rows['base_revenue'].to_numpy() * np.exp(self.predict_growth(rows))


# ----------------------------------------------------------------------------- baselines
class RuleForecaster(Forecaster):
    """A fixed rule; `growth` maps rows to forecast YoY log growth."""

    def __init__(self, name, growth):
        self.name, self._growth = name, growth

    def predict_growth(self, rows):
        return np.asarray(self._growth(rows), dtype=float)


def baselines(freq: str) -> dict:
    if freq == 'Q':
        rules = {
            'Same as last quarter': lambda r: r['log_revenue'] - np.log(r['base_revenue']),
            'Same quarter last year': lambda r: np.zeros(len(r)),
            'Same quarter last year x latest YoY growth': lambda r: r['yoy_0'],
            'Same quarter last year x 4-qtr avg growth': lambda r: r['yoy_mean4'],
        }
    else:
        rules = {
            'Same as last year': lambda r: np.zeros(len(r)),
            'Last year x latest growth': lambda r: r['yoy_0'],
            'Last year x 2-yr avg growth': lambda r: (r['yoy_0'] + r['yoy_1']) / 2,
        }
    return {name: (lambda n=name, g=g: RuleForecaster(n, g)) for name, g in rules.items()}


# ----------------------------------------------------------------------------- ML
class GrowthRegressor(Forecaster):
    """Any sklearn regressor trained on YoY growth, optionally as a residual to an anchor column."""

    family = 'ML'

    def __init__(self, name, estimator, features, anchor='yoy_0', family='ML'):
        self.name, self.estimator, self.features, self.anchor, self.family = name, estimator, features, anchor, family

    def _offset(self, rows):
        return rows[self.anchor].to_numpy() if self.anchor else 0.0

    def fit(self, train):
        train = train.sort_values('target_t')        # keeps inner CV folds in time order
        self.estimator.fit(train[self.features], train['y'].to_numpy() - self._offset(train))
        return self

    def predict_growth(self, rows):
        return self.estimator.predict(rows[self.features]) + self._offset(rows)


class LevelRegressor(Forecaster):
    """v1 framing kept for the ablation: predict revenue in crore from revenue-level inputs."""

    family = 'Ablation'

    def __init__(self, name, estimator, features):
        self.name, self.estimator, self.features = name, estimator, features

    def fit(self, train):
        self.estimator.fit(train[self.features], train['target_revenue'])
        return self

    def predict(self, rows):
        return self.estimator.predict(rows[self.features])

    def predict_growth(self, rows):
        return np.log(self.predict(rows) / rows['base_revenue'].to_numpy())


class MeanEnsemble(Forecaster):
    """Equal-weight average of member growth forecasts (simple averages are hard to beat)."""

    family = 'ML'

    def __init__(self, name, members):
        self.name, self.members = name, members

    def fit(self, train):
        self.members = [m.fit(train) for m in self.members]
        return self

    def predict_growth(self, rows):
        return np.mean([m.predict_growth(rows) for m in self.members], axis=0)


def _ridge():
    return make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-2, 4, 40), cv=TimeSeriesSplit(n_splits=4)))


def _huber():
    return make_pipeline(StandardScaler(), HuberRegressor(epsilon=1.35, alpha=1.0, max_iter=2000))


def _forest():
    return RandomForestRegressor(n_estimators=400, min_samples_leaf=5, max_features=0.5, random_state=SEED, n_jobs=4)


def _lgbm():
    # small-data settings: shallow trees, strong regularisation, few rows per leaf
    return lgb.LGBMRegressor(n_estimators=300, learning_rate=0.02, num_leaves=7, max_depth=3, min_child_samples=8,
                             subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=5.0,
                             random_state=SEED, verbose=-1, n_jobs=4)


def ml_models(freq: str) -> dict:
    feats = feature_sets(freq)['tabular']
    models = {
        'Ridge': lambda: GrowthRegressor('Ridge', _ridge(), feats),
        'Huber': lambda: GrowthRegressor('Huber', _huber(), feats),
        'Random Forest': lambda: GrowthRegressor('Random Forest', _forest(), feats),
    }
    if freq == 'Q':
        models['LightGBM'] = lambda: GrowthRegressor('LightGBM', _lgbm(), feats)
        models['Ensemble (Ridge + RF + LightGBM)'] = lambda: MeanEnsemble(
            'Ensemble (Ridge + RF + LightGBM)',
            [GrowthRegressor('Ridge', _ridge(), feats), GrowthRegressor('Random Forest', _forest(), feats),
             GrowthRegressor('LightGBM', _lgbm(), feats)])
    else:
        models['Ensemble (Ridge + RF)'] = lambda: MeanEnsemble(
            'Ensemble (Ridge + RF)', [GrowthRegressor('Ridge', _ridge(), feats), GrowthRegressor('Random Forest', _forest(), feats)])
    return models


def ablation_models(freq: str) -> dict:
    """Same learner, three framings: revenue level (v1) -> raw growth -> residual to the best rule."""
    if freq != 'Q':
        return {}
    fs = feature_sets(freq)
    gbr = lambda: GradientBoostingRegressor(n_estimators=100, max_depth=3, learning_rate=0.05, subsample=0.8, random_state=SEED)
    return {
        'GBM on revenue level (v1 framing)': lambda: LevelRegressor('GBM on revenue level (v1 framing)', gbr(), fs['level']),
        'GBM on growth (no anchor)': lambda: GrowthRegressor('GBM on growth (no anchor)', gbr(), fs['tabular'], anchor=None, family='Ablation'),
        'GBM on growth + residual to rule': lambda: GrowthRegressor('GBM on growth + residual to rule', gbr(), fs['tabular'], family='Ablation'),
    }
