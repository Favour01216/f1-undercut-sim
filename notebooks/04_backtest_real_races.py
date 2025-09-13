#!/usr/bin/env python3
"""
F1 Undercut Simulator - Real Race Data Backtest & Predictive Accuracy Analysis

This script evaluates the predictive accuracy of the F1 undercut simulator by backtesting
against real race data from OpenF1/FastF1/Jolpica APIs.

Key Features:
- Real race data integration with caching
- Undercut attempt detection from timing data
- Predictive accuracy metrics (Brier score, calibration)
- Offline mode support for CI/CD environments
- Comprehensive visualization and reporting

Usage:
    python notebooks/04_backtest_real_races.py [--offline]
    
Environment Variables:
    OFFLINE=1 - Run in offline mode using cached data only

Author: F1 Undercut Simulator Team
Date: 2024
"""

import os
import sys
import argparse
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import requests
import json
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import patch
import time

# Add backend to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app import app
from services.model_params import get_parameters_manager

# Set random seed for deterministic results
np.random.seed(42)

# Configuration
RACES = [
    (2024, "bahrain"),
    (2024, "imola"),
    (2023, "monza")
]

CACHE_DIR = Path("features/backtest_cache")
OUTPUT_DIR = Path("docs/figs")

class F1BacktestAnalyzer:
    """Comprehensive F1 undercut backtest analyzer with real race data integration."""
    
    def __init__(self, offline_mode: bool = False):
        self.offline_mode = offline_mode
        self.client = TestClient(app)
        self.cache_dir = CACHE_DIR
        self.output_dir = OUTPUT_DIR
        
        # Model parameter management
        self.params_manager = get_parameters_manager()
        self.model_quality_log = []  # Track which parameters were used for each simulation
        
        # Create directories
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"🏁 F1 Undercut Simulator - Real Race Backtest Analysis")
        print(f"   Mode: {'OFFLINE (cached data only)' if offline_mode else 'ONLINE (will fetch & cache)'}")
        print(f"   Cache: {self.cache_dir}")
        print(f"   Output: {self.output_dir}")
        print(f"   Model Parameters: Loaded {len(self.params_manager.load_degradation_params())} degradation, {len(self.params_manager.load_outlap_params())} outlap")
        
    def fetch_or_load_data(self, gp: str, year: int) -> Dict[str, pd.DataFrame]:
        """
        Fetch or load cached race data for a specific GP and year.
        
        Returns:
            Dictionary with keys: 'laps', 'pit_events', 'sessions', 'results'
        """
        cache_prefix = f"{gp}_{year}"
        data = {}
        
        # Define cache files
        cache_files = {
            'laps': f"{cache_prefix}_laps.parquet",
            'pit_events': f"{cache_prefix}_pit_events.parquet", 
            'sessions': f"{cache_prefix}_sessions.parquet",
            'results': f"{cache_prefix}_results.parquet"
        }
        
        if self.offline_mode:
            print(f"📁 Loading cached data for {gp.upper()} {year}...")
            for key, filename in cache_files.items():
                cache_path = self.cache_dir / filename
                if cache_path.exists():
                    data[key] = pd.read_parquet(cache_path)
                    print(f"   ✅ {key}: {len(data[key])} records")
                else:
                    print(f"   ❌ {key}: Cache missing - {filename}")
                    data[key] = pd.DataFrame()  # Empty DataFrame
            return data
        
        print(f"🌐 Fetching fresh data for {gp.upper()} {year}...")
        
        try:
            # Fetch sessions first to get session_key
            sessions_url = "https://api.openf1.org/v1/sessions"
            sessions_params = {"year": year}
            print(f"   Fetching sessions...")
            
            response = requests.get(sessions_url, params=sessions_params, timeout=30)
            response.raise_for_status()
            sessions_data = response.json()
            
            # Convert to DataFrame and find race session
            sessions_df = pd.DataFrame(sessions_data)
            
            # Try to find race session for this GP
            gp_sessions = sessions_df[
                sessions_df['location'].str.lower().str.contains(gp.lower(), na=False) |
                sessions_df['country_name'].str.lower().str.contains(gp.lower(), na=False) |
                sessions_df['circuit_short_name'].str.lower().str.contains(gp.lower(), na=False)
            ]
            
            race_session = gp_sessions[gp_sessions['session_name'] == 'Race']
            
            if race_session.empty:
                print(f"   ⚠️  No race session found for {gp} {year}")
                # Return empty DataFrames
                for key in cache_files.keys():
                    data[key] = pd.DataFrame()
                return data
                
            session_key = race_session.iloc[0]['session_key']
            print(f"   Found race session: {session_key}")
            
            # Fetch laps data
            print(f"   Fetching laps data...")
            laps_url = "https://api.openf1.org/v1/laps"
            laps_params = {"session_key": session_key}
            laps_response = requests.get(laps_url, params=laps_params, timeout=60)
            laps_response.raise_for_status()
            laps_data = laps_response.json()
            data['laps'] = pd.DataFrame(laps_data)
            print(f"   ✅ Laps: {len(data['laps'])} records")
            
            # Fetch pit events
            print(f"   Fetching pit events...")
            pit_url = "https://api.openf1.org/v1/pit"
            pit_params = {"session_key": session_key}
            pit_response = requests.get(pit_url, params=pit_params, timeout=30)
            pit_response.raise_for_status()
            pit_data = pit_response.json()
            data['pit_events'] = pd.DataFrame(pit_data)
            print(f"   ✅ Pit Events: {len(data['pit_events'])} records")
            
            # Store sessions data
            data['sessions'] = sessions_df
            
            # Fetch results from Jolpica (Ergast-compatible)
            print(f"   Fetching results from Jolpica...")
            try:
                # Map circuit names to Ergast circuit IDs (simplified mapping)
                circuit_map = {
                    'bahrain': 'bahrain',
                    'imola': 'imola', 
                    'monza': 'monza'
                }
                
                circuit_id = circuit_map.get(gp.lower(), gp.lower())
                results_url = f"http://ergast.com/api/f1/{year}/circuits/{circuit_id}/results.json"
                results_response = requests.get(results_url, timeout=30)
                results_response.raise_for_status()
                results_json = results_response.json()
                
                # Extract results data
                if 'MRData' in results_json and 'RaceTable' in results_json['MRData']:
                    races = results_json['MRData']['RaceTable'].get('Races', [])
                    if races:
                        race_results = races[0].get('Results', [])
                        results_list = []
                        for result in race_results:
                            results_list.append({
                                'position': result.get('position'),
                                'driver_code': result.get('Driver', {}).get('code', ''),
                                'constructor': result.get('Constructor', {}).get('name', ''),
                                'laps': result.get('laps'),
                                'status': result.get('status'),
                                'points': result.get('points')
                            })
                        data['results'] = pd.DataFrame(results_list)
                    else:
                        data['results'] = pd.DataFrame()
                else:
                    data['results'] = pd.DataFrame()
                    
                print(f"   ✅ Results: {len(data['results'])} records")
                
            except Exception as e:
                print(f"   ⚠️  Results fetch failed: {e}")
                data['results'] = pd.DataFrame()
            
            # Cache all data
            print(f"   💾 Caching data...")
            for key, df in data.items():
                cache_path = self.cache_dir / cache_files[key]
                if not df.empty:
                    df.to_parquet(cache_path, index=False)
                    print(f"   ✅ Cached {key}: {cache_path}")
                
        except Exception as e:
            print(f"   ❌ Data fetch failed: {e}")
            if self.offline_mode:
                raise RuntimeError(f"Offline mode but no cache available for {gp} {year}")
            # Return empty DataFrames on fetch failure
            for key in cache_files.keys():
                data[key] = pd.DataFrame()
        
        return data
    
    def detect_undercut_attempts(self, race_data: Dict[str, pd.DataFrame], gp: str, year: int) -> pd.DataFrame:
        """
        Detect undercut attempts from race timing data using heuristics.
        
        Returns:
            DataFrame with detected undercut attempts and metadata
        """
        laps_df = race_data['laps']
        pit_events_df = race_data['pit_events']
        
        if laps_df.empty or pit_events_df.empty:
            print(f"   ⚠️  Insufficient data for undercut detection in {gp} {year}")
            return pd.DataFrame()
        
        print(f"🔍 Detecting undercut attempts for {gp.upper()} {year}...")
        
        attempts = []
        
        # Clean and prepare data
        if 'lap_duration' in laps_df.columns:
            laps_df = laps_df.copy()
            laps_df['lap_time_s'] = laps_df['lap_duration']
        elif 'duration_sector_3' in laps_df.columns:
            # Calculate approximate lap time from sectors if duration not available
            sector_cols = ['duration_sector_1', 'duration_sector_2', 'duration_sector_3']
            available_sectors = [col for col in sector_cols if col in laps_df.columns]
            if available_sectors:
                laps_df = laps_df.copy()
                laps_df['lap_time_s'] = laps_df[available_sectors].sum(axis=1)
            else:
                print(f"   ⚠️  No lap time data available")
                return pd.DataFrame()
        else:
            print(f"   ⚠️  No lap time columns found")
            return pd.DataFrame()
        
        # Filter valid laps (remove outliers and invalid times)
        if 'lap_time_s' in laps_df.columns:
            laps_df = laps_df[
                (laps_df['lap_time_s'].notna()) & 
                (laps_df['lap_time_s'] > 60) &  # Reasonable minimum lap time
                (laps_df['lap_time_s'] < 200)   # Reasonable maximum lap time
            ].copy()
        
        if laps_df.empty:
            print(f"   ⚠️  No valid lap times after filtering")
            return pd.DataFrame()
        
        # Get unique drivers and laps
        drivers = laps_df['driver_number'].unique()
        laps = sorted(laps_df['lap_number'].unique())
        
        print(f"   📊 Analyzing {len(drivers)} drivers across {len(laps)} laps")
        
        # For each lap, detect pit stops and potential undercuts
        for lap_num in laps[1:-1]:  # Skip first and last lap
            # Get pit events for this lap
            lap_pits = pit_events_df[pit_events_df['lap_number'] == lap_num]
            
            if lap_pits.empty:
                continue
                
            # For each driver who pitted on this lap
            for _, pit_event in lap_pits.iterrows():
                driver_a = pit_event['driver_number']
                
                # Get driver A's lap data for this lap and previous
                driver_a_prev = laps_df[
                    (laps_df['driver_number'] == driver_a) & 
                    (laps_df['lap_number'] == lap_num - 1)
                ]
                driver_a_current = laps_df[
                    (laps_df['driver_number'] == driver_a) & 
                    (laps_df['lap_number'] == lap_num)
                ]
                
                if driver_a_prev.empty or driver_a_current.empty:
                    continue
                
                # Find drivers ahead of A on the previous lap (potential undercut targets)
                prev_lap_times = laps_df[laps_df['lap_number'] == lap_num - 1].copy()
                if prev_lap_times.empty:
                    continue
                    
                # Simple gap estimation: use cumulative race time if available, otherwise skip
                # This is a simplified approach - in reality we'd need sector times and positions
                potential_targets = prev_lap_times[
                    (prev_lap_times['driver_number'] != driver_a) &
                    (prev_lap_times['driver_number'].isin(drivers))
                ].copy()
                
                # For each potential target
                for _, target_lap in potential_targets.iterrows():
                    driver_b = target_lap['driver_number']
                    
                    # Check if driver B stayed out (didn't pit this lap)
                    driver_b_pit_this_lap = lap_pits[lap_pits['driver_number'] == driver_b]
                    if not driver_b_pit_this_lap.empty:
                        continue  # Driver B also pitted, not an undercut attempt
                    
                    # Get driver B's next lap data
                    driver_b_next = laps_df[
                        (laps_df['driver_number'] == driver_b) & 
                        (laps_df['lap_number'] == lap_num + 1)
                    ]
                    
                    if driver_b_next.empty:
                        continue
                    
                    # Simplified gap calculation (this is a heuristic approximation)
                    # In reality, we'd need live timing data with sector splits
                    gap_estimate = abs(driver_a_prev.iloc[0]['lap_time_s'] - target_lap['lap_time_s'])
                    
                    # Filter: only consider small gaps as undercut opportunities
                    if gap_estimate > 3.5:
                        continue
                    
                    # Check for SC/VSC (simplified - look for unusually slow laps)
                    lap_times_this_lap = laps_df[laps_df['lap_number'] == lap_num]['lap_time_s']
                    lap_times_next_lap = laps_df[laps_df['lap_number'] == lap_num + 1]['lap_time_s']
                    
                    # If average lap time is significantly slower, likely SC/VSC
                    if (lap_times_this_lap.mean() > lap_times_this_lap.quantile(0.9) * 1.1 or
                        lap_times_next_lap.mean() > lap_times_next_lap.quantile(0.9) * 1.1):
                        continue  # Skip SC/VSC periods
                    
                    # Determine actual outcome (simplified)
                    # Look at positions a few laps later to see who came out ahead
                    outcome = self._determine_undercut_outcome(
                        laps_df, driver_a, driver_b, lap_num, pit_events_df
                    )
                    
                    if outcome is None:
                        continue  # Could not determine outcome
                    
                    # Get tire compound information
                    compound_a = "MEDIUM"  # Default assumption - in practice would parse from pit data
                    if 'compound' in driver_a_current.columns:
                        compound_a = driver_a_current.iloc[0]['compound'] 
                    
                    # Get tire age for driver B
                    tyre_age_b = 10  # Default assumption
                    if 'stint_lap' in target_lap:
                        tyre_age_b = target_lap['stint_lap']
                    
                    # Record the attempt
                    attempts.append({
                        'gp': gp,
                        'year': year,
                        'lap': lap_num,
                        'driver_a': driver_a,
                        'driver_b': driver_b,
                        'compound_a': compound_a,
                        'tyre_age_b': tyre_age_b,
                        'gap_pre': gap_estimate,
                        'outcome': outcome,
                        'lap_time_a_prev': driver_a_prev.iloc[0]['lap_time_s'],
                        'lap_time_b_prev': target_lap['lap_time_s']
                    })
        
        attempts_df = pd.DataFrame(attempts)
        print(f"   🎯 Detected {len(attempts_df)} undercut attempts")
        
        return attempts_df
    
    def _determine_undercut_outcome(self, laps_df: pd.DataFrame, driver_a: int, driver_b: int, 
                                   pit_lap: int, pit_events_df: pd.DataFrame) -> Optional[int]:
        """
        Determine if an undercut attempt was successful.
        
        Returns:
            1 if successful (A ahead of B), 0 if failed, None if indeterminate
        """
        # Look for driver B's next pit stop
        driver_b_future_pits = pit_events_df[
            (pit_events_df['driver_number'] == driver_b) & 
            (pit_events_df['lap_number'] > pit_lap)
        ]
        
        if driver_b_future_pits.empty:
            # Driver B never pitted after - compare final race positions
            # This is simplified - in practice we'd need final classification data
            return None
        
        b_pit_lap = driver_b_future_pits.iloc[0]['lap_number']
        comparison_lap = b_pit_lap + 2  # A few laps after both have pitted
        
        # Get lap times for comparison lap
        a_lap = laps_df[
            (laps_df['driver_number'] == driver_a) & 
            (laps_df['lap_number'] == comparison_lap)
        ]
        b_lap = laps_df[
            (laps_df['driver_number'] == driver_b) & 
            (laps_df['lap_number'] == comparison_lap)
        ]
        
        if a_lap.empty or b_lap.empty:
            return None
        
        # Simplified outcome: compare cumulative race time if available
        # Otherwise use lap time differential as proxy
        if 'race_time' in a_lap.columns and 'race_time' in b_lap.columns:
            return 1 if a_lap.iloc[0]['race_time'] < b_lap.iloc[0]['race_time'] else 0
        else:
            # Use lap time as rough proxy (not ideal but workable)
            return 1 if a_lap.iloc[0]['lap_time_s'] < b_lap.iloc[0]['lap_time_s'] else 0
    
    def run_simulator_predictions(self, attempts_df: pd.DataFrame) -> pd.DataFrame:
        """Run simulator predictions for each detected undercut attempt."""
        if attempts_df.empty:
            return attempts_df
        
        print(f"🎲 Running simulator predictions for {len(attempts_df)} attempts...")
        print(f"🔍 Validating model parameters (R²>0.1 threshold)...")
        
        predictions = []
        
        for idx, attempt in attempts_df.iterrows():
            # Validate model parameters before simulation
            circuit = attempt['gp'].lower()
            compound = attempt['compound_a'].upper()
            
            # Check degradation model quality
            deg_params = self.params_manager.get_degradation_params(
                circuit=circuit, 
                compound=compound,
                min_r2=0.1  # R² threshold
            )
            
            # Check outlap model quality  
            outlap_params = self.params_manager.get_outlap_params(
                circuit=circuit,
                compound=compound,
                min_samples=5
            )
            
            # Log model quality for this attempt
            model_quality_entry = {
                'idx': idx,
                'gp': attempt['gp'],
                'year': attempt['year'],
                'circuit': circuit,
                'compound': compound,
                'deg_r2': deg_params.r2 if deg_params else None,
                'deg_rmse': deg_params.rmse if deg_params else None,
                'deg_scope': deg_params.scope if deg_params else 'missing',
                'deg_n_samples': deg_params.n_samples if deg_params else 0,
                'outlap_scope': outlap_params.scope if outlap_params else 'missing',
                'outlap_n_samples': outlap_params.n_samples if outlap_params else 0
            }
            self.model_quality_log.append(model_quality_entry)
            
            # Prepare simulator payload
            payload = {
                "gp": attempt['gp'],
                "year": attempt['year'],
                "driver_a": f"DRIVER_{attempt['driver_a']}",  # Convert to string format
                "driver_b": f"DRIVER_{attempt['driver_b']}",
                "compound_a": attempt['compound_a'],
                "lap_now": attempt['lap'],
                "samples": 1000
            }
            
            try:
                # Patch gap calculation to return measured gap
                with patch('app.calculate_driver_gap') as mock_gap:
                    mock_gap.return_value = attempt['gap_pre']
                    
                    # Call simulator
                    response = self.client.post("/simulate", json=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        predictions.append({
                            'idx': idx,
                            'p_undercut': data['p_undercut'],
                            'pitLoss_s': data['pitLoss_s'],
                            'outLapDelta_s': data['outLapDelta_s']
                        })
                    else:
                        print(f"   ⚠️  Simulation failed for attempt {idx}: {response.status_code}")
                        predictions.append({
                            'idx': idx,
                            'p_undercut': 0.5,  # Default neutral prediction
                            'pitLoss_s': 25.0,
                            'outLapDelta_s': 1.0
                        })
                        
            except Exception as e:
                print(f"   ⚠️  Error in simulation {idx}: {e}")
                predictions.append({
                    'idx': idx,
                    'p_undercut': 0.5,
                    'pitLoss_s': 25.0,
                    'outLapDelta_s': 1.0
                })
        
        # Merge predictions back to attempts
        predictions_df = pd.DataFrame(predictions)
        if not predictions_df.empty:
            attempts_enhanced = attempts_df.reset_index().merge(
                predictions_df, left_index=True, right_on='idx', how='left'
            )
            # Fill missing predictions
            attempts_enhanced['p_undercut'] = attempts_enhanced['p_undercut'].fillna(0.5)
            attempts_enhanced['pitLoss_s'] = attempts_enhanced['pitLoss_s'].fillna(25.0)
            attempts_enhanced['outLapDelta_s'] = attempts_enhanced['outLapDelta_s'].fillna(1.0)
            
            print(f"   ✅ Generated predictions for {len(attempts_enhanced)} attempts")
            return attempts_enhanced
        else:
            # Add default columns if no predictions
            attempts_df = attempts_df.copy()
            attempts_df['p_undercut'] = 0.5
            attempts_df['pitLoss_s'] = 25.0
            attempts_df['outLapDelta_s'] = 1.0
            return attempts_df
    
    def compute_metrics(self, results_df: pd.DataFrame) -> Dict:
        """Compute predictive accuracy metrics."""
        if results_df.empty or 'p_undercut' not in results_df.columns:
            return {'brier_score': None, 'n_attempts': 0}
        
        print(f"📊 Computing predictive accuracy metrics...")
        
        predictions = results_df['p_undercut'].values
        outcomes = results_df['outcome'].values
        
        # Remove any NaN values
        valid_mask = ~(np.isnan(predictions) | np.isnan(outcomes))
        predictions = predictions[valid_mask]
        outcomes = outcomes[valid_mask]
        
        if len(predictions) == 0:
            return {'brier_score': None, 'n_attempts': 0}
        
        # Brier Score
        brier_score = np.mean((predictions - outcomes) ** 2)
        
        # Reliability/Calibration analysis
        n_bins = min(10, len(predictions) // 2)  # Adjust bins for small samples
        if n_bins < 2:
            n_bins = 2
            
        # Equal-frequency binning
        bin_boundaries = np.percentile(predictions, np.linspace(0, 100, n_bins + 1))
        bin_indices = np.digitize(predictions, bin_boundaries) - 1
        bin_indices = np.clip(bin_indices, 0, n_bins - 1)
        
        reliability_data = []
        for i in range(n_bins):
            mask = bin_indices == i
            if np.sum(mask) > 0:
                avg_pred = np.mean(predictions[mask])
                avg_outcome = np.mean(outcomes[mask])
                count = np.sum(mask)
                reliability_data.append({
                    'bin': i,
                    'count': count,
                    'avg_predicted': avg_pred,
                    'avg_observed': avg_outcome,
                    'bin_lower': bin_boundaries[i] if i < len(bin_boundaries) else 0,
                    'bin_upper': bin_boundaries[i + 1] if i + 1 < len(bin_boundaries) else 1
                })
        
        metrics = {
            'brier_score': brier_score,
            'n_attempts': len(predictions),
            'mean_prediction': np.mean(predictions),
            'success_rate': np.mean(outcomes),
            'reliability_data': reliability_data
        }
        
        print(f"   ✅ Brier Score: {brier_score:.4f}")
        print(f"   ✅ Mean Prediction: {np.mean(predictions):.3f}")
        print(f"   ✅ Actual Success Rate: {np.mean(outcomes):.3f}")
        
        return metrics
    
    def create_visualizations(self, results_df: pd.DataFrame, metrics: Dict):
        """Create all required visualizations."""
        if results_df.empty or not metrics['reliability_data']:
            print("⚠️  Insufficient data for visualizations")
            return
        
        print("📈 Creating visualizations...")
        
        # 1. Calibration/Reliability Plot
        self._plot_calibration(metrics['reliability_data'])
        
        # 2. Scatter Plot - Predictions vs Outcomes
        self._plot_scatter(results_df)
        
        print("   ✅ All visualizations created")
    
    def _plot_calibration(self, reliability_data: List[Dict]):
        """Create calibration reliability plot."""
        if not reliability_data:
            return
            
        # Extract data for plotting
        bin_centers = [d['avg_predicted'] for d in reliability_data]
        observed_rates = [d['avg_observed'] for d in reliability_data]
        counts = [d['count'] for d in reliability_data]
        
        # Create plot
        plt.figure(figsize=(8, 8))
        
        # Perfect calibration line
        plt.plot([0, 1], [0, 1], 'k--', alpha=0.7, linewidth=2, label='Perfect Calibration')
        
        # Calibration points (size proportional to count)
        sizes = [c * 20 for c in counts]  # Scale point sizes
        plt.scatter(bin_centers, observed_rates, s=sizes, alpha=0.7, 
                   color='blue', edgecolors='darkblue', linewidth=1,
                   label='Observed vs Predicted')
        
        # Formatting
        plt.xlabel('Predicted Probability', fontsize=12)
        plt.ylabel('Observed Frequency', fontsize=12)
        plt.title('F1 Undercut Simulator - Calibration Analysis', fontsize=14)
        plt.xlim(0, 1)
        plt.ylim(0, 1)
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # Add text annotation with sample sizes
        textstr = f'Total Attempts: {sum(counts)}\nBins: {len(reliability_data)}'
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        plt.text(0.02, 0.98, textstr, transform=plt.gca().transAxes, fontsize=10,
                verticalalignment='top', bbox=props)
        
        # Save plot
        output_path = self.output_dir / "calibration_reliability.png"
        plt.savefig(output_path, dpi=180, bbox_inches='tight')
        plt.close()
        print(f"   📊 Calibration plot saved: {output_path}")
        
        # Save reliability data to CSV
        reliability_df = pd.DataFrame(reliability_data)
        csv_path = self.output_dir / "decile_reliability.csv"
        reliability_df.to_csv(csv_path, index=False, float_format='%.6f')
        print(f"   💾 Reliability data saved: {csv_path}")
    
    def _plot_scatter(self, results_df: pd.DataFrame):
        """Create scatter plot of predictions vs outcomes."""
        if 'p_undercut' not in results_df.columns or 'outcome' not in results_df.columns:
            return
            
        predictions = results_df['p_undercut'].values
        outcomes = results_df['outcome'].values
        
        # Remove NaN values
        valid_mask = ~(np.isnan(predictions) | np.isnan(outcomes))
        predictions = predictions[valid_mask]
        outcomes = outcomes[valid_mask]
        
        if len(predictions) == 0:
            return
        
        # Add jitter to outcomes for better visualization
        jittered_outcomes = outcomes + np.random.normal(0, 0.02, size=len(outcomes))
        
        plt.figure(figsize=(10, 6))
        
        # Scatter plot
        plt.scatter(predictions, jittered_outcomes, alpha=0.6, s=30, color='blue', 
                   edgecolors='darkblue', linewidth=0.5)
        
        # Reference lines
        plt.axhline(y=0.5, color='red', linestyle='--', alpha=0.5, label='Decision Boundary')
        plt.axvline(x=0.5, color='red', linestyle='--', alpha=0.5)
        
        # Formatting
        plt.xlabel('Predicted Undercut Probability', fontsize=12)
        plt.ylabel('Actual Outcome (0=Fail, 1=Success)', fontsize=12)
        plt.title('F1 Undercut Simulator - Predictions vs Actual Outcomes', fontsize=14)
        plt.xlim(0, 1)
        plt.ylim(-0.1, 1.1)
        plt.grid(True, alpha=0.3)
        
        # Add summary statistics
        mean_pred = np.mean(predictions)
        success_rate = np.mean(outcomes)
        brier = np.mean((predictions - outcomes) ** 2)
        
        textstr = f'Mean Prediction: {mean_pred:.3f}\nSuccess Rate: {success_rate:.3f}\nBrier Score: {brier:.4f}\nSamples: {len(predictions)}'
        props = dict(boxstyle='round', facecolor='lightgray', alpha=0.8)
        plt.text(0.02, 0.98, textstr, transform=plt.gca().transAxes, fontsize=10,
                verticalalignment='top', bbox=props)
        
        # Save plot
        output_path = self.output_dir / "pred_vs_actual_scatter.png"
        plt.savefig(output_path, dpi=180, bbox_inches='tight')
        plt.close()
        print(f"   📊 Scatter plot saved: {output_path}")
    
    def create_summary_report(self, all_results: List[pd.DataFrame]) -> pd.DataFrame:
        """Create comprehensive summary report."""
        print("📋 Creating summary report...")
        
        summary_rows = []
        
        # Per-race summaries
        for results_df in all_results:
            if results_df.empty:
                continue
                
            gp = results_df.iloc[0]['gp']
            year = results_df.iloc[0]['year']
            
            metrics = self.compute_metrics(results_df)
            
            summary_rows.append({
                'gp': gp.upper(),
                'year': year,
                'n_attempts': metrics['n_attempts'],
                'mean_p': metrics.get('mean_prediction', np.nan),
                'success_rate': metrics.get('success_rate', np.nan),
                'brier': metrics.get('brier_score', np.nan),
                'pit_loss_mean': results_df['pitLoss_s'].mean() if 'pitLoss_s' in results_df else np.nan,
                'outlap_mean': results_df['outLapDelta_s'].mean() if 'outLapDelta_s' in results_df else np.nan
            })
        
        # Overall summary
        if all_results:
            combined_df = pd.concat([df for df in all_results if not df.empty], ignore_index=True)
            if not combined_df.empty:
                overall_metrics = self.compute_metrics(combined_df)
                
                summary_rows.append({
                    'gp': 'OVERALL',
                    'year': 'ALL',
                    'n_attempts': overall_metrics['n_attempts'],
                    'mean_p': overall_metrics.get('mean_prediction', np.nan),
                    'success_rate': overall_metrics.get('success_rate', np.nan),
                    'brier': overall_metrics.get('brier_score', np.nan),
                    'pit_loss_mean': combined_df['pitLoss_s'].mean() if 'pitLoss_s' in combined_df else np.nan,
                    'outlap_mean': combined_df['outLapDelta_s'].mean() if 'outLapDelta_s' in combined_df else np.nan
                })
        
        summary_df = pd.DataFrame(summary_rows)
        
        # Save summary
        summary_path = self.output_dir / "backtest_summary.csv"
        summary_df.to_csv(summary_path, index=False, float_format='%.6f')
        print(f"   💾 Summary saved: {summary_path}")
        
        return summary_df
    
    def save_model_quality_csv(self):
        """Save model quality log to CSV for analysis."""
        if not self.model_quality_log:
            print("   ⚠️  No model quality data to save")
            return
            
        print(f"💾 Saving model quality analysis...")
        
        # Convert to DataFrame
        quality_df = pd.DataFrame(self.model_quality_log)
        
        # Add summary statistics per circuit/compound combination
        summary_stats = quality_df.groupby(['circuit', 'compound']).agg({
            'deg_r2': ['mean', 'std', 'count'],
            'deg_rmse': ['mean', 'std'],
            'deg_scope': lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else 'unknown',
            'deg_n_samples': 'mean',
            'outlap_scope': lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else 'unknown',
            'outlap_n_samples': 'mean'
        }).round(6)
        
        # Flatten column names
        summary_stats.columns = ['_'.join(col).strip() for col in summary_stats.columns]
        summary_stats = summary_stats.reset_index()
        
        # Save detailed log
        quality_path = self.output_dir / "backtest_model_quality.csv"
        quality_df.to_csv(quality_path, index=False, float_format='%.6f')
        print(f"   💾 Model quality data saved: {quality_path}")
        
        # Save summary statistics
        summary_path = self.output_dir / "backtest_model_quality_summary.csv"
        summary_stats.to_csv(summary_path, index=False, float_format='%.6f')
        print(f"   💾 Model quality summary saved: {summary_path}")
        
        # Print quick summary
        print(f"   📊 Model quality overview:")
        print(f"      Degradation models: {quality_df['deg_scope'].value_counts().to_dict()}")
        print(f"      Outlap models: {quality_df['outlap_scope'].value_counts().to_dict()}")
        print(f"      Mean R²: {quality_df['deg_r2'].mean():.3f} (±{quality_df['deg_r2'].std():.3f})")
        
    def print_summary_table(self, summary_df: pd.DataFrame):
        """Print formatted summary table to stdout."""
        print("\n" + "="*80)
        print("🏁 F1 UNDERCUT SIMULATOR - BACKTEST RESULTS SUMMARY")
        print("="*80)
        
        if summary_df.empty:
            print("❌ No results to display")
            return
            
        # Format table
        print(f"{'GP':<12} {'Year':<6} {'N':<4} {'Mean P':<8} {'Success':<8} {'Brier':<8} {'PitLoss':<8} {'Outlap':<7}")
        print("-" * 80)
        
        for _, row in summary_df.iterrows():
            gp = row['gp']
            year = str(row['year']) if pd.notna(row['year']) else 'ALL'
            n = int(row['n_attempts']) if pd.notna(row['n_attempts']) else 0
            mean_p = f"{row['mean_p']:.3f}" if pd.notna(row['mean_p']) else "N/A"
            success = f"{row['success_rate']:.3f}" if pd.notna(row['success_rate']) else "N/A" 
            brier = f"{row['brier']:.4f}" if pd.notna(row['brier']) else "N/A"
            pit_loss = f"{row['pit_loss_mean']:.1f}s" if pd.notna(row['pit_loss_mean']) else "N/A"
            outlap = f"{row['outlap_mean']:.2f}s" if pd.notna(row['outlap_mean']) else "N/A"
            
            print(f"{gp:<12} {year:<6} {n:<4} {mean_p:<8} {success:<8} {brier:<8} {pit_loss:<8} {outlap:<7}")
        
        print("="*80)
        
        # Key insights
        overall_row = summary_df[summary_df['gp'] == 'OVERALL']
        if not overall_row.empty and pd.notna(overall_row.iloc[0]['brier']):
            brier = overall_row.iloc[0]['brier']
            n_total = int(overall_row.iloc[0]['n_attempts'])
            
            print(f"📊 OVERALL PERFORMANCE:")
            print(f"   • Total Undercut Attempts Analyzed: {n_total}")
            print(f"   • Brier Score: {brier:.4f} (lower is better, 0.25 = random)")
            
            if brier < 0.20:
                print(f"   ✅ EXCELLENT predictive accuracy!")
            elif brier < 0.25:
                print(f"   ✅ GOOD predictive accuracy (better than random)")
            else:
                print(f"   ⚠️  Accuracy needs improvement (similar to random)")
                
        print("="*80)
    
    def run_full_analysis(self):
        """Run the complete backtest analysis."""
        print("\n🚀 Starting F1 Undercut Simulator Backtest Analysis\n")
        
        all_results = []
        
        # Process each race
        for year, gp in RACES:
            print(f"\n📍 Processing {gp.upper()} {year}")
            print("-" * 50)
            
            try:
                # Fetch/load data
                race_data = self.fetch_or_load_data(gp, year)
                
                # Detect undercut attempts
                attempts_df = self.detect_undercut_attempts(race_data, gp, year)
                
                if attempts_df.empty:
                    print(f"   ⚠️  No undercut attempts detected for {gp} {year}")
                    continue
                
                # Run simulator predictions
                results_df = self.run_simulator_predictions(attempts_df)
                
                # Store results
                all_results.append(results_df)
                
                print(f"   ✅ {gp.upper()} {year}: {len(results_df)} attempts processed")
                
            except Exception as e:
                print(f"   ❌ Error processing {gp} {year}: {e}")
                continue
        
        if not all_results:
            print("\n❌ No race data processed successfully")
            if self.offline_mode:
                print("\n💡 TIP: Run without --offline flag first to populate caches")
            return
        
        # Combine all results for overall analysis
        combined_results = pd.concat([df for df in all_results if not df.empty], ignore_index=True)
        
        # Compute overall metrics and create visualizations
        overall_metrics = self.compute_metrics(combined_results)
        self.create_visualizations(combined_results, overall_metrics)
        
        # Create summary report
        summary_df = self.create_summary_report(all_results)
        
        # Save model quality analysis
        self.save_model_quality_csv()
        
        # Print results
        self.print_summary_table(summary_df)
        
        print(f"\n🎉 Analysis complete! Check {self.output_dir} for detailed outputs.")


def main():
    """Main execution function with CLI support."""
    parser = argparse.ArgumentParser(description='F1 Undercut Simulator Backtest Analysis')
    parser.add_argument('--offline', action='store_true', 
                       help='Run in offline mode using cached data only')
    
    args = parser.parse_args()
    
    # Check environment variable as well
    offline_mode = args.offline or os.getenv('OFFLINE', '0') == '1'
    
    # Initialize and run analysis
    analyzer = F1BacktestAnalyzer(offline_mode=offline_mode)
    analyzer.run_full_analysis()


if __name__ == "__main__":
    main()
