"""
Feature engineering pipeline for Annual and Quarterly Indian Paint datasets.
Generates lagged variables, financial operational ratios, seasonal indicators,
rolling statistics, and future period target variables.
"""

from typing import Tuple, List, Optional
import pandas as pd
import numpy as np


def build_annual_features(
    df: pd.DataFrame,
    target_col: str = 'target_next_revenue',
    forecast_horizon: int = 1
) -> pd.DataFrame:
    """
    Engineer financial and operational features on Annual data.
    
    Target: next-period revenue (shift -forecast_horizon per company).
    """
    data = df.copy().sort_values(['company', 'fy_num']).reset_index(drop=True)
    
    # 1. Operational Ratios
    data['raw_material_ratio'] = data['raw_material_cost'] / data['revenue']
    data['capex_to_revenue'] = data['capex'] / data['revenue']
    data['ocf_to_revenue'] = data['operating_cash_flow'] / data['revenue']
    data['fcf_to_revenue'] = data['free_cash_flow'] / data['revenue']
    data['cash_to_assets'] = data['cash'] / data['total_assets']
    
    # 2. Historical Lags per company
    for lag in [1, 2]:
        data[f'revenue_lag{lag}'] = data.groupby('company')['revenue'].shift(lag)
        data[f'ebitda_lag{lag}'] = data.groupby('company')['ebitda'].shift(lag)
        data[f'pat_lag{lag}'] = data.groupby('company')['pat'].shift(lag)
        data[f'raw_mat_ratio_lag{lag}'] = data.groupby('company')['raw_material_ratio'].shift(lag)
        
    # 3. Growth momentum
    data['revenue_growth_lag1'] = data.groupby('company')['revenue_growth'].shift(1)
    data['ebitda_growth_lag1'] = data.groupby('company')['ebitda_growth'].shift(1)
    data['margin_expansion'] = data['ebitda_margin'] - data.groupby('company')['ebitda_margin'].shift(1)
    
    # 4. Target variable: Next period revenue
    data[target_col] = data.groupby('company')['revenue'].shift(-forecast_horizon)
    
    return data


def build_quarterly_features(
    df: pd.DataFrame,
    target_col: str = 'target_next_revenue',
    forecast_horizon: int = 1
) -> pd.DataFrame:
    """
    Engineer operational, seasonal, lag, and rolling features on Quarterly data.
    
    Target: next-quarter revenue (shift -forecast_horizon per company).
    """
    data = df.copy().sort_values(['company', 'period_end']).reset_index(drop=True)
    
    # 1. Operational cost ratio
    data['raw_material_ratio'] = data['raw_material_cost'] / data['revenue']
    
    # 2. Lags per company (Lag 1: previous quarter, Lag 4: same quarter last year)
    for lag in [1, 2, 3, 4]:
        data[f'revenue_lag{lag}'] = data.groupby('company')['revenue'].shift(lag)
        data[f'ebitda_lag{lag}'] = data.groupby('company')['ebitda'].shift(lag)
        data[f'pat_lag{lag}'] = data.groupby('company')['pat'].shift(lag)
        data[f'raw_mat_ratio_lag{lag}'] = data.groupby('company')['raw_material_ratio'].shift(lag)
        data[f'ebitda_margin_lag{lag}'] = data.groupby('company')['ebitda_margin'].shift(lag)
        
    # 3. QoQ and YoY momentum
    data['revenue_qoq_growth'] = (data['revenue'] - data['revenue_lag1']) / data['revenue_lag1'] * 100.0
    data['ebitda_qoq_growth'] = (data['ebitda'] - data['ebitda_lag1']) / data['ebitda_lag1'] * 100.0
    data['revenue_yoy_growth_calc'] = (data['revenue'] - data['revenue_lag4']) / data['revenue_lag4'] * 100.0
    
    # 4. Rolling statistics (4 quarters)
    data['rolling_mean_4q'] = data.groupby('company')['revenue'].transform(
        lambda s: s.rolling(window=4, min_periods=2).mean()
    )
    data['rolling_std_4q'] = data.groupby('company')['revenue'].transform(
        lambda s: s.rolling(window=4, min_periods=2).std()
    )
    data['rolling_ebitda_margin_4q'] = data.groupby('company')['ebitda_margin'].transform(
        lambda s: s.rolling(window=4, min_periods=2).mean()
    )
    
    # 5. Seasonality indicators
    for q in ['Q1', 'Q2', 'Q3', 'Q4']:
        data[f'quarter_{q}'] = (data['quarter'] == q).astype(float)
        
    # 6. Target variable
    data[target_col] = data.groupby('company')['revenue'].shift(-forecast_horizon)
    
    return data


def prepare_feature_matrix(
    data: pd.DataFrame,
    feature_cols: List[str],
    target_col: str = 'target_next_revenue',
    include_company_dummies: bool = True,
    drop_na_target: bool = True
) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, List[str]]:
    """
    Prepare X and y with optional one-hot company dummies and proper imputation.
    
    Returns:
        X (pd.DataFrame), y (pd.Series), clean_df (pd.DataFrame), final_feature_cols (List[str])
    """
    df = data.copy()
    
    if drop_na_target:
        df = df[df[target_col].notna()].copy()
        
    # Generate company dummies if requested
    dummy_cols = []
    if include_company_dummies and 'company' in df.columns:
        dummies = pd.get_dummies(df['company'], prefix='comp', drop_first=False, dtype=float)
        dummy_cols = list(dummies.columns)
        df = pd.concat([df, dummies], axis=1)
        
    all_feature_cols = [c for c in feature_cols if c in df.columns] + dummy_cols
    
    # Fill remaining operational feature NaNs with company median then overall median
    X = df[all_feature_cols].copy()
    for col in all_feature_cols:
        if col not in dummy_cols:
            if X[col].isna().any():
                # Fill with median per company where possible
                company_medians = df.groupby('company')[col].transform('median')
                X[col] = X[col].fillna(company_medians)
                # Fallback to global median
                X[col] = X[col].fillna(X[col].median())
                # If still NaN, fill 0
                X[col] = X[col].fillna(0.0)
                
    y = df[target_col].copy() if target_col in df.columns else None
    
    return X, y, df, all_feature_cols
