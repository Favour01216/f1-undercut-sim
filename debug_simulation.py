#!/usr/bin/env python3
import requests
import json

# Get detailed debug info
response = requests.post('http://localhost:8000/simulate', json={
    'gp': 'bahrain', 
    'year': 2024, 
    'driver_a': 'VER', 
    'driver_b': 'HAM', 
    'compound_a': 'SOFT', 
    'lap_now': 16,
    'samples': 100  # Minimum allowed
})

print('Status:', response.status_code)
print('Response:')
print(response.text)