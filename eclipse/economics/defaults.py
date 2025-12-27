from .enums import BatteryChemistry, SystemCategory
# Battery costs and specifications by chemistry (2024 Swiss market)
BATTERY_DEFAULTS = {
    BatteryChemistry.LITHIUM_LFP: {
        "cost_per_kwh_chf": 450,
        "cycle_life": 6000,
        "calendar_life_years": 15,
    },
    BatteryChemistry.LITHIUM_NMC: {
        "cost_per_kwh_chf": 400,
        "cycle_life": 3000,
        "calendar_life_years": 12,
    },
    # ... other chemistries
}
# PV system costs by category (2024 Swiss market)
SYSTEM_DEFAULTS = {
    SystemCategory.ATTACHED_ROOF: {
        "cost_per_kwp_chf": 1800,
        "pronovo_rate_small": 440,  # CHF/kWp for <30kWp
        "pronovo_rate_large": 380,  # CHF/kWp for >=30kWp
    },
    SystemCategory.INTEGRATED_ROOF: {
        "cost_per_kwp_chf": 2200,
        "pronovo_rate_small": 470,
        "pronovo_rate_large": 410,
    },
    # ... other categories
}