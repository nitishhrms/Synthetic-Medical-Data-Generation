#!/usr/bin/env python3
"""
Training script for Tabular Diffusion Model

This script trains a diffusion model on the pilot clinical trial data
and saves the trained model for use in synthetic data generation.

Usage:
    python train_diffusion.py --data_path ../../data/pilot_trial_cleaned.csv --epochs 200

The model will be saved to src/models/diffusion_model.pt
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from diffusion_generator import train_diffusion_model
import torch

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Train tabular diffusion model for synthetic vitals generation')
    parser.add_argument('--data_path', type=str,
                        default='../../data/pilot_trial_cleaned.csv',
                        help='Path to pilot data CSV file')
    parser.add_argument('--save_path', type=str,
                        default='src/models/diffusion_model.pt',
                        help='Path to save trained model')
    parser.add_argument('--epochs', type=int, default=200,
                        help='Number of training epochs (default: 200)')
    parser.add_argument('--batch_size', type=int, default=128,
                        help='Batch size for training (default: 128)')
    parser.add_argument('--lr', type=float, default=1e-3,
                        help='Learning rate (default: 1e-3)')
    parser.add_argument('--timesteps', type=int, default=1000,
                        help='Number of diffusion timesteps (default: 1000)')
    parser.add_argument('--device', type=str,
                        default='cuda' if torch.cuda.is_available() else 'cpu',
                        help='Device to use for training (cpu or cuda)')

    args = parser.parse_args()

    print("=" * 80)
    print("TABULAR DIFFUSION MODEL TRAINING")
    print("=" * 80)
    print(f"\nConfiguration:")
    print(f"  Data path: {args.data_path}")
    print(f"  Save path: {args.save_path}")
    print(f"  Epochs: {args.epochs}")
    print(f"  Batch size: {args.batch_size}")
    print(f"  Learning rate: {args.lr}")
    print(f"  Timesteps: {args.timesteps}")
    print(f"  Device: {args.device}")
    print()

    # Train model
    diffusion, dataset = train_diffusion_model(
        data_path=args.data_path,
        save_path=args.save_path,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        device=args.device,
        num_timesteps=args.timesteps
    )

    print("\n" + "=" * 80)
    print("TRAINING COMPLETE!")
    print("=" * 80)
    print(f"\nModel saved to: {args.save_path}")
    print(f"To generate synthetic data, use the diffusion endpoint in the service.")
    print()
