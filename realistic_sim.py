#!/usr/bin/env python3
import sys
sys.path.append('backend')

import numpy as np

# Test with more realistic F1 values
pit_loss = 24.0  # More realistic modern F1 pit stop
outlap_delta = 0.5
gap_seconds = 5.0  # Smaller gap
degradation_penalty = 0.15

print("Realistic F1 undercut simulation:")
print(f"Initial situation:")
print(f"  - Driver A pit loss: {pit_loss:.1f}s")
print(f"  - Driver A outlap penalty: {outlap_delta:.1f}s") 
print(f"  - Initial gap: {gap_seconds:.1f}s")
print(f"  - Driver B degradation per lap: {degradation_penalty:.2f}s")

driver_a_immediate_loss = pit_loss + outlap_delta
stint_length = 3  # shorter undercut window

cumulative_driver_a_advantage = 0
cumulative_driver_b_degradation = 0

print(f"\nLap-by-lap simulation over {stint_length} laps:")
print(f"Driver A starts {driver_a_immediate_loss:.1f}s behind")

for lap in range(stint_length):
    # More aggressive tire advantage (like soft vs hard compound)
    initial_advantage = 4.5  # seconds per lap
    tire_advantage = initial_advantage * (0.85 ** lap)
    cumulative_driver_a_advantage += tire_advantage
    
    # Driver B loses time due to degradation
    lap_degradation = degradation_penalty * (1.3 ** lap)
    cumulative_driver_b_degradation += lap_degradation
    
    net_position = driver_a_immediate_loss - cumulative_driver_a_advantage - cumulative_driver_b_degradation
    
    print(f"  Lap {lap+1}: A gains {tire_advantage:.2f}s, B loses {lap_degradation:.2f}s, net gap: {net_position:.1f}s")

# Final calculation
net_time_difference = (driver_a_immediate_loss - 
                      cumulative_driver_a_advantage - 
                      cumulative_driver_b_degradation)

print(f"\nFinal result:")
print(f"  - Driver A total advantage gained: {cumulative_driver_a_advantage:.1f}s")
print(f"  - Driver B total time lost: {cumulative_driver_b_degradation:.1f}s")
print(f"  - Net time difference: {net_time_difference:.1f}s")
print(f"  - Initial gap to overcome: {gap_seconds:.1f}s")
print(f"  - Undercut {'SUCCESS' if net_time_difference < gap_seconds else 'FAILURE'}")

success_rate = max(0, min(1, (gap_seconds - net_time_difference) / 10))
print(f"  - Estimated success probability: {success_rate*100:.1f}%")