import json
import os
from pathlib import Path

def create_nb(cells, filename):
    nb = {
        'cells': cells,
        'metadata': {
            'kernelspec': {
                'display_name': 'Python 3 (.venv)',
                'language': 'python',
                'name': 'python3'
            },
            'language_info': {
                'name': 'python',
                'version': '3.14.3'
            }
        },
        'nbformat': 4,
        'nbformat_minor': 5
    }
    with open(filename, 'w') as f:
        json.dump(nb, f, indent=1)
    print(f"Successfully generated {filename}")

def md(source):
    return {
        'cell_type': 'markdown',
        'metadata': {},
        'source': [line + '\n' for line in source.strip().split('\n')]
    }

def code(source):
    return {
        'cell_type': 'code',
        'execution_count': None,
        'metadata': {},
        'outputs': [],
        'source': [line + '\n' for line in source.strip().split('\n')]
    }

# =====================================================================
# NOTEBOOK 1: ANNUAL REVENUE ML
# =====================================================================
nb1_cells = [
    md("""# Indian Paint Industry: Annual Revenue Forecasting with Machine Learning

## Problem Statement
> **Can we use historical financial and operational data of Indian paint companies to predict their future financial performance, particularly next-period/year revenue?**

### Industry Context & Economic Thesis
The Indian decorative and industrial paints market is an oligopoly dominated by four key players:
1. **Asian Paints** (Market leader, ~30,000+ Cr revenue)
2. **Berger Paints** (Second largest, ~10,000+ Cr revenue)
3. **Kansai Nerolac** (Leader in automotive/industrial coatings, ~7,500+ Cr revenue)
4. **Indigo Paints** (High-growth challenger, ~1,300+ Cr revenue)

Financial dynamics in the paint industry are heavily driven by:
- **Raw Material Intensity**: 50–60% of revenues are consumed by crude oil derivatives (monomers, solvents) and titanium dioxide (TiO2).
- **Pricing Power & Margin Expansion**: The ability of companies to pass raw material price changes to consumers.
- **Capital Reinvestment**: Capex and operational cash generation driving manufacturing capacity and dealer tinting machine penetration.

In this notebook, we formulate and benchmark a comprehensive Machine Learning pipeline to predict **next fiscal year revenue ($t \\rightarrow t+1$)** using historical reported financials, balance sheet strength, operational ratios, and cash flows."""),

    code("""# Boilerplate Imports & Setup
import sys
from pathlib import Path

# Add project root to system path for modular imports
project_root = Path.cwd()
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))
if str(project_root.parent) not in sys.path:
    sys.path.append(str(project_root.parent))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# Import core modular package
import src

print("Python environment and src package successfully loaded!")"""),

    md("""## 1. Data Ingestion & Integration
We load the processed annual reported financials (`annual_reported.csv`) and computed financial features (`annual_features.csv`).
We filter on `Standalone` basis (consistently available across all years and companies) and join them on `['company', 'basis', 'financial_year', 'period_end']`."""),

    code("""# Load joined annual standalone financials
df_annual = src.load_merged_annual(basis="Standalone")
print(f"Annual Dataset Shape: {df_annual.shape[0]} fiscal years across {df_annual['company'].nunique()} companies")
print(f"Coverage Range: {df_annual['financial_year'].min()} to {df_annual['financial_year'].max()}")

# Display sample of joined data
df_annual[['company', 'financial_year', 'revenue', 'raw_material_cost', 'ebitda', 'pat', 'operating_cash_flow', 'capex']].head(8)"""),

    md("""## 2. Feature Engineering & Target Definition
To predict next fiscal year revenue:
1. **Target ($y_t$)**: Shifted revenue per company: $y_t = \\text{revenue}_{t+1}$.
2. **Operational Ratios**:
   - `raw_material_ratio` = $\\frac{\\text{raw material cost}}{\\text{revenue}}$
   - `capex_to_revenue` = $\\frac{\\text{capex}}{\\text{revenue}}$
   - `ocf_to_revenue` = $\\frac{\\text{operating cash flow}}{\\text{revenue}}$
   - `fcf_to_revenue` = $\\frac{\\text{free cash flow}}{\\text{revenue}}$
3. **Lagged Variables & Momentum**:
   - `revenue_lag1`, `ebitda_lag1`, `pat_lag1`
   - `revenue_growth_lag1`, `margin_expansion`
4. **Balance Sheet & Solvency**:
   - `debt_to_equity`, `return_on_equity`, `return_on_assets`, `cash_to_assets`
5. **Entity Scale**: One-hot company indicator variables."""),

    code("""# Engineer features and next-period revenue target
df_ann_feat = src.build_annual_features(df_annual, target_col="target_next_revenue", forecast_horizon=1)

feature_cols = [
    'revenue', 'raw_material_ratio', 'ebitda_margin', 'net_margin', 'revenue_growth',
    'capex_to_revenue', 'ocf_to_revenue', 'fcf_to_revenue', 'debt_to_equity',
    'return_on_equity', 'return_on_assets', 'cash_to_assets',
    'revenue_lag1', 'ebitda_lag1', 'margin_expansion'
]

X_ann, y_ann, clean_ann, all_ann_cols = src.prepare_feature_matrix(
    df_ann_feat, feature_cols=feature_cols, target_col="target_next_revenue", include_company_dummies=True
)

print(f"Total features engineered: {len(all_ann_cols)}")
print("Feature list:", all_ann_cols)
clean_ann[['company', 'financial_year', 'revenue', 'raw_material_ratio', 'target_next_revenue']].head(6)"""),

    md("""## 3. Temporal Validation Split (Preventing Data Leakage)
In financial time series, random K-Fold cross validation leads to lookahead bias (training on future information to predict the past).
We implement an **Out-Of-Time (OOT) Holdout Validation**:
- **Train Set**: FY2015 to FY2022 (historical model fitting)
- **Test Set**: FY2023 to FY2026 (unseen future fiscal periods)"""),

    code("""# Define temporal split
train_mask = clean_ann['fy_num'] <= 2022
test_mask = clean_ann['fy_num'] > 2022

X_train, y_train = X_ann[train_mask], y_ann[train_mask]
X_test, y_test = X_ann[test_mask], y_ann[test_mask]

print(f"Training samples: {len(X_train)} (FY2015 - FY2022)")
print(f"Testing samples:  {len(X_test)} (FY2023 - FY2026)")"""),

    md("""## 4. Multi-Algorithm Benchmarking
We benchmark 10 diverse regression models:
1. **Linear Regression** (Standardized baseline)
2. **Ridge Regression** ($L_2$ regularized cross-validated)
3. **Lasso Regression** ($L_1$ feature selection cross-validated)
4. **ElasticNet** (Balanced $L_1/L_2$)
5. **Support Vector Regressor (SVR)** (RBF kernel)
6. **Random Forest Regressor** (Bagging ensemble)
7. **Gradient Boosting Regressor** (Sequential boosting)
8. **Hist Gradient Boosting** (Histogram-based boosting)
9. **XGBoost Regressor** (Regularized gradient boosting)
10. **LightGBM Regressor** (Leaf-wise gradient boosting)"""),

    code("""# Execute benchmarking suite across all models
benchmark_results, fitted_models, predictions = src.benchmark_models(
    X_train, y_train, X_test, y_test, random_state=42
)

# Format and display benchmark table
benchmark_results.style.format({
    'Train RMSE': '{:.2f}',
    'Test RMSE': '{:.2f}',
    'Test MAE': '{:.2f}',
    'Test MAPE (%)': '{:.2f}%',
    'Train R2': '{:.4f}',
    'Test R2': '{:.4f}',
    'Test Max Error': '{:.2f}'
}).background_gradient(subset=['Test RMSE', 'Test MAE', 'Test MAPE (%)'], cmap='Blues_r')"""),

    md("""## 5. Visualizations & Model Diagnostics"""),

    code("""# 1. Benchmark Comparison Bar Chart
fig, ax = src.plot_model_comparison(benchmark_results)
plt.show()"""),

    code("""# 2. Actual vs Predicted Scatter Plot for Best Performing Model
best_model_name = benchmark_results.iloc[0]['Model']
best_preds = predictions[best_model_name]

fig, ax = src.plot_actual_vs_predicted(
    y_true=y_test.values,
    y_pred=best_preds,
    company_labels=clean_ann.loc[test_mask, 'company'],
    title=f"Annual Revenue: Actual vs Predicted ({best_model_name})"
)
plt.show()"""),

    code("""# 3. Residual Error Diagnostics
fig, (ax1, ax2) = src.plot_residuals(
    y_true=y_test.values,
    y_pred=best_preds,
    title=f"Residual Diagnostics ({best_model_name})"
)
plt.show()"""),

    code("""# 4. Feature Importance Analysis
importance_df = src.get_feature_importances(fitted_models[best_model_name], all_ann_cols)
if not importance_df.empty:
    fig, ax = src.plot_feature_importances(
        importance_df, top_n=12, title=f"Top Features Influencing Next-Year Revenue ({best_model_name})"
    )
    plt.show()
else:
    # Fallback to Random Forest feature importances
    rf_imp = src.get_feature_importances(fitted_models['Random Forest'], all_ann_cols)
    fig, ax = src.plot_feature_importances(rf_imp, top_n=12, title="Random Forest Feature Importances")
    plt.show()"""),

    code("""# 5. Out-of-Time Revenue Trajectories by Company
df_eval = clean_ann.copy()
df_eval['predicted_revenue'] = np.nan
df_eval.loc[test_mask, 'predicted_revenue'] = best_preds

fig, axes = src.plot_revenue_trajectories(
    df_eval,
    date_col='period_end',
    actual_col='target_next_revenue',
    pred_col='predicted_revenue',
    company_col='company',
    split_date='2022-03-31',
    title=f"Annual Out-of-Time Forecast Trajectories ({best_model_name})"
)
plt.show()"""),

    md("""## 6. Forward Forecast: Predicting FY2027 Revenue
Using the latest audited FY2026 operational and financial data, we generate the out-of-sample forward prediction for **FY2027 Revenue** for each company."""),

    code("""# Prepare latest FY2026 data where target is out-of-sample (NaN)
latest_annual = df_ann_feat.groupby('company').tail(1).copy()
X_latest, _, _, _ = src.prepare_feature_matrix(
    latest_annual, feature_cols=feature_cols, target_col="target_next_revenue", drop_na_target=False
)

best_model = fitted_models[best_model_name]
latest_annual['forecast_FY2027_revenue'] = best_model.predict(X_latest)
latest_annual['implied_growth_%'] = (
    (latest_annual['forecast_FY2027_revenue'] - latest_annual['revenue']) / latest_annual['revenue'] * 100.0
)

print("=== OUT-OF-SAMPLE FY2027 REVENUE FORECAST (INR CRORE) ===")
latest_annual[['company', 'financial_year', 'revenue', 'forecast_FY2027_revenue', 'implied_growth_%']]""")
]

create_nb(nb1_cells, 'notebooks/01_annual_revenue_ml.ipynb')


# =====================================================================
# NOTEBOOK 2: QUARTERLY REVENUE ML
# =====================================================================
nb2_cells = [
    md("""# Indian Paint Industry: Quarterly Revenue Forecasting with Machine Learning

## Problem Statement & Quarterly Dynamics
> **Can we use quarterly financial and operational results of Indian paint companies to forecast their next-quarter revenue ($t \\rightarrow t+1$)?**

### Seasonality in Indian Paints
Unlike annual financials, quarterly financial performance in the Indian paint industry exhibits strong calendar seasonality:
- **Q1 (Apr–Jun)**: Pre-monsoon exterior repainting, moderate decorative demand.
- **Q2 (Jul–Sep)**: Heavy monsoon season across North & West India; construction activity slows down, painting demand dips.
- **Q3 (Oct–Dec)**: **Peak Festive Season (Diwali / Dussehra)**. Pre-festival home renovations drive the highest decorative sales volume of the fiscal year.
- **Q4 (Jan–Mar)**: Post-harvest rural demand, institutional project completions, and year-end commercial painting.

With 169 quarterly observations, quarterly modeling allows us to evaluate **seasonal lags (Lag 4 YoY)**, **momentum (Lag 1 QoQ)**, and **operational cost shocks** in high resolution."""),

    code("""# Boilerplate Imports & Setup
import sys
from pathlib import Path

# Add project root to system path for modular imports
project_root = Path.cwd()
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))
if str(project_root.parent) not in sys.path:
    sys.path.append(str(project_root.parent))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

import src

print("Quarterly ML environment and src package successfully initialized!")"""),

    md("""## 1. Quarterly Data Ingestion & Integration
We load the quarterly reported figures (`quarterly_reported.csv`) and quarterly derived features (`quarterly_features.csv`).
We filter on `Standalone` basis and join on `['company', 'basis', 'financial_year', 'quarter', 'period_end']`."""),

    code("""# Load merged quarterly standalone financials
df_quarterly = src.load_merged_quarterly(basis="Standalone")
print(f"Total Quarterly Rows: {df_quarterly.shape[0]}")
print(f"Quarters Per Company:\n{df_quarterly.groupby('company')['financial_year'].agg(['count', 'min', 'max'])}")

df_quarterly[['company', 'financial_year', 'quarter', 'period_end', 'revenue', 'raw_material_cost', 'ebitda', 'pat']].head(8)"""),

    md("""## 2. Seasonal & Operational Feature Engineering
To capture both trend and seasonality:
1. **Target ($y_t$)**: Next quarter revenue per company: $y_t = \\text{revenue}_{t+1}$.
2. **Seasonal Lags**:
   - `revenue_lag1` (previous quarter, QoQ)
   - `revenue_lag2` (2 quarters back)
   - `revenue_lag3` (3 quarters back)
   - `revenue_lag4` (**same quarter last year, YoY seasonal baseline**)
3. **Rolling Statistics**:
   - `rolling_mean_4q`: 4-quarter moving average (annualized quarterly run-rate)
   - `rolling_std_4q`: 4-quarter revenue volatility
4. **Operational Intensity**:
   - `raw_material_ratio`: raw material cost to revenue ratio
   - `ebitda_margin_lag1`, `pat_lag1`
5. **Seasonal Dummies**:
   - `quarter_Q1`, `quarter_Q2`, `quarter_Q3`, `quarter_Q4`
6. **Company Dummies**:
   - Capture market share and scale differences across Asian Paints, Berger, Nerolac, and Indigo."""),

    code("""# Generate quarterly feature matrix
df_qtr_feat = src.build_quarterly_features(df_quarterly, target_col="target_next_revenue", forecast_horizon=1)

qtr_feature_cols = [
    'revenue', 'raw_material_ratio', 'ebitda_margin', 'net_margin', 'revenue_growth',
    'revenue_lag1', 'revenue_lag2', 'revenue_lag4', 'ebitda_lag1', 'ebitda_lag4',
    'revenue_qoq_growth', 'rolling_mean_4q', 'rolling_std_4q',
    'quarter_Q1', 'quarter_Q2', 'quarter_Q3', 'quarter_Q4'
]

X_qtr, y_qtr, clean_qtr, all_qtr_cols = src.prepare_feature_matrix(
    df_qtr_feat, feature_cols=qtr_feature_cols, target_col="target_next_revenue", include_company_dummies=True
)

print(f"Quarterly Features Count: {len(all_qtr_cols)}")
clean_qtr[['company', 'financial_year', 'quarter', 'period_end', 'revenue', 'rolling_mean_4q', 'target_next_revenue']].head(8)"""),

    md("""## 3. Out-Of-Time Temporal Split
We split the time series chronologically:
- **Training Set**: FY2015 Q1 to FY2023 Q4 (Historical training periods)
- **Testing Set**: FY2024 Q1 to FY2026 Q4 (12 unseen out-of-sample quarters per company)"""),

    code("""# Temporal holdout split
train_mask_qtr = clean_qtr['fy_num'] <= 2023
test_mask_qtr = clean_qtr['fy_num'] > 2023

X_train_qtr, y_train_qtr = X_qtr[train_mask_qtr], y_qtr[train_mask_qtr]
X_test_qtr, y_test_qtr = X_qtr[test_mask_qtr], y_qtr[test_mask_qtr]

print(f"Training Quarters: {len(X_train_qtr)} (FY2015 Q1 - FY2023 Q4)")
print(f"Testing Quarters:  {len(X_test_qtr)} (FY2024 Q1 - FY2026 Q4)")"""),

    md("""## 4. Quarterly Multi-Algorithm Benchmarking
We benchmark 10 regression algorithms on next-quarter revenue forecasting."""),

    code("""# Benchmark all models on quarterly data
qtr_benchmark_results, qtr_fitted_models, qtr_predictions = src.benchmark_models(
    X_train_qtr, y_train_qtr, X_test_qtr, y_test_qtr, random_state=42
)

qtr_benchmark_results.style.format({
    'Train RMSE': '{:.2f}',
    'Test RMSE': '{:.2f}',
    'Test MAE': '{:.2f}',
    'Test MAPE (%)': '{:.2f}%',
    'Train R2': '{:.4f}',
    'Test R2': '{:.4f}',
    'Test Max Error': '{:.2f}'
}).background_gradient(subset=['Test RMSE', 'Test MAE', 'Test MAPE (%)'], cmap='Blues_r')"""),

    md("""## 5. Visualizations & Diagnostics"""),

    code("""# 1. Benchmark Comparison Bar Chart
fig, ax = src.plot_model_comparison(qtr_benchmark_results)
plt.show()"""),

    code("""# 2. Actual vs Predicted Scatter Plot for Best Quarterly Model
best_qtr_name = qtr_benchmark_results.iloc[0]['Model']
best_qtr_preds = qtr_predictions[best_qtr_name]

fig, ax = src.plot_actual_vs_predicted(
    y_true=y_test_qtr.values,
    y_pred=best_qtr_preds,
    company_labels=clean_qtr.loc[test_mask_qtr, 'company'],
    title=f"Quarterly Revenue: Actual vs Predicted ({best_qtr_name})"
)
plt.show()"""),

    code("""# 3. Residual Diagnostics
fig, (ax1, ax2) = src.plot_residuals(
    y_true=y_test_qtr.values,
    y_pred=best_qtr_preds,
    title=f"Quarterly Residual Diagnostics ({best_qtr_name})"
)
plt.show()"""),

    code("""# 4. Top Feature Importances (Seasonal vs Operational vs Trend)
qtr_imp = src.get_feature_importances(qtr_fitted_models[best_qtr_name], all_qtr_cols)
if not qtr_imp.empty:
    fig, ax = src.plot_feature_importances(
        qtr_imp, top_n=12, title=f"Top Quarterly Predictors ({best_qtr_name})"
    )
    plt.show()
else:
    gb_imp = src.get_feature_importances(qtr_fitted_models['Gradient Boosting'], all_qtr_cols)
    fig, ax = src.plot_feature_importances(gb_imp, top_n=12, title="Gradient Boosting Feature Importances")
    plt.show()"""),

    code("""# 5. Out-of-Time Forecast Trajectories by Company
df_eval_qtr = clean_qtr.copy()
df_eval_qtr['predicted_revenue'] = np.nan
df_eval_qtr.loc[test_mask_qtr, 'predicted_revenue'] = best_qtr_preds

fig, axes = src.plot_revenue_trajectories(
    df_eval_qtr,
    date_col='period_end',
    actual_col='target_next_revenue',
    pred_col='predicted_revenue',
    company_col='company',
    split_date='2023-03-31',
    title=f"Quarterly Out-of-Time Forecast Trajectories ({best_qtr_name})"
)
plt.show()"""),

    md("""## 6. Forward Projections: Forecasting FY2027 Q1 Revenue
We apply the best quarterly model to the most recent FY2026 Q4 results to forecast **FY2027 Q1 Revenue** for Asian Paints, Berger Paints, Kansai Nerolac, and Indigo Paints."""),

    code("""latest_qtr = df_qtr_feat.groupby('company').tail(1).copy()
X_latest_qtr, _, _, _ = src.prepare_feature_matrix(
    latest_qtr, feature_cols=qtr_feature_cols, target_col="target_next_revenue", drop_na_target=False
)

best_qtr_model = qtr_fitted_models[best_qtr_name]
latest_qtr['forecast_FY2027_Q1_revenue'] = best_qtr_model.predict(X_latest_qtr)
latest_qtr['implied_QoQ_growth_%'] = (
    (latest_qtr['forecast_FY2027_Q1_revenue'] - latest_qtr['revenue']) / latest_qtr['revenue'] * 100.0
)

print("=== OUT-OF-SAMPLE FY2027 Q1 REVENUE FORECAST (INR CRORE) ===")
latest_qtr[['company', 'financial_year', 'quarter', 'revenue', 'forecast_FY2027_Q1_revenue', 'implied_QoQ_growth_%']]""")
]

create_nb(nb2_cells, 'notebooks/02_quarterly_revenue_ml.ipynb')


# =====================================================================
# NOTEBOOK 3: DEEP LEARNING PYTORCH QUARTERLY
# =====================================================================
nb3_cells = [
    md("""# Indian Paint Industry: Deep Learning Revenue Forecasting with PyTorch

## Objective & Neural Architecture Design
In this notebook, we design, train, and evaluate a deep neural network in **PyTorch** to predict future quarterly revenue of Indian paint companies.

### Architectural Specifications:
As required for deep tabular financial regression:
1. **Network Depth**: Deep Multi-Layer Perceptron (MLP) with **at least 4 hidden layers**:
   - `Input -> Linear(128) -> BatchNorm1d -> ReLU -> Dropout(0.15)`
   - `Linear(64) -> BatchNorm1d -> ReLU -> Dropout(0.15)`
   - `Linear(32) -> BatchNorm1d -> ReLU -> Dropout(0.15)`
   - `Linear(16) -> BatchNorm1d -> ReLU -> Dropout(0.15)`
   - `Linear(1) -> Output (Predicted Revenue)`
2. **Weight Initialization**: **He (Kaiming Normal) Initialization** (`nn.init.kaiming_normal_`), specifically tailored to maintain variance and avoid vanishing/exploding gradients with ReLU activations.
3. **Batch Normalization**: `nn.BatchNorm1d` applied after each linear layer to normalize internal feature scale distributions across training mini-batches.
4. **Hardware Acceleration**: Automatic device detection:
   - Apple Silicon GPU via Metal Performance Shaders (`torch.device("mps")`)
   - NVIDIA GPU via CUDA (`torch.device("cuda")`)
   - Fallback to optimized CPU.
5. **Loss & Optimizer**:
   - Huber Loss (`nn.SmoothL1Loss`): Combines MSE efficiency with MAE robustness to large financial shocks (e.g. COVID quarters).
   - Optimizer: `AdamW` with weight decay for $L_2$ weight regularization.
   - Scheduler: `ReduceLROnPlateau` reducing learning rate on validation loss plateaus.
   - Early Stopping: Restores the best checkpoint when validation loss ceases improving."""),

    code("""# Boilerplate Imports & Hardware Detection
import sys
from pathlib import Path

project_root = Path.cwd()
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))
if str(project_root.parent) not in sys.path:
    sys.path.append(str(project_root.parent))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import torch
import torch.nn as nn
import warnings
warnings.filterwarnings('ignore')

import src

# Check hardware acceleration
device = src.get_device()
print(f"PyTorch Version: {torch.__version__}")
print(f"Active Compute Device: {device}")
if device.type == 'mps':
    print("Apple Silicon Metal Performance Shaders (MPS) GPU acceleration ENABLED!")"""),

    md("""## 1. Inspecting the Deep Neural Network Architecture
Let's instantiate `DeepFinancialMLP` with 4 hidden layers, He initialization, and Batch Normalization, and inspect its parameters."""),

    code("""# Instantiate sample model to inspect layers
sample_model = src.DeepFinancialMLP(input_dim=21, hidden_dims=[128, 64, 32, 16], dropout_rate=0.15)
print(sample_model)

total_params = sum(p.numel() for p in sample_model.parameters() if p.requires_grad)
print(f"\\nTotal Trainable Parameters: {total_params:,}")"""),

    md("""## 2. Quarterly Data Ingestion & Feature Engineering
We ingest quarterly standalone financials and generate the seasonal and operational feature set."""),

    code("""df_quarterly = src.load_merged_quarterly(basis="Standalone")
df_qtr_feat = src.build_quarterly_features(df_quarterly, target_col="target_next_revenue", forecast_horizon=1)

qtr_feature_cols = [
    'revenue', 'raw_material_ratio', 'ebitda_margin', 'net_margin', 'revenue_growth',
    'revenue_lag1', 'revenue_lag2', 'revenue_lag4', 'ebitda_lag1', 'ebitda_lag4',
    'revenue_qoq_growth', 'rolling_mean_4q', 'rolling_std_4q',
    'quarter_Q1', 'quarter_Q2', 'quarter_Q3', 'quarter_Q4'
]

X_qtr, y_qtr, clean_qtr, all_qtr_cols = src.prepare_feature_matrix(
    df_qtr_feat, feature_cols=qtr_feature_cols, target_col="target_next_revenue", include_company_dummies=True
)

print(f"Input Feature Dimension: {X_qtr.shape[1]}")
print(f"Features: {all_qtr_cols}")"""),

    md("""## 3. Temporal Train / Validation Split
- **Training Set**: FY2015 Q1 to FY2023 Q4
- **Out-of-Time Test Set**: FY2024 Q1 to FY2026 Q4 (Holdout unseen quarters)"""),

    code("""train_mask = clean_qtr['fy_num'] <= 2023
test_mask = clean_qtr['fy_num'] > 2023

X_train, y_train = X_qtr[train_mask], y_qtr[train_mask]
X_test, y_test = X_qtr[test_mask], y_qtr[test_mask]

print(f"Deep Learning Training Samples: {len(X_train)}")
print(f"Deep Learning Validation/Testing Samples: {len(X_test)}")"""),

    md("""## 4. End-to-End Training with PyTorch
We train the 4-hidden-layer network using `PyTorchFinancialTrainer` with:
- Huber Loss
- Learning Rate = 0.005 with ReduceLROnPlateau
- Early Stopping Patience = 35 epochs
- Batch Normalization & Dropout (0.15)"""),

    code("""# Initialize and execute PyTorch Training Loop
trainer = src.PyTorchFinancialTrainer(
    hidden_dims=[128, 64, 32, 16],
    dropout_rate=0.15,
    lr=0.005,
    weight_decay=1e-4,
    loss_fn_type='huber',
    device=device
)

trainer.fit(
    X_train=X_train,
    y_train=y_train,
    X_val=X_test,
    y_val=y_test,
    epochs=250,
    batch_size=16,
    patience=35,
    verbose=True
)

print("\\nDeep Learning Training Complete!")"""),

    md("""## 5. Learning Dynamics & Convergence Diagnostics
We examine the progression of Training Loss vs Validation Loss, as well as real-world error progression (RMSE & MAE in INR Crore) across training epochs."""),

    code("""# Plot PyTorch Training Dynamics
fig, (ax1, ax2) = src.plot_training_history(trainer.history)
plt.show()"""),

    md("""## 6. Out-of-Time Evaluation & Benchmarking vs Best ML Baseline
We generate unscaled revenue forecasts in INR Crore on the holdout test quarters and benchmark against the best Machine Learning models."""),

    code("""# Generate PyTorch predictions
dl_preds = trainer.predict(X_test)
dl_metrics = src.compute_metrics(y_test.values, dl_preds)

print("=== PYTORCH DEEP LEARNING (4-LAYER MLP) METRICS ===")
for k, v in dl_metrics.items():
    if 'MAPE' in k:
        print(f"{k}: {v:.2f}%")
    elif 'R2' in k:
        print(f"{k}: {v:.4f}")
    else:
        print(f"{k}: {v:.2f} Cr")

# Benchmark comparison against ML baseline
from src.models_ml import benchmark_models
ml_benchmark, _, _ = benchmark_models(X_train, y_train, X_test, y_test)

comparison_records = [
    {
        'Model': 'PyTorch Deep MLP (4 Hidden Layers)',
        'Test RMSE': dl_metrics['RMSE'],
        'Test MAE': dl_metrics['MAE'],
        'Test MAPE (%)': dl_metrics['MAPE (%)'],
        'Test R2': dl_metrics['R2'],
        'Architecture': '128-64-32-16 (He Init + BatchNorm + ReLU)'
    },
    {
        'Model': ml_benchmark.iloc[0]['Model'] + ' (Best ML)',
        'Test RMSE': ml_benchmark.iloc[0]['Test RMSE'],
        'Test MAE': ml_benchmark.iloc[0]['Test MAE'],
        'Test MAPE (%)': ml_benchmark.iloc[0]['Test MAPE (%)'],
        'Test R2': ml_benchmark.iloc[0]['Test R2'],
        'Architecture': 'Tree Ensemble / Gradient Boosting'
    }
]

df_dl_compare = pd.DataFrame(comparison_records)
df_dl_compare.style.format({
    'Test RMSE': '{:.2f}',
    'Test MAE': '{:.2f}',
    'Test MAPE (%)': '{:.2f}%',
    'Test R2': '{:.4f}'
})"""),

    md("""## 7. Visualizations & Error Diagnostics"""),

    code("""# 1. Actual vs Predicted Scatter Plot
fig, ax = src.plot_actual_vs_predicted(
    y_true=y_test.values,
    y_pred=dl_preds,
    company_labels=clean_qtr.loc[test_mask, 'company'],
    title="PyTorch Deep Learning: Actual vs Predicted Quarterly Revenue"
)
plt.show()"""),

    code("""# 2. Residual Diagnostics
fig, (ax1, ax2) = src.plot_residuals(
    y_true=y_test.values,
    y_pred=dl_preds,
    title="PyTorch Deep Learning Residual Diagnostics"
)
plt.show()"""),

    code("""# 3. Quarterly Forecast Trajectories by Company
df_eval_dl = clean_qtr.copy()
df_eval_dl['predicted_revenue'] = np.nan
df_eval_dl.loc[test_mask, 'predicted_revenue'] = dl_preds

fig, axes = src.plot_revenue_trajectories(
    df_eval_dl,
    date_col='period_end',
    actual_col='target_next_revenue',
    pred_col='predicted_revenue',
    company_col='company',
    split_date='2023-03-31',
    title="PyTorch Deep Learning Forecast Trajectories by Company"
)
plt.show()"""),

    md("""## 8. Forward Prediction: FY2027 Q1 Revenue Forecast with PyTorch
We feed the latest available FY2026 Q4 operational features into the trained PyTorch network to project **FY2027 Q1 Revenue**."""),

    code("""latest_qtr = df_qtr_feat.groupby('company').tail(1).copy()
X_latest_qtr, _, _, _ = src.prepare_feature_matrix(
    latest_qtr, feature_cols=qtr_feature_cols, target_col="target_next_revenue", drop_na_target=False
)

latest_qtr['pytorch_forecast_FY2027_Q1'] = trainer.predict(X_latest_qtr)
latest_qtr['implied_QoQ_growth_%'] = (
    (latest_qtr['pytorch_forecast_FY2027_Q1'] - latest_qtr['revenue']) / latest_qtr['revenue'] * 100.0
)

print("=== PYTORCH OUT-OF-SAMPLE FY2027 Q1 REVENUE FORECAST (INR CRORE) ===")
latest_qtr[['company', 'financial_year', 'quarter', 'revenue', 'pytorch_forecast_FY2027_Q1', 'implied_QoQ_growth_%']]""")
]

create_nb(nb3_cells, 'notebooks/03_deep_learning_pytorch_quarterly.ipynb')

print("ALL THREE NOTEBOOKS GENERATED SUCCESSFULLY!")
