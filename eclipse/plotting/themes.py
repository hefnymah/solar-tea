"""
Shared Plotting Themes and Utilities
====================================
Common styling configuration for consistent visualization across Eclipse.
"""

import matplotlib.pyplot as plt

# Eclipse Color Palette
COLORS = {
    'primary': '#2E86AB',      # Blue
    'secondary': '#A23B72',    # Purple
    'success': '#06A77D',      # Green
    'warning': '#F18F01',      # Orange
    'danger': '#C73E1D',       # Red
    'dark': '#2B2D42',         # Dark gray
    'light': '#EDF2F4',        # Light gray
}

# Season Colors
SEASON_COLORS = {
    'winter': '#4A90E2',   # Blue
    'spring': '#7ED321',   # Green
    'summer': '#F5A623',   # Orange
    'autumn': '#BD10E0',   # Purple
}

def apply_eclipse_style():
    """Apply Eclipse default plot styling."""
    plt.style.use('seaborn-v0_8-darkgrid')
    plt.rcParams.update({
        'figure.facecolor': 'white',
        'axes.facecolor': '#F9F9F9',
        'axes.edgecolor': '#CCCCCC',
        'axes.labelcolor': COLORS['dark'],
        'text.color': COLORS['dark'],
        'xtick.color': COLORS['dark'],
        'ytick.color': COLORS['dark'],
        'grid.color': '#E0E0E0',
        'grid.linestyle': '--',
        'grid.alpha': 0.5,
    })
