"""
Tabular Diffusion Model for Synthetic Clinical Trial Data Generation

This module implements a Denoising Diffusion Probabilistic Model (DDPM)
adapted for tabular medical data. It generates realistic synthetic vitals
records by learning the underlying data distribution from real pilot data.

Architecture:
- Forward process: Gradually adds Gaussian noise to data
- Reverse process: Learned denoising network removes noise step-by-step
- MLP-based network suitable for tabular data

Reference: Ho et al. "Denoising Diffusion Probabilistic Models" (NeurIPS 2020)
Adapted for tabular data following TabDDPM approach
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from typing import Dict, List, Optional, Tuple
import os
from pathlib import Path


class TabularDataset(Dataset):
    """Dataset for tabular vitals data"""

    def __init__(self, data: pd.DataFrame, numerical_cols: List[str],
                 categorical_cols: List[str], stats: Optional[Dict] = None):
        """
        Args:
            data: DataFrame with vitals records
            numerical_cols: List of numerical column names
            categorical_cols: List of categorical column names
            stats: Optional dictionary with normalization statistics
        """
        self.numerical_cols = numerical_cols
        self.categorical_cols = categorical_cols

        # Separate numerical and categorical data
        self.numerical_data = data[numerical_cols].values.astype(np.float32)
        self.categorical_data = data[categorical_cols].values

        # Normalize numerical data
        if stats is None:
            self.mean = self.numerical_data.mean(axis=0)
            self.std = self.numerical_data.std(axis=0) + 1e-6
        else:
            self.mean = stats['mean']
            self.std = stats['std']

        self.numerical_data = (self.numerical_data - self.mean) / self.std

        # One-hot encode categorical data
        self.categorical_encoders = {}
        encoded_categoricals = []

        for col in categorical_cols:
            unique_vals = sorted(data[col].unique())
            self.categorical_encoders[col] = {val: idx for idx, val in enumerate(unique_vals)}

            # One-hot encode
            col_data = data[col].values
            encoded = np.zeros((len(col_data), len(unique_vals)), dtype=np.float32)
            for i, val in enumerate(col_data):
                encoded[i, self.categorical_encoders[col][val]] = 1.0
            encoded_categoricals.append(encoded)

        if encoded_categoricals:
            self.categorical_encoded = np.concatenate(encoded_categoricals, axis=1)
        else:
            self.categorical_encoded = np.zeros((len(data), 0), dtype=np.float32)

        # Combine numerical and categorical
        self.data = np.concatenate([self.numerical_data, self.categorical_encoded], axis=1)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return torch.from_numpy(self.data[idx])

    def get_stats(self) -> Dict:
        """Get normalization statistics"""
        return {
            'mean': self.mean,
            'std': self.std,
            'categorical_encoders': self.categorical_encoders
        }

    def inverse_transform(self, data: np.ndarray) -> pd.DataFrame:
        """Convert normalized data back to original format"""
        n_numerical = len(self.numerical_cols)

        # Denormalize numerical data
        numerical_data = data[:, :n_numerical] * self.std + self.mean

        # Decode categorical data
        categorical_data = {}
        offset = n_numerical

        for col in self.categorical_cols:
            n_classes = len(self.categorical_encoders[col])
            col_encoded = data[:, offset:offset+n_classes]

            # Get class with highest probability (argmax)
            col_indices = col_encoded.argmax(axis=1)

            # Map back to original values
            reverse_encoder = {idx: val for val, idx in self.categorical_encoders[col].items()}
            categorical_data[col] = [reverse_encoder[idx] for idx in col_indices]

            offset += n_classes

        # Create DataFrame
        result_data = {}
        for i, col in enumerate(self.numerical_cols):
            result_data[col] = numerical_data[:, i]
        for col in self.categorical_cols:
            result_data[col] = categorical_data[col]

        return pd.DataFrame(result_data)


class DenoisingNetwork(nn.Module):
    """MLP-based denoising network for tabular data"""

    def __init__(self, input_dim: int, hidden_dims: List[int] = [256, 512, 256],
                 num_timesteps: int = 1000):
        super().__init__()

        self.input_dim = input_dim
        self.num_timesteps = num_timesteps

        # Time embedding
        time_emb_dim = 64
        self.time_embed = nn.Sequential(
            nn.Linear(1, time_emb_dim),
            nn.SiLU(),
            nn.Linear(time_emb_dim, time_emb_dim)
        )

        # Main network
        layers = []
        prev_dim = input_dim + time_emb_dim

        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.LayerNorm(hidden_dim),
                nn.SiLU(),
                nn.Dropout(0.1)
            ])
            prev_dim = hidden_dim

        layers.append(nn.Linear(prev_dim, input_dim))

        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor, t: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Noisy data [batch_size, input_dim]
            t: Timestep [batch_size, 1]
        Returns:
            Predicted noise [batch_size, input_dim]
        """
        # Normalize timestep to [0, 1]
        t_normalized = t.float() / self.num_timesteps

        # Time embedding
        t_emb = self.time_embed(t_normalized)

        # Concatenate input and time embedding
        x_t = torch.cat([x, t_emb], dim=1)

        # Predict noise
        return self.network(x_t)


class TabularDiffusion:
    """Tabular Diffusion Model for synthetic data generation"""

    def __init__(self, input_dim: int, device: str = 'cpu',
                 num_timesteps: int = 1000, beta_schedule: str = 'linear'):
        """
        Args:
            input_dim: Dimension of input data
            device: Device to run model on ('cpu' or 'cuda')
            num_timesteps: Number of diffusion timesteps
            beta_schedule: Noise schedule ('linear' or 'cosine')
        """
        self.device = device
        self.num_timesteps = num_timesteps

        # Create denoising network
        self.model = DenoisingNetwork(input_dim, num_timesteps=num_timesteps).to(device)

        # Define beta schedule (noise schedule)
        if beta_schedule == 'linear':
            self.betas = torch.linspace(0.0001, 0.02, num_timesteps).to(device)
        elif beta_schedule == 'cosine':
            steps = num_timesteps + 1
            s = 0.008
            t = torch.linspace(0, num_timesteps, steps)
            alphas_cumprod = torch.cos(((t / num_timesteps) + s) / (1 + s) * np.pi * 0.5) ** 2
            alphas_cumprod = alphas_cumprod / alphas_cumprod[0]
            self.betas = 1 - (alphas_cumprod[1:] / alphas_cumprod[:-1])
            self.betas = torch.clip(self.betas, 0.0001, 0.9999).to(device)

        # Compute alphas and other useful quantities
        self.alphas = 1.0 - self.betas
        self.alphas_cumprod = torch.cumprod(self.alphas, dim=0)
        self.alphas_cumprod_prev = F.pad(self.alphas_cumprod[:-1], (1, 0), value=1.0)

        # Calculations for diffusion q(x_t | x_{t-1})
        self.sqrt_alphas_cumprod = torch.sqrt(self.alphas_cumprod)
        self.sqrt_one_minus_alphas_cumprod = torch.sqrt(1.0 - self.alphas_cumprod)

        # Calculations for posterior q(x_{t-1} | x_t, x_0)
        self.posterior_variance = (
            self.betas * (1.0 - self.alphas_cumprod_prev) / (1.0 - self.alphas_cumprod)
        )

    def q_sample(self, x_0: torch.Tensor, t: torch.Tensor,
                 noise: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Forward diffusion process: Add noise to data
        q(x_t | x_0) = N(x_t; sqrt(alpha_cumprod_t) * x_0, (1 - alpha_cumprod_t) * I)
        """
        if noise is None:
            noise = torch.randn_like(x_0)

        sqrt_alphas_cumprod_t = self.sqrt_alphas_cumprod[t].view(-1, 1)
        sqrt_one_minus_alphas_cumprod_t = self.sqrt_one_minus_alphas_cumprod[t].view(-1, 1)

        return sqrt_alphas_cumprod_t * x_0 + sqrt_one_minus_alphas_cumprod_t * noise

    def p_sample(self, x_t: torch.Tensor, t: int) -> torch.Tensor:
        """
        Reverse diffusion process: Remove noise from data (single step)
        p(x_{t-1} | x_t)
        """
        batch_size = x_t.shape[0]

        # Predict noise
        t_tensor = torch.full((batch_size, 1), t, device=self.device, dtype=torch.long)
        predicted_noise = self.model(x_t, t_tensor)

        # Compute x_0 prediction
        alpha_t = self.alphas[t]
        alpha_cumprod_t = self.alphas_cumprod[t]
        beta_t = self.betas[t]

        # Predict x_0 from x_t and predicted noise
        x_0_pred = (x_t - torch.sqrt(1 - alpha_cumprod_t) * predicted_noise) / torch.sqrt(alpha_cumprod_t)

        # Compute mean of p(x_{t-1} | x_t)
        model_mean = (
            torch.sqrt(alpha_t) * (1 - self.alphas_cumprod_prev[t]) * x_t +
            torch.sqrt(self.alphas_cumprod_prev[t]) * beta_t * x_0_pred
        ) / (1 - alpha_cumprod_t)

        if t == 0:
            return model_mean
        else:
            # Add noise
            noise = torch.randn_like(x_t)
            posterior_variance_t = self.posterior_variance[t]
            return model_mean + torch.sqrt(posterior_variance_t) * noise

    @torch.no_grad()
    def sample(self, num_samples: int) -> torch.Tensor:
        """
        Generate samples by running reverse diffusion process
        Start from random noise and denoise step by step
        """
        # Start from random noise
        x_t = torch.randn(num_samples, self.model.input_dim, device=self.device)

        # Iteratively denoise
        for t in reversed(range(self.num_timesteps)):
            x_t = self.p_sample(x_t, t)

        return x_t

    def train_step(self, x_0: torch.Tensor, optimizer: torch.optim.Optimizer) -> float:
        """Single training step"""
        batch_size = x_0.shape[0]

        # Sample random timesteps
        t = torch.randint(0, self.num_timesteps, (batch_size,), device=self.device)

        # Sample noise
        noise = torch.randn_like(x_0)

        # Add noise to data
        x_t = self.q_sample(x_0, t, noise)

        # Predict noise
        t_tensor = t.unsqueeze(1)
        predicted_noise = self.model(x_t, t_tensor)

        # Compute loss (MSE between predicted and actual noise)
        loss = F.mse_loss(predicted_noise, noise)

        # Backprop and optimize
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        return loss.item()


def train_diffusion_model(
    data_path: str,
    save_path: str,
    num_epochs: int = 100,
    batch_size: int = 128,
    learning_rate: float = 1e-3,
    device: str = 'cpu',
    num_timesteps: int = 1000
) -> Tuple[TabularDiffusion, TabularDataset]:
    """
    Train diffusion model on pilot vitals data

    Args:
        data_path: Path to CSV file with pilot data
        save_path: Path to save trained model
        num_epochs: Number of training epochs
        batch_size: Batch size for training
        learning_rate: Learning rate
        device: Device to train on
        num_timesteps: Number of diffusion timesteps

    Returns:
        Trained diffusion model and dataset (for denormalization)
    """
    # Load and prepare data
    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)

    # Define numerical and categorical columns
    numerical_cols = ['SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature']
    categorical_cols = ['VisitName', 'TreatmentArm']

    # Create dataset
    dataset = TabularDataset(df, numerical_cols, categorical_cols)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # Create model
    input_dim = dataset.data.shape[1]
    print(f"Input dimension: {input_dim}")

    diffusion = TabularDiffusion(input_dim, device=device, num_timesteps=num_timesteps)
    optimizer = torch.optim.AdamW(diffusion.model.parameters(), lr=learning_rate)

    # Training loop
    print(f"Training for {num_epochs} epochs...")
    diffusion.model.train()

    for epoch in range(num_epochs):
        epoch_loss = 0.0
        num_batches = 0

        for batch in dataloader:
            batch = batch.to(device)
            loss = diffusion.train_step(batch, optimizer)
            epoch_loss += loss
            num_batches += 1

        avg_loss = epoch_loss / num_batches

        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{num_epochs}, Loss: {avg_loss:.4f}")

    # Save model
    print(f"Saving model to {save_path}...")
    save_dir = Path(save_path).parent
    save_dir.mkdir(parents=True, exist_ok=True)

    torch.save({
        'model_state_dict': diffusion.model.state_dict(),
        'input_dim': input_dim,
        'num_timesteps': num_timesteps,
        'dataset_stats': dataset.get_stats(),
        'numerical_cols': numerical_cols,
        'categorical_cols': categorical_cols
    }, save_path)

    print("Training complete!")
    return diffusion, dataset


def load_diffusion_model(model_path: str, device: str = 'cpu') -> Tuple[TabularDiffusion, Dict]:
    """Load trained diffusion model"""
    checkpoint = torch.load(model_path, map_location=device)

    diffusion = TabularDiffusion(
        checkpoint['input_dim'],
        device=device,
        num_timesteps=checkpoint['num_timesteps']
    )
    diffusion.model.load_state_dict(checkpoint['model_state_dict'])
    diffusion.model.eval()

    return diffusion, checkpoint


def generate_synthetic_vitals(
    model_path: str,
    n_samples: int,
    device: str = 'cpu',
    seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Generate synthetic vitals data using trained diffusion model

    Args:
        model_path: Path to trained model checkpoint
        n_samples: Number of samples to generate
        device: Device to run on
        seed: Random seed for reproducibility

    Returns:
        DataFrame with synthetic vitals records
    """
    if seed is not None:
        torch.manual_seed(seed)
        np.random.seed(seed)

    # Load model
    diffusion, checkpoint = load_diffusion_model(model_path, device)

    # Generate samples
    with torch.no_grad():
        synthetic_data = diffusion.sample(n_samples).cpu().numpy()

    # Create temporary dataset for denormalization
    numerical_cols = checkpoint['numerical_cols']
    categorical_cols = checkpoint['categorical_cols']
    stats = checkpoint['dataset_stats']

    # Recreate dataset just for inverse transform
    # Create dummy DataFrame
    dummy_data = {col: [0] * n_samples for col in numerical_cols + categorical_cols}
    dummy_df = pd.DataFrame(dummy_data)

    temp_dataset = TabularDataset(dummy_df, numerical_cols, categorical_cols, stats=stats)

    # Denormalize and decode
    result_df = temp_dataset.inverse_transform(synthetic_data)

    # Add SubjectID (will be added by the service based on n_per_arm)
    result_df['SubjectID'] = [f"DIFF{i:04d}" for i in range(n_samples)]

    # Ensure data is in valid ranges (clip to physiological ranges)
    result_df['SystolicBP'] = result_df['SystolicBP'].clip(95, 200).round().astype(int)
    result_df['DiastolicBP'] = result_df['DiastolicBP'].clip(55, 130).round().astype(int)
    result_df['HeartRate'] = result_df['HeartRate'].clip(50, 120).round().astype(int)
    result_df['Temperature'] = result_df['Temperature'].clip(35.0, 40.0).round(1)

    return result_df


if __name__ == "__main__":
    # Training script
    import argparse

    parser = argparse.ArgumentParser(description='Train tabular diffusion model')
    parser.add_argument('--data_path', type=str, required=True, help='Path to pilot data CSV')
    parser.add_argument('--save_path', type=str, default='models/diffusion_model.pt',
                        help='Path to save model')
    parser.add_argument('--epochs', type=int, default=100, help='Number of epochs')
    parser.add_argument('--batch_size', type=int, default=128, help='Batch size')
    parser.add_argument('--lr', type=float, default=1e-3, help='Learning rate')
    parser.add_argument('--device', type=str, default='cpu', help='Device (cpu or cuda)')
    parser.add_argument('--timesteps', type=int, default=1000, help='Number of diffusion timesteps')

    args = parser.parse_args()

    train_diffusion_model(
        args.data_path,
        args.save_path,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        device=args.device,
        num_timesteps=args.timesteps
    )
