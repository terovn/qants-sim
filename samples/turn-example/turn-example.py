#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Turn Point Detection Example
# 
# Demonstrates the Turn indicator with candlestick plotting
#
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import datetime
import os.path
import sys

# Import backtrader
import backtrader as bt


class TurnStrategy(bt.Strategy):
    """
    Simple strategy that uses Turn indicator to detect peaks and troughs
    """
    
    params = (
        ('space', 3),        # Turn indicator space parameter
        ('thresh', 0.5),     # Turn indicator threshold parameter
    )
    
    def __init__(self):
        # Add Turn indicator
        self.turn = bt.indicators.Turn(
            self.data, 
            space=self.p.space,
            thresh=self.p.thresh
        )
        
        # Track turn points
        self.turn_count = 0
    
    def next(self):
        # Check for turn points
        import math
        
        if not math.isnan(self.turn.high[0]):
            self.turn_count += 1
            print(f'Peak turn detected at {self.data.datetime.date(0)}: {self.turn.high[0]:.2f}')
        
        if not math.isnan(self.turn.low[0]):
            self.turn_count += 1
            print(f'Trough turn detected at {self.data.datetime.date(0)}: {self.turn.low[0]:.2f}')
    
    def stop(self):
        print(f'\nStrategy completed. Total turn points detected: {self.turn_count}')


def runstrat(args=None):
    args = parse_args(args)

    cerebro = bt.Cerebro()

    # Data feed
    if args.data is not None:
        datapath = args.data
    else:
        # Default to sample data
        datapath = os.path.join(os.path.dirname(__file__), 
                               '../../datas/orcl-2014.txt')
    
    if not os.path.exists(datapath):
        print(f'Data file not found: {datapath}')
        return
    
    # Create data feed
    data = bt.feeds.YahooFinanceCSVData(dataname=datapath)
    cerebro.adddata(data)

    # Add strategy
    cerebro.addstrategy(TurnStrategy, 
                       space=args.space,
                       thresh=args.thresh)

    # Run the strategy
    print(f'Running Turn indicator example with space={args.space}, thresh={args.thresh}%')
    cerebro.run()

    # Plot if requested
    if args.plot:
        print('Generating plot with candlestick chart and Turn markers...')
        kwargs = {}
        if args.plot is not True:  # evals to True but is not True
            kwargs = eval('dict(' + args.plot + ')')  # args were passed
        
        # Force candlestick style for better visualization
        kwargs.update(style='candlestick')
        cerebro.plot(**kwargs)


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Turn Point Detection Example'
    )

    parser.add_argument('--data', default=None, required=False,
                        help='Data file to use (default: sample ORCL data)')

    parser.add_argument('--space', default=3, type=int, required=False,
                        help='Turn indicator space parameter')

    parser.add_argument('--thresh', default=0.5, type=float, required=False,
                        help='Turn indicator threshold parameter (%)')

    # Plot options
    parser.add_argument('--plot', '-p', nargs='?', default=False,
                        metavar='kwargs', const=True,
                        help='Plot the read data and turn points')

    return parser.parse_args(pargs)


if __name__ == '__main__':
    runstrat()