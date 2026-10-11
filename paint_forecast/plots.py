"""Figures for the README (static PNGs, colour-blind-checked palette)."""

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

from .config import COMPANIES, FIGURES_DIR, TEST_WINDOW
from .data import label_to_t, load_panel

BLUE, ORANGE, AQUA, YELLOW, MAGENTA = '#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4'
INK, INK2, MUTED, GRID, AXIS, SURF, BAND = '#0b0b0b', '#52514e', '#898781', '#e1e0d9', '#c3c2b7', '#ffffff', '#f0efec'
FAMILY = {'Baseline': AQUA, 'ML': BLUE, 'DL': ORANGE, 'Guidance': YELLOW, 'Ablation': BLUE}
COMPANY = dict(zip(COMPANIES, [BLUE, ORANGE, AQUA, YELLOW]))
FEATURE_LABELS = {
    'industry_yoy': 'Industry YoY growth, latest quarter', 'yoy_0': 'Own YoY growth, latest quarter',
    'yoy_1': 'Own YoY growth, 1 quarter earlier', 'yoy_2': 'Own YoY growth, 2 quarters earlier',
    'yoy_3': 'Own YoY growth, 3 quarters earlier (base quarter)', 'yoy_mean4': 'Own YoY growth, 4-quarter average',
    'industry_gm_chg': 'Industry gross-margin change', 'gm_chg': 'Own gross-margin change (YoY, pp)',
    'em_chg': 'Own EBITDA-margin change (YoY, pp)', 'accel': 'Growth acceleration (yoy_0 - yoy_1)',
}

plt.rcParams.update({
    'font.family': ['Arial', 'DejaVu Sans'], 'font.size': 8.5, 'axes.labelsize': 8, 'xtick.labelsize': 7.5,
    'ytick.labelsize': 7.5, 'legend.fontsize': 7.5, 'legend.frameon': False,
    'axes.edgecolor': AXIS, 'axes.linewidth': 0.6, 'axes.labelcolor': INK2, 'axes.titlecolor': INK, 'axes.titlesize': 9.5,
    'axes.titleweight': 'bold', 'axes.titlelocation': 'left', 'axes.titlepad': 8, 'xtick.color': MUTED, 'ytick.color': MUTED,
    'xtick.labelcolor': INK2, 'ytick.labelcolor': INK2, 'xtick.major.size': 0, 'ytick.major.size': 0,
    'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': 0.5, 'axes.spines.top': False, 'axes.spines.right': False,
    'figure.facecolor': SURF, 'axes.facecolor': SURF, 'savefig.dpi': 200, 'savefig.bbox': 'tight', 'savefig.facecolor': SURF,
})


def _save(fig, name):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES_DIR / name)
    plt.close(fig)


def revenue_index():
    p = load_panel('A')
    idx = p.pivot(index='period', columns='company', values='revenue').loc['FY2016':]
    idx = idx / idx.loc['FY2019'] * 100
    x, labels = np.arange(len(idx)), [f'FY{s[4:]}' for s in idx.index]
    fig, ax = plt.subplots(figsize=(7.4, 2.7))
    i24 = list(idx.index).index('FY2024')
    ax.axvspan(i24 - 0.5, x[-1] + 0.5, color=BAND, lw=0, zorder=0)
    ax.text(i24 - 0.35, 243, 'Test years (slowdown)', color=INK2, fontsize=7.5, va='top')
    ax.text(list(idx.index).index('FY2020'), 243, 'Post-COVID boom: Asian Paints\nFY22 +36%, FY23 +19%', color=INK2, fontsize=7.5, va='top', ha='center')
    for c in COMPANIES:
        v = idx[c].to_numpy()
        ax.plot(x, v, color=COMPANY[c], lw=2, marker='o', ms=3.2, mec=SURF, mew=0.8, label=c)
        ax.text(x[-1] + 0.2, v[-1] + {'Asian Paints': -6, 'Berger Paints': 6}.get(c, 0), f'{c} {v[-1]:.0f}', color=INK2, fontsize=7.5, va='center')
    ax.set_xticks(x, labels); ax.set_xlim(-0.3, x[-1] + 2.6); ax.set_ylim(60, 250)
    ax.set_ylabel('Revenue index (FY2019 = 100)')
    ax.set_title('Fast growth until FY2023, then almost flat: the test years are a different regime')
    ax.legend(loc='upper left', ncol=4, bbox_to_anchor=(0, -0.12))
    _save(fig, 'revenue_index.png')


def _bars(ax, summary, title, cap=None):
    d = summary.sort_values('MAPE %', ascending=False).reset_index(drop=True)
    y = np.arange(len(d))
    vals = d['MAPE %'] if cap is None else d['MAPE %'].clip(upper=cap)
    ax.barh(y, vals, height=0.62, color=[FAMILY[f] for f in d['family']], zorder=2)
    top = vals.max()
    for i, (v, raw) in enumerate(zip(vals, d['MAPE %'])):
        ax.text(v + top * 0.015, i, f'{raw:.2f}%' + (' >' if cap and raw > cap else ''), va='center', fontsize=7, color=INK2)
    best_rule = d.loc[d['family'] == 'Baseline', 'MAPE %'].min()
    ax.axvline(best_rule, color=INK2, lw=0.8, zorder=3)
    ax.set_yticks(y, d['model'], fontsize=7.3)
    ax.set_xlim(0, top * 1.22); ax.grid(axis='y', visible=False)
    ax.set_xlabel('Test MAPE (%), lower is better.  Line = best simple rule')
    ax.set_title(title, fontsize=8.8)


def leaderboard(q, a):
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.0), gridspec_kw={'width_ratios': [1.35, 1], 'wspace': 0.95})
    _bars(axes[0], q['summary_test'], f"A. Next quarter ({q['meta']['n_test_rows']} forecasts, FY24 Q1 - FY26 Q4)")
    _bars(axes[1], a['summary_test'], f"B. Next year ({a['meta']['n_test_rows']} forecasts, FY24 - FY26)")
    fig.legend(handles=[Patch(color=AQUA, label='Simple rule (no ML)'), Patch(color=BLUE, label='Machine learning'),
                        Patch(color=ORANGE, label='Deep learning (PyTorch)')], loc='lower center', ncol=3, bbox_to_anchor=(0.5, -0.05))
    fig.subplots_adjust(bottom=0.2)
    _save(fig, 'leaderboard.png')


def ablation(q):
    d = q['ablation_test'].copy()
    d['family'] = np.where(d['family'] == 'Baseline', 'Baseline', 'ML')
    fig, ax = plt.subplots(figsize=(7.2, 2.2))
    _bars(ax, d, 'Same learner (gradient boosting), three framings: what you predict matters more than the model')
    _save(fig, 'ablation_framing.png')


def trajectories(q):
    preds, s = q['predictions'], q['summary_test']
    t0, t1 = (label_to_t(x, 'Q') for x in TEST_WINDOW['Q'])
    test = preds[(preds['target_t'] >= t0) & (preds['target_t'] <= t1)]
    rule = s.loc[s['family'] == 'Baseline', 'model'].iloc[0]
    ml = s.loc[s['family'] == 'ML', 'model'].iloc[0]
    dl = s.loc[s['family'] == 'DL', 'model'].iloc[0]
    fig, axes = plt.subplots(2, 2, figsize=(9.0, 5.0), gridspec_kw={'hspace': 0.55, 'wspace': 0.2})
    for ax, c in zip(axes.flat, COMPANIES):
        d = test[test['company'] == c]
        a = d[d['model'] == rule].sort_values('target_t')
        x = np.arange(len(a))
        m = d[d['model'] == ml].sort_values('target_t')
        ax.fill_between(x, m['lower'], m['upper'], color=BLUE, alpha=0.12, lw=0, label=f'{ml}: 80% interval')
        ax.plot(x, a['actual'], color=INK, lw=2, marker='o', ms=3.5, mec=SURF, mew=0.8, label='Actual', zorder=5)
        ax.plot(x, a['forecast'], color=AQUA, lw=1.6, marker='^', ms=3.5, mec=SURF, mew=0.8, label=rule, zorder=4)
        ax.plot(x, m['forecast'], color=BLUE, lw=1.6, marker='s', ms=3.2, mec=SURF, mew=0.8, label=ml, zorder=4)
        ax.plot(x, d[d['model'] == dl].sort_values('target_t')['forecast'], color=ORANGE, lw=1.4, marker='D', ms=2.8,
                mec=SURF, mew=0.6, label=dl, zorder=3)
        ax.set_xticks(x[::2], [p.replace('FY20', 'FY') for p in a['target_period'].iloc[::2]], fontsize=6.8)
        ax.set_title(c, fontsize=8.6); ax.set_ylabel('INR crore', fontsize=7.5)
    h, l = axes.flat[0].get_legend_handles_labels()
    fig.legend(h, l, loc='lower center', ncol=3, bbox_to_anchor=(0.5, -0.04))
    fig.subplots_adjust(bottom=0.16)
    _save(fig, 'test_trajectories.png')


def next_quarter_check(q):
    f, s = q['forward'], q['summary_test']
    picks = [(s.loc[s['family'] == 'ML', 'model'].iloc[0], BLUE), (s.loc[s['family'] == 'DL', 'model'].iloc[0], ORANGE),
             (s.loc[s['family'] == 'Baseline', 'model'].iloc[0], AQUA), ('Management guidance', YELLOW),
             (f.loc[f['model'].str.startswith('Hybrid'), 'model'].iloc[0], MAGENTA)]
    fig, ax = plt.subplots(figsize=(9.0, 3.1))
    bw, x = 0.15, np.arange(len(COMPANIES))
    lows, highs = [], []
    for i, (name, col) in enumerate(picks):
        err = [f.loc[(f['company'] == c) & (f['model'] == name), 'error %'].iloc[0] for c in COMPANIES]
        pos = x + (i - 2) * (bw + 0.012)
        mae = np.mean(np.abs(err))
        ax.bar(pos, err, width=bw, color=col, label=f'{name}  (mean abs. error {mae:.1f}%)', zorder=2)
        lows.append(min(err)); highs.append(max(err))
        for p_, e in zip(pos, err):
            ax.text(p_, e + (0.8 if e >= 0 else -0.8), f'{e:+.0f}' if round(e) else '0', ha='center',
                    va='bottom' if e >= 0 else 'top', fontsize=6.4, color=INK2)
    ax.axhline(0, color=INK2, lw=0.8, zorder=3)
    lab = []
    for c in COMPANIES:
        r = f[f['company'] == c].iloc[0]
        lab.append(f"{c}\nactual {r['actual']:,.0f} Cr (YoY {r['actual YoY %']:+.0f}%)")
    ax.set_xticks(x, lab, fontsize=7.3); ax.grid(axis='x', visible=False)
    ax.set_ylim(min(lows) - 2, max(max(highs), 0) + 1.5)
    ax.set_ylabel('Forecast error vs actual (%)')
    ax.set_title('Q1 FY2027 (Apr-Jun 2026), published after the data ends: every forecast was too low (the price-hike quarter)')
    ax.legend(loc='upper center', ncol=2, bbox_to_anchor=(0.5, -0.2))
    _save(fig, 'q1fy27_check.png')


def feature_effects(q, top=10):
    d = q['feature_effects'].head(top).iloc[::-1]
    fig, ax = plt.subplots(figsize=(6.4, 2.8))
    ax.barh(np.arange(len(d)), d['lightgbm_gain_share'] * 100, height=0.6, color=BLUE, zorder=2)
    for i, v in enumerate(d['lightgbm_gain_share'] * 100):
        ax.text(v + 0.4, i, f'{v:.1f}%', va='center', fontsize=7, color=INK2)
    ax.set_yticks(np.arange(len(d)), [FEATURE_LABELS.get(f, f) for f in d['feature']], fontsize=7.4); ax.grid(axis='y', visible=False)
    ax.set_xlabel('Share of LightGBM split gain (%)')
    ax.set_title('What the correction model uses (fit on all data)')
    _save(fig, 'feature_effects.png')


def make_all(q, a):
    revenue_index()
    leaderboard(q, a)
    ablation(q)
    trajectories(q)
    next_quarter_check(q)
    feature_effects(q)
