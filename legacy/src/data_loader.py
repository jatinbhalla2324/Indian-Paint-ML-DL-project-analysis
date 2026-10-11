"""
Data loading and preprocessing utilities for Indian Paint Financial Dataset.
Handles loading reported and derived feature CSVs, merging them, and filtering by accounting basis.
"""

from pathlib import Path
from typing import Tuple, Optional
import pandas as pd
import numpy as np


def get_default_data_dir() -> Path:
    """Resolve data directory relative to project root or current working directory."""
    cwd = Path.cwd()
    if (cwd / 'data' / 'processed').exists():
        return cwd / 'data' / 'processed'
    if (cwd.parent / 'data' / 'processed').exists():
        return cwd.parent / 'data' / 'processed'
    return Path(__file__).resolve().parents[2] / 'data' / 'processed'


def load_raw_data(data_dir: Optional[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load all 4 core financial CSVs.
    
    Returns:
        tuple: (annual_reported, annual_features, quarterly_reported, quarterly_features)
    """
    dpath = Path(data_dir) if data_dir else get_default_data_dir()
    
    ar = pd.read_csv(dpath / 'annual_reported.csv', na_values=['', 'NA'])
    af = pd.read_csv(dpath / 'annual_features.csv', na_values=['', 'NA'])
    qr = pd.read_csv(dpath / 'quarterly_reported.csv', na_values=['', 'NA'])
    qf = pd.read_csv(dpath / 'quarterly_features.csv', na_values=['', 'NA'])
    
    return ar, af, qr, qf


def load_merged_annual(basis: str = 'Standalone', data_dir: Optional[str] = None) -> pd.DataFrame:
    """
    Load and merge annual reported and feature datasets on common keys.
    
    Args:
        basis: 'Standalone' or 'Consolidated'. Default is 'Standalone'.
        data_dir: Directory containing processed CSVs.
        
    Returns:
        pd.DataFrame sorted by company and financial year.
    """
    ar, af, _, _ = load_raw_data(data_dir)
    
    if basis:
        ar = ar[ar['basis'] == basis].copy()
        af = af[af['basis'] == basis].copy()
        
    join_keys = ['company', 'basis', 'financial_year', 'period_end']
    feat_cols = [c for c in af.columns if c not in join_keys]
    
    merged = pd.merge(ar, af[join_keys + feat_cols], on=join_keys, how='inner')
    
    merged['fy_num'] = merged['financial_year'].str.extract(r'FY(\d+)').astype(int)
    merged = merged.sort_values(['company', 'fy_num']).reset_index(drop=True)
    merged['period_end'] = pd.to_datetime(merged['period_end'])
    
    return merged


def load_merged_quarterly(basis: str = 'Standalone', data_dir: Optional[str] = None) -> pd.DataFrame:
    """
    Load and merge quarterly reported and feature datasets on common keys.
    
    Args:
        basis: 'Standalone' or 'Consolidated'. Default is 'Standalone'.
        data_dir: Directory containing processed CSVs.
        
    Returns:
        pd.DataFrame sorted chronologically by company and period_end.
    """
    _, _, qr, qf = load_raw_data(data_dir)
    
    if basis:
        qr = qr[qr['basis'] == basis].copy()
        qf = qf[qf['basis'] == basis].copy()
        
    join_keys = ['company', 'basis', 'financial_year', 'quarter', 'period_end']
    feat_cols = [c for c in qf.columns if c not in join_keys]
    
    merged = pd.merge(qr, qf[join_keys + feat_cols], on=join_keys, how='inner')
    
    merged['period_end'] = pd.to_datetime(merged['period_end'])
    merged['fy_num'] = merged['financial_year'].str.extract(r'FY(\d+)').astype(int)
    merged = merged.sort_values(['company', 'period_end']).reset_index(drop=True)
    
    return merged
