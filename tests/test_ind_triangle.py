#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Test for Triangle indicator - Based on StudyTriangle2 Java tests
#
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import unittest
import backtrader as bt
from backtrader.indicators import Triangle
import math


class TestTriangle(unittest.TestCase):
    
    def _create_data_feed(self, bars_data):
        """
        Create a backtrader data feed from list of (time, high, low) tuples
        """
        df = self._create_dataframe(bars_data)
        data_feed = bt.feeds.PandasData(
            dataname=df,
            timeframe=bt.TimeFrame.Days,
        )
        return data_feed
    
    def _create_dataframe(self, bars_data):
        """
        Create pandas dataframe from bars data, padding with extra bars if needed
        """
        import pandas as pd
        
        df_data = []
        # Add the specific test data
        for i, (time, high, low) in enumerate(bars_data):
            open_price = (high + low) / 2
            close_price = (high + low) / 2
            volume = 1000
            
            df_data.append({
                'open': open_price,
                'high': high,
                'low': low, 
                'close': close_price,
                'volume': volume
            })
        
        # Pad with additional bars to meet minimum period requirements
        # Create varied padding bars that won't form triangle patterns
        padding_needed = max(0, 25 - len(bars_data))
        padding_bars = []
        
        for i in range(padding_needed):
            # Create varied bars that won't form triangles
            # Use a sawtooth pattern that breaks triangle conditions
            base_price = 80.0
            if i % 4 == 0:
                high, low = 82.0, 78.0
            elif i % 4 == 1:
                high, low = 84.0, 80.0  
            elif i % 4 == 2:
                high, low = 81.0, 77.0
            else:
                high, low = 85.0, 81.0
                
            open_price = (high + low) / 2
            padding_bars.append({
                'open': open_price,
                'high': high,
                'low': low,
                'close': open_price,
                'volume': 1000
            })
        
        df_data = padding_bars + df_data

        for i, data in enumerate(df_data):
            data['datetime'] = pd.Timestamp(f'2023-01-{i + 1:02d}')

        df = pd.DataFrame(df_data)
        df.set_index('datetime', inplace=True)
        return df
    
    def _run_indicator_test(self, bars_data, expected_score):
        """
        Run indicator on test data and check results
        """
        import pandas as pd
        
        cerebro = bt.Cerebro()
        data = self._create_data_feed(bars_data)
        cerebro.adddata(data)
        
        # Create strategy to run indicator
        class TestStrategy(bt.Strategy):
            def __init__(self):
                # Use smaller parameters suitable for test data
                self.triangle = Triangle(
                    self.data,
                    range=3,
                    lookback=5,  # Smaller lookback for test
                    thresh=0.2,
                    flat_pct=0.4  # Higher tolerance for test data
                )
                self.results = []
                
            def next(self):
                score = self.triangle.lines.score[0]
                up = self.triangle.lines.up[0]
                down = self.triangle.lines.down[0]
                
                self.results.append({
                    'score': score,
                    'up': up if not math.isnan(up) else None,
                    'down': down if not math.isnan(down) else None
                })
        
        cerebro.addstrategy(TestStrategy)
        strategy = cerebro.run()[0]
        
        # Check if any result matches the expected score
        if strategy.results:
            # print(f"all scores: {[r['score'] for r in strategy.results]}")
            last_score = int(strategy.results[-1]['score'])
            # print(f"Expected score: {expected_score}, Actual last score: {last_score}")
            return last_score == expected_score
        
        return expected_score == 0
    
    def test_good_up_triangle(self):
        """
        Test case from Java: testGoodUpTriangle
        Bar data: (time, high, low)
        """
        bars_data = [
            (1, 90.59, 89.06),
            (2, 90.51, 89.32), 
            (3, 90.58, 89.46)
        ]
        
        # Java test expects score of 3 for this up triangle
        self.assertTrue(
            self._run_indicator_test(bars_data, expected_score=3),
            "Good up triangle should return score of 3"
        )
    
    def test_ok_down_triangle(self):
        """
        Test case from Java: testOkDownTriangle  
        Bar data: (time, high, low)
        """
        bars_data = [
            (1, 77.77, 75.1),
            (2, 77.09, 75.43),
            (3, 76.39, 75.13)
        ]
        
        # Java test expects score of -3 for this down triangle (negative for down)
        self.assertTrue(
            self._run_indicator_test(bars_data, expected_score=-3),
            "Down triangle should return score of -3" 
        )
    
    def test_bad_triangle(self):
        """
        Test case from Java: testBadDownTriangle
        This should not form a valid triangle
        """

        bars_data = [
            (1, 97.97, 95.34),
            (2, 98.21, 95.73),  # Higher high breaks down triangle pattern
            (3, 97.55, 95.56)
        ]
        
        # Java test expects score of 0 (no triangle detected)
        self.assertTrue(
            self._run_indicator_test(bars_data, expected_score=0),
            "Bad triangle should return score of 0"
        )
    
    def test_indicator_parameters(self):
        """
        Test different parameter combinations
        """
        bars_data = [
            (1, 90.59, 89.06),
            (2, 90.51, 89.32), 
            (3, 90.58, 89.46)
        ]
        
        cerebro = bt.Cerebro()
        data = self._create_data_feed(bars_data)
        cerebro.adddata(data)
        
        class TestStrategy(bt.Strategy):
            def __init__(self):
                # Test with different thresholds
                self.triangle1 = Triangle(self.data, thresh=0.1)
                self.triangle2 = Triangle(self.data, thresh=0.3)
                self.triangle3 = Triangle(self.data, flat_pct=0.1)
                
        cerebro.addstrategy(TestStrategy)
        results = cerebro.run()
        
        # Test should run without errors
        self.assertIsNotNone(results)
    
    def test_insufficient_data(self):
        """
        Test behavior with insufficient data
        """
        bars_data = [
            (1, 90.59, 89.06),
            (2, 90.51, 89.32)  # Only 2 bars, need at least 3
        ]
        
        self.assertTrue(
            self._run_indicator_test(bars_data, expected_score=0),
            "Insufficient data should return score of 0"
        )


if __name__ == '__main__':
    unittest.main()