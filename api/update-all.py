"""
Bulk Update All Trading Pairs
Place in: /api/update-all.py

This endpoint is called by GitHub Actions to update all pairs periodically
"""
from http.server import BaseHTTPRequestHandler
import json
import sys
import os
import time
import math
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from database import get_db
from fetchers import DataFetcher
from technical import TechnicalAnalyzer, SignalGenerator


def clean_nan_from_dict(obj):
    """Recursively clean NaN values from dictionaries"""
    if isinstance(obj, dict):
        return {k: clean_nan_from_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan_from_dict(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0.0
        return obj
    return obj


class handler(BaseHTTPRequestHandler):
    """Bulk update serverless function"""
    
    def do_POST(self):
        """Update all trading pairs"""
        try:
            # Verify authorization (simple secret key)
            auth_header = self.headers.get('Authorization', '')
            expected_key = os.environ.get('UPDATE_SECRET_KEY', 'default-secret')
            
            if f'Bearer {expected_key}' != auth_header:
                self._send_error(401, 'Unauthorized')
                return
            
            # Initialize
            fetcher = DataFetcher()
            db = get_db()
            
            if not db:
                self._send_error(500, 'Database connection failed')
                return
            
            # Define all pairs
            crypto_pairs = ['BTCUSDT', 'ETHUSDT', 'ETCUSDT', 'SOLUSDT', 'DOGEUSDT']
            forex_pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'GBPJPY', 'AUDUSD', 'USDCAD']
            
            results = {
                'timestamp': datetime.utcnow(),
                'crypto': {'success': 0, 'failed': 0, 'pairs': []},
                'forex': {'success': 0, 'failed': 0, 'pairs': []},
                'news': {'processed': 0}
            }
            
            # Process crypto pairs
            for symbol in crypto_pairs:
                try:
                    result = self._analyze_pair(symbol, 'crypto', fetcher, db)
                    if result['success']:
                        results['crypto']['success'] += 1
                        results['crypto']['pairs'].append({
                            'symbol': symbol,
                            'status': 'success',
                            'confidence': result.get('confidence', 0)
                        })
                    else:
                        results['crypto']['failed'] += 1
                        results['crypto']['pairs'].append({
                            'symbol': symbol,
                            'status': 'failed',
                            'error': result.get('error', 'Unknown error')
                        })
                    
                    time.sleep(2)  # Rate limiting
                    
                except Exception as e:
                    results['crypto']['failed'] += 1
                    results['crypto']['pairs'].append({
                        'symbol': symbol,
                        'status': 'failed',
                        'error': str(e)
                    })
            
            # Process forex pairs
            for symbol in forex_pairs:
                try:
                    result = self._analyze_pair(symbol, 'forex', fetcher, db)
                    if result['success']:
                        results['forex']['success'] += 1
                        results['forex']['pairs'].append({
                            'symbol': symbol,
                            'status': 'success',
                            'confidence': result.get('confidence', 0)
                        })
                    else:
                        results['forex']['failed'] += 1
                        results['forex']['pairs'].append({
                            'symbol': symbol,
                            'status': 'failed',
                            'error': result.get('error', 'Unknown error')
                        })
                    
                    time.sleep(3)  # Longer delay for forex (API limits)
                    
                except Exception as e:
                    results['forex']['failed'] += 1
                    results['forex']['pairs'].append({
                        'symbol': symbol,
                        'status': 'failed',
                        'error': str(e)
                    })
            
            # Fetch and process news
            try:
                articles = fetcher.fetch_market_news()
                all_pairs = crypto_pairs + forex_pairs
                
                for article in articles:
                    relevant_pairs = fetcher.analyze_news_relevance(article, all_pairs)
                    sentiment = fetcher.calculate_sentiment(article)
                    impact_score = fetcher.calculate_impact_score(article, relevant_pairs)
                    
                    news_data = {
                        'title': article['title'],
                        'source': article['source'],
                        'url': article.get('url', ''),
                        'published_at': article['published_at'],
                        'sentiment': sentiment,
                        'relevant_pairs': relevant_pairs,
                        'impact_score': impact_score
                    }
                    
                    db.save_news(news_data)
                    results['news']['processed'] += 1
                    
            except Exception as e:
                results['news']['error'] = str(e)
            
            # Cleanup old data
            deleted_prices = db.cleanup_old_prices(days_to_keep=30)
            deleted_news = db.cleanup_old_news(days_to_keep=7)
            
            results['cleanup'] = {
                'deleted_prices': deleted_prices,
                'deleted_news': deleted_news
            }
            
            # Update system metadata
            db.update_last_run('bulk_update')
            
            # Get system stats
            results['stats'] = db.get_system_stats()
            
            db.close()
            
            self._send_response(200, results)
            
        except Exception as e:
            self._send_error(500, f'Error: {str(e)}')
    
    def _analyze_pair(self, symbol, pair_type, fetcher, db):
        """Analyze single pair (helper function)"""
        try:
            # Fetch current price
            if pair_type == 'crypto':
                price_data = fetcher.fetch_crypto_price(symbol)
                history = fetcher.fetch_crypto_history(symbol, days=7)
            else:
                price_data = fetcher.fetch_forex_price(symbol)
                history = fetcher.fetch_forex_history_eodhd(symbol, days=7)
            
            if not price_data:
                return {'success': False, 'error': 'Failed to fetch price data'}
            
            # Get or use existing history
            if not history or len(history) < 14:
                history = db.get_price_history(symbol, hours=168)
            
            # Save current price
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
            
            # Check if we have enough data
            if not history or len(history) < 14:
                # Store basic data
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
                
                # Clean NaN values
                basic_result = clean_nan_from_dict(basic_result)
                
                db.save_pair_analysis(basic_result)
                return {'success': True, 'confidence': 0, 'note': 'Insufficient data'}
            
            # Perform technical analysis
            analyzer = TechnicalAnalyzer(history)
            
            technical_data = {
                'rsi': analyzer.calculate_rsi(),
                'macd': analyzer.calculate_macd(),
                'bollinger_bands': analyzer.calculate_bollinger_bands(),
                'atr': analyzer.calculate_atr(),
                'support_resistance': analyzer.find_support_resistance(),
                'trend': analyzer.get_trend(),
                'volume': analyzer.calculate_volume_analysis()
            }
            
            # Generate signal
            signal_gen = SignalGenerator(technical_data, price_data['price'])
            signal = signal_gen.generate_signal()
            
            # Compile and save
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
            
            # Clean NaN values
            full_analysis = clean_nan_from_dict(full_analysis)
            
            db.save_pair_analysis(full_analysis)
            
            return {
                'success': True,
                'confidence': signal['confidence']
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_response(self, status_code, data):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        
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
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
