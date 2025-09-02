# Turn Indicator Examples

This directory contains example scripts for using the Turn indicator in qants-sim/backtrader.

## Files

- `turn-example.py` - Basic Turn indicator example with sample data
- `turn-plot.py` - Advanced plotting utility for Turn indicator with ticker-based data loading
- `README.md` - This documentation file

## Turn Indicator Overview

The Turn indicator identifies price turning points (peaks and troughs) in OHLC data by analyzing price action around a central bar within a specified range.

### Parameters

- **space** (default: 3): Number of bars on each side of central bar to check for extrema
- **thresh** (default: 0.5): Minimum percentage change threshold for valid turns
- **lookback**: Automatically calculated as `2 * space + 1`

### Output Lines

- **high**: Price level where peak turn detected (NaN otherwise) - displayed as green circles
- **low**: Price level where trough turn detected (NaN otherwise) - displayed as red circles

## Usage Examples

### Basic Example with Sample Data

```bash
# Run with default parameters using sample data
python samples/turn-example/turn-example.py --plot

# Use custom parameters
python samples/turn-example/turn-example.py --space 5 --thresh 1.0 --plot

# Use specific data file
python samples/turn-example/turn-example.py --data datas/orcl-2014.txt --plot
```

### Advanced Plotting with Ticker Data

```bash
# Plot AAPL turn points for 2024
python samples/turn-example/turn-plot.py --ticker AAPL --fromdate 2024-01-01 --todate 2024-12-31 --plot

# Use custom parameters with TSLA
python samples/turn-example/turn-plot.py --ticker TSLA --fromdate 2024-06-01 --todate 2024-08-31 --space 5 --thresh 1.0 --plot

# Include volume chart and turn point annotations
python samples/turn-example/turn-plot.py --ticker MSFT --fromdate 2024-01-01 --plot --volume --annotations

# Run analysis without plotting
python samples/turn-example/turn-plot.py --ticker NVDA --fromdate 2024-01-01 --todate 2024-06-30
```

## Command Line Options for turn-plot.py

### Data Source Options
- `--ticker TICKER` - Stock ticker symbol (auto-discovers data file)
- `--datadir DIR` - Directory containing ticker data files (default: /mnt/c/tools/airflow/data/price_vol/ib/long/1_day)
- `--data FILE` - Manual data file specification (fallback if ticker not used)

### Date Range Options
- `--fromdate YYYY-MM-DD` - Starting date
- `--todate YYYY-MM-DD` - Ending date

### Indicator Parameters
- `--space INT` - Turn indicator space parameter (default: 3)
- `--thresh FLOAT` - Turn indicator threshold parameter (default: 0.5)

### Plotting Options
- `--plot` - Generate and display plot
- `--volume` - Include volume subplot in plot
- `--annotations` - Add turn point value annotations to plot

## Sample Output

When running with turn detection, you'll see output like:

```
Turn Indicator Parameters:
  space: 3
  thresh: 0.5%
  lookback: 7

Peak turn detected at 2024-01-11: level=187.05 (#1)
Trough turn detected at 2024-01-17: level=180.30 (#1)
Peak turn detected at 2024-01-24: level=196.38 (#2)
...

Turn Analysis Summary:
  Total turns detected: 41
  Peak turns: 21
  Trough turns: 20
```

## Integration in Your Own Strategy

```python
import backtrader as bt
import math

class MyStrategy(bt.Strategy):
    def __init__(self):
        # Add Turn indicator
        self.turn = bt.indicators.Turn(self.data, space=3, thresh=0.5)
    
    def next(self):
        # Check for peak turns
        if not math.isnan(self.turn.high[0]):
            print(f'Peak turn at {self.turn.high[0]:.2f}')
            # Your peak turn logic here
        
        # Check for trough turns
        if not math.isnan(self.turn.low[0]):
            print(f'Trough turn at {self.turn.low[0]:.2f}')
            # Your trough turn logic here
```

## Data Format Requirements

The turn-plot.py script expects TSV data files in the qAnts format:
- Compressed .gz files organized in ticker subdirectories
- QantIBDailyPriceVolData format with OHLCV data
- Date/time stamps for proper time series analysis

## Notes

- The Turn indicator requires at least `2 * space + 1` bars of historical data
- Turn detection has a delay of `space` bars (shows turns after they're confirmed)
- Consecutive same-type turns are filtered (keeps only better peaks/troughs)
- Plotting uses candlestick charts for better turn point visualization
- Green circles indicate peak turns, red circles indicate trough turns