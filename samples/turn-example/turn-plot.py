#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
"""
Turn Indicator Sample Script

This script loads price data from TSV files using QantIBPriceVolData
and plots the Turn indicator with custom visualization:
- Green circles for peak turns
- Red circles for trough turns
- Turn point detection on candlestick charts
"""

import argparse
import datetime
import math
import os
import glob
import backtrader as bt
from backtrader.feeds.qant_ib import QantIBPriceVolData
import backtrader.indicators as btind


class TurnStrategy(bt.Strategy):
    """
    Strategy that adds Turn indicator for visualization purposes
    """

    params = (
        ('space', 2),        # Turn indicator space parameter
        ('thresh', 0.5),     # Turn indicator threshold parameter
    )

    def __init__(self):
        # Add Turn indicator with specified parameters
        self.turn = btind.Turn(
            self.data,
            space=self.params.space,
            thresh=self.params.thresh
        )

        # Print turn parameters for reference
        print(f"Turn Indicator Parameters:")
        print(f"  space: {self.turn.params.space}")
        print(f"  thresh: {self.turn.params.thresh}%")
        print(f"  lookback: {2 * self.turn.params.space + 1}")

        # Track turn statistics
        self.peak_count = 0
        self.trough_count = 0

    def next(self):
        # Track and print turn signals when detected
        if not math.isnan(self.turn.high[0]):
            self.peak_count += 1
            print(f"Peak turn detected at {self.data.datetime.date(0)}: "
                  f"level={self.turn.high[0]:.2f} (#{self.peak_count})")

        if not math.isnan(self.turn.low[0]):
            self.trough_count += 1
            print(f"Trough turn detected at {self.data.datetime.date(0)}: "
                  f"level={self.turn.low[0]:.2f} (#{self.trough_count})")

    def stop(self):
        total_turns = self.peak_count + self.trough_count
        print(f"\nTurn Analysis Summary:")
        print(f"  Total turns detected: {total_turns}")
        print(f"  Peak turns: {self.peak_count}")
        print(f"  Trough turns: {self.trough_count}")


class TurnWithTextStrategy(TurnStrategy):
    """
    Enhanced Turn strategy that adds text annotations for turn point values
    """

    def __init__(self):
        super(TurnWithTextStrategy, self).__init__()
        # Store turn points for annotation
        self.turn_annotations = []

    def next(self):
        # Call parent method to handle basic turn tracking
        super(TurnWithTextStrategy, self).next()
        
        # Store turn points for later annotation
        if not math.isnan(self.turn.high[0]):
            self.turn_annotations.append({
                'date': self.data.datetime.date(0),
                'type': 'peak',
                'value': self.turn.high[0],
                'bar_index': len(self)
            })

        if not math.isnan(self.turn.low[0]):
            self.turn_annotations.append({
                'date': self.data.datetime.date(0),
                'type': 'trough', 
                'value': self.turn.low[0],
                'bar_index': len(self)
            })


def find_data_file(ticker, data_dir):
    """
    Find the data file for a given ticker in the specified directory
    The files are organized in subdirectories by ticker name and compressed as .gz
    """
    # Look for files in ticker subdirectory - {ticker}/{ticker}_*.tsv.gz
    pattern = os.path.join(data_dir, ticker, f'{ticker}_*.tsv.gz')
    files = glob.glob(pattern)

    if not files:
        raise FileNotFoundError(f"No data file found for ticker {ticker} in {data_dir}")

    # Return the file with the biggest filename (string comparison) if multiple exist
    return max(files)


def add_turn_annotations(cerebro_plot, strategy_results):
    """
    Add text annotations to the plot showing turn point values
    """
    try:
        import matplotlib.pyplot as plt
        
        # Get the strategy instance
        strategy = strategy_results[0]
        if not hasattr(strategy, 'turn_annotations'):
            return
            
        # Get the current figure and axes
        fig = plt.gcf()
        axes = fig.get_axes()
        
        if not axes:
            return
            
        # Find the main price chart axis (usually the first one)
        main_ax = axes[0]
        
        # Add annotations for each turn point
        for annotation in strategy.turn_annotations:
            x_pos = annotation['bar_index'] 
            y_pos = annotation['value']
            text = f"{annotation['value']:.1f}"
            
            if annotation['type'] == 'peak':
                # Position text above peak with green background
                main_ax.annotate(text, xy=(x_pos, y_pos), 
                               xytext=(0, 10), textcoords='offset points',
                               ha='center', va='bottom',
                               bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.7),
                               fontsize=8, fontweight='bold')
            else:  # trough
                # Position text below trough with red background  
                main_ax.annotate(text, xy=(x_pos, y_pos),
                               xytext=(0, -15), textcoords='offset points', 
                               ha='center', va='top',
                               bbox=dict(boxstyle='round,pad=0.3', facecolor='lightcoral', alpha=0.7),
                               fontsize=8, fontweight='bold')
                               
        print(f"Added {len(strategy.turn_annotations)} turn point annotations")
        
    except ImportError:
        print("Matplotlib not available for annotations")
    except Exception as e:
        print(f"Error adding annotations: {e}")


def runstrategy():
    args = parse_args()

    # Create cerebro engine
    cerebro = bt.Cerebro()

    # Parse date range if provided
    fromdate = None
    todate = None
    if args.fromdate:
        fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')
    if args.todate:
        todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')

    # Determine data file path
    if args.ticker:
        # Auto-discover data file based on ticker
        data_path = find_data_file(args.ticker, args.datadir)
        ticker_name = args.ticker
        print(f"Using data file: {data_path}")
    else:
        # Use explicitly provided data file
        data_path = args.data
        ticker_name = os.path.basename(data_path).split('_')[-2] if '_' in os.path.basename(data_path) else 'DATA'

    # Load data using QantIBPriceVolData
    try:
        data = QantIBPriceVolData(
            dataname=data_path,
            fromdate=fromdate,
            todate=todate,
            name=ticker_name  # Set name for plotting
        )
    except Exception as e:
        print(f"Error loading data file {data_path}: {e}")
        return

    # Add data to cerebro
    cerebro.adddata(data)

    # Choose strategy based on whether annotations are requested
    if args.annotations:
        strategy_class = TurnWithTextStrategy
        print("Using enhanced strategy with text annotations")
    else:
        strategy_class = TurnStrategy
        print("Using standard strategy")

    # Add strategy with parameters
    cerebro.addstrategy(strategy_class, 
                       space=args.space,
                       thresh=args.thresh)

    # Run backtest
    print(f"Running Turn indicator analysis for {ticker_name}...")
    if fromdate:
        print(f"Date range: {fromdate.strftime('%Y-%m-%d')} to {todate.strftime('%Y-%m-%d') if todate else 'latest'}")
    
    results = cerebro.run()

    # Plot results with custom styling
    if args.plot:
        print("Plotting results...")
        try:
            cerebro.plot(
                volume=args.volume,    # Show volume if requested
                style='candlestick',   # Use candlestick chart
                barup='green',         # Green up candles
                bardown='red',         # Red down candles
                figsize=(16, 10)       # Larger figure size
            )
            
            # Add text annotations if requested and strategy supports it
            if args.annotations:
                add_turn_annotations(cerebro, results)
            
            print("Plot displayed successfully!")
            
        except Exception as e:
            print(f"Plotting error: {e}")
            print("Turn analysis completed without plotting...")


def parse_args():
    parser = argparse.ArgumentParser(
        description='Turn Indicator Plotting Example',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Ticker-based data loading
    parser.add_argument(
        '--ticker', '-s',
        help='Stock ticker symbol (e.g., AAPL, MSFT). Will auto-discover data file.'
    )

    parser.add_argument(
        '--datadir',
        default='/mnt/c/tools/airflow/data/price_vol/ib/long/1_day',
        help='Directory containing ticker data files'
    )

    # Manual data file specification (fallback)
    parser.add_argument(
        '--data', '-d',
        default='samples/qant_data/price_vol_ib_1d_AAPL_20250820000000.tsv',
        help='TSV data file to load (used if --ticker not specified)'
    )

    parser.add_argument(
        '--fromdate', '-f',
        help='Starting date in YYYY-MM-DD format'
    )

    parser.add_argument(
        '--todate', '-t',
        help='Ending date in YYYY-MM-DD format'
    )

    # Turn indicator parameters
    parser.add_argument(
        '--space',
        type=int,
        default=2,
        help='Turn indicator space parameter (bars around central point)'
    )

    parser.add_argument(
        '--thresh',
        type=float,
        default=0.5,
        help='Turn indicator threshold parameter (minimum %% change)'
    )

    # Plotting options
    parser.add_argument(
        '--plot', '-p',
        action='store_true',
        help='Generate and display plot'
    )

    parser.add_argument(
        '--volume',
        action='store_true',
        help='Include volume subplot in plot'
    )

    parser.add_argument(
        '--annotations',
        action='store_true',
        help='Add turn point value annotations to plot'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.ticker and not args.data:
        parser.error('Either --ticker or --data must be specified')

    return args


if __name__ == '__main__':
    runstrategy()