"""Load the reported financials into a clean company x period panel."""

import numpy as np
import pandas as pd

from .config import BASIS, DATA_DIR, FIRST_FY


def period_index(financial_year: pd.Series, quarter: pd.Series | None = None) -> pd.Series:
    """Integer time index: FY2015 = 0 (annual) or FY2015 Q1 = 0 (quarterly)."""
    fy = financial_year.str.extract(r'FY(\d{4})', expand=False).astype(int)
    if quarter is None:
        return fy - FIRST_FY
    return (fy - FIRST_FY) * 4 + quarter.str[1].astype(int) - 1


def period_label(t: int, freq: str) -> str:
    if freq == 'A':
        return f'FY{FIRST_FY + t}'
    return f'FY{FIRST_FY + t // 4} Q{t % 4 + 1}'


def label_to_t(label: str, freq: str) -> int:
    fy = int(label[2:6])
    if freq == 'A':
        return fy - FIRST_FY
    return (fy - FIRST_FY) * 4 + int(label[-1]) - 1


def load_panel(freq: str = 'Q', basis: str = BASIS, data_dir=DATA_DIR) -> pd.DataFrame:
    """Return one row per company and period with revenue, margins and a time index `t`.

    Raises if a company has a gap in its series, because every lag below is a row shift.
    """
    if freq not in ('Q', 'A'):
        raise ValueError("freq must be 'Q' or 'A'")
    name = 'quarterly_reported.csv' if freq == 'Q' else 'annual_reported.csv'
    raw = pd.read_csv(data_dir / name, na_values=['', 'NA'])
    raw = raw[raw['basis'] == basis].copy()

    cols = ['company', 'financial_year', 'period_end', 'revenue', 'raw_material_cost', 'ebitda', 'pat']
    if freq == 'Q':
        cols.insert(2, 'quarter')
    df = raw[cols].copy()
    df['t'] = period_index(df['financial_year'], df['quarter'] if freq == 'Q' else None)
    df['period'] = [period_label(t, freq) for t in df['t']]
    df['period_end'] = pd.to_datetime(df['period_end'])
    df = df.dropna(subset=['revenue'])
    df = df.sort_values(['company', 't']).reset_index(drop=True)

    df['gross_margin'] = (df['revenue'] - df['raw_material_cost']) / df['revenue'] * 100
    df['ebitda_margin'] = df['ebitda'] / df['revenue'] * 100
    # A missing margin (e.g. Berger FY2026 Q3) takes the previous period's value: past data only.
    df['margin_filled'] = df['gross_margin'].isna() | df['ebitda_margin'].isna()
    df[['gross_margin', 'ebitda_margin']] = df.groupby('company')[['gross_margin', 'ebitda_margin']].ffill()
    df['log_revenue'] = np.log(df['revenue'])

    gaps = df.groupby('company')['t'].apply(lambda s: (s.diff().dropna() != 1).any())
    if gaps.any():
        raise ValueError(f'Non-consecutive periods for: {list(gaps[gaps].index)}')
    return df
