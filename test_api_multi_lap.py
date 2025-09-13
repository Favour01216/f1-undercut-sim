"""
Test the multi-lap simulation by starting the server and making HTTP requests.
"""

import requests
import json
import time

def test_multi_lap_api():
    """Test the multi-lap simulation via HTTP API."""
    base_url = "http://localhost:8000"
    
    print("=== Testing Multi-Lap Undercut API ===")
    
    # Test cases with different H values and scenarios
    test_cases = [
        {
            "name": "Default 2-lap strict undercut",
            "payload": {
                "gp": "bahrain",
                "year": 2024,
                "driver_a": "44",
                "driver_b": "1", 
                "compound_a": "MEDIUM",
                "lap_now": 25,
                "samples": 100,
                "H": 2,
                "p_pit_next": 1.0
            }
        },
        {
            "name": "5-lap with 50% B pits scenario",
            "payload": {
                "gp": "monza",
                "year": 2023,
                "driver_a": "16",
                "driver_b": "55",
                "compound_a": "SOFT", 
                "lap_now": 30,
                "samples": 100,
                "H": 5,
                "p_pit_next": 0.5
            }
        },
        {
            "name": "Single lap undercut",
            "payload": {
                "gp": "silverstone",
                "year": 2024,
                "driver_a": "63",
                "driver_b": "44",
                "compound_a": "HARD",
                "lap_now": 40,
                "samples": 100,
                "H": 1,
                "p_pit_next": 1.0
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   H={test_case['payload']['H']}, p_pit_next={test_case['payload']['p_pit_next']}")
        
        try:
            # Make request
            response = requests.post(
                f"{base_url}/simulate",
                json=test_case['payload'],
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"   ✅ Success!")
                print(f"   P(undercut): {result['p_undercut']:.1%}")
                print(f"   Expected margin: {result.get('expected_margin_s', 'N/A'):.2f}s")
                print(f"   90% CI: [{result.get('ci_low_s', 'N/A'):.2f}s, {result.get('ci_high_s', 'N/A'):.2f}s]")
                print(f"   H used: {result.get('H_used', 'N/A')}")
                
                # Show scenario breakdown if available
                scenarios = result.get('assumptions', {}).get('scenario_distribution', {})
                if scenarios:
                    total = sum(scenarios.values())
                    print(f"   Scenarios: B stays out {scenarios.get('b_stays_out', 0)}/{total}, B pits lap 1 {scenarios.get('b_pits_lap1', 0)}/{total}")
                
            else:
                print(f"   ❌ Failed: {response.status_code}")
                print(f"   Error: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ⚠️  Server not running. Start with: uvicorn backend.app:app --reload")
            break
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_backward_compatibility():
    """Test that old requests still work (without H and p_pit_next)."""
    print(f"\n=== Testing Backward Compatibility ===")
    
    old_style_payload = {
        "gp": "bahrain",
        "year": 2024,
        "driver_a": "44",
        "driver_b": "1",
        "compound_a": "MEDIUM",
        "lap_now": 25,
        "samples": 50
        # Note: No H or p_pit_next parameters
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/simulate",
            json=old_style_payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Backward compatibility works!")
            print(f"   Default H used: {result.get('H_used', 'N/A')}")
            print(f"   P(undercut): {result['p_undercut']:.1%}")
        else:
            print(f"   ❌ Failed: {response.status_code} - {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"   ⚠️  Server not running")
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    print("🏁 Multi-Lap Undercut Simulation Test")
    print("Make sure the server is running: uvicorn backend.app:app --reload")
    print()
    
    test_multi_lap_api()
    test_backward_compatibility()
    
    print(f"\n🏁 Testing complete!")