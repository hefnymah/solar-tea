"""
Equipment Database Module
=========================
Manages equipment database loading, conversion, and searching.

Example:
    from eclipse.equipment import EquipmentDatabase
    
    db = EquipmentDatabase()
    modules_df = db.get_modules()
    results = db.search_modules('Trina', limit=5)
"""

import pandas as pd
from typing import Tuple


class EquipmentDatabase:
    """
    Manages equipment database operations.
    
    Provides lazy-loaded access to module and inverter databases,
    with search functionality.
    
    Attributes:
        _modules_df: Cached modules DataFrame
        _inverters_df: Cached inverters DataFrame
    """
    
    def __init__(self):
        """Initialize database with lazy loading."""
        self._modules_df: pd.DataFrame | None = None
        self._inverters_df: pd.DataFrame | None = None
    
    def get_modules(self) -> pd.DataFrame:
        """
        Get modules database as DataFrame.
        
        Returns:
            DataFrame with modules indexed by name.
        """
        if self._modules_df is None:
            self._load_databases()
        return self._modules_df.copy()
    
    def get_inverters(self) -> pd.DataFrame:
        """
        Get inverters database as DataFrame.
        
        Returns:
            DataFrame with inverters indexed by name.
        """
        if self._inverters_df is None:
            self._load_databases()
        return self._inverters_df.copy()
    
    def get_databases(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Get both modules and inverters databases.
        
        Returns:
            Tuple of (modules_df, inverters_df)
        """
        if self._modules_df is None or self._inverters_df is None:
            self._load_databases()
        return self._modules_df.copy(), self._inverters_df.copy()
    
    def _load_databases(self) -> None:
        """Load equipment databases from config."""
        from eclipse.config.equipments import MODULE_DB, INVERTER_DB
        
        # Convert list of dataclasses to DataFrame
        mod_data = {m.name: m.__dict__ for m in MODULE_DB}
        self._modules_df = pd.DataFrame.from_dict(mod_data, orient='index')
        
        inv_data = {inv.name: inv.__dict__ for inv in INVERTER_DB}
        self._inverters_df = pd.DataFrame.from_dict(inv_data, orient='index')
    
    def search_modules(self, query: str, limit: int = 5) -> pd.DataFrame:
        """
        Search modules by name (case-insensitive).
        
        Args:
            query: Search term to match in module names.
            limit: Maximum number of results.
            
        Returns:
            DataFrame with matching modules.
        """
        modules = self.get_modules()
        return self._search(modules, query, limit)
    
    def search_inverters(self, query: str, limit: int = 5) -> pd.DataFrame:
        """
        Search inverters by name (case-insensitive).
        
        Args:
            query: Search term to match in inverter names.
            limit: Maximum number of results.
            
        Returns:
            DataFrame with matching inverters.
        """
        inverters = self.get_inverters()
        return self._search(inverters, query, limit)
    
    @staticmethod
    def _search(df: pd.DataFrame, query: str, limit: int) -> pd.DataFrame:
        """
        Perform case-insensitive search on DataFrame index.
        
        Args:
            df: DataFrame to search.
            query: Search term.
            limit: Maximum results.
            
        Returns:
            Filtered DataFrame.
        """
        matches = df[df.index.str.contains(query, case=False, na=False)]
        return matches.head(limit)
