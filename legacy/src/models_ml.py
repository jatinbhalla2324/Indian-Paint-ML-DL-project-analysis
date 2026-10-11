"""
Machine Learning modeling suite for Indian Paint Revenue Forecasting.
Provides model registry, time-series split evaluation, metrics calculation,
and standardized benchmarking across 9+ algorithms.
"""

from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, RidgeCV, LassoCV, ElasticNetCV
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, HistGradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score, max_error
import xgboost as xgb
import lightgbm as lgb


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calculate standard financial forecasting performance metrics."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    
    mae = mean_absolute_error(y_true, y_pred)
    rmse = root_mean_squared_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    max_err = max_error(y_true, y_pred)
    
    # Avoid zero division in MAPE
    mask = y_true != 0
    mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100.0 if np.any(mask) else np.nan
    
    return {
        'MAE': mae,
        'RMSE': rmse,
        'MAPE (%)': mape,
        'R2': r2,
        'Max Error': max_err
    }


def get_model_registry(random_state: int = 42) -> Dict[str, Any]:
    """
    Instantiate diverse regression algorithms with optimal hyperparameters for financial panel data.
    """
    models = {
        'Linear Regression': Pipeline([
            ('scaler', StandardScaler()),
            ('reg', LinearRegression())
        ]),
        'Ridge Regression': Pipeline([
            ('scaler', StandardScaler()),
            ('reg', RidgeCV(alphas=np.logspace(-3, 3, 20)))
        ]),
        'Lasso Regression': Pipeline([
            ('scaler', StandardScaler()),
            ('reg', LassoCV(alphas=np.logspace(-3, 3, 20), max_iter=10000, tol=1e-3, random_state=random_state))
        ]),
        'ElasticNet': Pipeline([
            ('scaler', StandardScaler()),
            ('reg', ElasticNetCV(l1_ratio=[0.1, 0.5, 0.7, 0.9], alphas=np.logspace(-3, 3, 20), max_iter=10000, tol=1e-3, random_state=random_state))
        ]),
        'Support Vector Regressor': Pipeline([
            ('scaler', StandardScaler()),
            ('reg', SVR(kernel='rbf', C=100.0, epsilon=1.0))
        ]),
        'Random Forest': RandomForestRegressor(
            n_estimators=150, max_depth=6, min_samples_split=3, random_state=random_state, n_jobs=-1
        ),
        'Gradient Boosting': GradientBoostingRegressor(
            n_estimators=100, max_depth=3, learning_rate=0.05, subsample=0.8, random_state=random_state
        ),
        'Hist Gradient Boosting': HistGradientBoostingRegressor(
            max_iter=100, max_depth=4, learning_rate=0.05, random_state=random_state
        ),
        'XGBoost': xgb.XGBRegressor(
            n_estimators=100, max_depth=3, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, random_state=random_state, n_jobs=-1
        ),
        'LightGBM': lgb.LGBMRegressor(
            n_estimators=100, max_depth=4, num_leaves=15, learning_rate=0.05, subsample=0.8, random_state=random_state, verbose=-1, n_jobs=-1
        )
    }
    return models


def benchmark_models(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    random_state: int = 42
) -> Tuple[pd.DataFrame, Dict[str, Any], Dict[str, np.ndarray]]:
    """
    Train and evaluate all registered models on Out-Of-Time test set.
    
    Returns:
        metrics_df: Summary DataFrame sorted by RMSE.
        fitted_models: Dictionary of trained model objects.
        predictions: Dictionary of predicted arrays on test set.
    """
    registry = get_model_registry(random_state=random_state)
    results = []
    fitted_models = {}
    predictions = {}
    
    for name, model in registry.items():
        try:
            model.fit(X_train, y_train)
            y_pred_train = model.predict(X_train)
            y_pred_test = model.predict(X_test)
            
            m_train = compute_metrics(y_train, y_pred_train)
            m_test = compute_metrics(y_test, y_pred_test)
            
            fitted_models[name] = model
            predictions[name] = y_pred_test
            
            results.append({
                'Model': name,
                'Train RMSE': m_train['RMSE'],
                'Test RMSE': m_test['RMSE'],
                'Test MAE': m_test['MAE'],
                'Test MAPE (%)': m_test['MAPE (%)'],
                'Train R2': m_train['R2'],
                'Test R2': m_test['R2'],
                'Test Max Error': m_test['Max Error']
            })
        except Exception as e:
            print(f'Error training {name}: {e}')
            
    metrics_df = pd.DataFrame(results).sort_values('Test RMSE').reset_index(drop=True)
    return metrics_df, fitted_models, predictions


def get_feature_importances(model: Any, feature_names: List[str]) -> pd.DataFrame:
    """Extract feature importances or standardized coefficients from a fitted model."""
    # If Pipeline (Linear / Ridge / Lasso / SVR)
    if isinstance(model, Pipeline):
        reg = model.named_steps.get('reg')
        if hasattr(reg, 'coef_'):
            coefs = np.abs(reg.coef_).ravel()
            return pd.DataFrame({'feature': feature_names, 'importance': coefs}).sort_values('importance', ascending=False)
    # Tree / Ensemble
    if hasattr(model, 'feature_importances_'):
        return pd.DataFrame({'feature': feature_names, 'importance': model.feature_importances_}).sort_values('importance', ascending=False)
    return pd.DataFrame(columns=['feature', 'importance'])
