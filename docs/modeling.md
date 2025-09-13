# 🔬 F1 Undercut Simulator - Modeling Documentation

_Comprehensive technical documentation for tire age calculation and edge case handling_

---

## 📖 Overview

This document provides detailed technical information about the tire age calculation methodology used in the F1 Undercut Simulator. The TyreAgeCalculator is a critical component that ensures accurate modeling of tire degradation by properly tracking tire age across complex race scenarios.

---

## 🏁 Tire Age Definition

### Core Concept

**Tire Age** represents the number of racing laps completed on a specific set of tires. This is fundamental to F1 strategy analysis as tire performance degrades predictably with age.

### Age Progression Rules

- **Age 1**: First lap after tire change (out-lap from pit stop)
- **Age 2+**: Subsequent laps on the same tire set
- **Reset**: Age returns to 1 when new tires are fitted during a pit stop
- **Pause**: Age does NOT increment during Safety Car (SC) or Virtual Safety Car (VSC) periods
- **Pause**: Age does NOT increment during pit lane traversal

### Example Race Progression

```
Lap 1-10:  Tire age [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
Lap 11:    Pit stop → Tire age resets to 1
Lap 12-15: Tire age [2, 3, 4, 5]
Lap 16-17: Safety Car → Tire age [5, 5] (no increment)
Lap 18-20: Normal racing → Tire age [6, 7, 8]
```

---

## ⚙️ Technical Implementation

### Input Requirements

#### Laps DataFrame

Required columns:

- `driver_number` (int): Unique identifier for each driver
- `lap_number` (int): Sequential lap number in the race

Optional columns:

- `is_pit_out_lap` (bool): Explicit flag for pit exit laps
- `lap_time` (float): Lap duration in seconds (for SC detection)
- `lap_duration` (float): Alternative lap duration column
- `track_status` (str): Official track status codes

#### Pits DataFrame

Required columns:

- `driver_number` (int): Must match driver numbers in laps data
- `lap_number` (int): Lap on which pit stop occurred

### Output Format

Returns the input laps DataFrame with an additional `tyre_age` column containing integer tire age values starting from 1.

### Algorithm Overview

```python
for each driver:
    current_age = 1
    for each lap:
        if pit_stop_occurred or is_pit_out_lap:
            current_age = 1  # Reset
        elif safety_car_active:
            # Keep current age (no increment)
        else:
            current_age += 1  # Normal increment

        tyre_age[lap] = current_age
```

---

## 🚨 Edge Case Handling

### 1. Double Pit Stops (Unsafe Release)

**Scenario**: Driver pits twice on the same lap due to unsafe release or equipment issues.

**Problem**: Naive implementations might reset tire age twice, causing incorrect age progression.

**Solution**: Use `drop_duplicates(subset=['lap_number'], keep='last')` to retain only the final pit stop entry for each lap.

**Example**:

```python
# Raw pit data with double stop
pits_df = pd.DataFrame({
    'lap_number': [15, 15],  # Two entries for lap 15
    'driver_number': [1, 1]
})

# After deduplication: only one entry remains
# Tire age resets once on lap 15
```

### 2. Safety Car / Virtual Safety Car Periods

**Scenario**: Race is neutralized due to incidents, resulting in artificially slow lap times.

**Problem**: Tire degradation effectively pauses during neutralized conditions, so tire age should not increment.

**Solution**: Multi-method SC detection:

1. Check `track_status` column for official codes ('4'=SC, '6'=VSC)
2. Detect anomalously slow laps (>30% slower than normal)
3. Analyze sector timing flags for yellow/red indicators

**Example**:

```python
# Normal racing: age increments
Lap 20: Age 10 → Age 11
Lap 21: Age 11 → Age 12

# Safety Car period: age holds
Lap 22: SC detected → Age 12 (no change)
Lap 23: SC continues → Age 12 (no change)

# Racing resumes: age increments
Lap 24: SC ends → Age 12 → Age 13
```

### 3. Missing Pit Data

**Scenario**: Pit stop occurred but not recorded in pit data, only marked via `is_pit_out_lap=True`.

**Problem**: Without explicit pit data, tire age calculation might miss tire changes.

**Solution**: Use `is_pit_out_lap` flag as primary indicator, falling back to pit data for validation.

**Example**:

```python
# Lap marked as pit out but missing from pit data
lap_data = {'lap_number': 25, 'is_pit_out_lap': True}
# Still triggers tire age reset to 1
```

### 4. First Lap Behavior

**Scenario**: Race start where all drivers begin with fresh tires.

**Problem**: Determining initial tire age for lap 1.

**Solution**: Initialize all drivers with tire age 1 on lap 1, representing the first lap on race start tires.

### 5. Pit Lane Traversal Timing

**Scenario**: Lap times >200 seconds indicating pit lane traversal.

**Problem**: These laps have different performance characteristics.

**Solution**: Detect pit-related laps through timing analysis and handle appropriately without affecting age calculation logic.

---

## 🧪 Validation & Testing

### Test Coverage

The comprehensive test suite validates:

1. **Basic Functionality**

   - Standard tire age progression (1, 2, 3, ...)
   - Single pit stop reset behavior
   - Multiple driver independence

2. **Edge Cases**

   - Double pit stops on same lap
   - Safety Car period handling
   - Missing `is_pit_out_lap` columns
   - Empty input DataFrames
   - Single lap races
   - Final lap pit stops
   - Consecutive pit stops

3. **Integration Scenarios**
   - Multi-driver races with different strategies
   - Realistic 57-lap GP distance with 2-stop strategy
   - Combined SC periods and pit stops

### Example Test Case

```python
def test_safety_car_with_pit_stop():
    # Setup: 10 laps with SC on laps 3-4 and pit on lap 5
    expected_ages = [1, 2, 2, 2, 1, 2, 3, 4, 5, 6]
    #                ^  ^  ^  ^  ^  ^  ^  ^  ^  ^
    #                1  2  SC SC PIT 2  3  4  5  6

    result = calculator.compute_tyre_age(laps_df, pits_df)
    assert result['tyre_age'].tolist() == expected_ages
```

### Debug Mode

Enable detailed logging for troubleshooting:

```python
calculator = TyreAgeCalculator(debug=True)
# Outputs: "Lap 15: Pit stop, age reset to 1"
#          "Lap 22: SC/VSC, age held at 8"
```

---

## 📊 Real-World Examples

### Bahrain GP 2024 Pattern

```python
# Typical 2-stop strategy over 57 laps
pit_laps = [15, 38]  # Lap 15 and 38 pit stops

# Resulting tire age progression:
# Laps 1-15:  [1, 2, 3, ..., 14, 1]     # First stint + pit
# Laps 16-38: [2, 3, 4, ..., 23, 1]     # Second stint + pit
# Laps 39-57: [2, 3, 4, ..., 20]        # Final stint
```

### Monaco GP with Safety Car

```python
# High SC probability, typical 1-stop strategy
sc_laps = [35, 36, 37, 38]  # 4-lap SC period
pit_lap = 40  # Pit during/after SC

# Tire aging accounts for SC neutralization:
# - Ages 34-34-34-34 during SC (no increment)
# - Reset to 1 on pit lap 40
# - Normal progression thereafter
```

---

## 🔗 Integration Points

### OpenF1 Client Integration

The TyreAgeCalculator integrates with the OpenF1 client via:

```python
from services.tyre_age import TyreAgeCalculator

# In OpenF1 client
calculator = TyreAgeCalculator()
laps_with_age = calculator.compute_tyre_age(laps_df, pits_df)
```

### Degradation Model Usage

The resulting tire age data feeds into degradation modeling:

```python
# DegModel expects 'tyre_age' column
deg_model = DegModel()
deg_model.fit(laps_with_age[['lap_time', 'tyre_age', 'compound']])
```

### Performance Considerations

- **Vectorized Operations**: Uses NumPy for efficient tire age computation
- **Memory Efficient**: Processes drivers independently to manage memory usage
- **Caching Compatible**: Output format matches OpenF1 client cache expectations

---

## 📝 Best Practices

### When to Use

- ✅ Analyzing historical race data for strategy insights
- ✅ Validating undercut simulation model inputs
- ✅ Research on tire degradation patterns
- ✅ Building strategy optimization algorithms

### When NOT to Use

- ❌ Real-time race strategy (requires live timing integration)
- ❌ Predictive modeling without historical lap data
- ❌ Analysis of non-F1 racing series (different tire regulations)

### Data Quality Recommendations

1. **Validate Input Data**: Ensure lap and pit data cover the same time period
2. **Check for Completeness**: Missing laps can cause age calculation errors
3. **Verify Driver Numbers**: Inconsistent driver IDs break per-driver calculations
4. **Monitor Edge Cases**: Log warnings for unusual patterns (e.g., >5 pit stops)

---

## 🔧 Troubleshooting

### Common Issues

**Issue**: Tire ages start from 0 instead of 1

```python
# Problem: Old implementation started from 0
# Solution: Updated to start from 1 (F1 convention)
```

**Issue**: SC laps incorrectly increment tire age

```python
# Problem: Missing SC detection
# Solution: Enable debug mode to verify SC detection
calculator = TyreAgeCalculator(debug=True)
```

**Issue**: Double pit stops cause negative tire ages

```python
# Problem: Processing duplicate pit entries
# Solution: Automatic deduplication in _get_driver_pit_events()
```

### Debug Checklist

1. Enable debug logging: `TyreAgeCalculator(debug=True)`
2. Verify input column names match requirements
3. Check for NaN values in critical columns
4. Validate lap number sequences are continuous
5. Confirm pit lap numbers exist in lap data

---

## 📚 References

- **F1 Technical Regulations**: Tire usage and compound rules
- **OpenF1 API Documentation**: Data source specifications
- **Pandas Documentation**: DataFrame manipulation best practices
- **NumPy Documentation**: Vectorized computation patterns

---

_Last Updated: December 2024_  
_Version: 1.0.0_  
_Maintainer: F1 Undercut Simulator Team_
