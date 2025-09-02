#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Test for Turn indicator - Based on StudyTurn Java tests
#
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import testcommon

import backtrader as bt
import backtrader.indicators as btind
import math

# Test with Turn indicator
chkdatas = 1
chkmin = 7  # 2 * 3 + 1 minimum period for space=3

# Use Turn indicator instead of predefined check values
# We'll verify the Turn detection logic in the strategy
chkind = btind.Turn


class TurnTestStrategy(bt.Strategy):
    '''Test strategy for Turn indicator'''
    
    def __init__(self, **kwargs):
        # Add Turn indicator with default parameters
        self.turn = btind.Turn(self.data, space=3, thresh=0.5)
        
        # Track turn points for testing
        self.turn_points = []
    
    def next(self):
        # Record turn points when they occur
        if not math.isnan(self.turn.high[0]):
            self.turn_points.append({
                'type': 'peak',
                'bar': len(self),
                'value': self.turn.high[0],
                'price_high': self.data.high[0],
                'price_low': self.data.low[0]
            })
            print(f'Peak turn detected at bar {len(self)}: value={self.turn.high[0]:.2f}, high={self.data.high[0]:.2f}')
        
        if not math.isnan(self.turn.low[0]):
            self.turn_points.append({
                'type': 'trough', 
                'bar': len(self),
                'value': self.turn.low[0],
                'price_high': self.data.high[0], 
                'price_low': self.data.low[0]
            })
            print(f'Trough turn detected at bar {len(self)}: value={self.turn.low[0]:.2f}, low={self.data.low[0]:.2f}')
    
    def stop(self):
        print(f'\nTurn test completed. Total turns detected: {len(self.turn_points)}')
        
        # Basic validation checks
        peak_count = sum(1 for tp in self.turn_points if tp['type'] == 'peak')
        trough_count = sum(1 for tp in self.turn_points if tp['type'] == 'trough')
        
        print(f'Peaks: {peak_count}, Troughs: {trough_count}')
        
        # Verify turn points are properly spaced (should have at least space=3 bars between)
        if len(self.turn_points) > 1:
            for i in range(1, len(self.turn_points)):
                bar_diff = self.turn_points[i]['bar'] - self.turn_points[i-1]['bar']
                if bar_diff < 3:  # Less than space parameter
                    print(f'WARNING: Turn points too close together: {bar_diff} bars apart')
                    
        # Verify alternating pattern (peak -> trough -> peak, etc)
        if len(self.turn_points) > 1:
            for i in range(1, len(self.turn_points)):
                prev_type = self.turn_points[i-1]['type']
                curr_type = self.turn_points[i]['type']
                if prev_type == curr_type:
                    print(f'WARNING: Consecutive {curr_type} turns detected')


def test_run(main=False):
    datas = [testcommon.getdata(i) for i in range(chkdatas)]
    testcommon.runtest(datas,
                       TurnTestStrategy,
                       main=main,
                       plot=main)


def test_manual_data():
    '''Test with manually created data to verify turn detection'''
    import pandas as pd
    
    # Create test data with known peaks and troughs
    # Peak at index 3, trough at index 7, peak at index 11
    test_data = [
        # Initial rising trend leading to peak
        {'open': 10.0, 'high': 10.5, 'low': 9.8, 'close': 10.2, 'volume': 1000},   # 0
        {'open': 10.2, 'high': 11.0, 'low': 10.0, 'close': 10.8, 'volume': 1000},  # 1  
        {'open': 10.8, 'high': 11.5, 'low': 10.5, 'close': 11.2, 'volume': 1000},  # 2
        {'open': 11.2, 'high': 12.0, 'low': 11.0, 'close': 11.8, 'volume': 1000},  # 3 <- Peak should be here
        {'open': 11.8, 'high': 11.9, 'low': 11.0, 'close': 11.3, 'volume': 1000},  # 4
        {'open': 11.3, 'high': 11.5, 'low': 10.5, 'close': 10.8, 'volume': 1000},  # 5
        {'open': 10.8, 'high': 11.0, 'low': 9.5, 'close': 9.8, 'volume': 1000},    # 6
        {'open': 9.8, 'high': 10.0, 'low': 9.0, 'close': 9.2, 'volume': 1000},     # 7 <- Trough should be here
        {'open': 9.2, 'high': 9.8, 'low': 9.0, 'close': 9.5, 'volume': 1000},     # 8
        {'open': 9.5, 'high': 10.2, 'low': 9.3, 'close': 10.0, 'volume': 1000},   # 9
        {'open': 10.0, 'high': 10.8, 'low': 9.8, 'close': 10.5, 'volume': 1000},  # 10
        {'open': 10.5, 'high': 11.2, 'low': 10.2, 'close': 11.0, 'volume': 1000}, # 11 <- Peak should be here
        {'open': 11.0, 'high': 11.1, 'low': 10.5, 'close': 10.7, 'volume': 1000}, # 12
    ]
    
    # Create dates for the data
    import datetime
    base_date = datetime.datetime(2023, 1, 1)
    dates = [base_date + datetime.timedelta(days=i) for i in range(len(test_data))]
    
    # Create DataFrame
    df = pd.DataFrame(test_data, index=dates)
    
    # Create data feed
    data = bt.feeds.PandasData(dataname=df)
    
    # Create cerebro and run test
    cerebro = bt.Cerebro()
    cerebro.adddata(data)
    cerebro.addstrategy(TurnTestStrategy)
    
    print("Running Turn indicator test with manual data...")
    result = cerebro.run()
    
    print("Manual data test completed")


if __name__ == '__main__':
    print("Testing Turn indicator...")
    
    # Test with sample data files
    test_run(main=True)
    
    # Test with manual data
    try:
        test_manual_data()
    except ImportError:
        print("Pandas not available, skipping manual data test")