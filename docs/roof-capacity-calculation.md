# Roof Capacity Calculation Guide

## Overview

The `max_capacity_kwp` property automatically calculates the maximum PV system capacity based on available roof area and panel efficiency.

## Formula

```python
max_capacity_kwp = roof_area_m² × module_efficiency
```

## Default Settings

- **Module Efficiency**: 0.20 (20% - standard panels)
- **Space Required**: ~5 m² per kWp

## Calculation Example

```python
from eclipse.pvsim import RoofConfig

roof = RoofConfig(
    tilt=30,                # 30° tilt
    azimuth=180,           # South-facing
    max_area_m2=50,        # 50 m² available
    module_efficiency=0.20  # 20% efficient panels
)

print(roof.max_capacity_kwp)  # → 10.0 kWp
```

**Breakdown:**
- 50 m² × 0.20 = **10 kWp maximum**

## Panel Efficiency Options

| Panel Type | Efficiency | m²/kWp | Max kWp (50 m²) |
|-----------|-----------|--------|-----------------|
| Budget    | 18%       | 5.6    | 9.0 kWp        |
| Standard  | 20%       | 5.0    | 10.0 kWp       |
| Premium   | 22%       | 4.5    | 11.0 kWp       |
| High-Eff  | 25%       | 4.0    | 12.5 kWp       |

## Determining Your Roof Area

### Method 1: Manual Measurement
```python
length_m = 10
width_m = 5
usable_factor = 0.7  # Account for chimneys, vents, etc.

usable_area = length_m * width_m * usable_factor
# → 35 m²
```

### Method 2: Satellite Imagery
1. Use Google Maps/Google Earth
2. Measure roof dimensions
3. Apply usable factor (70-80%)

### Method 3: Professional Survey
- Most accurate
- Solar installer measures during site visit
- Accounts for shading, obstructions

## Usable Area Factors

Not all roof area is usable:

| Obstacle | Area Loss |
|----------|-----------|
| Chimneys | ~5-10% |
| Vents/Skylights | ~5-10% |
| Shading | ~10-30% |
| Access paths | ~5-10% |

**Typical usable area: 70-80% of total roof**

## Real-World Examples

### Small House (30 m² roof)
```python
RoofConfig(max_area_m2=30, module_efficiency=0.20)
# → 6.0 kWp max
```

### Medium House (50 m² roof)
```python
RoofConfig(max_area_m2=50, module_efficiency=0.20)
# → 10.0 kWp max
```

### Large House (100 m² roof)
```python
RoofConfig(max_area_m2=100, module_efficiency=0.20)
# → 20.0 kWp max
```

## Integration with Sizing

The system automatically respects roof constraints:

```python
sizer = PVSystemSizer(data, location, roof)

# If optimization requests 15 kWp but roof only supports 10 kWp:
result = sizer.size_for_self_sufficiency(target_percent=100)

if result.constrained_by_roof:
    print(f"Limited to {result.recommended_kwp} kWp")
    print(f"Roof constraint: {roof.max_capacity_kwp} kWp")
```

## Best Practices

1. **Measure Conservatively**: Better to underestimate than overestimate
2. **Account for Obstructions**: Chimneys, vents, skylights
3. **Consider Shading**: Trees, neighboring buildings
4. **Use Professional Help**: For accurate assessment

## Panel Efficiency Selection Guide

**Budget-Conscious:**
- Use 18% efficiency
- More affordable panels
- Slightly larger area needed

**Standard (Recommended):**
- Use 20% efficiency
- Good balance of cost/performance
- Most common in examples

**Premium:**
- Use 22%+ efficiency
- Maximize limited roof space
- Higher upfront cost

## Formula Derivation

**Industry Standard:**
- 1 kWp panel produces 1000W peak power
- Under standard test conditions (STC): 1000 W/m² irradiance
- Panel efficiency = electrical output / solar input

**Example:**
- 1 m² panel at 20% efficiency
- Solar input: 1000 W/m²
- Electrical output: 1000 × 0.20 = 200 W = 0.20 kWp

**Therefore:** 1 m² → 0.20 kWp at 20% efficiency ✅
