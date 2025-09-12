#!/usr/bin/env python3
"""
Simple test script to demonstrate the new API clients.
Run this to verify the OpenF1Client and JolpicaClient are working correctly.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.openf1 import OpenF1Client
from services.jolpica import JolpicaClient


def test_openf1_client():
    """Test the OpenF1Client functionality."""
    print("🔥 Testing OpenF1Client...")
    
    with OpenF1Client() as client:
        try:
            # Test get_laps - this might fail if no data available for the specific GP
            print("  → Fetching lap data for Bahrain 2024...")
            laps_df = client.get_laps("bahrain", 2024)
            print(f"    ✅ Retrieved {len(laps_df)} lap records")
            if not laps_df.empty:
                print(f"    📊 Columns: {list(laps_df.columns)}")
            
            # Test get_pit_events
            print("  → Fetching pit events for Bahrain 2024...")
            pit_df = client.get_pit_events("bahrain", 2024)
            print(f"    ✅ Retrieved {len(pit_df)} pit stop records")
            if not pit_df.empty:
                print(f"    📊 Columns: {list(pit_df.columns)}")
                
        except Exception as e:
            print(f"    ❌ OpenF1 test failed: {e}")


def test_jolpica_client():
    """Test the JolpicaClient functionality."""
    print("\n🏎️ Testing JolpicaClient...")
    
    with JolpicaClient() as client:
        try:
            # Test get_schedule
            print("  → Fetching 2024 race schedule...")
            schedule_df = client.get_schedule(2024)
            print(f"    ✅ Retrieved {len(schedule_df)} races")
            if not schedule_df.empty:
                print(f"    📊 Sample races: {list(schedule_df['race_name'].head(3))}")
            
            # Test get_results - using Monaco as it's a well-known GP
            print("  → Fetching Monaco 2024 results...")
            results_df = client.get_results("monaco", 2024)
            print(f"    ✅ Retrieved {len(results_df)} race results")
            if not results_df.empty:
                print(f"    🏆 Winner: {results_df.iloc[0]['given_name']} {results_df.iloc[0]['family_name']}")
                
        except Exception as e:
            print(f"    ❌ Jolpica test failed: {e}")


def main():
    """Run all tests."""
    print("🚀 Testing F1 API Clients")
    print("=" * 40)
    
    test_openf1_client()
    test_jolpica_client()
    
    print("\n✨ Tests completed!")
    print("\n📁 Check the 'features/' directory for cached Parquet files")


if __name__ == "__main__":
    main()
