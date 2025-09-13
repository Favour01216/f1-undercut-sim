# Multi-Lap Undercut Simulation

## Overview

The F1 Undercut Simulator now supports **multi-lap undercut scenarios** that simulate strategy battles over H laps instead of just a single lap comparison. This provides more realistic modeling of how undercuts actually play out in races.

## Key Features

### 🏁 Multi-Lap Horizon (H Parameter)

- **Parameter**: `H` (1-5 laps, default: 2)
- **Purpose**: Simulate undercut success over multiple laps
- **Validation**: Must be between 1 and 5 laps

### 🎲 Strategic Pit Response (p_pit_next Parameter)

- **Parameter**: `p_pit_next` (0.0-1.0, default: 1.0)
- **Purpose**: Probability that driver B responds by pitting on lap 1 after A pits
- **Scenarios**:
  - `1.0` = Strict undercut (B always responds immediately)
  - `0.5` = 50% chance B responds, 50% stays out
  - `0.0` = B never responds (stays out for all H laps)

### 📊 Enhanced Statistics

- **Expected Margin**: Mean time difference across all simulations
- **90% Confidence Intervals**: Statistical uncertainty bounds (5th-95th percentiles)
- **Scenario Distribution**: Breakdown of B's strategic responses

## API Changes

### Request Model (Backward Compatible)

```json
{
  "gp": "bahrain",
  "year": 2024,
  "driver_a": "44",
  "driver_b": "1",
  "compound_a": "MEDIUM",
  "lap_now": 25,
  "samples": 1000,
  "H": 3, // NEW: Number of laps (default: 2)
  "p_pit_next": 0.7 // NEW: B pit response probability (default: 1.0)
}
```

### Response Model (Enhanced)

```json
{
  "p_undercut": 0.68,
  "pitLoss_s": 24.2,
  "outLapDelta_s": 1.4,
  "avgMargin_s": 1.8, // Backward compatibility
  "expected_margin_s": 1.8, // NEW: Expected margin
  "ci_low_s": -0.5, // NEW: 90% CI lower bound
  "ci_high_s": 4.1, // NEW: 90% CI upper bound
  "H_used": 3, // NEW: Laps simulated
  "assumptions": {
    "scenario_distribution": {
      // NEW: Strategy breakdown
      "b_stays_out": 300,
      "b_pits_lap1": 700
    },
    "H_laps_simulated": 3,
    "p_pit_next": 0.7
    // ... other assumptions
  }
}
```

## Simulation Logic

### At t0 (Lap Now):

1. **Driver A pits**: Incurs pit loss + outlap penalty
2. **Driver B decision**: Stay out or pit on lap 1 (probability `p_pit_next`)

### Scenario 1: B Stays Out (probability = 1 - p_pit_next)

```
Lap 1: A (fresh, age 1) vs B (old, age N+1)
Lap 2: A (fresh, age 2) vs B (old, age N+2)
...
Lap H: A (fresh, age H) vs B (old, age N+H)
```

### Scenario 2: B Pits on Lap 1 (probability = p_pit_next)

```
Lap 1: A (fresh, age 1) vs B (old, age N+1) + B pits
Lap 2: A (fresh, age 2) vs B (fresh, age 1)
...
Lap H: A (fresh, age H) vs B (fresh, age H-1)
```

### Success Determination

- **Cumulative Time Comparison**: After H laps, compare total time difference
- **A Wins If**: `time_B_cumulative > time_A_cumulative`
- **Monte Carlo**: Repeat with stochastic pit loss, outlap penalties, and degradation residuals

## Strategic Insights

### H=1 (Single Lap)

- Classic undercut scenario
- High success rate if gap > pit loss + outlap penalty
- Minimal degradation advantage

### H=2-3 (Typical Undercut Window)

- More realistic multi-lap battles
- Degradation advantage accumulates
- Strategic responses matter

### H=4-5 (Extended Strategy Battle)

- Long-term tire performance dominates
- Strategic responses crucial
- Higher variance in outcomes

### p_pit_next Variations

- **1.0**: Models "forced response" scenarios
- **0.5-0.8**: Models realistic strategic uncertainty
- **0.0**: Models "staying out" strategies

## Example Use Cases

### 1. Classic Undercut Analysis (H=2, p_pit_next=1.0)

```json
{
  "H": 2,
  "p_pit_next": 1.0,
  "description": "Traditional 2-lap undercut with immediate response"
}
```

### 2. Strategic Uncertainty (H=3, p_pit_next=0.6)

```json
{
  "H": 3,
  "p_pit_next": 0.6,
  "description": "60% chance opponent responds, 40% stays out"
}
```

### 3. Long Stint Battle (H=5, p_pit_next=0.3)

```json
{
  "H": 5,
  "p_pit_next": 0.3,
  "description": "Opponent likely to stay out, test long-term advantage"
}
```

## Model Integration

### DegModel Enhancement

- **Per-Lap Degradation**: `get_fresh_tire_advantage(old_age, new_age)`
- **Cumulative Effect**: Degradation compounds over H laps
- **Stochastic Variation**: Random residuals per lap

### PitModel Integration

- **Pit Loss Sampling**: Normal distribution with variation
- **Multiple Pit Scenarios**: Both drivers may pit during simulation

### OutlapModel Enhancement

- **Cold Tire Penalties**: Applied to both drivers when they pit
- **Compound-Specific**: Different penalties for SOFT/MEDIUM/HARD

## Statistical Outputs

### Confidence Intervals

- **90% CI**: 5th and 95th percentiles of margin distribution
- **Interpretation**: Range of likely outcomes
- **Uncertainty Quantification**: Wider CI = more uncertain outcome

### Scenario Distribution

- **Strategic Insights**: How often each scenario occurs
- **Response Analysis**: Impact of pit response probability
- **Validation**: Ensure scenarios match expected probabilities

## Performance Considerations

### Computational Complexity

- **Linear in H**: Each additional lap adds minimal computation
- **Linear in Samples**: More samples = better statistics
- **Model Complexity**: Degradation models add slight overhead

### Caching Strategy

- **Cache Key**: Includes H and p_pit_next parameters
- **Invalidation**: Same cache expiry as single-lap simulations
- **Performance**: Multi-lap simulations cached like single-lap

## Validation & Testing

### Test Coverage

- ✅ H parameter validation (1-5 range)
- ✅ p_pit_next validation (0.0-1.0 range)
- ✅ Backward compatibility (default values)
- ✅ Scenario distribution accuracy
- ✅ Confidence interval calculation
- ✅ Multi-lap degradation modeling

### Expected Behaviors

- **H=1**: Should match original single-lap logic
- **p_pit_next=0**: All simulations show "B stays out"
- **p_pit_next=1**: All simulations show "B pits lap 1"
- **CI Width**: Should increase with H (more uncertainty)

## Migration Guide

### Existing Clients

- **No Changes Required**: Default values maintain compatibility
- **Optional Enhancement**: Add H and p_pit_next for better modeling

### Frontend Integration

- **New UI Elements**: Sliders for H (1-5) and p_pit_next (0-100%)
- **Enhanced Visualization**: Show confidence intervals and scenario breakdown
- **Progressive Enhancement**: Add features without breaking existing UI

## Future Enhancements

### Potential Extensions

- **Variable Pit Windows**: Allow B to pit on different laps (not just lap 1)
- **Multiple Compounds**: Different tire strategies for A and B
- **Safety Car Integration**: Random SC periods affecting strategy
- **Fuel Load Modeling**: Account for fuel weight advantages

### Advanced Statistics

- **Success Probability by Lap**: P(undercut success) for each individual lap
- **Optimal Pit Timing**: When B should respond for best counter-strategy
- **Risk-Adjusted Metrics**: Success probability weighted by margin size
