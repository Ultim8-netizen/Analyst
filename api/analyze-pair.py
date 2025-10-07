"""
Analyze Individual Trading Pair
Place in: /api/analyze-pair.py

This is a Vercel serverless function that analyzes a single trading pair
"""
from http.server import BaseHTTPRequestHandler
import json
import sys
import os
from datetime import datetime

# Add utils directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from database import get_db
from fetchers import DataFetcher
from technical import TechnicalAnalyzer, SignalGenerator


class handler(BaseHTTPRequestHandler):
    """Vercel serverless function handler"""
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            # Parse query parameters
            query = self._parse_query()
            symbol = query.get('symbol')
            
            if not symbol:
                self._send_error(400, 'Missing symbol parameter')
                return
            
            # Validate symbol
            valid_symbols = [
                'BTCUSDT', 'ETHUSDT', 'ETCUSDT', 'SOLUSDT', 'DOGEUSDT',
                'EURUSD', 'GBPUSD', 'USDJPY', 'GBPJPY', 'AUDUSD', 'USDCAD'
            ]
            
            if symbol not in valid_symbols:
                self._send_error(400, f'Invalid symbol: {symbol}')
                return
            
            # Fetch and analyze
            result = self._analyze_pair(symbol)
            
            if result:
                self._send_response(200, result)
            else:
                self._send_error(500, 'Failed to analyze pair')
                
        except Exception as e:
            self._send_error(500, f'Error: {str(e)}')
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            # Read POST data
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            symbol = data.get('symbol')
            
            if not symbol:
                self._send_error(400, 'Missing symbol in request body')
                return
            
            result = self._analyze_pair(symbol)
            
            if result:
                self._send_response(200, result)
            else:
                self._send_error(500, 'Failed to analyze pair')
                
        except Exception as e:
            self._send_error(500, f'Error: {str(e)}')
    
    def _analyze_pair(self, symbol):
        """Core analysis logic"""
        try:
            # Initialize components
            fetcher = DataFetcher()
            db = get_db()
            
            if not db:
                return {'error': 'Database connection failed'}
            
            # Determine pair type
            pair_type = 'crypto' if 'USDT' in symbol else 'forex'
            
            # Fetch current price
            if pair_type == 'crypto':
                price_data = fetcher.fetch_crypto_price(symbol)
                history = fetcher.fetch_crypto_history(symbol, days=7)
            else:
                price_data = fetcher.fetch_forex_price(symbol)
                history = fetcher.fetch_forex_history_eodhd(symbol, days=7)
            
            if not price_data:
                db.close()
                return {'error': f'Failed to fetch price data for {symbol}'}
            
            # If no history available, try from database
            if not history or len(history) < 14:
                history = db.get_price_history(symbol, hours=168)
            
            # Need at least 14 data points for technical analysis
            if not history or len(history) < 14:
                # Store current price and return basic data
                basic_result = {
                    'symbol': symbol,
                    'type': pair_type,
                    'price': price_data['price'],
                    'change_24h': price_data.get('change_24h', 0),
                    'volume': price_data.get('volume', 0),
                    'technical': None,
                    'signal': {
                        'direction': 'INSUFFICIENT_DATA',
                        'confidence': 0,
                        'entry': price_data['price'],
                        'tp': price_data['price'] * 1.02,
                        'sl': price_data['price'] * 0.98,
                        'risk_reward': 2.0
                    },
                    'timestamp': datetime.utcnow()
                }
                
                db.save_pair_analysis(basic_result)
                db.close()
                return basic_result
            
            # Save current price to history
            current_candle = {
                'symbol': symbol,
                'timestamp': datetime.utcnow(),
                'open': price_data['price'],
                'high': price_data['price'],
                'low': price_data['price'],
                'close': price_data['price'],
                'volume': price_data.get('volume', 0)
            }
            db.save_price_history(symbol, current_candle)
            
            # Perform technical analysis
            analyzer = TechnicalAnalyzer(history)
            
            rsi = analyzer.calculate_rsi()
            macd = analyzer.calculate_macd()
            bb = analyzer.calculate_bollinger_bands()
            atr = analyzer.calculate_atr()
            sr = analyzer.find_support_resistance()
            trend = analyzer.get_trend()
            volume = analyzer.calculate_volume_analysis()
            
            technical_data = {
                'rsi': rsi,
                'macd': macd,
                'bollinger_bands': bb,
                'atr': atr,
                'support_resistance': sr,
                'trend': trend,
                'volume': volume
            }
            
            # Generate trading signal
            signal_gen = SignalGenerator(technical_data, price_data['price'])
            signal = signal_gen.generate_signal()
            
            # Compile full analysis
            full_analysis = {
                'symbol': symbol,
                'type': pair_type,
                'price': price_data['price'],
                'change_24h': price_data.get('change_24h', 0),
                'volume': price_data.get('volume', 0),
                'technical': technical_data,
                'signal': signal,
                'timestamp': datetime.utcnow(),
                'source': price_data.get('source', 'unknown')
            }
            
            # Save to database
            db.save_pair_analysis(full_analysis)
            
            # Get relevant news
            news = db.get_pair_news(symbol, hours=24)
            full_analysis['news'] = news[:5] if news else []
            
            db.close()
            
            return full_analysis
            
        except Exception as e:
            print(f"Error analyzing {symbol}: {str(e)}")
            return {'error': str(e)}
    
    def _parse_query(self):
        """Parse URL query parameters"""
        from urllib.parse import urlparse, parse_qs
        
        parsed = urlparse(self.path)
        query_params = parse_qs(parsed.query)
        
        # Convert lists to single values
        return {k: v[0] if len(v) == 1 else v for k, v in query_params.items()}
    
    def _send_response(self, status_code, data):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        # Convert datetime objects to strings
        response = json.dumps(data, default=str)
        self.wfile.write(response.encode())
    
    def _send_error(self, status_code, message):
        """Send error response"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        error_response = json.dumps({'error': message})
        self.wfile.write(error_response.encode())
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()