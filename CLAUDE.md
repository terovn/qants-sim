# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a customized fork of the Backtrader backtesting platform with qAnts-specific extensions. Backtrader is a Python backtesting framework for trading strategies that supports live trading, indicators, analyzers, and plotting capabilities.

## Installation & Setup

Install the package in development mode:
```bash
pip install -e .
```

Optional dependencies:
- `pip install backtrader[plotting]` for matplotlib plotting support
- Interactive Brokers: `pip install git+https://github.com/blampe/IbPy.git`
- TA-Lib indicators require separate ta-lib installation

## Testing

The project uses Python's built-in unittest framework:

```bash
# Run all tests
python -m unittest discover tests/

# Run specific test file
python tests/test_ind_sma.py

# Run specific test with unittest module
python -m unittest tests.test_ind_sma
```

Note: Many test files are designed to run as standalone scripts and will generate extensive output showing indicator calculations.

## Core Architecture

### Main Components

1. **Cerebro Engine** (`backtrader/cerebro.py`)
   - Central orchestrator that manages strategies, data feeds, brokers, and observers
   - Handles backtesting execution and optimization
   - Entry point for running trading simulations

2. **Strategy Framework** (`backtrader/strategy.py`)
   - Base class for implementing trading logic
   - SignalStrategy subclass for signal-based strategies
   - Includes lifecycle methods: `__init__`, `next()`, `notify_order()`, `notify_trade()`

3. **Data Feeds** (`backtrader/feeds/`)
   - Support for multiple data sources: CSV, Yahoo Finance, Interactive Brokers, Oanda, etc.
   - Special qAnts extension: `qant_ib.py` for custom IB integration
   - Handles OHLCV data and various timeframes

4. **Indicators** (`backtrader/indicators/`)
   - Extensive library of 100+ technical indicators
   - Moving averages, oscillators, trend indicators
   - Custom indicator development support

5. **Brokers** (`backtrader/brokers/`)
   - Simulated broker for backtesting (`bbroker.py`)
   - Live broker connections (IB, Oanda, etc.)
   - Order management and commission handling

6. **Analyzers** (`backtrader/analyzers/`)
   - Performance analysis tools
   - Risk metrics, returns, drawdowns, Sharpe ratio, etc.

## Key Patterns & Conventions

### Strategy Development
```python
import backtrader as bt

class MyStrategy(bt.Strategy):
    params = (
        ('period', 20),
    )
    
    def __init__(self):
        self.sma = bt.indicators.SMA(self.data, period=self.params.period)
    
    def next(self):
        if not self.position:
            if self.data.close > self.sma:
                self.buy()
        else:
            if self.data.close < self.sma:
                self.sell()
```

### Running Backtests
```python
cerebro = bt.Cerebro()
cerebro.addstrategy(MyStrategy)
cerebro.adddata(data)
cerebro.run()
cerebro.plot()  # requires matplotlib
```

## Development Commands

### Sample Execution
```bash
# Run SMA crossover example with parameters
python samples/sigsmacross/sigsmacross.py --data MSFT --cash 100000 --plot

# Run with btrun utility
btrun --strategy MyStrategy --data data.csv
```

### Data Processing
```bash
# Tools for data manipulation
python tools/yahoodownload.py MSFT 2020-01-01 2023-12-31
python tools/rewrite-data.py input.csv output.csv
```

## File Organization

- `backtrader/` - Core framework code
- `samples/` - Example strategies and use cases  
- `tests/` - Unit tests for indicators and functionality
- `datas/` - Sample data files for testing
- `tools/` - Utility scripts for data processing
- `contrib/` - Additional samples and utilities

## Testing Strategy

Tests are primarily focused on:
- Indicator calculations and accuracy
- Data handling and processing
- Order execution and broker simulation
- Strategy optimization

Each indicator test (`test_ind_*.py`) validates calculations against expected values using historical data.

## Custom Extensions (qAnts)

- `backtrader/feeds/qant_ib.py` - Custom Interactive Brokers data feed
- Various modifications throughout the codebase for enhanced functionality
- Additional data processing capabilities

## Version Information

- Python 3.2+ support
- Current version follows X.Y.Z.I format where I = number of built-in indicators
- Uses semantic versioning for compatibility

## Important Notes

- In backtrader, lines follow a different index scheme, with [0] pointing to the current value, [-1] the last value before that, and [-2] the value before [-1], etc...