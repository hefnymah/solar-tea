
import math
from typing import Tuple
from eclipse.config.equipment_models import MockModule

def check_roof_fit(
    roof_width: float, 
    roof_height: float, 
    module: MockModule, 
    setback: float = 0.5,
    landscape: bool = False
) -> Tuple[int, float]:
    """
    Calculates max modules fitting on a rectangular roof.
    Returns (num_modules, total_area_used).
    """
    usable_width = roof_width - (2 * setback)
    usable_height = roof_height - (2 * setback)
    
    if usable_width <= 0 or usable_height <= 0:
        return 0, 0.0
    
    mod_w = module.width_m
    mod_h = module.height_m
    
    if landscape:
        # Swap module dims for calculation
        dim1, dim2 = mod_h, mod_w
    else:
        dim1, dim2 = mod_w, mod_h
        
    cols = math.floor(usable_width / dim1)
    rows = math.floor(usable_height / dim2)
    
    total_modules = cols * rows
    area_used = total_modules * (mod_w * mod_h)
    
    return total_modules, area_used

def suggest_best_orientation(roof_width, roof_height, module, setback=0.5):
    """
    Compares Portrait vs Landscape to maximize module count.
    """
    count_p, area_p = check_roof_fit(roof_width, roof_height, module, setback, landscape=False)
    count_l, area_l = check_roof_fit(roof_width, roof_height, module, setback, landscape=True)
    
    if count_l > count_p:
        return "Landscape", count_l
    else:
        return "Portrait", count_p
