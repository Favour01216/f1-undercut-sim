#!/usr/bin/env python3
import sys
sys.path.append('backend')

from backend.models.pit import PitModel
from backend.services.openf1 import OpenF1Client

client = OpenF1Client()
pits = client.get_pit_events('bahrain', 2024)
model = PitModel()
model.fit(pits)

print('Pit model fitted')
print('Pit stop samples:')
for i in range(5):
    sample = model.sample(1)
    print(f'Sample {i+1}: {sample:.1f}s')

print(f'\nPit events data sample:')
print(pits[['driver_number', 'lap_number', 'pit_duration']].head())