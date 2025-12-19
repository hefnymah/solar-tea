# Solar Tea - PV & Battery Sizing Tool

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
sys-size/
├── main.py              # Entry point script
├── data/                # Cached CSV databases (Sandia/CEC)
├── src/
│   ├── equipment_db.py  # Data loading, search, and compatibility checks
│   ├── pv_generation.py # PVLib simulation logic
│   ├── battery_sizing.py# Basic battery simulation & cost optimization
│   ├── battery_pysam.py # NREL PySAM wrapper
│   └── roof_sizing.py   # Roof layout logic
└── requirements.txt     # Dependencies
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone git@github.com:hefnymah/solar-tea.git
   cd solar-tea/sys-size
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
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

## Dependencies

- **pvlib**: Core PV modeling.
- **nrel-pysam**: Battery dispatch validation.
- **pandas/numpy/scipy**: Data handling and optimization.
