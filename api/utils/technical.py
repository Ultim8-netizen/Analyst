"""
Technical Analysis Calculations
Place in: /api/utils/technical.py
"""
import numpy as np
import pandas as pd
import math
from datetime import datetime, timedelta


def safe_float(value, default=0.0):
    """Convert value to float, handling NaN and inf"""
    try:
        if value is None:
            return default
        if isinstance(value, (int, float)):
            if math.isnan(value) or math.isinf(value):
                return default
        return float(value)
    except (ValueError, TypeError):
        return default


class TechnicalAnalyzer:
    """Calculate real technical indicators from price history"""
    
    def __init__(self, price_history):
        """
        Initialize with price history from MongoDB
        price_history: list of dicts with keys: timestamp, open, high, low, close, volume
        """
        if not price_history or len(price_history) < 14:
            raise ValueError("Insufficient price data for analysis (need at least 14 periods)")
        
        # Convert to DataFrame for easier manipulation
        self.df = pd.DataFrame(price_history)
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        self.df.sort_values('timestamp', inplace=True)
        self.df.reset_index(drop=True, inplace=True)
        
    def calculate_rsi(self, period=14):
        """Calculate Relative Strength Index"""
        delta = self.df['close'].diff()
        
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        result = rsi.iloc[-1]
        return safe_float(result, 50.0)
    
    def calculate_macd(self, fast=12, slow=26, signal=9):
        """Calculate MACD (Moving Average Convergence Divergence)"""
        exp1 = self.df['close'].ewm(span=fast, adjust=False).mean()
        exp2 = self.df['close'].ewm(span=slow, adjust=False).mean()
        
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        macd_val = safe_float(macd_line.iloc[-1], 0.0)
        signal_val = safe_float(signal_line.iloc[-1], 0.0)
        hist_val = safe_float(histogram.iloc[-1], 0.0)
        
        return {
            'macd': round(macd_val, 6),
            'signal': round(signal_val, 6),
            'histogram': round(hist_val, 6),
            'trend': 'bullish' if hist_val > 0 else 'bearish'
        }
    
    def calculate_bollinger_bands(self, period=20, std_dev=2):
        """Calculate Bollinger Bands"""
        sma = self.df['close'].rolling(window=period).mean()
        std = self.df['close'].rolling(window=period).std()
        
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        
        current_price = safe_float(self.df['close'].iloc[-1], 0.0)
        
        upper_val = safe_float(upper.iloc[-1], current_price * 1.02)
        middle_val = safe_float(sma.iloc[-1], current_price)
        lower_val = safe_float(lower.iloc[-1], current_price * 0.98)
        
        return {
            'upper': round(upper_val, 6),
            'middle': round(middle_val, 6),
            'lower': round(lower_val, 6),
            'position': self._bb_position(current_price, upper_val, lower_val)
        }
    
    def _bb_position(self, price, upper, lower):
        """Determine price position relative to Bollinger Bands"""
        if price >= upper:
            return 'overbought'
        elif price <= lower:
            return 'oversold'
        else:
            return 'neutral'
    
    def calculate_atr(self, period=14):
        """Calculate Average True Range (for volatility and SL/TP)"""
        high = self.df['high']
        low = self.df['low']
        close = self.df['close'].shift(1)
        
        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        result = atr.iloc[-1]
        return safe_float(result, 0.0001)
    
    def find_support_resistance(self, lookback=50):
        """
        Find support and resistance levels using local minima/maxima
        """
        if len(self.df) < lookback:
            lookback = len(self.df)
        
        recent_data = self.df.tail(lookback)
        
        # Find local minima (support)
        support_levels = []
        for i in range(1, len(recent_data) - 1):
            if (recent_data['low'].iloc[i] < recent_data['low'].iloc[i-1] and 
                recent_data['low'].iloc[i] < recent_data['low'].iloc[i+1]):
                support_levels.append(recent_data['low'].iloc[i])
        
        # Find local maxima (resistance)
        resistance_levels = []
        for i in range(1, len(recent_data) - 1):
            if (recent_data['high'].iloc[i] > recent_data['high'].iloc[i-1] and 
                recent_data['high'].iloc[i] > recent_data['high'].iloc[i+1]):
                resistance_levels.append(recent_data['high'].iloc[i])
        
        current_price = safe_float(self.df['close'].iloc[-1], 0.0)
        
        # Get nearest support and resistance
        support = max([s for s in support_levels if s < current_price], default=current_price * 0.97)
        resistance = min([r for r in resistance_levels if r > current_price], default=current_price * 1.03)
        
        return {
            'support': round(safe_float(support, current_price * 0.97), 6),
            'resistance': round(safe_float(resistance, current_price * 1.03), 6)
        }
    
    def calculate_ema(self, period=20):
        """Calculate Exponential Moving Average"""
        ema = self.df['close'].ewm(span=period, adjust=False).mean()
        result = ema.iloc[-1]
        fallback = safe_float(self.df['close'].iloc[-1], 0.0)
        return safe_float(result, fallback)
    
    def get_trend(self):
        """Determine overall trend using multiple EMAs"""
        if len(self.df) < 50:
            return 'insufficient_data'
        
        ema_20 = self.calculate_ema(20)
        ema_50 = self.calculate_ema(50)
        current_price = safe_float(self.df['close'].iloc[-1], 0.0)
        
        # Strong uptrend
        if current_price > ema_20 > ema_50:
            return 'strong_uptrend'
        # Uptrend
        elif current_price > ema_20 or ema_20 > ema_50:
            return 'uptrend'
        # Strong downtrend
        elif current_price < ema_20 < ema_50:
            return 'strong_downtrend'
        # Downtrend
        elif current_price < ema_20 or ema_20 < ema_50:
            return 'downtrend'
        else:
            return 'sideways'
    
    def calculate_volume_analysis(self):
        """Analyze volume patterns"""
        avg_volume = self.df['volume'].tail(20).mean()
        current_volume = self.df['volume'].iloc[-1]
        
        avg_volume = safe_float(avg_volume, 1.0)
        current_volume = safe_float(current_volume, 1.0)
        
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        volume_ratio = safe_float(volume_ratio, 1.0)
        
        return {
            'current': int(current_volume),
            'average': int(avg_volume),
            'ratio': round(volume_ratio, 2),
            'status': 'high' if volume_ratio > 1.5 else 'normal' if volume_ratio > 0.7 else 'low'
        }
    
    def get_price_change(self, periods=24):
        """Calculate price change over specified periods"""
        if len(self.df) < periods:
            periods = len(self.df) - 1
        
        current = safe_float(self.df['close'].iloc[-1], 0.0)
        previous = safe_float(self.df['close'].iloc[-(periods + 1)], current)
        
        if previous == 0:
            return 0.0
        
        change = ((current - previous) / previous) * 100
        
        return safe_float(change, 0.0)


class SignalGenerator:
    """Generate trading signals based on technical analysis"""
    
    def __init__(self, technical_data, current_price):
        """
        Initialize with technical indicators
        technical_data: dict containing RSI, MACD, BB, ATR, support/resistance
        current_price: current market price
        """
        self.tech = technical_data
        self.price = safe_float(current_price, 0.0)
    
    def calculate_position_size(self, account_risk=5, account_balance=100, lot_size=0.01):
        """
        Calculate position parameters for $5 max risk
        
        For forex: 0.01 lot = 1000 units
        For crypto: Using USDT value directly
        """
        atr = safe_float(self.tech.get('atr', 0.0001), 0.0001)
        
        # Stop loss at 1.5 x ATR (reasonable for 4hr timeframe)
        sl_distance = atr * 1.5
        
        # Risk-reward ratio of 2:1 minimum
        tp_distance = sl_distance * 2.5
        
        return {
            'sl_distance': round(safe_float(sl_distance, 0.0001), 6),
            'tp_distance': round(safe_float(tp_distance, 0.0001), 6),
            'risk_amount': account_risk
        }
    
    def generate_signal(self):
        """
        Generate comprehensive trading signal
        Returns: dict with direction, confidence, entry, tp, sl
        """
        signals = []
        confidence_factors = []
        
        # RSI Signal
        rsi = safe_float(self.tech.get('rsi', 50.0), 50.0)
        if rsi < 30:
            signals.append('LONG')
            confidence_factors.append(25)
        elif rsi > 70:
            signals.append('SHORT')
            confidence_factors.append(25)
        elif 40 < rsi < 60:
            confidence_factors.append(10)
        
        # MACD Signal
        macd = self.tech.get('macd', {})
        if macd.get('trend') == 'bullish' and safe_float(macd.get('histogram', 0), 0) > 0:
            signals.append('LONG')
            confidence_factors.append(20)
        elif macd.get('trend') == 'bearish' and safe_float(macd.get('histogram', 0), 0) < 0:
            signals.append('SHORT')
            confidence_factors.append(20)
        
        # Bollinger Bands
        bb = self.tech.get('bollinger_bands', {})
        if bb.get('position') == 'oversold':
            signals.append('LONG')
            confidence_factors.append(15)
        elif bb.get('position') == 'overbought':
            signals.append('SHORT')
            confidence_factors.append(15)
        
        # Support/Resistance
        sr = self.tech.get('support_resistance', {})
        support = safe_float(sr.get('support', self.price * 0.97), self.price * 0.97)
        resistance = safe_float(sr.get('resistance', self.price * 1.03), self.price * 1.03)
        
        if self.price <= support * 1.01:
            signals.append('LONG')
            confidence_factors.append(20)
        elif self.price >= resistance * 0.99:
            signals.append('SHORT')
            confidence_factors.append(20)
        
        # Trend alignment
        trend = self.tech.get('trend', 'sideways')
        if trend in ['strong_uptrend', 'uptrend']:
            signals.append('LONG')
            confidence_factors.append(20)
        elif trend in ['strong_downtrend', 'downtrend']:
            signals.append('SHORT')
            confidence_factors.append(20)
        
        # Determine final signal
        long_count = signals.count('LONG')
        short_count = signals.count('SHORT')
        
        if long_count > short_count:
            direction = 'LONG'
            confidence = min(sum(confidence_factors[:long_count]), 95)
        elif short_count > long_count:
            direction = 'SHORT'
            confidence = min(sum(confidence_factors[:short_count]), 95)
        else:
            direction = 'NEUTRAL'
            confidence = 40
        
        # Calculate entry, TP, SL
        position = self.calculate_position_size()
        
        if direction == 'LONG':
            entry = self.price
            sl = entry - position['sl_distance']
            tp = entry + position['tp_distance']
        elif direction == 'SHORT':
            entry = self.price
            sl = entry + position['sl_distance']
            tp = entry - position['tp_distance']
        else:
            entry = self.price
            sl = entry - position['sl_distance']
            tp = entry + position['tp_distance']
        
        sl_dist = safe_float(position['sl_distance'], 0.0001)
        tp_dist = safe_float(position['tp_distance'], 0.0001)
        risk_reward = tp_dist / sl_dist if sl_dist > 0 else 2.5
        
        return {
            'direction': direction,
            'confidence': round(safe_float(confidence, 0.0), 1),
            'entry': round(safe_float(entry, 0.0), 6),
            'tp': round(safe_float(tp, 0.0), 6),
            'sl': round(safe_float(sl, 0.0), 6),
            'risk_reward': round(safe_float(risk_reward, 2.5), 2),
            'atr': safe_float(self.tech.get('atr', 0.0001), 0.0001)
        }
