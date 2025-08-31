#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
"""
Triangle Indicator Sample Script

This script loads AAPL price data from a TSV file using QantIBDailyPriceVolData
and plots the Triangle indicator with custom visualization:
- Green circles for up triangles
- Red circles for down triangles
- Score line showing triangle strength
"""

import argparse
import datetime
import math
import os
import glob
import backtrader as bt
from backtrader.feeds.qant_ib import QantIBDailyPriceVolData
import backtrader.indicators as btind


class TriangleStrategy(bt.Strategy):
    """
    Strategy that adds Triangle indicator for visualization purposes
    """

    def __init__(self):
        # Add Triangle indicator with default parameters
        self.triangle = btind.SquareTriangle(self.data)

        # Print triangle parameters for reference
        print(f"Triangle Parameters:")
        print(f"  max_extra_area_ratio: {self.triangle.params.max_extra_area_ratio}")
        print(f"  min_range: {self.triangle.params.min_range}")
        print(f"  flat_pct: {self.triangle.params.flat_pct}")

    def next(self):
        # Optional: Print triangle signals when detected
        if not math.isnan(self.triangle.up[0]):
            print(f"Up Triangle detected at {self.data.datetime.date(0)}: "
                  f"score={self.triangle.score[0]:.1f}, level={self.triangle.up[0]:.2f}")

        if not math.isnan(self.triangle.down[0]):
            print(f"Down Triangle detected at {self.data.datetime.date(0)}: "
                  f"score={self.triangle.score[0]:.1f}, level={self.triangle.down[0]:.2f}")

        # Also check for any non-zero score values
        if self.triangle.score[0] != 0:
            if math.isnan(self.triangle.up[0]) and math.isnan(self.triangle.down[0]):
                print(f"Triangle score at {self.data.datetime.date(0)}: {self.triangle.score[0]:.1f}")


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

    # Load data using QantIBDailyPriceVolData
    data = QantIBDailyPriceVolData(
        dataname=data_path,
        fromdate=fromdate,
        todate=todate,
        name=ticker_name  # Set name for plotting
    )

    # Add data to cerebro
    cerebro.adddata(data)

    # Add strategy
    cerebro.addstrategy(TriangleStrategy)

    # Run backtest
    print("Running Triangle indicator analysis...")
    results = cerebro.run()

    # Plot results with custom styling
    print("Plotting results...")
    try:
        cerebro.plot(
            volume=True,  # Show volume
            style='candlestick',  # Use candlestick chart
            barup='green',  # Green up candles
            bardown='red',  # Red down candles
            figsize=(16, 10)  # Larger figure size
        )
        print("Plot displayed successfully!")
    except Exception as e:
        print(f"Plotting error: {e}")
        print("Running without plotting...")


def parse_args():
    parser = argparse.ArgumentParser(
        description='Triangle Indicator Plotting Example',
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

    args = parser.parse_args()

    # Validate arguments
    if not args.ticker and not args.data:
        parser.error('Either --ticker or --data must be specified')

    return args


if __name__ == '__main__':
    runstrategy()