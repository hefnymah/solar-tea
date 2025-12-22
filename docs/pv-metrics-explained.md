# Understanding PV System Metrics

## Self-Sufficiency vs Self-Consumption

When analyzing a PV (solar) system's performance, two key metrics help you understand how well your system works. They measure different aspects of energy flow and answer different questions.

---

## 🏠 Self-Sufficiency (Autarchy)

**Question:** *"How much of MY CONSUMPTION is covered by solar?"*

```
Self-Sufficiency = (Energy Used from PV / Total Consumption) × 100
```

### Consumer Perspective

This metric tells you **how independent you are from the grid**.

**Example:**
- Your annual consumption: 2,331 kWh
- Energy you used directly from PV: 696 kWh
- **Self-Sufficiency: 29.9%**

**Interpretation:** 
- ✅ 30% of your electricity comes from your own solar panels
- ⚠️ 70% still needs to come from the grid (nighttime, cloudy days)

### Why It Matters
- Higher self-sufficiency = less dependent on grid electricity
- Lower electricity bills (less purchased from utility)
- Greater energy independence

---

## ☀️ Self-Consumption

**Question:** *"How much of MY SOLAR GENERATION do I actually use?"*

```
Self-Consumption = (Energy Used from PV / Total PV Generation) × 100
```

### Producer Perspective

This metric tells you **how efficiently you use the solar energy you generate**.

**Example:**
- Your PV generates: 1,864 kWh/year
- Energy you use directly from PV: 696 kWh
- Energy exported to grid: 1,168 kWh
- **Self-Consumption: 37.3%**

**Interpretation:**
- ✅ 37% of your solar production is used immediately
- 📤 63% is exported to the grid (surplus during sunny days)

### Why It Matters
- Higher self-consumption = better utilization of your investment
- Less energy wasted through grid export (if feed-in tariffs are low)
- More direct savings on electricity costs

---

## 📊 Typical Results Example

From a real sizing scenario (2.36 kWp system, 2,331 kWh annual consumption):

| Metric | Value | Meaning |
|--------|-------|---------|
| **Self-Sufficiency** | 32.1% | Only 32% of consumption covered by PV |
| **Self-Consumption** | 32.1% | Only 32% of PV generation used directly |
| **Annual Generation** | 2,331 kWh | Matches consumption exactly |
| **Grid Import** | 1,584 kWh | 68% of consumption from grid |
| **Grid Export** | 1,584 kWh | 68% of PV generation exported |

---

## ⏰ The Timing Mismatch Problem

**Why is there a gap between the target and achieved self-sufficiency?**

Without battery storage, you face a fundamental **timing mismatch**:

### Daytime (Sunny Hours)
- ☀️ PV generation: **HIGH**
- 🏠 Consumption: Low (most people at work/school)
- 📤 Result: **Large grid export** (surplus energy wasted)

### Nighttime (Evening/Morning)
- 🌙 PV generation: **ZERO**
- 🏠 Consumption: High (cooking, lighting, heating)
- 📥 Result: **All from grid** (100% grid dependent)

### Visualization

```
Hour  |  0  2  4  6  8 10 12 14 16 18 20 22
PV    |  ▁▁▁▁▃▅▇█████▇▅▃▁▁▁▁▁  (Sun pattern)
Load  |  ▅▃▂▂▃▄▄▆▆▇█████▇▅▄▃  (Typical home)
      |     🌙        ☀️        🌙
```

**Mismatch = Low self-sufficiency despite adequate generation!**

---

## 🔋 Solution: Battery Storage

Adding a battery system transforms your energy independence:

### Without Battery
| Metric | Value |
|--------|-------|
| Self-Sufficiency | 30% |
| Self-Consumption | 37% |
| Grid Import | High |
| Grid Export | High |

### With Battery (10 kWh)
| Metric | Value |
|--------|-------|
| Self-Sufficiency | **70-85%** ⬆️ |
| Self-Consumption | **80-95%** ⬆️ |
| Grid Import | **Low** ⬇️ |
| Grid Export | **Low** ⬇️ |

### How Battery Helps

**Daytime:**
- 📥 Store surplus PV → battery charging
- ✅ Increase self-consumption (less export)

**Nighttime:**
- 📤 Use stored energy → battery discharging
- ✅ Increase self-sufficiency (less import)

---

## 🎯 Optimization Strategies

### 1. **Maximize Self-Sufficiency** (Goal: Energy Independence)
- Add battery storage (10-15 kWh recommended)
- Shift consumption to solar hours (timers, smart devices)
- Oversize PV system slightly

### 2. **Maximize Self-Consumption** (Goal: Investment ROI)
- Match PV size to daytime consumption
- Use energy-intensive appliances during peak sun
- Add small battery for evening load shifting

### 3. **Balanced Approach** (Recommended)
- Size PV for 100-120% of annual consumption
- Add battery for 50-70% evening load coverage
- Smart home automation for load shifting

---

## 📈 Improving Both Metrics

| Strategy | Self-Sufficiency | Self-Consumption | Cost |
|----------|------------------|------------------|------|
| PV Only (Larger) | + | -- | € |
| PV + Small Battery (5 kWh) | ++ | ++ | €€ |
| PV + Medium Battery (10 kWh) | +++ | +++ | €€€ |
| PV + Large Battery (15 kWh) | ++++ | ++++ | €€€€ |
| PV + Battery + Load Shifting | +++++ | +++++ | €€€ |

---

## 💡 Key Takeaways

1. **Self-Sufficiency** measures your independence from the grid
2. **Self-Consumption** measures how efficiently you use your PV generation
3. Both metrics are limited by **timing mismatch** without storage
4. **Battery storage** is the key to achieving high values for both
5. Optimal system design balances PV capacity, battery size, and cost

---

## 🔮 Future: Battery Integration

The `eclipse.pvsim` module is designed to support battery sizing in future versions:

```python
# Future API (planned)
from eclipse.pvsim import PVSystemSizer

result = sizer.size_with_battery(
    target_self_sufficiency=80,
    battery_kwh=10.0,
    battery_power_kw=5.0
)

print(f"With battery: {result.self_sufficiency_pct}% self-sufficient")
```

Stay tuned! 🚀
