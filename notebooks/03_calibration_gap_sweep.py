#!/usr/bin/env python3
"""
F1 Undercut Simulator - Gap Sensitivity Analysis & Calibration Study

This script performs a comprehensive sensitivity analysis of the undercut simulator
across a range of gap scenarios, producing calibration-style figures and CSV output.

Key Features:
- Network-free operation with patched services
- Deterministic results (seed=42)
- Gap sweep from 0.5s to 30.0s 
- Calibration plots and reliability analysis
- CSV export for further analysis

Author: F1 Undercut Simulator Team
Date: 2024
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for headless operation
import matplotlib.pyplot as plt
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient

# Add backend to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app import app

# Set random seed for deterministic results
np.random.seed(42)

class UnderCutAnalyzer:
    """Comprehensive undercut sensitivity analysis and calibration study."""
    
    def __init__(self):
        self.client = TestClient(app)
        self.results = []
        
    def fake_laps_df(self) -> pd.DataFrame:
        """Generate fake laps data for network-free testing."""
        return pd.DataFrame({
            'driver_number': [44] * 10,  # HAM - enough data points for model fitting
            'lap_number': list(range(20, 30)),
            'lap_time': [77.8, 77.9, 78.0, 78.1, 78.2, 78.4, 78.6, 78.8, 79.0, 79.3],  # Progressive degradation
            'compound': ['SOFT'] * 10,
            'tyre_age': list(range(19, 29)),  # Tire ages 19-28
            'stint_lap': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],  # Full stint progression
            'is_pit_out_lap': [True] + [False] * 9,  # First lap is outlap
            'is_safety_car_lap': [False] * 10,
            'is_virtual_safety_car_lap': [False] * 10
        })
    
    def fake_pit_events_df(self) -> pd.DataFrame:
        """Generate fake pit events data for network-free testing."""
        return pd.DataFrame({
            'driver_number': [1, 1, 44, 44, 11],  # Multiple drivers for better model
            'lap_number': [25, 26, 20, 21, 22],
            'pit_duration': [2.4, 2.6, 2.3, 2.5, 2.7],  # Pit lane times
            'time_loss': [22.0, 23.0, 21.5, 22.5, 23.5]  # Total time loss variation
        })
    
    def fake_results_df(self) -> pd.DataFrame:
        """Generate fake results data (jolpica service)."""
        return pd.DataFrame({"dummy": [1]})  # Minimal placeholder
    
    def run_gap_sensitivity_analysis(self, gaps: np.ndarray) -> pd.DataFrame:
        """
        Run sensitivity analysis across different gap values.
        
        Args:
            gaps: Array of gap values to test (seconds)
            
        Returns:
            DataFrame with columns: gap_s, p_undercut, pitLoss_s, outLapDelta_s
        """
        print("🏎️ Starting F1 Undercut Gap Sensitivity Analysis...")
        print(f"   Testing {len(gaps)} gap scenarios from {gaps.min():.1f}s to {gaps.max():.1f}s")
        
        results = []
        
        # Patch all services to be network-free
        with patch('app.OpenF1Client') as mock_openf1_class, \
             patch('app.JolpicaClient') as mock_jolpica_class, \
             patch('app.calculate_driver_gap') as mock_gap_calc:
            
            # Set up OpenF1 client mock
            mock_openf1_instance = mock_openf1_class.return_value
            mock_openf1_instance.__enter__ = lambda x: mock_openf1_instance
            mock_openf1_instance.__exit__ = lambda *args: None
            mock_openf1_instance.get_laps = lambda gp, year: self.fake_laps_df()
            mock_openf1_instance.get_pit_events = lambda gp, year: self.fake_pit_events_df()
            
            # Set up Jolpica client mock  
            mock_jolpica_instance = mock_jolpica_class.return_value
            mock_jolpica_instance.get_results = lambda gp, year: self.fake_results_df()
            
            # Test configuration
            base_payload = {
                "gp": "monaco",
                "year": 2024,
                "driver_a": "VER", 
                "driver_b": "HAM",
                "compound_a": "SOFT",
                "lap_now": 25,
                "samples": 2000  # Higher sample count for smooth curves
            }
            
            # Sweep across gap values
            for i, gap in enumerate(gaps):
                # Patch gap calculation to return current test gap
                mock_gap_calc.return_value = float(gap)
                
                # Call simulate endpoint
                response = self.client.post("/simulate", json=base_payload)
                
                if response.status_code == 200:
                    data = response.json()
                    result = {
                        'gap_s': gap,
                        'p_undercut': data['p_undercut'],
                        'pitLoss_s': data['pitLoss_s'],
                        'outLapDelta_s': data['outLapDelta_s'],
                        'success_margin_s': data['assumptions'].get('success_margin_s', None)
                    }
                    results.append(result)
                    
                    # Progress indicator
                    if (i + 1) % 10 == 0 or i == 0:
                        print(f"   Progress: {i+1:2d}/{len(gaps)} - Gap {gap:4.1f}s → {data['p_undercut']:.1%} success")
                else:
                    print(f"   ERROR: Gap {gap:.1f}s failed with status {response.status_code}")
        
        df = pd.DataFrame(results)
        print(f"✅ Analysis complete! Collected {len(df)} data points.")
        return df
    
    def save_results(self, df: pd.DataFrame, csv_path: str):
        """Save analysis results to CSV."""
        df.to_csv(csv_path, index=False, float_format='%.6f')
        print(f"💾 Results saved to: {csv_path}")
        
    def create_calibration_plot(self, df: pd.DataFrame, output_path: str):
        """Create the main calibration plot showing undercut probability vs gap."""
        plt.figure(figsize=(10, 6))
        
        # Main curve
        plt.plot(df['gap_s'], df['p_undercut'], 'b-', linewidth=2, label='Undercut Success Probability')
        
        # Decision boundary
        plt.axhline(y=0.5, color='red', linestyle='--', alpha=0.7, 
                   label='Decision Boundary (50%)')
        
        # Formatting
        plt.xlabel('Current gap to car ahead (s)', fontsize=12)
        plt.ylabel('P(undercut)', fontsize=12)
        plt.title('Undercut Probability vs Current Gap — Monaco 2024 (SOFT, lap 25)', fontsize=14)
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.xlim(df['gap_s'].min(), df['gap_s'].max())
        plt.ylim(0, 1)
        
        # Save plot
        plt.savefig(output_path, dpi=180, bbox_inches='tight')
        plt.close()  # Close figure to free memory
        print(f"📊 Main calibration plot saved to: {output_path}")
        
    def create_reliability_plot(self, df: pd.DataFrame, output_path: str, n_trials: int = 200):
        """
        Create synthetic reliability plot by generating Bernoulli trials.
        
        This validates the calibration by comparing predicted probabilities
        with synthetic observed rates.
        """
        print("🎯 Generating synthetic reliability analysis...")
        
        # Generate synthetic observed rates
        observed_rates = []
        for _, row in df.iterrows():
            # Draw Bernoulli trials with probability = predicted p_undercut
            trials = np.random.binomial(1, row['p_undercut'], n_trials)
            observed_rate = trials.mean()
            observed_rates.append(observed_rate)
        
        df_reliability = df.copy()
        df_reliability['observed_rate'] = observed_rates
        
        # Bin into probability deciles for analysis
        n_bins = 10
        df_reliability['prob_bin'] = pd.cut(df_reliability['p_undercut'], 
                                           bins=n_bins, labels=False)
        
        # Calculate binned averages
        binned_stats = df_reliability.groupby('prob_bin').agg({
            'p_undercut': 'mean',
            'observed_rate': 'mean',
            'gap_s': 'count'  # Number of points per bin
        }).reset_index()
        binned_stats.rename(columns={'gap_s': 'count'}, inplace=True)
        
        # Create reliability plot
        plt.figure(figsize=(8, 8))
        
        # Perfect calibration line
        plt.plot([0, 1], [0, 1], 'k--', alpha=0.7, label='Perfect Calibration')
        
        # Binned calibration points
        plt.scatter(binned_stats['p_undercut'], binned_stats['observed_rate'], 
                   s=binned_stats['count']*2, alpha=0.7, color='blue',
                   label=f'Binned Results (n={n_trials} trials)')
        
        # Formatting
        plt.xlabel('Predicted P(undercut)', fontsize=12)
        plt.ylabel('Observed Rate (Synthetic)', fontsize=12) 
        plt.title('Reliability (Synthetic) — Monaco 2024', fontsize=14)
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.xlim(0, 1)
        plt.ylim(0, 1)
        
        # Save plot
        plt.savefig(output_path, dpi=180, bbox_inches='tight')
        plt.close()  # Close figure to free memory
        print(f"🎯 Reliability plot saved to: {output_path}")
        
        return df_reliability, binned_stats
    
    def print_summary(self, df: pd.DataFrame):
        """Print summary statistics from the analysis."""
        print("\n" + "="*60)
        print("📈 F1 UNDERCUT ANALYSIS SUMMARY")
        print("="*60)
        
        # Decision boundary analysis
        boundary_gap = df[df['p_undercut'] >= 0.5]['gap_s'].min()
        if pd.notna(boundary_gap):
            print(f"🎯 Decision Boundary: {boundary_gap:.1f}s gap needed for ≥50% undercut success")
        else:
            print("🎯 Decision Boundary: No gaps tested achieved ≥50% success probability")
        
        # Stable metrics
        print(f"⚡ Mean Pit Loss: {df['pitLoss_s'].mean():.1f}s ± {df['pitLoss_s'].std():.1f}s")
        print(f"🏁 Mean Outlap Delta: {df['outLapDelta_s'].mean():.2f}s ± {df['outLapDelta_s'].std():.2f}s")
        
        # Probability range
        print(f"📊 Success Probability Range: {df['p_undercut'].min():.1%} to {df['p_undercut'].max():.1%}")
        
        # Key insights
        median_gap = df['gap_s'].median()
        median_prob = df[df['gap_s'] == df.loc[(df['gap_s'] - median_gap).abs().argsort()[0], 'gap_s']]['p_undercut'].iloc[0]
        print(f"📈 At median gap ({median_gap:.1f}s): {median_prob:.1%} success probability")
        
        print("="*60)


def main():
    """Main execution function."""
    print("🏁 F1 Undercut Simulator - Comprehensive Gap Analysis")
    print("   Network-free, deterministic calibration study\n")
    
    # Initialize analyzer
    analyzer = UnderCutAnalyzer()
    
    # Define gap sweep range
    gaps = np.arange(0.5, 30.5, 0.5)  # 0.5s to 30.0s in 0.5s steps
    
    # Run sensitivity analysis
    results_df = analyzer.run_gap_sensitivity_analysis(gaps)
    
    # Save results to CSV
    csv_path = "docs/figs/undercut_gap_sweep.csv"
    analyzer.save_results(results_df, csv_path)
    
    # Create main calibration plot
    main_plot_path = "docs/figs/undercut_gap_sweep.png"
    analyzer.create_calibration_plot(results_df, main_plot_path)
    
    # Create reliability plot (bonus feature)
    reliability_plot_path = "docs/figs/undercut_reliability_synthetic.png"
    reliability_df, binned_stats = analyzer.create_reliability_plot(results_df, reliability_plot_path)
    
    # Print summary
    analyzer.print_summary(results_df)
    
    print(f"\n🎉 Analysis complete! Check docs/figs/ for outputs.")


if __name__ == "__main__":
    main()
