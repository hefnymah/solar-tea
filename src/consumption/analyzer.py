
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

class ConsumptionAnalyzer:
    """
    Analyzes energy consumption data to generate load profiles and insights.
    Handles data loading, resampling, and visualization.
    """
    
    def __init__(self, output_dir=None):
        self.output_dir = output_dir
        self.df_hourly = None
        self.daily_profile_seasonal = None
        
        # Configuration
        self.target_col = 'Consumption_kWh'
        self.time_col_candidates = ['zeit', 'timestamp', 'date', 'time']
        self.cons_col_candidates = ['stromverbrauch_kwh', 'verbrauch_kwh', 'consumption', 'consumption_kwh', 'wert']
        
        # Season mapping
        self.seasons = {
            'Winter': [12, 1, 2],
            'Spring': [3, 4, 5],
            'Summer': [6, 7, 8],
            'Autumn': [9, 10, 11]
        }
        self.season_colors = {
            'Winter': 'blue',
            'Spring': 'green',
            'Summer': 'red',
            'Autumn': 'orange'
        }
        
        # Seasonal Representative Weeks Configuration (Month, Day)
        self.seasonal_weeks_config = {
            'Winter': (1, 15),
            'Spring': (4, 15),
            'Summer': (7, 15),
            'Autumn': (10, 15)
        }

    def _get_season(self, month):
        for season, months in self.seasons.items():
            if month in months:
                return season
        return 'Unknown'

    def load_data(self, file_path):
        """
        Loads CSV data, standardizes columns, and resamples to hourly resolution.
        """
        print(f"Loading: {os.path.basename(file_path)}")
        
        try:
            # Try loading with different separators if needed, but 'python' engine with sep=None is usually good
            df = pd.read_csv(file_path, sep=None, engine='python')
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return False

        # 1. Normalize Column Names
        df.columns = [c.strip().lower() for c in df.columns]
        
        # 2. Identify Time Column
        time_col = next((c for c in df.columns if c in self.time_col_candidates), None)
        if not time_col:
            # Fallback: assume first column
            time_col = df.columns[0]
            
        # 3. Identify Consumption Column
        cons_col = next((c for c in df.columns if c in self.cons_col_candidates), None)
        if not cons_col:
            # Fallback: assume second column
            cons_col = df.columns[1] if len(df.columns) > 1 else None
            
        if not cons_col:
            print("Error: Could not identify consumption column.")
            return False

        # 4. Process Index
        # Try parsing with default inference first (handles ISO YYYY-MM-DD standard best)
        try:
            df[time_col] = pd.to_datetime(df[time_col])
        except ValueError:
            # Fallback if standard parsing fails, try dayfirst for European formats
            try:
                df[time_col] = pd.to_datetime(df[time_col], dayfirst=True)
            except Exception as e:
                print(f"Error parsing dates in {time_col}: {e}")
                return False

        df.set_index(time_col, inplace=True)
        
        # 5. Resample to Hourly (Summing energy)
        # Check frequency or just force resample
        df_resampled = df[[cons_col]].resample('h').sum()
        df_resampled.rename(columns={cons_col: self.target_col}, inplace=True)
        
        # 6. Add Time Features
        df_resampled['Month'] = df_resampled.index.month
        df_resampled['Hour'] = df_resampled.index.hour
        df_resampled['Season'] = df_resampled['Month'].apply(self._get_season)
        
        self.df_hourly = df_resampled
        print(f"   Loaded and resampled to {len(self.df_hourly)} hourly records.")
        
        # Validate the data
        try:
            self._validate()
        except ValueError as e:
            print(f"   Validation warning: {e}")
            # Continue anyway but warn the user
        
        return True
    
    def _validate(self) -> None:
        """Validates that the consumption data meets quality standards."""
        if self.df_hourly is None:
            return
            
        n = self.df_hourly.shape[0]
        if n not in (8760, 8784):
            raise ValueError(
                f"Expected full-year hourly data (8760/8784 rows), got {n}"
            )
        
        if (self.df_hourly[self.target_col] < 0).any():
            raise ValueError("Load profile contains negative values.")

    def analyze(self):
        """Performs aggregation analysis."""
        if self.df_hourly is None:
            return

        # Typical Daily Profile per Season
        self.daily_profile_seasonal = self.df_hourly.groupby(['Season', 'Hour'])[self.target_col].mean().unstack(level=0)
        
        # Ensure column order
        season_order = ['Winter', 'Spring', 'Summer', 'Autumn']
        existing_cols = [s for s in season_order if s in self.daily_profile_seasonal.columns]
        self.daily_profile_seasonal = self.daily_profile_seasonal[existing_cols]

    def plot_all(self, filename_prefix=""):
        """Generates all standard plots."""
        if self.df_hourly is None:
            return

        out_dir = self.output_dir if self.output_dir else "output"
        os.makedirs(out_dir, exist_ok=True)
        
        # Prefix handling
        prefix = f"{filename_prefix}_" if filename_prefix else ""

        self._plot_monthly(out_dir, prefix)
        self._plot_weekly(out_dir, prefix)
        self._plot_seasonal_weeks(out_dir, prefix) # Added
        self._plot_seasonal_daily_profile(out_dir, prefix)
        self._plot_heatmap(out_dir, prefix)
    
    def plot_date_range(self, start_date, end_date, output_path=None, title=None, smooth=True):
        """
        Plot consumption for a custom date range.
        
        Parameters:
        -----------
        start_date : str or pd.Timestamp
            Start date (e.g., '2024-01-15' or pd.Timestamp(2024, 1, 15))
        end_date : str or pd.Timestamp
            End date (inclusive)
        output_path : str, optional
            Full path to save the plot. If None, displays interactively.
        title : str, optional
            Custom plot title. Auto-generated if None.
        smooth : bool, default=True
            Apply spline smoothing to the curve
        """
        if self.df_hourly is None or self.df_hourly.empty:
            print("Error: No data loaded. Call load_data() first.")
            return
        
        # Parse dates
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        # For single day, ensure we get full 24 hours (00:00 to 23:00)
        days_span = (end - start).days
        if days_span == 0:
            # Single day: extend to end of day
            end = start.replace(hour=23, minute=59, second=59)
        
        # Extract data slice
        mask = (self.df_hourly.index >= start) & (self.df_hourly.index <= end)
        df_slice = self.df_hourly.loc[mask]
        
        if df_slice.empty:
            print(f"No data found for range {start.date()} to {end.date()}")
            return
        
        # Create plot
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Special handling for single day: use hour as x-axis
        if days_span == 0:
            hours = df_slice.index.hour
            y = df_slice[self.target_col].values
            
            # Bar chart for single day shows values more clearly
            ax.bar(hours, y, color='steelblue', edgecolor='darkblue', alpha=0.7, width=0.8)
            
            # Optionally add line overlay
            if smooth and len(hours) > 3:
                try:
                    from scipy.interpolate import make_interp_spline
                    x = np.arange(len(hours))
                    x_smooth = np.linspace(0, len(hours)-1, 200)
                    spl = make_interp_spline(x, y, k=3)
                    y_smooth = spl(x_smooth)
                    y_smooth = np.maximum(y_smooth, 0)
                    hours_smooth = np.linspace(hours.min(), hours.max(), 200)
                    ax.plot(hours_smooth, y_smooth, color='red', linewidth=2, label='Trend', alpha=0.8)
                    ax.legend()
                except Exception:
                    pass
            
            ax.set_xlabel("Hour of Day")
            ax.set_xticks(range(0, 24))
            ax.set_xlim(-0.5, 23.5)
            
            # Auto-generate title
            if title is None:
                title = f"Hourly Consumption - {start.strftime('%b %d, %Y')}"
        
        else:
            # Multi-day: use original time-series approach
            x = np.arange(len(df_slice))
            y = df_slice[self.target_col].values
            
            # Plot raw points
            ax.scatter(df_slice.index, y, color='steelblue', alpha=0.3, s=10)
            
            # Smoothed curve
            if smooth and len(x) > 3:
                try:
                    from scipy.interpolate import make_interp_spline
                    x_smooth = np.linspace(x.min(), x.max(), min(500, len(x)*10))
                    spl = make_interp_spline(x, y, k=3)
                    y_smooth = spl(x_smooth)
                    y_smooth = np.maximum(y_smooth, 0)
                    
                    time_smooth = pd.date_range(start=df_slice.index[0], end=df_slice.index[-1], periods=len(x_smooth))
                    ax.plot(time_smooth, y_smooth, color='darkblue', linewidth=2, label='Consumption (Smoothed)')
                except Exception:
                    ax.plot(df_slice.index, y, color='darkblue', linewidth=2, label='Consumption')
            else:
                ax.plot(df_slice.index, y, color='darkblue', linewidth=2, label='Consumption')
            
            # Auto-generate title if not provided
            if title is None:
                days = days_span + 1
                title = f"Consumption: {start.strftime('%b %d, %Y')} - {end.strftime('%b %d, %Y')} ({days} days)"
            
            # Format x-axis based on range duration
            if days_span <= 7:
                # Hourly or daily ticks for week or less
                import matplotlib.dates as mdates
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d\n%H:%M'))
            elif days_span <= 60:
                # Daily ticks for up to 2 months
                import matplotlib.dates as mdates
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
            else:
                # Weekly ticks for longer ranges
                import matplotlib.dates as mdates
                ax.xaxis.set_major_locator(mdates.WeekdayLocator())
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
            
            ax.set_xlabel("Date")
            ax.legend()
            plt.xticks(rotation=45)
        
        ax.set_title(title)
        ax.set_ylabel("Consumption (kWh)")
        ax.grid(True, linestyle='--', alpha=0.5)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path)
            print(f"Plot saved to: {output_path}")
            plt.close()
        else:
            plt.show()

    def _plot_monthly(self, out_dir, prefix):
        annual_kwh = self.df_hourly[self.target_col].sum()
        df_monthly = self.df_hourly[self.target_col].resample('ME').sum()
        
        plt.figure(figsize=(10, 6))
        # Plot bar chart
        ax = df_monthly.plot(kind='bar', color='steelblue', edgecolor='black')
        
        plt.title(f"Monthly Consumption (Total: {annual_kwh:.0f} kWh)")
        plt.ylabel("Energy (kWh)")
        plt.xlabel("Month")
        
        # Format X-axis to show Month Name (e.g. Jan, Feb)
        # Assuming index is DatetimeIndex. 
        # When pandas plots bar chart of datetime index, it treats them as categorical string labels.
        # We can extract month names and set them.
        month_labels = [d.strftime('%b') for d in df_monthly.index]
        ax.set_xticklabels(month_labels, rotation=0)
        
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, f"{prefix}monthly_consumption.png"))
        plt.close()

    def _plot_weekly(self, out_dir, prefix):
        """Plots the weeks with Maximum and Minimum total consumption."""
        if self.df_hourly is None or self.df_hourly.empty:
            return

        # Resample to weekly sum to find max/min weeks
        df_weekly = self.df_hourly[self.target_col].resample('W').sum()
        
        if df_weekly.empty:
            return
            
        max_week_date = df_weekly.idxmax()
        min_week_date = df_weekly.idxmin()
        
        # Calculate start dates (Monday of that week)
        # resample('W') defaults to Sunday (W-SUN). 
        # So the timestamp is the END of the week.
        # Let's find the range for extraction.
        
        def get_week_slice(end_date):
            # End date from resample is inclusive? Standard pandas 'W' is week ending Sunday
            # So start is end_date - 6 days
            start = end_date - pd.Timedelta(days=6)
            # Ensure we cover the full day of end_date
            end_slice = end_date + pd.Timedelta(hours=23, minutes=59)
            
            mask = (self.df_hourly.index >= start) & (self.df_hourly.index <= end_slice)
            return self.df_hourly.loc[mask], start, end_date

        max_week_df, max_start, max_end = get_week_slice(max_week_date)
        min_week_df, min_start, min_end = get_week_slice(min_week_date)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Plot Max Week
        if not max_week_df.empty:
            # Normalize to 0-167 hours
            x_max = np.arange(len(max_week_df))
            ax.plot(x_max, max_week_df[self.target_col].values, color='red', label=f"Max Week ({max_start.strftime('%b %d')} - {max_end.strftime('%b %d')})", linewidth=2)
            
        # Plot Min Week
        if not min_week_df.empty:
            x_min = np.arange(len(min_week_df))
            ax.plot(x_min, min_week_df[self.target_col].values, color='green', label=f"Min Week ({min_start.strftime('%b %d')} - {min_end.strftime('%b %d')})", linewidth=2)
            
        ax.set_title("Extreme Weeks Consumption Analysis (High vs Low)")
        ax.set_ylabel("Consumption (kWh)")
        ax.set_xlabel("Day of Week")
        
        # X-ticks
        ticks = np.arange(0, 168+24, 24)
        labels = [f"Day {i+1}" for i in range(len(ticks))]
        ax.set_xticks(ticks)
        ax.set_xticklabels(labels)
        
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, f"{prefix}extreme_weeks_profile.png"))
        plt.close()
        
    def _plot_seasonal_weeks(self, out_dir, prefix):
        """Plots a representative week for each season with smooth curves in subplots."""
        if self.df_hourly is None or self.df_hourly.empty:
            return

        # Determine year
        year = pd.Series(self.df_hourly.index.year).mode()[0]
        
        # Import scipy for smoothing
        try:
            from scipy.interpolate import make_interp_spline
            has_scipy = True
        except ImportError:
            has_scipy = False
        
        fig, axes = plt.subplots(4, 1, figsize=(12, 16), sharey=False)
        season_order = ['Winter', 'Spring', 'Summer', 'Autumn']
        
        for i, season in enumerate(season_order):
            ax = axes[i]
            
            # Extract week
            if season in self.seasonal_weeks_config:
                month, day = self.seasonal_weeks_config[season]
                try:
                    start_date = pd.Timestamp(year=year, month=month, day=day)
                    end_date = start_date + pd.Timedelta(days=7)
                    mask = (self.df_hourly.index >= start_date) & (self.df_hourly.index < end_date)
                    df_slice = self.df_hourly.loc[mask]
                    
                    if not df_slice.empty:
                        # Normalize x-axis for smoothing
                        x = np.arange(len(df_slice))
                        y = df_slice[self.target_col].values
                        color = self.season_colors.get(season, 'black')
                        
                        # Plot raw points lightly
                        ax.scatter(df_slice.index, y, color=color, alpha=0.3, s=10)
                        
                        # Smooth curve
                        if has_scipy and len(x) > 3:
                            try:
                                # Create smooth x-axis
                                x_smooth = np.linspace(x.min(), x.max(), 500)
                                spl = make_interp_spline(x, y, k=3)
                                y_smooth = spl(x_smooth)
                                y_smooth = np.maximum(y_smooth, 0)
                                
                                # Convert numeric smooth x back to datetime for plotting compatibility?
                                # It's easier to plot the smooth curve against a generated date range
                                time_smooth = pd.date_range(start=df_slice.index[0], end=df_slice.index[-1], periods=500)
                                ax.plot(time_smooth, y_smooth, color=color, linewidth=2, label=f"{season} (Smooth)")
                            except Exception:
                                ax.plot(df_slice.index, y, color=color, linewidth=2, label=season)
                        else:
                             ax.plot(df_slice.index, y, color=color, linewidth=2, label=season)

                        ax.set_title(f"{season} Week ({start_date.date()} - {end_date.date()})")
                        ax.set_ylabel("kWh")
                        ax.grid(True, alpha=0.3)
                    else:
                        ax.text(0.5, 0.5, "No Data", ha='center', va='center')
                        ax.set_title(f"{season} Week - N/A")
                except ValueError:
                    ax.text(0.5, 0.5, "Invalid Date", ha='center', va='center')
            else:
                ax.text(0.5, 0.5, "Config Missing", ha='center', va='center')
        
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, f"{prefix}seasonal_weeks_profile.png"))
        plt.close()

    def _plot_seasonal_daily_profile(self, out_dir, prefix):
        if self.daily_profile_seasonal is None:
            self.analyze()
            
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Import here to avoid hard dependency at module level if not installed, 
        # though it's expected in this project.
        try:
            from scipy.interpolate import make_interp_spline
            has_scipy = True
        except ImportError:
            has_scipy = False
            print("Warning: scipy not found, plotting raw lines instead of smooth curves.")
        
        x = np.arange(24) # 0..23
        x_smooth = np.linspace(x.min(), x.max(), 300)

        for season in self.daily_profile_seasonal.columns:
            y = self.daily_profile_seasonal[season].values
            color = self.season_colors.get(season, 'black')
            
            # Smooth curve if scipy is available
            if has_scipy:
                try:
                    spl = make_interp_spline(x, y, k=3)
                    y_smooth = spl(x_smooth)
                    # Clip negative values (spline feature)
                    y_smooth = np.maximum(y_smooth, 0)
                    
                    ax.plot(x_smooth, y_smooth, label=season, color=color, linewidth=2)
                except Exception:
                    # Fallback to straight lines if spline fails
                    ax.plot(x, y, label=season, color=color, linewidth=2)
            else:
                ax.plot(x, y, label=season, color=color, linewidth=2)
            
        ax.set_title("Typical Daily Load Profile by Season")
        ax.set_xlabel("Hour of Day")
        ax.set_ylabel("Average Consumption (kWh)")
        ax.set_xticks(range(0, 24))
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, f"{prefix}seasonal_daily_profile.png"))
        plt.close()

    def _plot_heatmap(self, out_dir, prefix):
        # 2D Heatmap: Day of Year vs Hour
        # Pivot table: Index=Date, Columns=Hour
        pivoted = self.df_hourly.pivot_table(index=self.df_hourly.index.date, columns='Hour', values=self.target_col)
        
        if pivoted.empty:
            return

        plt.figure(figsize=(12, 8))
        plt.imshow(pivoted.T, aspect='auto', cmap='plasma', origin='upper', extent=[0, len(pivoted), 24, 0])
        plt.colorbar(label='kWh')
        plt.title("Consumption Heatmap (Hour vs Day)")
        plt.ylabel("Hour of Day")
        plt.xlabel("Day of Year")
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, f"{prefix}consumption_heatmap.png"))
        plt.close()
