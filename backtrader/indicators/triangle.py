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
import math


class Triangle(Indicator):
    '''
    Triangle Pattern Detector
    
    Detects triangle consolidation patterns in price data by analyzing
    the overlap between actual price action and a perfect triangle shape.
    
    Up Triangle: Flat highs with progressively higher lows
    Down Triangle: Flat lows with progressively lower highs
    
    Parameters:
    - thresh: Maximum allowed ratio of non-overlapping area (default 0.2)
    - range: Minimum bars needed for valid triangle (default 3)  
    - flat_pct: Maximum percentage difference for flat tops/bottoms (default 0.2)
    - lookback: Number of bars to analyze (default 20)
    
    Outputs:
    - score: Triangle strength/length (positive for up triangles, negative for down triangles, 0 if none)
    - up: Price level where up triangle detected (NaN otherwise)
    - down: Price level where down triangle detected (NaN otherwise)
    '''
    
    alias = ('LongTri', 'Triangle2', 'LongTriangle2')
    
    lines = ('score', 'up', 'down')
    
    params = (
        ('thresh', 0.2),      # max allowed ratio of non-overlapping area
        ('range', 3),         # minimum bars for valid triangle
        ('flat_pct', 0.2),    # max pct difference for flat tops/bottoms  
        ('lookback', 20),     # number of bars to look back
    )
    
    plotinfo = dict(
        plot=True,
        plothlines=[0.0],
        plotabove=False,
    )
    
    plotlines = dict(
        score=dict(color='blue'),
        up=dict(marker='o', markersize=8, color='green', fillstyle='full', ls=''),
        down=dict(marker='o', markersize=8, color='red', fillstyle='full', ls=''),
    )
    
    def __init__(self):
        super(Triangle, self).__init__()
        # Set minimum period
        self.addminperiod(max(self.p.range, self.p.lookback))
        
        # Set plotmaster to display underlying data as candlesticks
        self.plotinfo.plotmaster = self.data
    
    
    def _get_triangle_score(self, bars, flip=False):
        """
        Calculate triangle score for given bars
        
        Args:
            bars: List of OHLC bars to analyze
            flip: If True, analyze as down triangle (flip high/low)
            
        Returns:
            dict with keys: direction, length, entry_price, ex_pct
        """
        if len(bars) < self.p.range:
            return None
            
        result = {
            'direction': 'short' if flip else 'long',
            'length': 0,
            'entry_price': float('-inf') if not flip else float('inf'),
            'ex_pct': 0
        }
        
        # Get start and end bars for triangle base
        bar_end = bars[-1]
        bar_start = bars[-(self.p.range)]
        
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
        
        # Test triangle conditions
        flat_diff_pct = abs((high_end - high_start) * 100.0 / high_start) if high_start != 0 else float('inf')
        
        # Up triangle: flat highs + higher lows
        # Down triangle: flat lows + lower highs (after flip)
        if (flat_diff_pct <= self.p.flat_pct and 
            low_end > low_start and 
            low_end < high_start):
            
            ex_total = 0.0
            area_total = high_end - low_end
            next_bar_low = low_end
            
            # Analyze bars from newest to oldest
            max_bars = min(self.p.range * 2, len(bars))
            for i in range(max_bars):
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
                per_low = low_end - (low_end - low_start) * i / (self.p.range - 1)
                thres = high_end - per_low
                
                # Calculate deviations from perfect triangle
                ex_top = abs(bi_high - high_end)
                ex_bot = abs(bi_low - per_low)
                
                ex_total += ex_top + ex_bot
                area_total += thres
                
                # Check if deviation exceeds threshold
                if area_total > 0 and ex_total / area_total > self.p.thresh:
                    break
                
                # Update result
                result['ex_pct'] = ex_total / area_total if area_total > 0 else 0
                if flip:
                    # For flipped data, we want the minimum (which corresponds to max in original)
                    result['entry_price'] = min(result['entry_price'], bi_high)
                else:
                    result['entry_price'] = max(result['entry_price'], bi_high)
                result['length'] += 1
        
        # Fix entry price for flipped data
        if flip and result['length'] >= self.p.range:
            result['entry_price'] = -result['entry_price']
        
        return result if result['length'] >= self.p.range else None
    
    def next(self):
        # Initialize outputs
        self.lines.score[0] = 0.0
        self.lines.up[0] = float('nan')
        self.lines.down[0] = float('nan')
        
        # Need enough data
        if len(self) < max(self.p.range, self.p.lookback):
            return
        
        # Debug: print current bar info
        #print(f"Triangle next(): len={len(self)}, high={self.data.high[0]}, low={self.data.low[0]}")
            
        # Get bars for analysis - scan from current position backwards
        lookback_bars = min(self.p.lookback, len(self))
        start_idx = max(0, len(self) - lookback_bars)
        
        # Analyze each position within lookback window
        for idx in range(len(self) - 1, start_idx + self.p.range - 2, -1):
            if idx < self.p.range - 1:
                continue
                
            # Get bars for this analysis window
            bars = []
            for i in range(idx - self.p.range + 1, idx + 1):
                if i < 0:
                    continue
                ago_offset = len(self) - 1 - i
                bars.append({
                    'high': self.data.high[-ago_offset],
                    'low': self.data.low[-ago_offset],
                    'time': i
                })
            
            if len(bars) < self.p.range:
                continue
                
            # Test for up triangle first
            triangle = self._get_triangle_score(bars, flip=False)
            
            # If no up triangle, test for down triangle
            if triangle is None or triangle['length'] < self.p.range:
                triangle = self._get_triangle_score(bars, flip=True)
            
            # If valid triangle found
            if triangle is not None and triangle['length'] >= self.p.range:
                # Score is negative for down triangles, positive for up triangles
                if triangle['direction'] == 'short':
                    score = -float(triangle['length'])
                    self.lines.down[0] = float(bars[-1]['low'])
                else:
                    score = float(triangle['length'])
                    self.lines.up[0] = float(bars[-1]['high'])
                    
                self.lines.score[0] = score
                
                # Skip ahead to avoid overlapping detections
                break