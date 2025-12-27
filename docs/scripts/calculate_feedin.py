
from typing import Dict, Any, Optional
from tariff_service import TariffService

class FeedInTariffCalculator:
    """
    Replicates the logic of "Abnahmevergütung" (Feed-in Tariff) 
    from Excel 'Eingaben' sheet (Rows 68-73).
    """
    
    def __init__(self):
        self.tariff_service = TariffService()

    def calculate(
        self, 
        address: str, 
        annual_production_kwh: float, 
        share_feedin_percent: float = 20.0,
        year: str = "2024"
    ) -> Dict[str, Any]:
        """
        Calculate feed-in tariff parameters.
        
        Args:
            address: Swiss address to fetch real market rates.
            annual_production_kwh: Total annual solar production.
            share_feedin_percent: Percentage of production exported (Row 69). Default 20%.
            year: Year for the tariff data.
            
        Returns:
            Dictionary containing the calculated rows.
        """
        
        # 1. Fetch Real Rates
        summary = self.tariff_service.get_tariffs_for_address(address, year=year)
        
        energy_rate = 0.0
        hkn_rate = 0.0
        provider_name = "Unknown"
        
        if summary and summary.best_feedin_tariff:
            tariff = summary.best_feedin_tariff
            provider_name = tariff.provider_name
            # Use 'best_rate' logic or specific energy/hkn if available
            # Note: TariffService.FeedInTariff separates energy and eco_bonus (HKN)
            if tariff.energy_chf_kwh:
                energy_rate = tariff.energy_chf_kwh
            elif tariff.energy_rp_kwh:
                energy_rate = tariff.energy_rp_kwh / 100.0
                
            if tariff.eco_bonus_rp_kwh:
                hkn_rate = tariff.eco_bonus_rp_kwh / 100.0
        else:
            print(f"⚠️  Warning: No feed-in tariff found for {address}. Using defaults (0.0).")

        # 2. Perform Calculations
        
        # Row 71: Abnahmevergütung Energie (CHF/kWh)
        # Value from API
        row_71_energy_chf = energy_rate
        
        # Row 72: Herkunftsnachweis (HKN) (CHF/kWh)
        # Value from API
        row_72_hkn_chf = hkn_rate
        
        # Row 73: Abnahmevergütung Total (CHF/kWh)
        # Formula: Energy + HKN
        row_73_total_chf = row_71_energy_chf + row_72_hkn_chf
        
        # Row 69: Anteil Solarstrom mit Abnahmevergütung in %
        # Input value (default 20.0)
        row_69_share_percent = share_feedin_percent
        
        # Row 70: Anteil Solarstrom mit Abnahmevergütung in kWh
        # Formula: Annual Production * (Share / 100)
        row_70_volume_kwh = annual_production_kwh * (row_69_share_percent / 100.0)
        
        # Construct Result Dictionary matching Excel structure
        return {
            "parameters": {
                "address": address,
                "provider": provider_name,
                "year": year
            },
            "rows": {
                69: {
                    "label": "Anteil Solarstrom mit Abnahmevergütung in %",
                    "value": row_69_share_percent,
                    "unit": "%",
                    "description": "(konstant über Lebensdauer)"
                },
                70: {
                    "label": "Anteil Solarstrom mit Abnahmevergütung in kWh",
                    "value": row_70_volume_kwh,
                    "unit": "kWh",
                    "description": "(Ø Anteil Solarstrom...)"
                },
                71: {
                    "label": "Abnahmevergütung Energie",
                    "value": row_71_energy_chf,
                    "unit": "CHF/kWh",
                    "description": "(inkl. MWSt.)"
                },
                72: {
                    "label": "Herkunftsnachweis (HKN)",
                    "value": row_72_hkn_chf,
                    "unit": "CHF/kWh",
                    "description": "(inkl. MWSt.)"
                },
                73: {
                    "label": "Abnahmevergütung Total",
                    "value": row_73_total_chf,
                    "unit": "CHF/kWh",
                    "description": "(inkl. MWSt.)"
                }
            }
        }
