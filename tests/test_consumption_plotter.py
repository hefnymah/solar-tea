"""
Unit tests for ConsumptionPlotter class.
"""

import os
from pathlib import Path

import pytest

from eclipse.consumption.plotter import ConsumptionPlotter


class TestConsumptionPlotterInitialization:
    """Test suite for ConsumptionPlotter initialization."""
    
    def test_initialization_default(self, mock_consumption_data):
        """Test initialization with defaults."""
        # Arrange & Act
        plotter = ConsumptionPlotter(mock_consumption_data)
        
        # Assert
        assert isinstance(plotter, ConsumptionPlotter)
        assert plotter.output_dir == 'output'
        assert plotter.season_colors == ConsumptionPlotter.SEASON_COLORS
    
    def test_initialization_custom_output_dir(self, mock_consumption_data, output_dir):
        """Test initialization with custom output directory."""
        # Arrange & Act
        plotter = ConsumptionPlotter(mock_consumption_data, output_dir=output_dir)
        
        # Assert
        assert plotter.output_dir == output_dir
    
    def test_initialization_custom_colors(self, mock_consumption_data):
        """Test initialization with custom season colors."""
        # Arrange
        custom_colors = {
            'winter': 'cyan',
            'spring': 'lime',
            'summer': 'magenta',
            'autumn': 'yellow'
        }
        
        # Act
        plotter = ConsumptionPlotter(mock_consumption_data, season_colors=custom_colors)
        
        # Assert
        assert plotter.season_colors == custom_colors
    
    def test_data_property(self, mock_consumption_data):
        """Test data property returns associated ConsumptionData."""
        # Arrange
        plotter = ConsumptionPlotter(mock_consumption_data)
        
        # Act
        data = plotter.data
        
        # Assert
        assert data is mock_consumption_data


class TestConsumptionPlotterPlotGeneration:
    """Test suite for plot generation methods."""
    
    def test_plot_monthly_creates_file(self, mock_consumption_data, output_dir):
        """Test that plot_monthly creates a PNG file."""
        # Arrange
        plotter = ConsumptionPlotter(mock_consumption_data, output_dir=output_dir)
        filename = "test_monthly.png"
        
        # Act
        path = plotter.plot_monthly(filename)
        
        # Assert
        assert os.path.exists(path)
        assert path.endswith(filename)
        assert Path(path).suffix == '.png'
    
    def test_plot_extreme_weeks_creates_file(self, mock_consumption_data, output_dir):
        """Test that plot_extreme_weeks creates a PNG file."""
        # Arrange
        plotter = ConsumptionPlotter(mock_consumption_data, output_dir=output_dir)
        filename = "test_extreme.png"
        
        # Act
        path = plotter.plot_extreme_weeks(filename)
        
        # Assert
        assert os.path.exists(path)
    
    def test_plot_seasonal_weeks_creates_file(self, mock_consumption_data, output_dir):
        """Test that plot_seasonal_weeks creates a PNG file."""
        # Arrange
        plotter = ConsumptionPlotter(mock_consumption_data, output_dir=output_dir)
        filename = "test_seasonal_weeks.png"
        
        # Act
        path = plotter.plot_seasonal_weeks(filename)
        
        # Assert
        assert os.path.exists(path)
    
    def test_plot_seasonal_daily_profile_creates_file(self, mock_consumption_data, output_dir):
        """Test that plot_seasonal_daily_profile creates a PNG file."""
        # Arrange
        plotter = ConsumptionPlotter(mock_consumption_data, output_dir=output_dir)
        filename = "test_daily_profile.png"
        
        # Act
        path = plotter.plot_seasonal_daily_profile(filename)
        
        # Assert
        assert os.path.exists(path)
    
    def test_plot_heatmap_creates_file(self, mock_consumption_data, output_dir):
        """Test that plot_heatmap creates a PNG file."""
        # Arrange
        plotter = ConsumptionPlotter(mock_consumption_data, output_dir=output_dir)
        filename = "test_heatmap.png"
        
        # Act
        path = plotter.plot_heatmap(filename)
        
        # Assert
        assert os.path.exists(path)
    
    def test_plot_all_creates_all_files(self, mock_consumption_data, output_dir):
        """Test that plot_all creates all expected plots."""
        # Arrange
        plotter = ConsumptionPlotter(mock_consumption_data, output_dir=output_dir)
        
        # Act
        paths = plotter.plot_all(prefix="test")
        
        # Assert
        assert isinstance(paths, dict)
        assert len(paths) == 5
        assert all(k in paths for k in [
            'monthly', 'extreme_weeks', 'seasonal_weeks', 
            'seasonal_daily', 'heatmap'
        ])
        assert all(os.path.exists(p) for p in paths.values())
    
    def test_plot_date_range_single_day(self, mock_consumption_data, output_dir):
        """Test plotting a single day range."""
        # Arrange
        plotter = ConsumptionPlotter(mock_consumption_data, output_dir=output_dir)
        output_path = os.path.join(output_dir, "date_range_test.png")
        
        # Act
        path = plotter.plot_date_range(
            "2024-01-15", 
            "2024-01-15", 
            output_path=output_path
        )
        
        # Assert
        assert path == output_path
        assert os.path.exists(path)
    
    def test_plot_date_range_multi_day(self, mock_consumption_data, output_dir):
        """Test plotting a multi-day range."""
        # Arrange
        plotter = ConsumptionPlotter(mock_consumption_data, output_dir=output_dir)
        output_path = os.path.join(output_dir, "week_test.png")
        
        # Act
        path = plotter.plot_date_range(
            "2024-01-15", 
            "2024-01-21", 
            output_path=output_path
        )
        
        # Assert
        assert os.path.exists(path)
    
    def test_plot_date_range_no_data(self, mock_consumption_data, output_dir, capsys):
        """Test plotting with no data in range."""
        # Arrange
        plotter = ConsumptionPlotter(mock_consumption_data, output_dir=output_dir)
        
        # Act
        result = plotter.plot_date_range(
            "2025-01-01", 
            "2025-01-02", 
            output_path=None
        )
        
        # Assert
        assert result is None
        captured = capsys.readouterr()
        assert "No data found" in captured.out


class TestConsumptionPlotterOutputDirectory:
    """Test suite for output directory management."""
    
    def test_output_dir_created_automatically(self, mock_consumption_data, tmp_path):
        """Test that output directory is created if it doesn't exist."""
        # Arrange
        new_dir = str(tmp_path / "new_outputs")
        plotter = ConsumptionPlotter(mock_consumption_data, output_dir=new_dir)
        
        # Act
        plotter.plot_monthly("test.png")
        
        # Assert
        assert os.path.exists(new_dir)
    
    def test_filename_prefix_in_all_plots(self, mock_consumption_data, output_dir):
        """Test that prefix is applied to all plot filenames."""
        # Arrange
        plotter = ConsumptionPlotter(mock_consumption_data, output_dir=output_dir)
        prefix = "mypre fix"
        
        # Act
        paths = plotter.plot_all(prefix=prefix)
        
        # Assert
        for path in paths.values():
            filename = os.path.basename(path)
            assert filename.startswith(prefix)
