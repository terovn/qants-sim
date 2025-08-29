#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Triangle Pattern Detection Example
#
# This sample demonstrates the Triangle indicator based on StudyTriangle2
# from the qAnts Java project. The indicator detects triangle patterns
# and outputs 3 series: score, up, and down.
#
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import sys
import math
import backtrader as bt


class TriangleStrategy(bt.Strategy):
    '''
    Strategy that uses the Triangle indicator to detect triangle patterns
    '''
    
    params = (
        ('thresh', 0.2),      # Triangle detection threshold
        ('range', 3),         # Minimum bars for triangle
        ('flat_pct', 0.2),    # Flatness percentage
        ('lookback', 20),     # Lookback period
        ('printlog', True),   # Print log messages
    )
    
    def log(self, txt, dt=None):
        ''' Logging function '''
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()}, {txt}')
    
    def __init__(self):
        # Initialize the Triangle indicator
        self.triangle = bt.indicators.Triangle(
            self.data,
            thresh=self.params.thresh,
            range=self.params.range,
            flat_pct=self.params.flat_pct,
            lookback=self.params.lookback
        )
        
        # For tracking positions
        self.order = None
        
        # Track triangle detections
        self.triangle_count = 0
        self.up_triangles = 0
        self.down_triangles = 0
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}')
            elif order.issell():
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}')
                
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
            
        self.order = None
    
    def next(self):
        # Get triangle indicator values
        score = self.triangle.lines.score[0]
        up_signal = self.triangle.lines.up[0]
        down_signal = self.triangle.lines.down[0]
        
        # Log triangle detections
        if score != 0:
            self.triangle_count += 1
            
            if score > 0 and not math.isnan(up_signal):
                self.up_triangles += 1
                self.log(f'UP TRIANGLE detected! Score: {score:.0f}, Level: {up_signal:.2f}')
                
                # Example trading logic: Buy on up triangle
                if not self.position:
                    self.log(f'BUY CREATE, {self.data.close[0]:.2f}')
                    self.order = self.buy()
                    
            elif score < 0 and not math.isnan(down_signal):
                self.down_triangles += 1
                self.log(f'DOWN TRIANGLE detected! Score: {score:.0f}, Level: {down_signal:.2f}')
                
                # Example trading logic: Sell on down triangle
                if self.position:
                    self.log(f'SELL CREATE, {self.data.close[0]:.2f}')
                    self.order = self.sell()
    
    def stop(self):
        self.log(f'Triangle Statistics:')
        self.log(f'  Total Triangles: {self.triangle_count}')
        self.log(f'  Up Triangles: {self.up_triangles}')
        self.log(f'  Down Triangles: {self.down_triangles}')
        self.log(f'Final Portfolio Value: {self.broker.getvalue():.2f}')


def run_triangle_example(args=None):
    args = parse_args(args)
    
    cerebro = bt.Cerebro()
    
    # Add data
    if args.data:
        data = bt.feeds.YahooFinanceCSVData(dataname=args.data)
    else:
        # Use sample data if no data file provided
        data = bt.feeds.YahooFinanceData(
            dataname='AAPL',
            fromdate=bt.datetime.datetime(2020, 1, 1),
            todate=bt.datetime.datetime(2023, 1, 1),
        )
    
    cerebro.adddata(data)
    
    # Add strategy
    cerebro.addstrategy(
        TriangleStrategy,
        thresh=args.thresh,
        range=args.range,
        flat_pct=args.flat_pct,
        lookback=args.lookback,
        printlog=args.printlog
    )
    
    # Set cash
    cerebro.broker.setcash(args.cash)
    
    # Set commission
    cerebro.broker.setcommission(commission=0.001)
    
    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    
    # Run backtest
    results = cerebro.run()
    strat = results[0]
    
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    
    # Print analyzer results
    print('\nPerformance Metrics:')
    print(f'Sharpe Ratio: {strat.analyzers.sharpe.get_analysis().get("sharperatio", "N/A")}')
    print(f'Total Return: {strat.analyzers.returns.get_analysis().get("rtot", 0):.4f}')
    print(f'Max Drawdown: {strat.analyzers.drawdown.get_analysis().get("max", {}).get("drawdown", 0):.2f}%')
    
    # Plot if requested
    if args.plot:
        cerebro.plot(style='candlestick', volume=False)


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Triangle Pattern Detection Example'
    )
    
    parser.add_argument('--data', default=None,
                        help='Data file to use (CSV format)')
    
    parser.add_argument('--cash', default=100000, type=float,
                        help='Starting cash')
    
    parser.add_argument('--thresh', default=0.2, type=float,
                        help='Triangle detection threshold')
    
    parser.add_argument('--range', default=3, type=int,
                        help='Minimum bars for triangle')
    
    parser.add_argument('--flat-pct', default=0.2, type=float,
                        help='Flatness percentage')
    
    parser.add_argument('--lookback', default=20, type=int,
                        help='Lookback period')
    
    parser.add_argument('--plot', action='store_true',
                        help='Plot the results')
    
    parser.add_argument('--printlog', action='store_true', default=True,
                        help='Print log messages')
    
    return parser.parse_args(pargs)


if __name__ == '__main__':
    run_triangle_example()