#!/usr/bin/env python3
import requests
import json

response = requests.post('http://localhost:8000/simulate', json={
    'gp': 'bahrain', 
    'year': 2024, 
    'driver_a': 'VER', 
    'driver_b': 'HAM', 
    'compound_a': 'SOFT', 
    'lap_now': 16
})

print('Status:', response.status_code)
result = response.json()
print(f'Success rate: {result["p_undercut"]*100:.1f}%')
print('Models used:', result['assumptions']['models_fitted'])
print('Gap:', f"{result['assumptions']['current_gap_s']:.2f}s")