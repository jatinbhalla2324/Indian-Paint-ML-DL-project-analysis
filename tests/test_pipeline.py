"""Leakage and correctness tests.  Run:  python -m unittest discover tests"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from paint_forecast.backtest import walk_forward
from paint_forecast.data import label_to_t, load_panel
from paint_forecast.features import build_features, feature_sets
from paint_forecast.metrics import diebold_mariano, mape
from paint_forecast.models import Forecaster, baselines


def all_feature_columns(freq='Q'):
    fs = feature_sets(freq)
    cols = list(fs['tabular']) + [c for step in (fs['sequence'] or []) for c in step] + list(fs['level'] or [])
    return list(dict.fromkeys(cols))


class TestData(unittest.TestCase):
    def test_every_company_series_is_consecutive(self):
        for freq in ('Q', 'A'):
            panel = load_panel(freq)
            self.assertTrue((panel.groupby('company')['t'].diff().dropna() == 1).all())

    def test_only_standalone_rows(self):
        raw = pd.read_csv(Path(__file__).resolve().parents[1] / 'data' / 'processed' / 'quarterly_reported.csv')
        n_standalone = (raw['basis'] == 'Standalone').sum()
        self.assertEqual(len(load_panel('Q')), n_standalone)


class TestNoLeakage(unittest.TestCase):
    def test_features_do_not_change_when_the_future_changes(self):
        """Scramble everything after FY2023 Q4; features of earlier rows must be identical."""
        panel = load_panel('Q')
        cut = label_to_t('FY2023 Q4', 'Q')
        shocked = panel.copy()
        future = shocked['t'] > cut
        shocked.loc[future, 'revenue'] *= 3.0
        shocked.loc[future, 'gross_margin'] -= 7.0
        shocked.loc[future, 'ebitda_margin'] += 4.0
        shocked['log_revenue'] = np.log(shocked['revenue'])

        cols = all_feature_columns('Q')
        before, after = build_features(panel, 'Q'), build_features(shocked, 'Q')
        past = before['t'] <= cut
        pd.testing.assert_frame_equal(before.loc[past, cols], after.loc[past, cols])

    def test_walk_forward_trains_only_on_published_targets(self):
        seen = []

        class Spy(Forecaster):
            name = 'spy'

            def fit(self, train):
                self.max_target = int(train['target_t'].max())
                return self

            def predict_growth(self, rows):
                seen.append((self.max_target, int(rows['t'].max())))
                return np.zeros(len(rows))

        feat = build_features(load_panel('Q'), 'Q')
        walk_forward(feat, {'spy': Spy}, 'Q', 'FY2019 Q1', 'FY2026 Q4', verbose=False)
        self.assertTrue(seen)
        for max_target, origin in seen:
            self.assertLessEqual(max_target, origin)


class TestTargets(unittest.TestCase):
    def test_target_is_next_quarter_yoy_log_growth(self):
        feat = build_features(load_panel('Q'), 'Q').set_index(['company', 'period'])
        row = feat.loc[('Asian Paints', 'FY2026 Q3')]
        expected = np.log(feat.loc[('Asian Paints', 'FY2026 Q4'), 'revenue'] / feat.loc[('Asian Paints', 'FY2025 Q4'), 'revenue'])
        self.assertAlmostEqual(row['y'], expected, places=10)
        self.assertEqual(row['target_period'], 'FY2026 Q4')

    def test_last_period_has_no_target(self):
        feat = build_features(load_panel('Q'), 'Q')
        last = feat[feat['period'] == 'FY2026 Q4']
        self.assertTrue(last['y'].isna().all())
        self.assertTrue(last['base_revenue'].notna().all())   # the forward forecast still has a base


class TestBaselines(unittest.TestCase):
    def test_seasonal_naive_repeats_the_same_quarter_last_year(self):
        feat = build_features(load_panel('Q'), 'Q')
        preds = walk_forward(feat, {k: v for k, v in baselines('Q').items() if k == 'Same quarter last year'},
                             'Q', 'FY2026 Q4', 'FY2026 Q4', verbose=False)
        panel = load_panel('Q').set_index(['company', 'period'])
        for _, r in preds.iterrows():
            self.assertAlmostEqual(r['forecast'], panel.loc[(r['company'], 'FY2025 Q4'), 'revenue'], places=6)


class TestMetrics(unittest.TestCase):
    def test_mape(self):
        self.assertAlmostEqual(mape([100, 200], [110, 180]), 10.0)

    def test_diebold_mariano_sign(self):
        rng = np.random.default_rng(0)
        small, large = rng.normal(0, 1, 60), rng.normal(0, 3, 60)
        stat, p = diebold_mariano(small, large)
        self.assertLess(stat, 0)
        self.assertLess(p, 0.05)


if __name__ == '__main__':
    unittest.main()
