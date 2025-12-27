# Solar-Tea: PV & Battery Sizing Tool

A comprehensive Python-based tool for sizing Solar PV systems and Batteries, specifically tailored for Swiss residential scenarios. It integrates real equipment data, `pvlib` for production simulation, NREL's `PySAM` for battery dispatch, and a modular optimization framework.

## Features

- **PV System Sizing**: Size systems for self-sufficiency or self-consumption targets
- **Battery Integration**: Physics-based battery sizing with charging/discharging simulation
- **Smart Optimization**: Modular optimization framework with pluggable algorithms
- **High-Fidelity Simulation**:
  - Uses `pvlib` with PVGIS/TMY weather data
  - Battery simulation via NREL's `PySAM` or built-in SimpleBatterySimulator
- **Visualization**: Professional plots for monthly comparisons, seasonal profiles, battery SOC

## Package Structure

```
solar-tea/
├── eclipse/                                     # Main package
│   ├── consumption/                             # Load profile handling
│   │   ├── data.py                              # ConsumptionData class
│   │   └── plotter.py                           # Visualization
│   ├── simulation/                              # PV system simulation
│   │   ├── system_sizer.py                      # PVSystemSizer class
│   │   └── configs.py                           # Location, Roof, Battery configs
│   ├── battery/                                 # Battery simulation
│   │   ├── simple.py                            # SimpleBatterySimulator
│   │   └── pysam.py                             # PySAM integration
│   ├── economics/                             # Economics module
│   │   ├── __init__.py                        # Public API exports
│   │   ├── enums.py                           # All Enum definitions
│   │   ├── config.py                          # Dataclass configurations
│   │   ├── defaults.py                        # Swiss market defaults registry
│   │   ├── capex/
│   │   │   ├── __init__.py
│   │   │   └── calculator.py                  # CAPEX calculation logic
│   │   ├── opex/
│   │   │   ├── __init__.py
│   │   │   └── calculator.py                  # OPEX/maintenance logic
│   │   ├── subsidies/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                        # Abstract subsidy interface
│   │   │   └── che_pronovo.py                 # Swiss Pronovo implementation
│   │   └── analysis/
│   │       ├── __init__.py
│   │       └── cashflow.py                    # NPV, IRR, payback calculations
│   └── plotting/                              # Plotting module
│       ├── __init__.py                        # Public API exports
│       ├── enums.py                           # All Enum definitions
│       ├── config.py                          # Dataclass configurations
│       ├── defaults.py                        # Swiss market defaults registry
│       ├── capex/
│       │   ├── __init__.py
│       │   └── calculator.py                  # CAPEX calculation logic
│       ├── opex/
│       │   ├── __init__.py
│       │   └── calculator.py                  # OPEX/maintenance logic
│       ├── subsidies/
│       │   ├── __init__.py
│       │   ├── base.py                        # Abstract subsidy interface
│       │   └── che_pronovo.py                 # Swiss Pronovo implementation
│       └── analysis/
│           ├── __init__.py
│           └── cashflow.py                    # NPV, IRR, payback calculations
│   ├── optimization/                            # Optimization module
│   │   ├── base.py                              # Abstract Optimizer class
│   │   ├── objectives.py                        # Objective functions
│   │   └── sweep.py                             # SweepOptimizer (OOP demo)
│   └── config/                                  # Equipment configurations
├── examples/                                    # Usage examples
│   ├── 10-pv-system-sizing.py                   # Basic PV sizing
│   ├── 11-pv-battery-sizing.py                  # PV + battery demo
│   ├── 12-auto-pv-battery-optimization.py       # Auto optimization demo
│   ├── 13-ultimate-pv-battery-optimization.py   # Ultimate optimization demo
│   └── 14-optimization-module-demo.py           # OOP demo
├── docs/                                        # Documentation
├── tests/                                       # Unit tests
└── data/                                        # Sample data files
```

│
## Installation

```bash
# Clone repository
git clone git@github.com:hefnymah/solar-tea.git
cd solar-tea

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install package
pip install -e .

# With optional dependencies
pip install -e ".[optimization]"  # For advanced optimizers
pip install -e ".[economics]"     # For NPV/IRR calculations
pip install -e ".[all]"           # Everything
```

## Quick Start

### Basic PV Sizing

```python
from eclipse.consumption import ConsumptionData
from eclipse.simulation import PVSystemSizer, LocationConfig, RoofConfig

# Load consumption data
data = ConsumptionData.load("data/consumption/hourly.csv")

# Configure system
location = LocationConfig(latitude=47.38, longitude=8.54)
roof = RoofConfig(tilt=30, azimuth=180, max_area_m2=50)

# Size for 80% self-sufficiency
sizer = PVSystemSizer(data, location, roof)
result = sizer.size_for_self_sufficiency(target_percent=80)
print(result)
```

### Using the Optimization Module

```python
from eclipse.optimization import SweepOptimizer, OptimizationBounds

# Create optimizer (Strategy pattern - swappable)
optimizer = SweepOptimizer(priority='performance')

# Define search space
bounds = OptimizationBounds(pv_max_kwp=10.0, battery_max_kwh=20.0)

# Run optimization
result = optimizer.optimize(
    objective=lambda pv, bat: -sizer.simulate(pv, bat).self_sufficiency_pct,
    bounds=bounds,
    target_value=-80.0
)
```

## Examples

| Example | Description |
|---------|-------------|
| 10 | Basic PV system sizing |
| 11 | PV + fixed battery integration |
| 12 | Automatic battery optimization |
| 13 | Joint PV + battery optimization |
| 14 | OOP optimization module demo |

Run examples:
```bash
python examples/14-optimization-module-demo.py
```

## Architecture

### Optimization Layer
```
┌─────────────────────────────────────────────────────────────┐
│                    OPTIMIZATION LAYER                       │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐         │
│  │  JAYA   │  │ NSGA-II │  │  MILP   │  │ Sweep   │ ...     │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘         │
│       └────────────┴────────────┴────────────┘              │
│                         │                                   │
│              Common Objective Function                      │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────────┐
│                   TECHNO-ECONOMIC MODULE                    │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐      │
│  │ CAPEX Model  │  │ OPEX Model   │  │ Revenue Model │      │
│  │ (PV, Battery)│  │ (Maint, Grid)│  │ (Feed-in,     │      │
│  └──────────────┘  └──────────────┘  │  Self-consume)│      │
│                                      └───────────────┘      │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────────┐
│                    PHYSICS SIMULATION                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   PVLib      │  │   PySAM      │  │   Battery    │       │
│  │ (Irradiance, │  │ (Detailed    │  │ (Simple/PySAM│       │
│  │  PV Model)   │  │  PV+Storage) │  │  Simulator)  │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘

```
### Algorithm Selection Guide

| Algorithm | Best For | Pros | Cons |
|-----------|----------|------|------|
| **JAYA** | Single-objective | No parameters, fast | Local optima |
| **NSGA-II** | Multi-objective (cost vs performance) | Pareto front | Slower |
| **MILP/PuLP** | Linear/convex problems | Global optimum | Limited to linear models |
| **Sweep** | Quick estimates | Simple, interpretable | Coarse grid |


## Testing

```bash
pytest tests/ -v
pytest tests/ -v --cov=eclipse --cov-report=term-missing
```

## Dependencies

**Core:**
- `pvlib>=0.10` - PV modeling
- `nrel-pysam>=5.0` - Battery simulation
- `pandas>=2.0`, `numpy>=1.24`, `scipy>=1.10`
- `matplotlib>=3.7` - Visualization

**Optional:**
- `pymoo>=0.6` - NSGA-II multi-objective optimization
- `pulp>=2.7` - MILP linear programming
- `numpy-financial>=1.0` - Economic analysis

## License

MIT License - See [LICENSE](LICENSE) file.