"""
Technical Analysis Calculations
Place in: /api/utils/technical.py
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

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
        
        return rsi.iloc[-1]
    
    def calculate_macd(self, fast=12, slow=26, signal=9):
        """Calculate MACD (Moving Average Convergence Divergence)"""
        exp1 = self.df['close'].ewm(span=fast, adjust=False).mean()
        exp2 = self.df['close'].ewm(span=slow, adjust=False).mean()
        
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': round(macd_line.iloc[-1], 6),
            'signal': round(signal_line.iloc[-1], 6),
            'histogram': round(histogram.iloc[-1], 6),
            'trend': 'bullish' if histogram.iloc[-1] > 0 else 'bearish'
        }
    
    def calculate_bollinger_bands(self, period=20, std_dev=2):
        """Calculate Bollinger Bands"""
        sma = self.df['close'].rolling(window=period).mean()
        std = self.df['close'].rolling(window=period).std()
        
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        
        current_price = self.df['close'].iloc[-1]
        
        return {
            'upper': round(upper.iloc[-1], 6),
            'middle': round(sma.iloc[-1], 6),
            'lower': round(lower.iloc[-1], 6),
            'position': self._bb_position(current_price, upper.iloc[-1], lower.iloc[-1])
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
        
        return round(atr.iloc[-1], 6)
    
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
        
        current_price = self.df['close'].iloc[-1]
        
        # Get nearest support and resistance
        support = max([s for s in support_levels if s < current_price], default=current_price * 0.97)
        resistance = min([r for r in resistance_levels if r > current_price], default=current_price * 1.03)
        
        return {
            'support': round(support, 6),
            'resistance': round(resistance, 6)
        }
    
    def calculate_ema(self, period=20):
        """Calculate Exponential Moving Average"""
        ema = self.df['close'].ewm(span=period, adjust=False).mean()
        return round(ema.iloc[-1], 6)
    
    def get_trend(self):
        """Determine overall trend using multiple EMAs"""
        if len(self.df) < 50:
            return 'insufficient_data'
        
        ema_20 = self.calculate_ema(20)
        ema_50 = self.calculate_ema(50)
        current_price = self.df['close'].iloc[-1]
        
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
        
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
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
        
        current = self.df['close'].iloc[-1]
        previous = self.df['close'].iloc[-(periods + 1)]
        
        change = ((current - previous) / previous) * 100
        
        return round(change, 2)


class SignalGenerator:
    """Generate trading signals based on technical analysis"""
    
    def __init__(self, technical_data, current_price):
        """
        Initialize with technical indicators
        technical_data: dict containing RSI, MACD, BB, ATR, support/resistance
        current_price: current market price
        """
        self.tech = technical_data
        self.price = current_price
    
    def calculate_position_size(self, account_risk=5, account_balance=100, lot_size=0.01):
        """
        Calculate position parameters for $5 max risk
        
        For forex: 0.01 lot = 1000 units
        For crypto: Using USDT value directly
        """
        atr = self.tech['atr']
        
        # Stop loss at 1.5 x ATR (reasonable for 4hr timeframe)
        sl_distance = atr * 1.5
        
        # Risk-reward ratio of 2:1 minimum
        tp_distance = sl_distance * 2.5
        
        return {
            'sl_distance': round(sl_distance, 6),
            'tp_distance': round(tp_distance, 6),
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
        rsi = self.tech['rsi']
        if rsi < 30:
            signals.append('LONG')
            confidence_factors.append(25)  # Oversold
        elif rsi > 70:
            signals.append('SHORT')
            confidence_factors.append(25)  # Overbought
        elif 40 < rsi < 60:
            confidence_factors.append(10)  # Neutral is weak signal
        
        # MACD Signal
        macd = self.tech['macd']
        if macd['trend'] == 'bullish' and macd['histogram'] > 0:
            signals.append('LONG')
            confidence_factors.append(20)
        elif macd['trend'] == 'bearish' and macd['histogram'] < 0:
            signals.append('SHORT')
            confidence_factors.append(20)
        
        # Bollinger Bands
        bb = self.tech['bollinger_bands']
        if bb['position'] == 'oversold':
            signals.append('LONG')
            confidence_factors.append(15)
        elif bb['position'] == 'overbought':
            signals.append('SHORT')
            confidence_factors.append(15)
        
        # Support/Resistance
        sr = self.tech['support_resistance']
        if self.price <= sr['support'] * 1.01:  # Near support
            signals.append('LONG')
            confidence_factors.append(20)
        elif self.price >= sr['resistance'] * 0.99:  # Near resistance
            signals.append('SHORT')
            confidence_factors.append(20)
        
        # Trend alignment
        trend = self.tech['trend']
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
        
        risk_reward = position['tp_distance'] / position['sl_distance']
        
        return {
            'direction': direction,
            'confidence': round(confidence, 1),
            'entry': round(entry, 6),
            'tp': round(tp, 6),
            'sl': round(sl, 6),
            'risk_reward': round(risk_reward, 2),
            'atr': self.tech['atr']
        }