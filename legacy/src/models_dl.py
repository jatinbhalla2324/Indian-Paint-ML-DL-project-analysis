"""
PyTorch Deep Learning architecture and trainer for Indian Paint Revenue Prediction.
Implements a Deep Multi-Layer Perceptron (>= 4 hidden layers) with:
- He (Kaiming Normal) weight initialization
- Batch Normalization for training stability
- ReLU non-linear activation functions
- Dropout regularization
- Apple Silicon (MPS) / CUDA / CPU automatic hardware acceleration
- Huber/MSE loss, AdamW optimizer, ReduceLROnPlateau scheduler, and Early Stopping.
"""

import copy
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import StandardScaler
from src.models_ml import compute_metrics


def get_device() -> torch.device:
    """Automatically pick Apple Silicon MPS, NVIDIA CUDA, or fallback to CPU."""
    if torch.backends.mps.is_available():
        return torch.device('mps')
    elif torch.cuda.is_available():
        return torch.device('cuda')
    return torch.device('cpu')


class DeepFinancialMLP(nn.Module):
    """
    Deep Feedforward Network designed for tabular financial time-series forecasting.
    Includes at least 4 hidden layers, Batch Normalization, He initialization, and ReLU.
    """
    def __init__(
        self,
        input_dim: int,
        hidden_dims: List[int] = [128, 64, 32, 16],
        dropout_rate: float = 0.15
    ):
        super(DeepFinancialMLP, self).__init__()
        assert len(hidden_dims) >= 4, 'Must have at least 4 hidden layers as specified.'
        
        layers = []
        prev_dim = input_dim
        
        for i, h_dim in enumerate(hidden_dims):
            layers.append(nn.Linear(prev_dim, h_dim))
            layers.append(nn.BatchNorm1d(h_dim))
            layers.append(nn.ReLU())
            if dropout_rate > 0:
                layers.append(nn.Dropout(dropout_rate))
            prev_dim = h_dim
            
        # Final output regression layer
        layers.append(nn.Linear(prev_dim, 1))
        
        self.network = nn.Sequential(*layers)
        self._init_weights()
        
    def _init_weights(self):
        """Apply He (Kaiming Normal) initialization optimized for ReLU activations."""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, mode='fan_in', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0.0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1.0)
                nn.init.constant_(m.bias, 0.0)
                
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x).squeeze(-1)


class TabularFinancialDataset(Dataset):
    """PyTorch Dataset wrapping scaled feature matrix and target vectors."""
    def __init__(self, X: np.ndarray, y: Optional[np.ndarray] = None):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32) if y is not None else None
        
    def __len__(self) -> int:
        return len(self.X)
        
    def __getitem__(self, idx: int):
        if self.y is not None:
            return self.X[idx], self.y[idx]
        return self.X[idx]


class PyTorchFinancialTrainer:
    """
    Production-grade training loop for PyTorch Deep Neural Network.
    Handles data scaling, learning rate scheduling, early stopping, and history tracking.
    """
    def __init__(
        self,
        hidden_dims: List[int] = [128, 64, 32, 16],
        dropout_rate: float = 0.15,
        lr: float = 0.005,
        weight_decay: float = 1e-4,
        loss_fn_type: str = 'huber',
        device: Optional[torch.device] = None
    ):
        self.hidden_dims = hidden_dims
        self.dropout_rate = dropout_rate
        self.lr = lr
        self.weight_decay = weight_decay
        self.loss_fn_type = loss_fn_type
        self.device = device or get_device()
        
        self.scaler_X = StandardScaler()
        self.scaler_y = StandardScaler()
        self.model: Optional[DeepFinancialMLP] = None
        self.history: Dict[str, List[float]] = {
            'train_loss': [],
            'val_loss': [],
            'val_mae': [],
            'val_rmse': []
        }
        
    def fit(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame,
        y_val: pd.Series,
        epochs: int = 250,
        batch_size: int = 16,
        patience: int = 35,
        verbose: bool = True
    ) -> 'PyTorchFinancialTrainer':
        """Train deep neural network with early stopping and learning rate scheduling."""
        X_tr = self.scaler_X.fit_transform(X_train)
        y_tr = self.scaler_y.fit_transform(y_train.values.reshape(-1, 1)).ravel()
        
        X_v = self.scaler_X.transform(X_val)
        y_v = self.scaler_y.transform(y_val.values.reshape(-1, 1)).ravel()
        
        train_ds = TabularFinancialDataset(X_tr, y_tr)
        val_ds = TabularFinancialDataset(X_v, y_v)
        
        train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=len(val_ds), shuffle=False)
        
        self.model = DeepFinancialMLP(
            input_dim=X_tr.shape[1],
            hidden_dims=self.hidden_dims,
            dropout_rate=self.dropout_rate
        ).to(self.device)
        
        if self.loss_fn_type == 'huber':
            criterion = nn.SmoothL1Loss()
        else:
            criterion = nn.MSELoss()
            
        optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=self.lr,
            weight_decay=self.weight_decay
        )
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode='min', factor=0.5, patience=10, min_lr=1e-5
        )
        
        best_val_loss = float('inf')
        best_model_weights = None
        epochs_no_improve = 0
        
        for epoch in range(1, epochs + 1):
            # Training phase
            self.model.train()
            train_losses = []
            for bx, by in train_loader:
                bx, by = bx.to(self.device), by.to(self.device)
                optimizer.zero_grad()
                pred = self.model(bx)
                loss = criterion(pred, by)
                loss.backward()
                nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                optimizer.step()
                train_losses.append(loss.item())
                
            avg_train_loss = np.mean(train_losses)
            
            # Validation phase
            self.model.eval()
            val_losses = []
            val_preds_scaled = []
            with torch.no_grad():
                for bx, by in val_loader:
                    bx, by = bx.to(self.device), by.to(self.device)
                    pred = self.model(bx)
                    loss = criterion(pred, by)
                    val_losses.append(loss.item())
                    val_preds_scaled.append(pred.cpu().numpy())
                    
            avg_val_loss = np.mean(val_losses)
            scheduler.step(avg_val_loss)
            
            # Unscale predictions to calculate real world INR crore MAE & RMSE
            y_pred_unscaled = self.scaler_y.inverse_transform(val_preds_scaled[0].reshape(-1, 1)).ravel()
            val_metrics = compute_metrics(y_val.values, y_pred_unscaled)
            
            self.history['train_loss'].append(avg_train_loss)
            self.history['val_loss'].append(avg_val_loss)
            self.history['val_mae'].append(val_metrics['MAE'])
            self.history['val_rmse'].append(val_metrics['RMSE'])
            
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                best_model_weights = copy.deepcopy(self.model.state_dict())
                epochs_no_improve = 0
            else:
                epochs_no_improve += 1
                
            if verbose and (epoch == 1 or epoch % 25 == 0 or epoch == epochs):
                print(f'Epoch {epoch:3d}/{epochs} | Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f} | Val RMSE: {val_metrics["RMSE"]:.2f} Cr | Val MAE: {val_metrics["MAE"]:.2f} Cr')
                
            if epochs_no_improve >= patience:
                if verbose:
                    print(f'Early stopping triggered at epoch {epoch} (Best Val Loss: {best_val_loss:.4f})')
                break
                
        if best_model_weights is not None:
            self.model.load_state_dict(best_model_weights)
            
        return self
        
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Generate unscaled revenue predictions in INR crore."""
        assert self.model is not None, 'Model must be fitted before predict.'
        self.model.eval()
        X_scaled = self.scaler_X.transform(X)
        X_tensor = torch.tensor(X_scaled, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            preds_scaled = self.model(X_tensor).cpu().numpy().reshape(-1, 1)
        preds_unscaled = self.scaler_y.inverse_transform(preds_scaled).ravel()
        return preds_unscaled
