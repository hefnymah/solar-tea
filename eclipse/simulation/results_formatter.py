"""
Results Formatter
==================
Formatting and display utilities for PV sizing results.

This module provides reusable tools for:
- Printing formatted result summaries
- Displaying analysis insights
- Generating scenario comparison tables

Author: Eclipse Framework
"""

from __future__ import annotations
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from eclipse.simulation.system_sizer import SizingResult
    from eclipse.simulation.sizing_utils import ScenarioResult


class ResultsFormatter:
    """
    Format and display PV sizing results.
    
    Provides static methods for consistent, professional output formatting
    across all examples and applications.
    
    Example:
        >>> ResultsFormatter.print_summary(result)
        >>> ResultsFormatter.print_analysis(result)
        >>> ResultsFormatter.print_scenario_comparison(scenarios)
    """
    
    @staticmethod
    def print_summary(result: 'SizingResult', title: str = "SIMULATION RESULTS") -> None:
        """
        Print a formatted summary table of sizing results.
        
        Args:
            result: SizingResult object from simulation
            title: Section title (default: "SIMULATION RESULTS")
        """
        print(f"\n{'=' * 70}")
        print(title)
        print(f"{'=' * 70}")
        
        print(f"\n{'Metric':<45} {'Value':>20}")
        print("-" * 70)
        print(f"{'System Size':<45} {result.recommended_kwp:>17.2f} kWp")
        print(f"{'Annual PV Generation':<45} {result.annual_generation_kwh:>17,.0f} kWh")
        print(f"{'Annual Consumption':<45} {result.annual_consumption_kwh:>17,.0f} kWh")
        print("-" * 70)
        print(f"{'Self-Sufficiency (% consumption covered)':<45} {result.self_sufficiency_pct:>18.1f} %")
        print(f"{'Self-Consumption (% PV used locally)':<45} {result.self_consumption_pct:>18.1f} %")
        print("-" * 70)
        print(f"{'Grid Import Required':<45} {result.annual_grid_import_kwh:>17,.0f} kWh")
        print(f"{'Grid Export (Surplus)':<45} {result.annual_grid_export_kwh:>17,.0f} kWh")
        print(f"{'Self-Consumed Energy':<45} {result.annual_self_consumed_kwh:>17,.0f} kWh")
        print("-" * 70)
        print(f"{'Specific Yield':<45} {result.specific_yield_kwh_per_kwp:>14.0f} kWh/kWp/yr")
        print("=" * 70)
    
    @staticmethod
    def print_analysis(result: 'SizingResult', title: str = "ANALYSIS & INSIGHTS") -> None:
        """
        Print analysis and insights for a sizing result.
        
        Args:
            result: SizingResult object from simulation
            title: Section title (default: "ANALYSIS & INSIGHTS")
        """
        print(f"\n{'=' * 70}")
        print(title)
        print(f"{'=' * 70}")
        
        generation_ratio = result.annual_generation_kwh / result.annual_consumption_kwh
        
        print(f"\n📊 Generation/Consumption Ratio: {generation_ratio:.2f}x")
        
        if generation_ratio >= 1.0:
            surplus_pct = (generation_ratio - 1.0) * 100
            net_export = result.annual_grid_export_kwh - result.annual_grid_import_kwh
            print(f"   ✅ System generates MORE than consumed")
            print(f"   📈 Surplus: {surplus_pct:.1f}% over annual consumption")
            print(f"   💰 Net grid export: {net_export:,.0f} kWh/year")
        else:
            deficit_pct = (1.0 - generation_ratio) * 100
            net_import = result.annual_grid_import_kwh - result.annual_grid_export_kwh
            print(f"   ⚠️  System generates LESS than consumed")
            print(f"   📉 Deficit: {deficit_pct:.1f}% below annual consumption")
            print(f"   🔌 Net grid import: {net_import:,.0f} kWh/year")
        
        print(f"\n🏠 Energy Independence:")
        print(f"   Self-sufficiency: {result.self_sufficiency_pct:.1f}%")
        print(f"   → You cover {result.self_sufficiency_pct:.1f}% of consumption from PV")
        print(f"   → You still need {100 - result.self_sufficiency_pct:.1f}% from grid")
        
        print(f"\n🌞 PV Utilization:")
        print(f"   Self-consumption: {result.self_consumption_pct:.1f}%")
        print(f"   → You use {result.self_consumption_pct:.1f}% of PV generation locally")
        print(f"   → You export {100 - result.self_consumption_pct:.1f}% to grid")
    
    @staticmethod
    def print_scenario_comparison(
        scenarios: List['ScenarioResult'],
        title: str = "WHAT-IF SCENARIOS"
    ) -> None:
        """
        Print a comparison table of multiple sizing scenarios.
        
        Args:
            scenarios: List of ScenarioResult objects
            title: Section title (default: "WHAT-IF SCENARIOS")
        """
        print(f"\n{'=' * 70}")
        print(title)
        print(f"{'=' * 70}")
        
        print("\n💡 Testing different system sizes:")
        print(f"\n{'Size (kWp)':<12} {'Generation':<15} {'Self-Suff.':<12} "
              f"{'Grid Import':<15} {'Grid Export':<15}")
        print("-" * 70)
        
        for scenario in scenarios:
            print(f"{scenario.size_kwp:<12.1f} "
                  f"{scenario.annual_generation_kwh:<15,.0f} "
                  f"{scenario.self_sufficiency_pct:<12.1f} "
                  f"{scenario.grid_import_kwh:<15,.0f} "
                  f"{scenario.grid_export_kwh:<15,.0f}")
    
    @staticmethod
    def print_compact_summary(result: 'SizingResult') -> None:
        """
        Print a compact one-line summary.
        
        Args:
            result: SizingResult object from simulation
        """
        print(f"PV: {result.recommended_kwp:.1f} kWp | "
              f"Gen: {result.annual_generation_kwh:,.0f} kWh | "
              f"Self-Suff: {result.self_sufficiency_pct:.1f}% | "
              f"Self-Cons: {result.self_consumption_pct:.1f}%")
    
    @staticmethod
    def format_as_dict(result: 'SizingResult') -> dict:
        """
        Format sizing result as a dictionary for export/serialization.
        
        Args:
            result: SizingResult object from simulation
            
        Returns:
            Dictionary with key metrics
        """
        return {
            'system_size_kwp': result.recommended_kwp,
            'annual_generation_kwh': result.annual_generation_kwh,
            'annual_consumption_kwh': result.annual_consumption_kwh,
            'self_sufficiency_pct': result.self_sufficiency_pct,
            'self_consumption_pct': result.self_consumption_pct,
            'grid_import_kwh': result.annual_grid_import_kwh,
            'grid_export_kwh': result.annual_grid_export_kwh,
            'self_consumed_kwh': result.annual_self_consumed_kwh,
            'specific_yield_kwh_per_kwp': result.specific_yield_kwh_per_kwp
        }
    
    @staticmethod
    def plot_scenario_comparison(
        scenarios: List['ScenarioResult'],
        output_path: str = None,
        figsize: tuple = (14, 6),
        title: str = "PV System Sizing Comparison"
    ) -> str:
        """
        Create a visualization comparing multiple sizing scenarios.
        
        Generates a 2-panel plot:
        - Left: Self-sufficiency and self-consumption percentages
        - Right: Energy flows (generation, grid import/export)
        
        Args:
            scenarios: List of ScenarioResult objects
            output_path: Path to save figure (optional)
            figsize: Figure size (default: (14, 6))
            title: Plot title
            
        Returns:
            Path to saved figure if output_path provided, else None
            
        Example:
            >>> scenarios = SizingUtilities.run_scenarios(sizer, sizes)
            >>> ResultsFormatter.plot_scenario_comparison(scenarios, 'comparison.png')
        """
        import matplotlib.pyplot as plt
        import numpy as np
        
        # Extract data from scenarios
        sizes = [s.size_kwp for s in scenarios]
        self_suff = [s.self_sufficiency_pct for s in scenarios]
        self_cons = [s.self_consumption_pct for s in scenarios]
        generation = [s.annual_generation_kwh for s in scenarios]
        grid_import = [s.grid_import_kwh for s in scenarios]
        grid_export = [s.grid_export_kwh for s in scenarios]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
        
        # ========== Panel 1: Percentages ==========
        x = np.arange(len(sizes))
        width = 0.35
        
        bars1 = ax1.bar(x - width/2, self_suff, width, label='Self-Sufficiency', 
                        color='#52BE80', alpha=0.8, edgecolor='white')
        bars2 = ax1.bar(x + width/2, self_cons, width, label='Self-Consumption', 
                        color='#5DADE2', alpha=0.8, edgecolor='white')
        
        # Add value labels on bars
        for bar in bars1:
            height = bar.get_height()
            ax1.annotate(f'{height:.1f}%',
                        xy=(bar.get_x() + bar.get_width()/2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        for bar in bars2:
            height = bar.get_height()
            ax1.annotate(f'{height:.1f}%',
                        xy=(bar.get_x() + bar.get_width()/2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        ax1.set_xlabel('System Size (kWp)', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Percentage (%)', fontsize=12, fontweight='bold')
        ax1.set_title('Energy Independence Metrics', fontsize=13, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels([f'{s:.1f}' for s in sizes])
        ax1.legend(loc='upper right', fontsize=10)
        ax1.grid(True, alpha=0.3, axis='y')
        ax1.set_ylim(0, max(max(self_suff), max(self_cons)) * 1.2)
        
        # ========== Panel 2: Energy Flows ==========
        # Show Grid Import, Grid Export, Self-Consumed as bars + Self-Sufficiency as line
        self_consumed = [s.result.annual_self_consumed_kwh for s in scenarios]
        
        width = 0.25
        
        bars_import = ax2.bar(x - width, grid_import, width, label='Grid Import', 
                              color='#E74C3C', alpha=0.8, edgecolor='white')
        bars_export = ax2.bar(x, grid_export, width, label='Grid Export', 
                              color='#3498DB', alpha=0.8, edgecolor='white')
        bars_self = ax2.bar(x + width, self_consumed, width, label='Self-Consumed', 
                            color='#52BE80', alpha=0.8, edgecolor='white')
        
        ax2.set_xlabel('System Size (kWp)', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Energy (kWh/year)', fontsize=12, fontweight='bold')
        ax2.set_title('Annual Energy Distribution', fontsize=13, fontweight='bold')
        ax2.set_xticks(x)
        ax2.set_xticklabels([f'{s:.1f}' for s in sizes])
        ax2.grid(True, alpha=0.3, axis='y')
        
        # Format y-axis with thousands separator
        ax2.get_yaxis().set_major_formatter(
            plt.FuncFormatter(lambda x, p: f'{x:,.0f}')
        )
        
        # Add Self-Sufficiency on secondary y-axis
        ax2_right = ax2.twinx()
        ax2_right.plot(x, self_suff, 'o-', color='#9B59B6', linewidth=2.5, 
                      markersize=8, label='Self-Sufficiency %')
        ax2_right.set_ylabel('Self-Sufficiency (%)', fontsize=12, fontweight='bold', color='#9B59B6')
        ax2_right.tick_params(axis='y', labelcolor='#9B59B6')
        ax2_right.set_ylim(0, max(self_suff) * 1.3)
        
        # Combine legends from both axes
        bars_legend = ax2.legend(loc='upper left', fontsize=9)
        ax2_right.legend(loc='upper right', fontsize=9)
        
        # Main title
        fig.suptitle(title, fontsize=15, fontweight='bold', y=1.02)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            print(f"   ✓ Saved: {output_path}")
            return output_path
        else:
            plt.show()
            return None
