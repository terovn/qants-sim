#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Turn Point Detection Indicator - Based on StudyTurn from qAnts Java project
#
# Detects price turning points (peaks and troughs) in OHLC data by analyzing:
# - Peaks: Central bar with highest high surrounded by lower highs
# - Troughs: Central bar with lowest low surrounded by higher lows
# - Threshold validation to ensure meaningful price movements
#
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from . import Indicator


class Turn(Indicator):
    '''
    Turn Point Detection Indicator - based on StudyTurn from qants-trader Java.
    
    Identifies price turning points (peaks and troughs) in OHLC data by analyzing
    price action around a central bar within a specified range.
    
    Peak Turn: Central bar has highest high within 'space' bars on both sides
    Trough Turn: Central bar has lowest low within 'space' bars on both sides
    
    Parameters:
    - space: Number of bars on each side of central bar to check (default 3)
    - thresh: Minimum percentage change threshold for valid turns (default 0.5%)
    
    Outputs:
    - high: Price level where peak turn detected (NaN otherwise)
    - low: Price level where trough turn detected (NaN otherwise)
    
    Note: Uses rolling buffer of size (2 * space + 1) bars for analysis
    '''
    
    lines = ('high', 'low')
    
    params = (
        ('space', 2),        # bars around central point to check for extrema
        ('thresh', 0.5),     # minimum percentage change threshold
    )
    
    plotinfo = dict(
        plot=True,
        subplot=False,       # plot on main chart with price data
        plotmaster=None,     # will be set to data in __init__
        plotlinesondata=True, # plot markers on candlestick data
    )
    
    plotlines = dict(
        high=dict(marker='o', markersize=8, color='green', fillstyle='none', ls='', _plotskip=False),
        low=dict(marker='o', markersize=8, color='red', fillstyle='none', ls='', _plotskip=False),
    )
    
    def __init__(self):
        super(Turn, self).__init__()
        
        # Set minimum period needed: 2 * space + 1 (lookback as requested)
        self.addminperiod(2 * self.p.space + 1)
        
        # Plot on main chart with price data
        self.plotinfo.plotmaster = self.data
        
        # Track last turn types to handle consecutive same-type turns
        self._last_turn_type = None  # 'peak' or 'trough'
        self._last_peak_value = None
        self._last_trough_value = None
    
    def next(self):
        # Initialize outputs to NaN
        self.lines.high[0] = float('nan')
        self.lines.low[0] = float('nan')
        
        # We only analyze when we have enough bars after the central position
        # This ensures we analyze complete patterns
        if len(self) < 2 * self.p.space + 1:
            return
            
        # Analyze central bar (space bars back from current)
        central_idx = -self.p.space
        
        # Get OHLC values for central bar
        central_high = self.data.high[central_idx]
        central_low = self.data.low[central_idx]
        
        # Check if central bar is a peak or trough
        is_peak = self._is_peak(central_idx)
        is_trough = self._is_trough(central_idx)
        
        # Ignore if both peak and trough or neither
        if (is_peak and is_trough) or not (is_peak or is_trough):
            return
        
        # Check threshold requirements
        if is_peak and not self._meets_peak_threshold(central_high):
            return
        if is_trough and not self._meets_trough_threshold(central_low):
            return
        
        # Handle consecutive same-type turns
        if is_peak:
            if (self._last_turn_type == 'peak' and 
                self._last_peak_value is not None and
                central_high <= self._last_peak_value):
                return  # Ignore lower peak
                
            # Record this peak
            self.lines.high[central_idx] = central_high
            self._last_turn_type = 'peak'
            self._last_peak_value = central_high
        
        elif is_trough:
            if (self._last_turn_type == 'trough' and 
                self._last_trough_value is not None and
                central_low >= self._last_trough_value):
                return  # Ignore higher trough
                
            # Record this trough
            self.lines.low[central_idx] = central_low
            self._last_turn_type = 'trough'
            self._last_trough_value = central_low
    
    def _is_peak(self, central_idx):
        """
        Check if the bar at central_idx is a peak (highest high within space range)
        """
        central_high = self.data.high[central_idx]
        
        # Check bars before central (more negative indices)
        for i in range(1, self.p.space + 1):
            check_idx = central_idx - i
            if abs(check_idx) > len(self):
                continue
            if self.data.high[check_idx] >= central_high:
                return False
        
        # Check bars after central (less negative indices, towards current)
        for i in range(1, self.p.space + 1):
            check_idx = central_idx + i
            if check_idx > 0:
                break  # Don't go beyond current bar
            if self.data.high[check_idx] >= central_high:
                return False
        
        return True
    
    def _is_trough(self, central_idx):
        """
        Check if the bar at central_idx is a trough (lowest low within space range)
        """
        central_low = self.data.low[central_idx]
        
        # Check bars before central (more negative indices)
        for i in range(1, self.p.space + 1):
            check_idx = central_idx - i
            if abs(check_idx) > len(self):
                continue
            if self.data.low[check_idx] <= central_low:
                return False
        
        # Check bars after central (less negative indices, towards current)
        for i in range(1, self.p.space + 1):
            check_idx = central_idx + i
            if check_idx > 0:
                break  # Don't go beyond current bar
            if self.data.low[check_idx] <= central_low:
                return False
        
        return True
    
    def _meets_peak_threshold(self, peak_value):
        """
        Check if peak meets minimum threshold requirement
        """
        if self._last_turn_type != 'trough' or self._last_trough_value is None:
            return True  # No previous trough to compare against
        
        # Calculate percentage change from last trough to this peak
        if self._last_trough_value > 0:
            pct_change = (peak_value - self._last_trough_value) / self._last_trough_value * 100.0
            return pct_change >= self.p.thresh
        
        return True
    
    def _meets_trough_threshold(self, trough_value):
        """
        Check if trough meets minimum threshold requirement
        """
        if self._last_turn_type != 'peak' or self._last_peak_value is None:
            return True  # No previous peak to compare against
        
        # Calculate percentage change from last peak to this trough
        if trough_value > 0:
            pct_change = (self._last_peak_value - trough_value) / trough_value * 100.0
            return pct_change >= self.p.thresh
        
        return True