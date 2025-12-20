
# Solar-Tea: PV & Battery Sizing Tool

A comprehensive Python-based tool for sizing Solar PV systems and Batteries, specifically tailored for Swiss residential scenarios. It integrates real equipment data (Sandia/CEC), `pvlib` for production simulation, and NREL's `PySAM` for high-fidelity battery dispatch analysis.

## Features

- **Real Equipment Database**: Automatically downloads and caches `SandiaMod` (Modules) and `CECInverter` databases.
- **Smart Selection**: Searches for specific manufacturers (e.g., Canadian Solar, Fronius) and checks electrical compatibility (Voltage windows, current limits, DC/AC sizing).
- **High-Fidelity Simulation**:
  - Uses `pvlib` with full SAPM/CEC parameter support for accurate generation profiles.
  - Simulates battery behavior using NREL's `PySAM` BatteryStateful module.
- **Optimization**:
  - Heuristic battery sizing (Autonomy days).
  - Cost-optimal sizing (minimizing CapEx + OpEx).
- **Roof Fitting**: Geometric analysis to fit modules on a defined roof area (Portrait vs Landscape).

## Project Structure

```
solar-tea/
├── main.py                # Entry point script
├── data/                  # Cached CSV databases (Sandia/CEC)
├── customization/
│   └── pv_equipments.py   # User customizable equipment lists
├── src/
│   ├── equipment_models.py# Dataclass schemas
│   ├── equipment_logic.py # Data loading, search, and compatibility checks
│   ├── pv_generation.py   # PVLib simulation logic
│   ├── battery_sizing.py  # Basic battery simulation & cost optimization
│   ├── battery_pysam.py   # NREL PySAM wrapper
│   └── roof_sizing.py     # Roof layout logic
└── requirements.txt       # Dependencies
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone git@github.com:hefnymah/solar-tea.git
   cd solar-tea
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install the package**:
   
   Using `pyproject.toml` (recommended):
   ```bash
   pip install -e .
   ```
   
   Or with development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
   
   Or using `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```


## Usage

Run the main application:
```bash
python main.py
```

### What happens?
1. **Load Profile**: Generates a synthetic daily load profile for a Swiss household.
2. **Equipment Search**: Looks for specific hardware in the cached databases.
3. **Roof Analysis**: Fits selected modules to a 10m x 6m roof.
4. **PV Simulation**: Simulates annual production using local TMY (or clear sky proxy) weather data.
5. **Battery Optimization**: Calculates optimal battery size for 1-day autonomy and cost-effectiveness.
6. **Validation**: API calls to `PySAM` validate the self-sufficiency calculations.


## Testing

Run the test suite with pytest:

```bash
pytest tests/ -v
```

Run tests with coverage report:

```bash
pytest tests/ -v --cov=eclipse/consumption --cov-report=term-missing
```

The test suite includes comprehensive unit tests for:
- `TimeSeriesAccessor` - Data accessor with aggregation methods
- `SeasonalAccessor` - Seasonal data filtering and profiling
- `ConsumptionData` - Main OOP data entry point
- `ConsumptionPlotter` - Separated plotting logic

Current test coverage: **81%** across the consumption module.

## Dependencies

- **pvlib**: Core PV modeling.
- **nrel-pysam**: Battery dispatch validation.
- **pandas/numpy/scipy**: Data handling and optimization.
