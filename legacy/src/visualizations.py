"""
Visualization module using Seaborn and Matplotlib for financial forecasting analysis.
Provides reusable boilerplate functions for:
- Actual vs Predicted scatter plots
- Time-series revenue trajectories
- Residual diagnostics
- Cross-model benchmark bar charts
- Feature importance rankings
- Deep Learning loss curves
"""

from typing import List, Optional, Dict, Any
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# Set cohesive modern theme
sns.set_theme(style='whitegrid', font='sans-serif')
plt.rcParams['figure.autolayout'] = True
plt.rcParams['font.size'] = 11


def plot_actual_vs_predicted(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    company_labels: Optional[pd.Series] = None,
    title: str = 'Actual vs Predicted Next-Period Revenue (INR Crore)',
    figsize: tuple = (9, 7)
):
    """Scatter plot comparing true vs forecasted revenue with 45-degree identity line."""
    fig, ax = plt.subplots(figsize=figsize)
    
    df_plot = pd.DataFrame({'Actual': y_true, 'Predicted': y_pred})
    if company_labels is not None:
        df_plot['Company'] = company_labels.values
        sns.scatterplot(data=df_plot, x='Actual', y='Predicted', hue='Company', style='Company', s=90, alpha=0.85, ax=ax)
    else:
        sns.scatterplot(data=df_plot, x='Actual', y='Predicted', color='#1f77b4', s=90, alpha=0.85, ax=ax)
        
    min_val = min(np.min(y_true), np.min(y_pred)) * 0.95
    max_val = max(np.max(y_true), np.max(y_pred)) * 1.05
    ax.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, label='Perfect Forecast (y = x)')
    
    ax.set_xlim(min_val, max_val)
    ax.set_ylim(min_val, max_val)
    ax.set_title(title, fontsize=14, fontweight='bold', pad=12)
    ax.set_xlabel('Actual Revenue (INR Cr)', fontsize=12)
    ax.set_ylabel('Predicted Revenue (INR Cr)', fontsize=12)
    ax.legend(frameon=True, facecolor='white', framealpha=0.9)
    plt.tight_layout()
    return fig, ax


def plot_revenue_trajectories(
    df_results: pd.DataFrame,
    date_col: str = 'period_end',
    actual_col: str = 'revenue',
    pred_col: str = 'predicted_revenue',
    company_col: str = 'company',
    split_date: Optional[str] = None,
    title: str = 'Historical Trajectory & Out-of-Time Forecast by Company',
    figsize: tuple = (15, 9)
):
    """Multi-panel or faceted time-series line plot showing actual trajectory vs model predictions."""
    companies = df_results[company_col].unique()
    n_comp = len(companies)
    
    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=figsize, sharex=False)
    axes = axes.flatten()
    
    for i, comp in enumerate(companies):
        ax = axes[i]
        c_df = df_results[df_results[company_col] == comp].sort_values(date_col)
        
        ax.plot(c_df[date_col], c_df[actual_col], 'o-', label='Actual Revenue', color='#2b5c8f', lw=2.2, ms=4)
        if pred_col in c_df.columns:
            pred_sub = c_df.dropna(subset=[pred_col])
            ax.plot(pred_sub[date_col], pred_sub[pred_col], 's--', label='Model Forecast', color='#e05d26', lw=2.0, ms=4)
            
        if split_date:
            ax.axvline(pd.to_datetime(split_date), color='grey', linestyle=':', lw=1.8, label='Train / Test Split')
            
        ax.set_title(f'{comp}', fontsize=13, fontweight='bold')
        ax.set_xlabel('Period', fontsize=10)
        ax.set_ylabel('Revenue (INR Cr)', fontsize=10)
        ax.tick_params(axis='x', rotation=35)
        ax.legend(frameon=True, facecolor='white', framealpha=0.85, fontsize=9)
        
    plt.suptitle(title, fontsize=15, fontweight='bold', y=1.02)
    plt.tight_layout()
    return fig, axes


def plot_residuals(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    title: str = 'Residual Diagnostics',
    figsize: tuple = (14, 5)
):
    """Diagnostic plots: Residuals vs Predicted and Residual Distribution."""
    residuals = y_true - y_pred
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
    
    # 1. Residuals vs Predicted
    sns.scatterplot(x=y_pred, y=residuals, color='#34495e', alpha=0.75, s=65, ax=ax1)
    ax1.axhline(0, color='r', linestyle='--', lw=2)
    ax1.set_title('Residuals vs Fitted Values', fontsize=13, fontweight='bold')
    ax1.set_xlabel('Predicted Revenue (INR Cr)', fontsize=11)
    ax1.set_ylabel('Residual (Actual - Predicted)', fontsize=11)
    
    # 2. Residual Distribution Histogram
    sns.histplot(residuals, kde=True, color='#2980b9', bins=20, ax=ax2)
    ax2.axvline(0, color='r', linestyle='--', lw=2)
    ax2.set_title('Distribution of Forecasting Errors', fontsize=13, fontweight='bold')
    ax2.set_xlabel('Residual (INR Cr)', fontsize=11)
    ax2.set_ylabel('Count', fontsize=11)
    
    plt.tight_layout()
    return fig, (ax1, ax2)


def plot_model_comparison(
    metrics_df: pd.DataFrame,
    metrics: List[str] = ['Test RMSE', 'Test MAE', 'Test MAPE (%)'],
    figsize: tuple = (14, 6)
):
    """Bar chart comparing multiple models on error metrics."""
    df_melt = pd.melt(metrics_df, id_vars=['Model'], value_vars=metrics, var_name='Metric', value_name='Value')
    
    fig, ax = plt.subplots(figsize=figsize)
    sns.barplot(data=df_melt, x='Model', y='Value', hue='Metric', palette='viridis', ax=ax)
    
    ax.set_title('Model Performance Benchmark on Out-of-Time Test Set', fontsize=14, fontweight='bold', pad=12)
    ax.set_xlabel('Algorithm', fontsize=12)
    ax.set_ylabel('Metric Value', fontsize=12)
    ax.tick_params(axis='x', rotation=30)
    ax.legend(title='Metric', frameon=True)
    plt.tight_layout()
    return fig, ax


def plot_feature_importances(
    importance_df: pd.DataFrame,
    top_n: int = 15,
    title: str = 'Top Feature Drivers of Next-Period Revenue',
    figsize: tuple = (10, 6)
):
    """Horizontal bar chart ranking top predictive features."""
    top_df = importance_df.head(top_n).sort_values('importance', ascending=True)
    
    fig, ax = plt.subplots(figsize=figsize)
    sns.barplot(data=top_df, x='importance', y='feature', palette='mako', ax=ax)
    
    ax.set_title(title, fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel('Relative Importance / Coefficient Magnitude', fontsize=11)
    ax.set_ylabel('Feature Name', fontsize=11)
    plt.tight_layout()
    return fig, ax


def plot_training_history(
    history: Dict[str, List[float]],
    title: str = 'PyTorch Deep Learning Training Dynamics',
    figsize: tuple = (14, 5)
):
    """Dual plot showing Loss progression and Error metrics across epochs."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
    epochs = range(1, len(history['train_loss']) + 1)
    
    # 1. Training & Validation Loss
    ax1.plot(epochs, history['train_loss'], label='Train Loss (Huber/MSE)', color='#2980b9', lw=2)
    ax1.plot(epochs, history['val_loss'], label='Validation Loss', color='#e74c3c', lw=2)
    ax1.set_title('Loss Curve across Epochs', fontsize=13, fontweight='bold')
    ax1.set_xlabel('Epoch', fontsize=11)
    ax1.set_ylabel('Loss', fontsize=11)
    ax1.legend(frameon=True)
    
    # 2. Validation Metrics in INR Cr
    if 'val_rmse' in history and len(history['val_rmse']) > 0:
        ax2.plot(epochs, history['val_rmse'], label='Validation RMSE (INR Cr)', color='#27ae60', lw=2)
        ax2.plot(epochs, history['val_mae'], label='Validation MAE (INR Cr)', color='#f39c12', lw=2)
        ax2.set_title('Validation Error (INR Crore) Progression', fontsize=13, fontweight='bold')
        ax2.set_xlabel('Epoch', fontsize=11)
        ax2.set_ylabel('Error in INR Crore', fontsize=11)
        ax2.legend(frameon=True)
        
    plt.tight_layout()
    return fig, (ax1, ax2)
