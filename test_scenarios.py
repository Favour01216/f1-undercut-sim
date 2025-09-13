#!/usr/bin/env python3
import requests
import json

scenarios = [
    {'gp': 'bahrain', 'year': 2024, 'driver_a': 'VER', 'driver_b': 'HAM', 'compound_a': 'SOFT', 'lap_now': 10},
    {'gp': 'bahrain', 'year': 2024, 'driver_a': 'VER', 'driver_b': 'HAM', 'compound_a': 'SOFT', 'lap_now': 20},
    {'gp': 'bahrain', 'year': 2024, 'driver_a': 'VER', 'driver_b': 'HAM', 'compound_a': 'MEDIUM', 'lap_now': 16},
    {'gp': 'bahrain', 'year': 2024, 'driver_a': 'VER', 'driver_b': 'HAM', 'compound_a': 'HARD', 'lap_now': 16},
]

print("Testing different scenarios:")
for i, scenario in enumerate(scenarios, 1):
    response = requests.post('http://localhost:8000/simulate', json=scenario)
    result = response.json()
    
    print(f"{i}. {scenario['compound_a']} lap {scenario['lap_now']}: {result['p_undercut']*100:.1f}% success rate")