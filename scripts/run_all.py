"""Reproduce every result and figure in the README.

    python scripts/run_all.py            # full run (5 seeds per deep-learning model, a few minutes on a laptop CPU)
    python scripts/run_all.py --seeds 1  # quick run
"""

import argparse
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings('ignore', category=UserWarning)

import torch

from paint_forecast import pipeline, plots
from paint_forecast.config import FIGURES_DIR, RESULTS_DIR


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--seeds', type=int, default=5, help='random seeds per deep-learning ensemble')
    ap.add_argument('--device', default='cpu', help="torch device: 'cpu' (reproducible), 'mps' or 'cuda'")
    args = ap.parse_args()
    torch.set_num_threads(2)

    results = {}
    for freq in ('Q', 'A'):
        results[freq] = pipeline.run(freq, seeds=args.seeds, device=args.device)
        pipeline.save(results[freq])
    plots.make_all(results['Q'], results['A'])

    q, a = results['Q'], results['A']
    show = ['model', 'family', 'MAPE %', 'Rel. MAE', 'DM p-value']
    print('\nQuarterly test window (FY2024 Q1 - FY2026 Q4):\n', q['summary_test'][show].round(3).to_string(index=False))
    print('\nAnnual test window (FY2024 - FY2026):\n', a['summary_test'][show].round(3).to_string(index=False))
    print('\nQ1 FY2027 vs actual results:\n', q['forward_scores'].round(2).to_string(index=False))
    print(f'\nResults in {RESULTS_DIR}\nFigures in {FIGURES_DIR}')


if __name__ == '__main__':
    main()
