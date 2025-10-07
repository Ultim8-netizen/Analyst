"""
Get Analysis Data for Frontend
Place in: /api/get-analysis.py

This endpoint serves pre-computed analysis from MongoDB to the HTML frontend
"""
from http.server import BaseHTTPRequestHandler
import json
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from database import get_db


class handler(BaseHTTPRequestHandler):
    """Serve analysis data"""
    
    def do_GET(self):
        """Get all pairs or specific pair analysis"""
        try:
            query = self._parse_query()
            symbol = query.get('symbol')
            pair_type = query.get('type')  # 'crypto' or 'forex'
            
            db = get_db()
            if not db:
                self._send_error(500, 'Database connection failed')
                return
            
            # Get specific pair
            if symbol:
                analysis = db.get_pair_analysis(symbol)
                if analysis:
                    # Remove MongoDB _id field
                    if '_id' in analysis:
                        del analysis['_id']
                    
                    # Get news for this pair
                    news = db.get_pair_news(symbol, hours=24)
                    analysis['news'] = news[:5]
                    
                    self._send_response(200, analysis)
                else:
                    self._send_error(404, f'No analysis found for {symbol}')
                
                db.close()
                return
            
            # Get all pairs
            pairs = db.get_all_pairs(pair_type=pair_type)
            
            # Clean up MongoDB _id fields
            for pair in pairs:
                if '_id' in pair:
                    del pair['_id']
            
            # Get system stats
            stats = db.get_system_stats()
            
            # Get high confidence signals
            high_conf = db.get_high_confidence_signals(min_confidence=75)
            for pair in high_conf:
                if '_id' in pair:
                    del pair['_id']
            
            db.close()
            
            self._send_response(200, {
                'pairs': pairs,
                'high_confidence': high_conf,
                'stats': stats
            })
            
        except Exception as e:
            self._send_error(500, f'Error: {str(e)}')
    
    def do_POST(self):
        """Get multiple pairs or filtered data"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            symbols = data.get('symbols', [])
            min_confidence = data.get('min_confidence', 0)
            
            db = get_db()
            if not db:
                self._send_error(500, 'Database connection failed')
                return
            
            result = {}
            
            # Get specific symbols if provided
            if symbols:
                result['pairs'] = []
                for symbol in symbols:
                    analysis = db.get_pair_analysis(symbol)
                    if analysis:
                        if '_id' in analysis:
                            del analysis['_id']
                        result['pairs'].append(analysis)
            else:
                # Get all pairs
                all_pairs = db.get_all_pairs()
                for pair in all_pairs:
                    if '_id' in pair:
                        del pair['_id']
                result['pairs'] = all_pairs
            
            # Filter by confidence if specified
            if min_confidence > 0:
                result['pairs'] = [
                    p for p in result['pairs']
                    if p.get('signal', {}).get('confidence', 0) >= min_confidence
                ]
            
            # Get recent news
            recent_news = db.get_recent_news(hours=24, limit=10)
            result['news'] = recent_news
            
            # Get stats
            result['stats'] = db.get_system_stats()
            
            db.close()
            
            self._send_response(200, result)
            
        except Exception as e:
            self._send_error(500, f'Error: {str(e)}')
    
    def _parse_query(self):
        """Parse URL query parameters"""
        from urllib.parse import urlparse, parse_qs
        
        parsed = urlparse(self.path)
        query_params = parse_qs(parsed.query)
        
        return {k: v[0] if len(v) == 1 else v for k, v in query_params.items()}
    
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