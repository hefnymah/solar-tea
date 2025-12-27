from dataclasses import dataclass
from typing import TYPE_CHECKING
import math

if TYPE_CHECKING:
    from eclipse.config.equipment_models import MockModule

@dataclass(frozen=True)
class CapexResult:
    """
    Breakdown of system capital expenditure.
    
    Attributes:
        module_count (int): Number of modules required.
        module_model_name (str): Name of the PV module.
        module_cost_base (float): Base cost of modules (Purchase Price).
        module_margin_amount (float): Calculated margin amount.
        module_cost_total (float): Total cost to customer (Base + Margin).
        currency (str): Currency code (e.g., 'EUR', 'CHF').
    """
    module_count: int
    module_model_name: str
    module_cost_base: float
    module_margin_amount: float
    module_cost_total: float
    currency: str

class CapexCalculator:
    """
    Calculates system capital expenditure (CAPEX) including equipment costs and margins.
    """
    
    def calculate_module_cost(
        self, 
        system_size_kwp: float, 
        module_model: 'MockModule',
        margin_pct: float = 0.0
    ) -> CapexResult:
        """
        Calculates the total cost of PV modules for a given system size.
        
        Args:
            system_size_kwp: Target system size in kWp.
            module_model: The PV module equipment model containing specs and economics.
            margin_pct: Profit margin as a decimal (e.g., 0.20 for 20%).
            
        Returns:
            CapexResult: Detailed cost breakdown.
        """
        if system_size_kwp <= 0:
            return CapexResult(0, module_model.name, 0.0, 0.0, 0.0, "EUR")

        # 1. Calculate number of modules needed
        # Convert kWp to Wp and divide by module wattage
        system_watts = system_size_kwp * 1000.0
        num_modules = math.ceil(system_watts / module_model.power_watts)
        
        # 2. Get base economics
        # Safe access to economics dict or object (MockModule usually has .economics as SimpleNamespace or dict)
        price_per_unit = 0.0
        currency = "EUR"
        
        if hasattr(module_model, 'economics'):
            econ = module_model.economics
            # Handle SimpleNamespace or dict (MockModule usually converts to namespace in post_init)
            if hasattr(econ, 'price_per_unit'):
                price_per_unit = float(econ.price_per_unit)
                currency = getattr(econ, 'currency', "EUR")
            elif isinstance(econ, dict): 
                price_per_unit = float(econ.get('price_per_unit', 0.0))
                currency = econ.get('currency', "EUR")

        base_cost = num_modules * price_per_unit
        
        # 3. Calculate Margin
        margin_amount = base_cost * margin_pct
        total_cost = base_cost + margin_amount
        
        return CapexResult(
            module_count=num_modules,
            module_model_name=module_model.name,
            module_cost_base=base_cost,
            module_margin_amount=margin_amount,
            module_cost_total=total_cost,
            currency=currency
        )