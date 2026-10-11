"""Deep-learning forecasters (PyTorch), sized for a panel of about 150 training rows.

Design choices, and why:
* small networks (hundreds to a few thousand weights, not 14k) because the data is tiny;
* the same residual target as the ML models (growth minus latest growth);
* early stopping on the *last training periods* only, never on the test window, then a refit
  on all training rows for the chosen number of epochs;
* an ensemble over several random seeds, because single small networks are noisy.
"""

import copy

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from .config import SEED
from .features import feature_sets
from .models import Forecaster

MAX_CORRECTION = 0.35  # log points; same cap as the growth inputs


class MLP(nn.Module):
    def __init__(self, n_in, hidden=(32, 16), dropout=0.1):
        super().__init__()
        layers, prev = [], n_in
        for h in hidden:
            layers += [nn.Linear(prev, h), nn.ReLU(), nn.Dropout(dropout)]
            prev = h
        layers.append(nn.Linear(prev, 1))
        self.net = nn.Sequential(*layers)

    def forward(self, x_tab, x_seq=None):
        return self.net(x_tab).squeeze(-1)


class GRUNet(nn.Module):
    """Reads the last few quarters as a sequence, then adds static inputs (target quarter, company)."""

    def __init__(self, n_seq, n_static, hidden=16, dropout=0.1):
        super().__init__()
        self.gru = nn.GRU(n_seq, hidden, batch_first=True)
        self.head = nn.Sequential(nn.Linear(hidden + n_static, 16), nn.ReLU(), nn.Dropout(dropout), nn.Linear(16, 1))

    def forward(self, x_tab, x_seq):
        _, h = self.gru(x_seq)
        return self.head(torch.cat([h[-1], x_tab], dim=1)).squeeze(-1)


class TorchForecaster(Forecaster):
    family = 'DL'

    def __init__(self, name, kind='mlp', freq='Q', seeds=5, max_epochs=300, patience=30, lr=3e-3,
                 weight_decay=1e-3, batch_size=32, val_periods=4, anchor='yoy_0', device='cpu'):
        fs = feature_sets(freq)
        self.name, self.kind, self.anchor = name, kind, anchor
        self.tab_cols = fs['tabular'] if kind == 'mlp' else fs['static']
        self.seq_cols = fs['sequence'] if kind == 'gru' else None
        self.seeds = [SEED + i for i in range(seeds)]
        self.max_epochs, self.patience, self.lr, self.wd = max_epochs, patience, lr, weight_decay
        self.batch_size, self.val_periods, self.device = batch_size, val_periods, torch.device(device)

    # ---------- tensors
    def _arrays(self, rows):
        tab = rows[self.tab_cols].to_numpy(dtype=np.float32)
        seq = None
        if self.seq_cols:
            seq = np.stack([rows[step].to_numpy(dtype=np.float32) for step in self.seq_cols], axis=1)  # (n, L, f)
        return tab, seq

    def _scale(self, tab, seq):
        tab = (tab - self.tab_mu) / self.tab_sd
        if seq is not None:
            seq = (seq - self.seq_mu) / self.seq_sd
        to_t = lambda a: None if a is None else torch.tensor(a, dtype=torch.float32, device=self.device)
        return to_t(tab), to_t(seq)

    def _build(self, n_tab, n_seq):
        return MLP(n_tab) if self.kind == 'mlp' else GRUNet(n_seq, n_tab)

    def _train(self, seed, xt, xs, y, epochs=None, val=None):
        """Train one network. With `val`, return (best_epoch, net); otherwise train for `epochs`."""
        torch.manual_seed(seed)
        rng = np.random.default_rng(seed)
        net = self._build(xt.shape[1], None if xs is None else xs.shape[2]).to(self.device)
        opt = torch.optim.AdamW(net.parameters(), lr=self.lr, weight_decay=self.wd)
        loss_fn = nn.SmoothL1Loss()
        n = len(y)
        best, best_epoch, best_state, stale = np.inf, 1, None, 0
        for epoch in range(1, (epochs or self.max_epochs) + 1):
            net.train()
            for idx in np.array_split(rng.permutation(n), max(1, int(np.ceil(n / self.batch_size)))):
                opt.zero_grad()
                pred = net(xt[idx], None if xs is None else xs[idx])
                loss_fn(pred, y[idx]).backward()
                opt.step()
            if val is not None:
                vt, vs, vy = val
                net.eval()
                with torch.no_grad():
                    v = loss_fn(net(vt, vs), vy).item()
                if v < best - 1e-6:
                    best, best_epoch, best_state, stale = v, epoch, copy.deepcopy(net.state_dict()), 0
                else:
                    stale += 1
                    if stale >= self.patience:
                        break
        if val is not None:
            net.load_state_dict(best_state)
            return best_epoch, net
        return epochs, net

    # ---------- public API
    def fit(self, train):
        train = train.sort_values('target_t')
        tab, seq = self._arrays(train)
        # a column that is constant in a small training window (e.g. a quarter not seen yet) is
        # centred but not scaled, otherwise an unseen value at forecast time explodes
        safe_sd = lambda a: np.where(a.std(0) < 1e-6, 1.0, a.std(0))
        self.tab_mu, self.tab_sd = tab.mean(0), safe_sd(tab)
        if seq is not None:
            flat = seq.reshape(-1, seq.shape[2])
            self.seq_mu, self.seq_sd = flat.mean(0), safe_sd(flat)
        offset = train[self.anchor].to_numpy() if self.anchor else 0.0
        r = train['y'].to_numpy() - offset
        self.r_mu, self.r_sd = r.mean(), r.std() + 1e-6
        y = torch.tensor((r - self.r_mu) / self.r_sd, dtype=torch.float32, device=self.device)
        xt, xs = self._scale(tab, seq)

        # validation = the most recent `val_periods` target periods inside the training window
        periods = np.sort(train['target_t'].unique())
        is_val = train['target_t'].to_numpy() >= periods[-min(self.val_periods, len(periods) - 1)]
        fit_idx, val_idx = np.where(~is_val)[0], np.where(is_val)[0]
        sub = lambda a, i: None if a is None else a[i]

        self.nets, self.best_epochs = [], []
        for seed in self.seeds:
            best_epoch, _ = self._train(seed, sub(xt, fit_idx), sub(xs, fit_idx), y[fit_idx],
                                        val=(sub(xt, val_idx), sub(xs, val_idx), y[val_idx]))
            _, net = self._train(seed, xt, xs, y, epochs=best_epoch)     # refit on every training row
            net.eval()
            self.nets.append(net)
            self.best_epochs.append(best_epoch)
        return self

    def predict_growth(self, rows):
        tab, seq = self._arrays(rows)
        xt, xs = self._scale(tab, seq)
        with torch.no_grad():
            r = np.mean([net(xt, xs).cpu().numpy() for net in self.nets], axis=0) * self.r_sd + self.r_mu
        r = np.clip(r, -MAX_CORRECTION, MAX_CORRECTION)
        offset = rows[self.anchor].to_numpy() if self.anchor else 0.0
        return r + offset


def dl_models(freq: str, seeds: int = 5, device: str = 'cpu') -> dict:
    if freq != 'Q':
        return {}        # 40-odd annual rows cannot train a network; we say so instead of pretending
    tag = f'{seeds}-seed ensemble' if seeds > 1 else '1 seed'
    mlp, gru = f'MLP ({tag})', f'GRU ({tag})'
    return {
        mlp: lambda: TorchForecaster(mlp, 'mlp', freq, seeds=seeds, device=device),
        gru: lambda: TorchForecaster(gru, 'gru', freq, seeds=seeds, device=device),
    }
