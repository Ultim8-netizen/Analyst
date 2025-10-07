"""
Data Fetching from Multiple APIs
Place in: /api/utils/fetchers.py
"""
import os
import requests
import time
from datetime import datetime, timedelta

class DataFetcher:
    """Fetch data from multiple sources with rate limiting"""
    
    def __init__(self):
        # API Keys from environment variables
        self.alpha_vantage_key = os.environ.get('ALPHA_VANTAGE_KEY')
        self.polygon_key = os.environ.get('POLYGON_KEY')
        self.eodhd_key = os.environ.get('EODHD_KEY')
        self.newsapi_key = os.environ.get('NEWSAPI_KEY')
        
        # Rate limiting trackers
        self.last_call = {
            'alpha_vantage': 0,
            'polygon': 0,
            'eodhd': 0
        }
        
    def _rate_limit(self, api_name, min_interval):
        """Enforce minimum time between API calls"""
        elapsed = time.time() - self.last_call.get(api_name, 0)
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self.last_call[api_name] = time.time()
    
    # ==================== CRYPTO DATA (Primary: CoinGecko) ====================
    
    def fetch_crypto_price(self, symbol):
        """
        Fetch crypto price from CoinGecko (free, no key required)
        symbol: e.g., 'BTCUSDT', 'ETHUSDT'
        Returns: dict with current price data
        """
        # Map trading symbols to CoinGecko IDs
        coin_map = {
            'BTCUSDT': 'bitcoin',
            'ETHUSDT': 'ethereum',
            'ETCUSDT': 'ethereum-classic',
            'SOLUSDT': 'solana',
            'DOGEUSDT': 'dogecoin'
        }
        
        coin_id = coin_map.get(symbol)
        if not coin_id:
            raise ValueError(f"Unknown crypto symbol: {symbol}")
        
        try:
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            coin_data = data.get(coin_id, {})
            
            if not coin_data:
                raise ValueError(f"No data returned for {symbol}")
            
            return {
                'symbol': symbol,
                'type': 'crypto',
                'price': coin_data.get('usd', 0),
                'change_24h': coin_data.get('usd_24h_change', 0),
                'volume': coin_data.get('usd_24h_vol', 0),
                'timestamp': datetime.utcnow(),
                'source': 'coingecko'
            }
            
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return None
    
    def fetch_crypto_history(self, symbol, days=7):
        """
        Fetch historical crypto data from CoinGecko
        Returns: list of OHLCV dicts
        """
        coin_map = {
            'BTCUSDT': 'bitcoin',
            'ETHUSDT': 'ethereum',
            'ETCUSDT': 'ethereum-classic',
            'SOLUSDT': 'solana',
            'DOGEUSDT': 'dogecoin'
        }
        
        coin_id = coin_map.get(symbol)
        if not coin_id:
            return []
        
        try:
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc"
            params = {
                'vs_currency': 'usd',
                'days': days
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # Convert to standard OHLCV format
            history = []
            for candle in data:
                history.append({
                    'symbol': symbol,
                    'timestamp': datetime.fromtimestamp(candle[0] / 1000),
                    'open': candle[1],
                    'high': candle[2],
                    'low': candle[3],
                    'close': candle[4],
                    'volume': 0  # CoinGecko OHLC doesn't include volume
                })
            
            return history
            
        except Exception as e:
            print(f"Error fetching {symbol} history: {e}")
            return []
    
    # ==================== FOREX DATA ====================
    
    def fetch_forex_polygon(self, pair):
        """
        Fetch forex data from Polygon (5 calls/min free tier)
        pair: e.g., 'EURUSD', 'GBPUSD'
        """
        if not self.polygon_key:
            return None
        
        self._rate_limit('polygon', 12)  # 5 per minute = 12 sec spacing
        
        try:
            # Get previous day's close for comparison
            yesterday = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            # Polygon format: C:EURUSD
            ticker = f"C:{pair}"
            
            url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/hour/{yesterday}/{yesterday}"
            params = {'apiKey': self.polygon_key}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('resultsCount', 0) > 0:
                results = data['results']
                latest = results[-1]
                
                # Calculate 24h change (comparing to first candle of previous day)
                first_price = results[0]['o']
                current_price = latest['c']
                change = ((current_price - first_price) / first_price) * 100
                
                return {
                    'symbol': pair,
                    'type': 'forex',
                    'price': latest['c'],
                    'change_24h': change,
                    'volume': latest.get('v', 0),
                    'timestamp': datetime.utcnow(),
                    'source': 'polygon'
                }
            
            return None
            
        except Exception as e:
            print(f"Polygon error for {pair}: {e}")
            return None
    
    def fetch_forex_eodhd(self, pair):
        """
        Fetch forex data from EODHD (20 calls/day)
        pair: e.g., 'EURUSD', 'GBPUSD'
        """
        if not self.eodhd_key:
            return None
        
        self._rate_limit('eodhd', 5)
        
        try:
            # EODHD format: EURUSD.FOREX
            ticker = f"{pair}.FOREX"
            
            url = f"https://eodhistoricaldata.com/api/real-time/{ticker}"
            params = {'api_token': self.eodhd_key, 'fmt': 'json'}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'code' in data:
                return {
                    'symbol': pair,
                    'type': 'forex',
                    'price': data.get('close', 0),
                    'change_24h': data.get('change_p', 0),
                    'volume': 0,  # EODHD real-time doesn't include volume
                    'timestamp': datetime.utcnow(),
                    'source': 'eodhd'
                }
            
            return None
            
        except Exception as e:
            print(f"EODHD error for {pair}: {e}")
            return None
    
    def fetch_forex_alphavantage(self, pair):
        """
        Fetch forex data from Alpha Vantage (25 calls/day, fallback)
        pair: e.g., 'EURUSD', 'GBPUSD'
        """
        if not self.alpha_vantage_key:
            return None
        
        self._rate_limit('alpha_vantage', 13)  # 5 per minute
        
        try:
            from_currency = pair[:3]
            to_currency = pair[3:]
            
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'CURRENCY_EXCHANGE_RATE',
                'from_currency': from_currency,
                'to_currency': to_currency,
                'apikey': self.alpha_vantage_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'Realtime Currency Exchange Rate' in data:
                rate_data = data['Realtime Currency Exchange Rate']
                
                return {
                    'symbol': pair,
                    'type': 'forex',
                    'price': float(rate_data.get('5. Exchange Rate', 0)),
                    'change_24h': 0,  # Alpha Vantage doesn't provide 24h change in this endpoint
                    'volume': 0,
                    'timestamp': datetime.utcnow(),
                    'source': 'alphavantage'
                }
            
            return None
            
        except Exception as e:
            print(f"Alpha Vantage error for {pair}: {e}")
            return None
    
    def fetch_forex_price(self, pair):
        """
        Fetch forex with fallback strategy
        Priority: Polygon > EODHD > Alpha Vantage
        """
        # Try Polygon first (best for real-time)
        data = self.fetch_forex_polygon(pair)
        if data:
            return data
        
        # Try EODHD
        data = self.fetch_forex_eodhd(pair)
        if data:
            return data
        
        # Fallback to Alpha Vantage
        data = self.fetch_forex_alphavantage(pair)
        if data:
            return data
        
        return None
    
    def fetch_forex_history_eodhd(self, pair, days=7):
        """
        Fetch historical forex data from EODHD
        Returns: list of OHLCV dicts
        """
        if not self.eodhd_key:
            return []
        
        self._rate_limit('eodhd', 5)
        
        try:
            ticker = f"{pair}.FOREX"
            end_date = datetime.utcnow().strftime('%Y-%m-%d')
            start_date = (datetime.utcnow() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            url = f"https://eodhistoricaldata.com/api/eod/{ticker}"
            params = {
                'api_token': self.eodhd_key,
                'from': start_date,
                'to': end_date,
                'period': 'h',  # Hourly data
                'fmt': 'json'
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            history = []
            for candle in data:
                history.append({
                    'symbol': pair,
                    'timestamp': datetime.strptime(candle['date'], '%Y-%m-%d %H:%M:%S'),
                    'open': candle['open'],
                    'high': candle['high'],
                    'low': candle['low'],
                    'close': candle['close'],
                    'volume': candle.get('volume', 0)
                })
            
            return history
            
        except Exception as e:
            print(f"Error fetching {pair} history: {e}")
            return []
    
    # ==================== NEWS DATA ====================
    
    def fetch_market_news(self):
        """
        Fetch recent market news from NewsAPI
        Returns: list of news articles
        """
        if not self.newsapi_key:
            return []
        
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': 'forex OR cryptocurrency OR bitcoin OR trading',
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': 20,
                'apiKey': self.newsapi_key
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'ok':
                articles = []
                for article in data.get('articles', []):
                    articles.append({
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'source': article.get('source', {}).get('name', 'Unknown'),
                        'url': article.get('url', ''),
                        'published_at': datetime.strptime(
                            article['publishedAt'], 
                            '%Y-%m-%dT%H:%M:%SZ'
                        ) if article.get('publishedAt') else datetime.utcnow(),
                        'content': article.get('content', '')
                    })
                
                return articles
            
            return []
            
        except Exception as e:
            print(f"Error fetching news: {e}")
            return []
    
    def analyze_news_relevance(self, article, trading_pairs):
        """
        Determine which trading pairs are relevant to a news article
        Returns: list of relevant pair symbols
        """
        text = f"{article.get('title', '')} {article.get('description', '')}".lower()
        
        relevant_pairs = []
        
        # Keyword mapping
        keywords = {
            'BTCUSDT': ['bitcoin', 'btc'],
            'ETHUSDT': ['ethereum', 'eth'],
            'ETCUSDT': ['ethereum classic', 'etc'],
            'SOLUSDT': ['solana', 'sol'],
            'DOGEUSDT': ['dogecoin', 'doge'],
            'EURUSD': ['euro', 'eur', 'european', 'ecb'],
            'GBPUSD': ['pound', 'sterling', 'gbp', 'uk', 'britain'],
            'USDJPY': ['yen', 'jpy', 'japan', 'boj'],
            'GBPJPY': ['pound', 'yen', 'gbp', 'jpy'],
            'AUDUSD': ['aussie', 'aud', 'australia', 'rba'],
            'USDCAD': ['loonie', 'cad', 'canada', 'boc']
        }
        
        for pair, terms in keywords.items():
            if any(term in text for term in terms):
                relevant_pairs.append(pair)
        
        # If no specific pairs found but mentions crypto/forex generally
        if not relevant_pairs:
            if 'crypto' in text or 'bitcoin' in text:
                relevant_pairs = ['BTCUSDT', 'ETHUSDT']
            elif 'forex' in text or 'dollar' in text:
                relevant_pairs = ['EURUSD', 'GBPUSD']
        
        return relevant_pairs
    
    def calculate_sentiment(self, article):
        """
        Simple sentiment analysis using keyword matching
        Returns: float from -1 (negative) to 1 (positive)
        """
        text = f"{article.get('title', '')} {article.get('description', '')}".lower()
        
        positive_words = [
            'surge', 'rally', 'gain', 'rise', 'bullish', 'boom', 'growth',
            'profit', 'positive', 'up', 'strong', 'optimistic', 'recovery'
        ]
        
        negative_words = [
            'crash', 'fall', 'drop', 'decline', 'bearish', 'loss', 'weak',
            'negative', 'down', 'risk', 'concern', 'warning', 'crisis'
        ]
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        total = positive_count + negative_count
        
        if total == 0:
            return 0
        
        sentiment = (positive_count - negative_count) / total
        
        return round(sentiment, 2)
    
    def calculate_impact_score(self, article, relevant_pairs):
        """
        Calculate news impact score (0-10)
        Based on source credibility and relevance
        """
        score = 5  # Base score
        
        # Source credibility boost
        credible_sources = [
            'reuters', 'bloomberg', 'financial times', 'wall street journal',
            'cnbc', 'marketwatch', 'forbes', 'coindesk'
        ]
        
        source = article.get('source', '').lower()
        if any(cs in source for cs in credible_sources):
            score += 2
        
        # Relevance boost
        if len(relevant_pairs) > 2:
            score += 1
        
        # Recency boost
        published = article.get('published_at')
        if published:
            hours_old = (datetime.utcnow() - published).total_seconds() / 3600
            if hours_old < 6:
                score += 2
            elif hours_old < 24:
                score += 1
        
        return min(score, 10)