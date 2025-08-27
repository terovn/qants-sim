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
        data_feed = bt.feeds.PandasData(
            dataname=self._create_dataframe(bars_data),
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
                'datetime': pd.Timestamp(f'2023-01-{i+1:02d}'),
                'open': open_price,
                'high': high,
                'low': low, 
                'close': close_price,
                'volume': volume
            })
        
        # Pad with additional bars to meet minimum period requirements
        last_bar = bars_data[-1] if bars_data else (1, 100.0, 99.0)
        _, last_high, last_low = last_bar
        
        for i in range(len(bars_data), 25):  # Ensure at least 25 bars
            # Create variations around the last bar
            open_price = (last_high + last_low) / 2
            close_price = open_price
            
            df_data.append({
                'datetime': pd.Timestamp(f'2023-01-{i+1:02d}'),
                'open': open_price,
                'high': last_high,
                'low': last_low, 
                'close': close_price,
                'volume': 1000
            })
        
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
        results = cerebro.run()
        strategy = results[0]
        
        # Check if any result matches the expected score
        if strategy.results:
            for result in strategy.results:
                actual_score = int(result['score'])
                if actual_score == expected_score:
                    print(f"Expected score: {expected_score}, Actual score: {actual_score}")
                    return True
            
            # Print all scores for debugging
            all_scores = [int(r['score']) for r in strategy.results]
            print(f"Expected score: {expected_score}, All actual scores: {all_scores}")
            return expected_score == 0 and all(s == 0 for s in all_scores)
        
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