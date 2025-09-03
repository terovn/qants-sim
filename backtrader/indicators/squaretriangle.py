#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Triangle Pattern Indicator - Based on StudyTriangle2 from qAnts Java project
#
# Detects triangle patterns in price data by analyzing:
# - Up triangles: flat highs with rising lows  
# - Down triangles: flat lows with falling highs
# - Area overlap between actual price action and perfect triangle
#
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from . import Indicator


class SquareTriangle(Indicator):
    '''
    Triangle Pattern Detector - based on StudyTriangle2 from qants-trader Java.
    
    Detects triangle consolidation patterns in price data by analyzing
    the overlap between actual price action and a perfect triangle shape.
    
    Up Triangle: Flat highs with progressively higher lows
    Down Triangle: Flat lows with progressively lower highs
    
    Parameters:
    - max_area_diff_ratio: Maximum allowed ratio of non-overlapping area
    - min_range: Minimum bars needed for valid triangle (default 3)
    - flat_pct: Maximum percentage difference for flat tops/bottoms, 1 means 1%
    
    Outputs:
    - score: Triangle strength/length (positive for up triangles, negative for down triangles, 0 if none)
    - up: Price level where up triangle detected (NaN otherwise)
    - down: Price level where down triangle detected (NaN otherwise)
    '''
    
    alias = ('Triangle',)
    
    lines = ('score', 'up', 'down')
    
    params = (
        ('max_area_diff_ratio', 0.2),      # max allowed ratio of non-overlapping area
        ('min_range', 3),     # minimum bars for valid triangle
        ('flat_pct', 0.4),    # max percentage difference for flat tops/bottoms, 1 means 1%
    )
    
    plotinfo = dict(
        plot=True,
        plothlines=[0.0],
        plotabove=False,
        subplot=True,
    )
    
    plotlines = dict(
        score=dict(color='orange', linewidth=2, _plotskip=False),
        up=dict(marker='o', markersize=8, color='green', fillstyle='none', ls='', _plotskip=False),
        down=dict(marker='o', markersize=8, color='red', fillstyle='none', ls='', _plotskip=False),
    )
    
    def __init__(self):
        super(SquareTriangle, self).__init__()
        # Set minimum period - only need 'range' bars for triangle detection
        self.addminperiod(self.p.min_range)
        
        # Set plotmaster to display underlying data as candlesticks
        self.plotinfo.plotmaster = self.data
    
    
    
    def _get_triangle_score(self, bars, flip=False):
        """
        Calculate triangle score for given bars, testing progressively longer ranges
        to find the longest valid triangle pattern.
        
        Args:
            bars: List of OHLC bars to analyze
            flip: If True, analyze as down triangle (flip high/low)
            
        Returns:
            dict with keys: direction, length, ex_pct
        """
        if len(bars) < self.p.min_range:
            return None
        
        best_result = None
        
        # Test progressively longer ranges, starting from minimum range
        for test_range in range(self.p.min_range, len(bars) + 1):
            result = self._test_triangle_range(bars, test_range, flip)
            
            # If this range produces a valid triangle, keep it as best
            if result is not None and result['length'] >= test_range:
                best_result = result
            else:
                # If this range fails, stop extending (no longer ranges will work)
                break
        
        return best_result
    
    def _test_triangle_range(self, bars, test_range, flip=False):
        """
        Test triangle pattern for a specific range length
        
        Args:
            bars: List of OHLC bars to analyze
            test_range: Number of bars from end to use as triangle base
            flip: If True, analyze as down triangle (flip high/low)
            
        Returns:
            dict with triangle result or None if invalid
        """
        if len(bars) < test_range:
            return None
            
        result = {
            'direction': 'short' if flip else 'long',
            'length': 0,
            'ex_pct': 0
        }
        
        # Get start and end bars for triangle base
        bar_end = bars[-1]
        bar_start = bars[-test_range]
        
        if flip:
            # For down triangle, flip around x-axis (negate values and swap high/low)
            high_end = -float(bar_end['low'])
            low_end = -float(bar_end['high'])
            high_start = -float(bar_start['low'])  
            low_start = -float(bar_start['high'])
        else:
            # For up triangle
            high_end = float(bar_end['high'])
            low_end = float(bar_end['low'])
            high_start = float(bar_start['high'])
            low_start = float(bar_start['low'])
        
        # Test triangle conditions (initial flatness check)
        flat_diff_pct = abs((high_end - high_start) * 100.0 / high_start) if high_start != 0 else float('inf')
        
        # Up triangle: flat highs + higher lows
        # Down triangle: flat lows + lower highs (after flip)
        if (flat_diff_pct <= self.p.flat_pct and
            low_end > low_start and 
            low_end < high_start):
            
            ex_total = 0.0
            area_total = high_end - low_end
            next_bar_low = low_end
            
            # Analyze bars from newest to oldest (only test up to test_range bars)
            for i in range(test_range):
                if i >= len(bars):
                    break
                    
                bar_i = bars[-(i+1)]
                
                if flip:
                    # Flip around x-axis (negate and swap high/low)
                    bi_high = -float(bar_i['low'])
                    bi_low = -float(bar_i['high'])
                else:
                    bi_high = float(bar_i['high'])
                    bi_low = float(bar_i['low'])
                
                # Test for progressively higher lows (up) or lower highs (down)
                if bi_low > next_bar_low:
                    break
                next_bar_low = bi_low
                
                # Test flatness condition
                flat_diff_pct = abs((high_end - bi_high) * 100.0 / high_end) if high_end != 0 else float('inf')
                if flat_diff_pct > self.p.flat_pct:
                    break
                
                # Calculate perfect triangle low at this position
                per_low = low_end - (low_end - low_start) * i / (test_range - 1)
                thres = high_end - per_low
                
                # Calculate deviations from perfect triangle
                ex_top = abs(bi_high - high_end)
                ex_bot = abs(bi_low - per_low)
                
                ex_total += ex_top + ex_bot
                area_total += thres
                
                # Check if deviation exceeds threshold
                if area_total > 0 and ex_total / area_total > self.p.max_area_diff_ratio:
                    break
                
                # Update result
                result['ex_pct'] = ex_total / area_total if area_total > 0 else 0
                result['length'] += 1

        return result if result['length'] >= test_range else None
    
    def next(self):
        # Need enough data - only require range bars for triangle detection
        if len(self) < self.p.min_range:
            return
            
        # Initialize outputs
        self.lines.score[0] = 0.0
        self.lines.up[0] = float('nan')
        self.lines.down[0] = float('nan')

        # Look for triangles that end at the current bar (triangle completion detection)
        # This ensures each triangle pattern is detected exactly once - on the completion day
        idx = len(self) - 1  # Look at pattern ending at current bar
        
        if idx >= self.p.min_range - 1:
            # Get bars for this analysis window
            bars = []
            start_idx = max(0, idx - len(self) + 1)
            for i in range(start_idx, idx + 1):
                if i < 0:
                    continue
                ago_offset = len(self) - 1 - i
                bars.append({
                    'high': self.data.high[-ago_offset],
                    'low': self.data.low[-ago_offset],
                    'time': i
                })
            
            if len(bars) >= self.p.min_range:
                # Test for up triangle first
                triangle = self._get_triangle_score(bars, flip=False)
                
                # If no up triangle, test for down triangle
                if triangle is None or triangle['length'] < self.p.min_range:
                    triangle = self._get_triangle_score(bars, flip=True)
                
                # If valid triangle found
                if triangle is not None and triangle['length'] >= self.p.min_range:
                    # Score is negative for down triangles, positive for up triangles
                    if triangle['direction'] == 'short':
                        score = -float(triangle['length'])
                        # down line records the lowest price in the triangle
                        self.lines.down[0] = min([b['low'] for b in bars[-triangle['length']:]])
                    else:
                        score = float(triangle['length'])
                        # up line records the highest price in the triangle
                        self.lines.up[0] = max([b['high'] for b in bars[-triangle['length']:]])
                        
                    self.lines.score[0] = score
