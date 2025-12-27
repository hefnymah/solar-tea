# Pronovo Subsidy Calculation Guide

Swiss PV subsidy (Einmalvergütung - EIV) calculation methodology.

**Official Source**: [pronovo.ch/de/services/tarifrechner/](https://pronovo.ch/de/services/tarifrechner/)

---

## Subsidy Structure

The total subsidy (Förderbeitrag) consists of these components:

| Component | German | Description |
|-----------|--------|-------------|
| Base Contribution | Leistungsbeitrag | Tiered per-kWp amount |
| Tilt Angle Bonus | Neigungswinkelbonus | Bonus for steep installations ≥75° |
| Altitude Bonus | Höhenbonus | Bonus for high altitude ≥1500m |
| Parking Area Bonus | Parkflächenbonus | Bonus for parking coverage ≥100kWp |
| **Total Subsidy** | **Förderbeitrag** | Sum of all above |

---

## Tiered Rate Structure (2025)

The Performance Contribution uses **degressive tiers**:

### Standard EIV (Attached/Freestanding)
| Tier | Capacity Range | Rate (CHF/kWp) |
|------|----------------|----------------|
| 1 | 0 - 30 kWp | 400 |
| 2 | 30 - 100 kWp | 300 |
| 3 | > 100 kWp | 280 |

### Integrated EIV (Indach) - Premium Rates
| Tier | Capacity Range | Rate (CHF/kWp) |
|------|----------------|----------------|
| 1 | 0 - 30 kWp | 440 |
| 2 | 30 - 100 kWp | 330 |
| 3 | > 100 kWp | 310 |

### HEIV (Volleinspeisung) - Higher Rates
| Tier | Capacity Range | Rate (CHF/kWp) |
|------|----------------|----------------|
| 1 | 0 - 30 kWp | 450 |
| 2 | 30 - 100 kWp | 350 |
| 3 | > 100 kWp | 250 |

---

## Calculation Example

**50 kWp Attached System:**

```
Base Contribution (Grundbeitrag):     200.00 CHF
Performance Contribution:
  └─ Tier 1: 30 kWp × 400 CHF/kWp = 12,000.00 CHF
  └─ Tier 2: 20 kWp × 300 CHF/kWp =  6,000.00 CHF
  └─ Total Leistungsbeitrag:        18,000.00 CHF
───────────────────────────────────────────────────
Total Subsidy (Förderbeitrag):      18,200.00 CHF
```

---

## Bonus Eligibility

| Bonus | Condition | Rate (CHF/kWp) |
|-------|-----------|----------------|
| Tilt Angle | Tilt ≥ 75° | 200 (standard) / 400 (integrated) |
| Altitude | Height ≥ 1500m | 100 |
| Parking | Coverage of parking, capacity ≥ 100kWp | 250 |

---

## Installation Types Mapping

| Our `SystemCategory` | Pronovo Classification |
|----------------------|------------------------|
| `INTEGRATED_ROOF` | Integriert (Indach) |
| `INTEGRATED_FACADE` | Integriert |
| `ATTACHED_ROOF` | Angebaut |
| `ATTACHED_FACADE` | Angebaut |
| `COMBINED` | Angebaut |
| `FREE_STANDING` | Freistehend |

---

## Code Usage

```python
from eclipse.economics.subsidies import PronovoSubsidyService, PronovoSystemConfig
from eclipse.economics.enums import SystemCategory

service = PronovoSubsidyService()

config = PronovoSystemConfig(
    capacity_kwp=50.0,
    installation_type=SystemCategory.ATTACHED_ROOF,
    has_self_consumption=True,  # EIV (not HEIV)
    altitude_meters=None,       # No altitude bonus
    tilt_angle_degrees=None     # No tilt bonus
)

result = service.calculate(config)

print(f"Base Contribution:        {result.base_contribution:,.2f} CHF")
print(f"Performance Contribution: {result.performance_contribution:,.2f} CHF")
print(f"Total Subsidy:            {result.total_subsidy:,.2f} CHF")
```

---

## References

- [Pronovo Tariff Calculator](https://pronovo.ch/de/services/tarifrechner/)
- [Pronovo EIV Documentation](https://pronovo.ch/de/foerderprogramme/eiv/)
- Rates valid from April 2024 - March 2025
