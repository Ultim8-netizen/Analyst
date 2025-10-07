"""
Fetch and Process Market News
Place in: /api/fetch-news.py
"""
from http.server import BaseHTTPRequestHandler
import json
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from database import get_db
from fetchers import DataFetcher


class handler(BaseHTTPRequestHandler):
    """News fetching serverless function"""
    
    def do_GET(self):
        """Fetch and process news"""
        try:
            fetcher = DataFetcher()
            db = get_db()
            
            if not db:
                self._send_error(500, 'Database connection failed')
                return
            
            # Define trading pairs
            trading_pairs = [
                'BTCUSDT', 'ETHUSDT', 'ETCUSDT', 'SOLUSDT', 'DOGEUSDT',
                'EURUSD', 'GBPUSD', 'USDJPY', 'GBPJPY', 'AUDUSD', 'USDCAD'
            ]
            
            # Fetch news articles
            articles = fetcher.fetch_market_news()
            
            if not articles:
                self._send_response(200, {
                    'success': False,
                    'message': 'No news articles fetched',
                    'count': 0
                })
                return
            
            # Process each article
            processed_count = 0
            for article in articles:
                # Determine relevant pairs
                relevant_pairs = fetcher.analyze_news_relevance(article, trading_pairs)
                
                # Calculate sentiment and impact
                sentiment = fetcher.calculate_sentiment(article)
                impact_score = fetcher.calculate_impact_score(article, relevant_pairs)
                
                # Save to database
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
                processed_count += 1
            
            # Clean up old news (keep last 7 days)
            deleted = db.cleanup_old_news(days_to_keep=7)
            
            db.close()
            
            self._send_response(200, {
                'success': True,
                'processed': processed_count,
                'deleted_old': deleted,
                'message': f'Successfully processed {processed_count} news articles'
            })
            
        except Exception as e:
            self._send_error(500, f'Error: {str(e)}')
    
    def do_POST(self):
        """Get news for specific pair"""
        try:
            # Read POST data
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            symbol = data.get('symbol')
            hours = data.get('hours', 24)
            
            if not symbol:
                self._send_error(400, 'Missing symbol in request')
                return
            
            db = get_db()
            if not db:
                self._send_error(500, 'Database connection failed')
                return
            
            # Get pair-specific news
            news = db.get_pair_news(symbol, hours=hours)
            
            db.close()
            
            self._send_response(200, {
                'symbol': symbol,
                'count': len(news),
                'news': news
            })
            
        except Exception as e:
            self._send_error(500, f'Error: {str(e)}')
    
    def _send_response(self, status_code, data):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
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
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()