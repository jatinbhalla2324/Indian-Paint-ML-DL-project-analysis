import sys
from pathlib import Path

html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Indian Paint ML & DL Engineering Guide</title>
    <style>
        :root {
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #182234;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --accent-blue: #38bdf8;
            --accent-indigo: #818cf8;
            --accent-green: #34d399;
            --accent-orange: #fb923c;
            --border: #334155;
            --code-bg: #0b1120;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.7;
            padding: 40px 20px;
        }
        .container {
            max-width: 1100px;
            margin: 0 auto;
        }
        header {
            margin-bottom: 50px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 30px;
        }
        .badge {
            display: inline-block;
            background: linear-gradient(135deg, #38bdf822, #818cf822);
            color: var(--accent-blue);
            border: 1px solid #38bdf844;
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        h1 {
            font-size: 2.6rem;
            font-weight: 800;
            background: linear-gradient(135deg, #ffffff 40%, #94a3b8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 15px;
        }
        .lead {
            font-size: 1.2rem;
            color: var(--text-secondary);
            max-width: 850px;
        }
        .toc {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 50px;
        }
        .toc h3 {
            font-size: 1.1rem;
            color: var(--accent-blue);
            margin-bottom: 16px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .toc-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 10px;
        }
        .toc a {
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 0.95rem;
            transition: color 0.2s;
            display: flex;
            align-items: center;
        }
        .toc a:hover {
            color: var(--accent-blue);
        }
        .toc a span {
            color: var(--accent-indigo);
            font-weight: 700;
            margin-right: 8px;
        }
        section {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 36px;
            margin-bottom: 40px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        }
        h2 {
            font-size: 1.75rem;
            color: #ffffff;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            border-bottom: 1px solid #334155;
            padding-bottom: 12px;
        }
        h2 .sec-num {
            background: var(--accent-blue);
            color: #0f172a;
            font-size: 1rem;
            font-weight: 800;
            width: 32px;
            height: 32px;
            border-radius: 8px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-right: 14px;
        }
        h3 {
            font-size: 1.25rem;
            color: var(--accent-indigo);
            margin: 24px 0 12px 0;
        }
        p {
            color: var(--text-secondary);
            margin-bottom: 16px;
            font-size: 1.02rem;
        }
        ul, ol {
            color: var(--text-secondary);
            margin-left: 24px;
            margin-bottom: 20px;
        }
        li {
            margin-bottom: 8px;
        }
        strong {
            color: var(--text-primary);
        }
        .callout {
            background: #1e293b;
            border-left: 4px solid var(--accent-blue);
            padding: 18px 20px;
            border-radius: 0 8px 8px 0;
            margin: 20px 0;
            font-size: 0.98rem;
        }
        .callout-success {
            border-left-color: var(--accent-green);
        }
        .callout-warning {
            border-left-color: var(--accent-orange);
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 0.95rem;
        }
        th, td {
            padding: 12px 16px;
            text-align: left;
            border: 1px solid var(--border);
        }
        th {
            background: #1e293b;
            color: var(--accent-blue);
            font-weight: 600;
        }
        tr:nth-child(even) td {
            background: #151f30;
        }
        pre {
            background: var(--code-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
            overflow-x: auto;
            margin: 16px 0;
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 0.9rem;
            color: #e2e8f0;
        }
        code {
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            background: #0b1120;
            color: #38bdf8;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.88em;
        }
        .diagram {
            background: #0b1120;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            font-family: monospace;
            white-space: pre;
            color: #38bdf8;
            line-height: 1.4;
            overflow-x: auto;
            margin: 20px 0;
        }
        .tag {
            display: inline-block;
            background: #334155;
            color: #e2e8f0;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.78rem;
            font-weight: 600;
            margin-right: 6px;
        }
        footer {
            text-align: center;
            color: var(--text-muted);
            font-size: 0.85rem;
            padding: 40px 0 20px 0;
            border-top: 1px solid var(--border);
        }
    </style>
</head>
<body>
<div class="container">
    <header>
        <span class="badge">Master Architectural & Educational Guide</span>
        <h1>Indian Paint Companies ML & DL Architecture</h1>
        <p class="lead">A complete, end-to-end breakdown of the financial forecasting pipeline, data engineering, machine learning benchmarking, and PyTorch deep neural networks.</p>
    </header>

    <div class="toc">
        <h3>Contents</h3>
        <div class="toc-grid">
            <a href="#sec1"><span>01</span> Project Overview</a>
            <a href="#sec2"><span>02</span> Tech Stack & Tooling</a>
            <a href="#sec3"><span>03</span> Folder Structure Breakdown</a>
            <a href="#sec4"><span>04</span> System Architecture</a>
            <a href="#sec5"><span>05</span> End-to-End Execution Flow</a>
            <a href="#sec6"><span>06</span> Component Interconnections</a>
            <a href="#sec7"><span>07</span> Critical Code & Business Logic</a>
            <a href="#sec8"><span>08</span> Security & Error Handling</a>
            <a href="#sec9"><span>09</span> External Dependencies</a>
            <a href="#sec10"><span>10</span> Execution, Debugging & Deployment</a>
        </div>
    </div>

    <!-- SECTION 1 -->
    <section id="sec1">
        <h2><span class="sec-num">1</span> Project Overview</h2>
        <p><strong>The Core Research Question:</strong></p>
        <div class="callout">
            <em>"Can we use historical financial and operational data of Indian paint companies to predict their future financial performance, particularly next-period/year revenue?"</em>
        </div>
        <p><strong>The Answer:</strong> <strong>Yes.</strong> With careful feature engineering reflecting industry dynamics (raw material cost ratios, festive Q3 seasonality, and rolling moving averages), machine learning algorithms achieve a test $R^2$ of <strong>0.96 to 0.99</strong> with an average percentage error (MAPE) between <strong>9.5% and 12%</strong> on out-of-time unseen test data.</p>
        
        <h3>Industry Context & Economic Realities</h3>
        <p>The Indian paint market is an oligopoly dominated by 4 major listed companies:</p>
        <ul>
            <li><strong>Asian Paints</strong>: Undisputed market leader (~₹30,000+ Cr revenue).</li>
            <li><strong>Berger Paints</strong>: Second largest decorative paint manufacturer (~₹10,000+ Cr revenue).</li>
            <li><strong>Kansai Nerolac</strong>: Industrial & automotive coatings leader (~₹7,500+ Cr revenue).</li>
            <li><strong>Indigo Paints</strong>: Fastest growing challenger (~₹1,300+ Cr revenue).</li>
        </ul>
        <p>Financial outcomes are dictated by two primary external factors:</p>
        <ol>
            <li><strong>Raw Material Sensitivity</strong>: Over 50%–60% of revenue goes into crude oil derivatives (solvents, acrylic monomers) and titanium dioxide ($TiO_2$). Tracking the <code>raw_material_ratio</code> is critical to predicting gross margins and sales pricing adjustments.</li>
            <li><strong>Extreme Calendar Seasonality</strong>: Unlike annual figures, quarterly revenue exhibits sharp surges in <strong>Q3 (October–December)</strong> due to pre-Diwali festive home renovations, followed by lull periods in <strong>Q2 (monsoons)</strong>.</li>
        </ol>
    </section>

    <!-- SECTION 2 -->
    <section id="sec2">
        <h2><span class="sec-num">2</span> Tech Stack & Tooling</h2>
        <table>
            <thead>
                <tr>
                    <th>Component</th>
                    <th>Technology</th>
                    <th>Why This Was Chosen</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>Runtime Environment</strong></td>
                    <td>Python 3.14.3 + Virtual Environment (<code>.venv</code>)</td>
                    <td>Isolated execution preventing conflicts with system libraries on macOS.</td>
                </tr>
                <tr>
                    <td><strong>Data Processing</strong></td>
                    <td><code>pandas (3.0.6)</code> & <code>numpy (2.5.3)</code></td>
                    <td>Standard vectorized tabular operations for grouping, lagging, rolling run-rates, and multi-key joins.</td>
                </tr>
                <tr>
                    <td><strong>Classical Machine Learning</strong></td>
                    <td><code>scikit-learn (1.9.1)</code></td>
                    <td>Provides regularized linear models (<code>RidgeCV</code>, <code>LassoCV</code>, <code>ElasticNetCV</code>), ensemble trees (<code>RandomForest</code>, <code>GradientBoosting</code>), metrics, and pipelines.</td>
                </tr>
                <tr>
                    <td><strong>High-Performance Boosting</strong></td>
                    <td><code>xgboost (3.4.1)</code> & <code>lightgbm (4.7.0)</code></td>
                    <td>State-of-the-art gradient boosted trees with column subsampling, L1/L2 leaf penalties, and extreme execution speed.</td>
                </tr>
                <tr>
                    <td><strong>Deep Learning Framework</strong></td>
                    <td><code>PyTorch (2.14.1)</code></td>
                    <td>Allows custom neural network creation, explicit weight initialization (He/Kaiming), Batch Normalization, and custom loss functions.</td>
                </tr>
                <tr>
                    <td><strong>Hardware Acceleration</strong></td>
                    <td>Apple Silicon <strong>Metal Performance Shaders (MPS)</strong></td>
                    <td>Provides GPU acceleration natively on macOS without requiring external cloud GPUs. Falls back gracefully to CPU.</td>
                </tr>
                <tr>
                    <td><strong>Visualization</strong></td>
                    <td><code>matplotlib (3.11.2)</code> & <code>seaborn (0.13.2)</code></td>
                    <td>Publication-grade charting: residual plots, actual vs. predicted diagonals, error distributions, and historical trajectories.</td>
                </tr>
                <tr>
                    <td><strong>Interactive Notebooks</strong></td>
                    <td><code>nbformat</code> & <code>nbclient</code></td>
                    <td>Used to generate, validate, and execute reproducible Jupyter notebooks headlessly.</td>
                </tr>
            </tbody>
        </table>
    </section>

    <!-- SECTION 3 -->
    <section id="sec3">
        <h2><span class="sec-num">3</span> Folder Structure Breakdown</h2>
        <div class="diagram">indian-paint-ml-dl/
├── data/
│   └── processed/
│       ├── annual_reported.csv        # 85 rows: raw P&L, balance sheet & cash flow lines
│       ├── annual_features.csv        # 85 rows: derived annual ratios (margins, ROE, FCF)
│       ├── quarterly_reported.csv     # 312 rows: 3-month reported figures (no YTD blending)
│       ├── quarterly_features.csv     # 312 rows: quarterly derived growth & margin metrics
│       ├── sources.csv                # 3,082 rows: complete PDF page-level audit trail
│       └── document_index.csv         # 211 rows: official filings metadata & SHA-256
├── data_dictionary.md                 # Definitions, units (INR Cr, %), formulas
├── data_quality_report.md             # Accounting identities validation & restatements
├── notebooks/
│   ├── EDA.ipynb                      # Exploratory data analysis & quarterly distributions
│   ├── 01_annual_revenue_ml.ipynb     # Segment 1: Annual ML models & FY2027 forecast
│   ├── 02_quarterly_revenue_ml.ipynb  # Segment 2: Quarterly ML models & FY2027 Q1 forecast
│   └── 03_deep_learning_pytorch_quarterly.ipynb # Segment 3: PyTorch 4-layer Deep MLP
├── src/
│   ├── __init__.py                    # Unified package exports
│   ├── data_loader.py                 # Resilient data loading & basis filtering
│   ├── feature_engineering.py         # Multi-lag, operational ratio, and rolling transformers
│   ├── models_ml.py                   # 10-model registry, benchmarking & metric calculation
│   ├── models_dl.py                   # DeepFinancialMLP architecture & PyTorchFinancialTrainer
│   └── visualizations.py              # Seaborn/Matplotlib reusable plotting boilerplate
├── scripts/
│   ├── build_all_notebooks.py         # Notebook JSON generator script
│   └── build_and_execute_notebooks.py # Automated end-to-end headless execution engine
├── README.md                          # Full repository documentation & benchmark table
└── .venv/                             # Isolated Python 3.14 environment with installed wheels</div>
    </section>

    <!-- SECTION 4 -->
    <section id="sec4">
        <h2><span class="sec-num">4</span> System Architecture</h2>
        <p>The architecture is modular, decoupled, and designed following production ML best practices:</p>
        <div class="diagram">+-------------------------------------------------------------------------------+
|                             DATA LAYER (Processed CSVs)                       |
|   annual_reported.csv | annual_features.csv | quarterly_reported | features   |
+-------------------------------------------------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
|                      src/data_loader.py (Data Ingestion)                      |
|   - load_merged_annual(basis='Standalone')                                    |
|   - load_merged_quarterly(basis='Standalone')                                 |
+-------------------------------------------------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
|               src/feature_engineering.py (Feature & Target Engineering)       |
|   - Target Generation: target_next_revenue = shift(-1) per company             |
|   - Lags: t-1 (QoQ), t-2, t-4 (YoY Seasonality)                               |
|   - Operational Ratios: raw_material_cost / revenue, capex / revenue          |
|   - Rolling Run-Rates: 4-quarter rolling mean & std                           |
|   - Categorical Encoding: Company one-hot dummies, Quarter dummies (Q1-Q4)    |
+-------------------------------------------------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
|                    OUT-OF-TIME TEMPORAL SPLIT (Zero Data Leakage)             |
|   - Train: Historical periods up to FY2022 / FY2023 Q4                        |
|   - Test: Unseen future holdout periods (FY2023-FY2026 / FY2024-FY2026)       |
+-------------------------------------------------------------------------------+
                     /                                           \
                    v                                             v
+---------------------------------------+   +------------------------------------+
|         src/models_ml.py              |   |          src/models_dl.py          |
|  - Linear, Ridge, Lasso, ElasticNet   |   |  - DeepFinancialMLP (4 layers)     |
|  - SVR (RBF Kernel)                   |   |  - He (Kaiming Normal) Weight Init |
|  - Random Forest, GBDT, HistGB        |   |  - Batch Normalization 1D          |
|  - XGBoost, LightGBM                  |   |  - Huber Loss + AdamW Optimizer    |
|  - Metrics: MAE, RMSE, MAPE %, R2     |   |  - ReduceLROnPlateau + Early Stop  |
+---------------------------------------+   +------------------------------------+
                     \                                           /
                      v                                         v
+-------------------------------------------------------------------------------+
|                  src/visualizations.py (Diagnostics & Reporting)              |
|   - plot_actual_vs_predicted()      | plot_revenue_trajectories()             |
|   - plot_residuals()                | plot_model_comparison()                |
|   - plot_feature_importances()      | plot_training_history()                 |
+-------------------------------------------------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
|            FORWARD OUT-OF-SAMPLE FORECASTING (Predicting Future Horizon)       |
|   - Segment 1: FY2027 Annual Revenue Forecast                                 |
|   - Segment 2 & 3: FY2027 Q1 Quarterly Revenue Forecast                       |
+-------------------------------------------------------------------------------+</div>
    </section>

    <!-- SECTION 5 -->
    <section id="sec5">
        <h2><span class="sec-num">5</span> End-to-End Execution Flow</h2>
        <p>Here is what happens step-by-step when a notebook or pipeline runs:</p>
        <ol>
            <li><strong>Path Initialization & Import</strong>:
                <code>src</code> package is imported. <code>src/data_loader.py</code> dynamically resolves the relative path to <code>data/processed/</code>.
            </li>
            <li><strong>Ingestion & Basis Filtering</strong>:
                <code>load_merged_quarterly(basis='Standalone')</code> filters out consolidated figures so that series continuity is preserved, and performs an inner join on keys: <code>['company', 'basis', 'financial_year', 'quarter', 'period_end']</code>.
            </li>
            <li><strong>Feature Engineering</strong>:
                <code>build_quarterly_features()</code> calculates the target <code>target_next_revenue</code> by shifting <code>revenue</code> backward by 1 period (-1) grouped by company. For the latest row (FY2026 Q4), the target becomes <code>NaN</code>, representing the true forward prediction horizon.
            </li>
            <li><strong>Matrix Preparation & Imputation</strong>:
                <code>prepare_feature_matrix()</code> adds one-hot indicator columns (e.g. <code>comp_Asian Paints</code>, <code>comp_Berger Paints</code>) and imputes missing ratios using company-specific medians.
            </li>
            <li><strong>Temporal Slicing</strong>:
                A boolean mask partitions data: <code>train_mask = fy_num &lt;= 2023</code> and <code>test_mask = fy_num &gt; 2023</code>. No random shuffling is permitted.
            </li>
            <li><strong>Model Training</strong>:
                <ul>
                    <li>In ML: <code>benchmark_models()</code> iterates through all 10 registered models, fits them on <code>(X_train, y_train)</code>, and computes test predictions on <code>X_test</code>.</li>
                    <li>In PyTorch: <code>PyTorchFinancialTrainer</code> standardizes inputs via <code>StandardScaler</code>, initializes <code>DeepFinancialMLP</code> with He initialization, detects device (MPS/CPU), runs mini-batch training with Huber Loss, steps the learning rate scheduler, and restores the best validation weights via Early Stopping.</li>
                </ul>
            </li>
            <li><strong>Evaluation & Plotting</strong>:
                Predictions are evaluated using <code>compute_metrics()</code>. <code>src/visualizations.py</code> renders scatter plots, trajectories, and residual diagnostics.
            </li>
            <li><strong>Forward Projection</strong>:
                The fitted model is passed the latest FY2026 Q4 feature vector to produce the <strong>FY2027 Q1 revenue prediction</strong> for each paint company.
            </li>
        </ol>
    </section>

    <!-- SECTION 6 -->
    <section id="sec6">
        <h2><span class="sec-num">6</span> Component Breakdown & Connections</h2>
        <h3>1. Data Loading (<code>src/data_loader.py</code>)</h3>
        <p>Ensures that we never mix <em>Standalone</em> and <em>Consolidated</em> financial statements. Standalone statements are chosen by default because they span the entire historical period (FY2015 to FY2026) for Asian Paints, Berger, and Nerolac, and FY2018/FY2020 for Indigo Paints.</p>

        <h3>2. Feature Engineering (<code>src/feature_engineering.py</code>)</h3>
        <p>Translates raw balance-sheet and P&L figures into economic signals:</p>
        <ul>
            <li><code>raw_material_ratio</code>: Operational cost intensity.</li>
            <li><code>rolling_mean_4q</code>: Deseasonalized underlying annual run rate.</li>
            <li><code>revenue_lag4</code>: Baseline demand for the exact same quarter in the previous fiscal year.</li>
        </ul>

        <h3>3. Machine Learning Registry (<code>src/models_ml.py</code>)</h3>
        <p>Wraps all classical regression models. Models sensitive to feature scaling (Linear, Ridge, Lasso, ElasticNet, SVR) are wrapped in a <code>Pipeline([('scaler', StandardScaler()), ('reg', ...)])</code> to avoid scaling leaks.</p>

        <h3>4. Deep Learning Engine (<code>src/models_dl.py</code>)</h3>
        <p>Contains PyTorch tensors, Custom Dataset, Neural Architecture, and Trainer. Both inputs ($X$) and targets ($y$) are scaled using <code>StandardScaler</code>. Predictions are transformed back to real-world INR Crore using <code>scaler_y.inverse_transform()</code>.</p>

        <h3>5. Visual Diagnostics (<code>src/visualizations.py</code>)</h3>
        <p>Uses consistent Seaborn themes and palettes, ensuring all charts share font families, grid layouts, and color mappings across all three notebooks.</p>
    </section>

    <!-- SECTION 7 -->
    <section id="sec7">
        <h2><span class="sec-num">7</span> Important Code & Business Logic</h2>

        <h3>The Deep Neural Network Architecture (PyTorch)</h3>
        <pre><code>class DeepFinancialMLP(nn.Module):
    def __init__(self, input_dim: int, hidden_dims: List[int] = [128, 64, 32, 16], dropout_rate: float = 0.15):
        super(DeepFinancialMLP, self).__init__()
        assert len(hidden_dims) >= 4, "Must have at least 4 hidden layers as specified."
        
        layers = []
        prev_dim = input_dim
        for h_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, h_dim))
            layers.append(nn.BatchNorm1d(h_dim))
            layers.append(nn.ReLU())
            if dropout_rate > 0:
                layers.append(nn.Dropout(dropout_rate))
            prev_dim = h_dim
            
        layers.append(nn.Linear(prev_dim, 1)) # Output revenue
        self.network = nn.Sequential(*layers)
        self._init_weights()
        
    def _init_weights(self):
        """He (Kaiming Normal) initialization optimized for ReLU."""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, mode='fan_in', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0.0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1.0)
                nn.init.constant_(m.bias, 0.0)</code></pre>

        <h3>The Temporal Target Shift Logic</h3>
        <pre><code># Correct way to predict future period without leakage:
data['target_next_revenue'] = data.groupby('company')['revenue'].shift(-1)</code></pre>

        <h3>Why Batch Normalization Matters</h3>
        <p>In financial panel datasets, company revenue ranges vary from ₹300 Cr (Indigo Paints) to ₹8,000+ Cr (Asian Paints). <code>BatchNorm1d</code> standardizes feature representations dynamically across each batch, preventing early layer saturation and stabilizing gradient descent.</p>
    </section>

    <!-- SECTION 8 -->
    <section id="sec8">
        <h2><span class="sec-num">8</span> Security, Data Integrity & Error Handling</h2>
        <h3>Existing Integrity Measures</h3>
        <ul>
            <li><strong>Traceability</strong>: Every value in the dataset has an exact document name, page number, and SHA-256 hash in <code>sources.csv</code>.</li>
            <li><strong>Strict Accounting Identities</strong>: The raw extraction pipeline checked that <code>Revenue - Raw Material Cost &gt;= EBITDA</code> and that the sum of 4 quarters equals annual totals within 1% (accounting for restatements).</li>
            <li><strong>Leakage Prevention</strong>: Zero temporal shuffling. Training sets are strictly historical (&le; FY2022 or &le; FY2023), and test sets are strictly future holdouts.</li>
            <li><strong>Missing Value Safeguard</strong>: Missing operational ratios are imputed strictly within each company's historical median, falling back to industry median.</li>
        </ul>

        <h3>Identified Limitations & Vulnerabilities</h3>
        <div class="callout callout-warning">
            <strong>Key Engineering Watch-Outs:</strong>
            <ol>
                <li><strong>No Network Isolation Needed</strong>: This repository does not expose web APIs, HTTP ports, or databases, so remote network attacks are not applicable.</li>
                <li><strong>Dynamic Library Dependency (OpenMP)</strong>: <code>XGBoost</code> and <code>LightGBM</code> on macOS require <code>libomp.dylib</code>. The virtual environment dylibs were configured using <code>install_name_tool</code> to resolve this.</li>
                <li><strong>Small Panel Size</strong>: 169 quarters across 4 companies is a small panel for deep learning. Very deep networks (e.g. 10+ layers) risk memorization. Early stopping and dropout are essential guards.</li>
            </ol>
        </div>
    </section>

    <!-- SECTION 9 -->
    <section id="sec9">
        <h2><span class="sec-num">9</span> External Dependencies</h2>
        <p>The project runs entirely on local compute with zero third-party cloud API keys. The following libraries and system configurations are used:</p>
        <ul>
            <li><code>Python &gt;= 3.10</code> (Current environment: <code>Python 3.14.3</code>)</li>
            <li><code>PyTorch</code> (configured with Apple Silicon MPS acceleration)</li>
            <li><code>scikit-learn</code>, <code>xgboost</code>, <code>lightgbm</code></li>
            <li><code>pandas</code>, <code>numpy</code>, <code>scipy</code></li>
            <li><code>matplotlib</code>, <code>seaborn</code></li>
            <li><code>nbformat</code>, <code>nbclient</code>, <code>ipykernel</code></li>
        </ul>
    </section>

    <!-- SECTION 10 -->
    <section id="sec10">
        <h2><span class="sec-num">10</span> Execution, Debugging & Deployment</h2>
        <h3>How to Run the Code</h3>
        <p>1. Activate the virtual environment:</p>
        <pre><code>cd indian-paint-ml-dl
source .venv/bin/activate</code></pre>
        
        <p>2. Launch Jupyter Lab or VS Code:</p>
        <pre><code>jupyter lab notebooks/</code></pre>

        <p>3. Re-run or execute any notebook from the terminal:</p>
        <pre><code>python scripts/build_and_execute_notebooks.py</code></pre>

        <h3>Importing the Boilerplate in New Scripts</h3>
        <pre><code>import src

# Load quarterly data
df = src.load_merged_quarterly(basis="Standalone")

# Build features
df_feat = src.build_quarterly_features(df)
X, y, clean_df, feature_names = src.prepare_feature_matrix(df_feat, feature_cols=[...])

# Train deep neural net with He initialization and BatchNorm
trainer = src.PyTorchFinancialTrainer(hidden_dims=[128, 64, 32, 16])
trainer.fit(X_train, y_train, X_val, y_val)</code></pre>
    </section>

    <footer>
        <p>Indian Paint Industry Financial ML/DL Engineering Reference • Generated for Jatin Bhalla</p>
    </footer>
</div>
</body>
</html>
"""

target_path = Path(__file__).resolve().parent / "indian_paint_ml_dl_guide.html"
target_path.write_text(html_content, encoding="utf-8")
print(f"HTML guide generated at: {target_path}")
