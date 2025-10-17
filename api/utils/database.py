"""
MongoDB Connection and Database Utilities
Place in: /api/utils/database.py
"""
import os
from datetime import datetime, timedelta
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure

class TradingDatabase:
    def __init__(self):
        # MongoDB connection string from environment variable
        self.connection_string = os.environ.get('MONGODB_URI')
        self.client = None
        self.db = None
        
    def connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(
                self.connection_string,
                serverSelectionTimeoutMS=5000,
                maxPoolSize=10
            )
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client['trading_intelligence']
            return True
        except ConnectionFailure as e:
            print(f"MongoDB connection failed: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
    
    # ==================== PAIRS COLLECTION ====================
    
    def save_pair_analysis(self, pair_data):
        """
        Save or update analysis for a trading pair
        pair_data structure:
        {
            'symbol': 'BTCUSDT',
            'type': 'crypto' or 'forex',
            'price': float,
            'change_24h': float,
            'volume': float,
            'technical': {
                'rsi': float,
                'macd': dict,
                'bb': dict,
                'support': float,
                'resistance': float
            },
            'signal': {
                'direction': 'LONG' or 'SHORT',
                'confidence': float (0-100),
                'entry': float,
                'tp': float,
                'sl': float,
                'risk_reward': float
            },
            'timestamp': datetime
        }
        """
        collection = self.db['pairs_analysis']
        
        pair_data['updated_at'] = datetime.utcnow()
        
        # Upsert: update if exists, insert if new
        collection.update_one(
            {'symbol': pair_data['symbol']},
            {'$set': pair_data},
            upsert=True
        )
        
    def get_pair_analysis(self, symbol):
        """Get latest analysis for a specific pair"""
        collection = self.db['pairs_analysis']
        return collection.find_one({'symbol': symbol})
    
    def get_all_pairs(self, pair_type=None):
        """Get all pairs or filter by type (crypto/forex)"""
        collection = self.db['pairs_analysis']
        
        query = {}
        if pair_type:
            query['type'] = pair_type
        
        return list(collection.find(query).sort('symbol', ASCENDING))
    
    def get_high_confidence_signals(self, min_confidence=75):
        """Get pairs with high confidence signals"""
        collection = self.db['pairs_analysis']
        
        return list(collection.find({
            'signal.confidence': {'$gte': min_confidence}
        }).sort('signal.confidence', DESCENDING))
    
    # ==================== HISTORICAL PRICES ====================
    
    def save_price_history(self, symbol, price_data):
        """
        Save historical price point
        price_data structure:
        {
            'symbol': 'BTCUSDT',
            'timestamp': datetime,
            'open': float,
            'high': float,
            'low': float,
            'close': float,
            'volume': float
        }
        """
        collection = self.db['price_history']
        
        # Avoid duplicates
        existing = collection.find_one({
            'symbol': symbol,
            'timestamp': price_data['timestamp']
        })
        
        if not existing:
            collection.insert_one(price_data)
    
    def get_price_history(self, symbol, hours=168):
        """
        Get historical prices for a symbol
        Default: 168 hours (7 days)
        """
        collection = self.db['price_history']
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return list(collection.find({
            'symbol': symbol,
            'timestamp': {'$gte': cutoff_time}
        }).sort('timestamp', ASCENDING))
    
    def cleanup_old_prices(self, days_to_keep=30):
        """Remove price data older than specified days"""
        collection = self.db['price_history']
        
        cutoff_time = datetime.utcnow() - timedelta(days=days_to_keep)
        
        result = collection.delete_many({
            'timestamp': {'$lt': cutoff_time}
        })
        
        return result.deleted_count
    
    # ==================== NEWS COLLECTION ====================
    
    def save_news(self, news_data):
        """
        Save news article with pair relevance
        news_data structure:
        {
            'title': str,
            'source': str,
            'published_at': datetime,
            'sentiment': float (-1 to 1),
            'relevant_pairs': ['BTCUSDT', 'EURUSD'],
            'impact_score': float (0-10)
        }
        """
        collection = self.db['news']
        
        # Avoid duplicate articles
        existing = collection.find_one({
            'title': news_data['title'],
            'source': news_data['source']
        })
        
        if not existing:
            news_data['created_at'] = datetime.utcnow()
            collection.insert_one(news_data)
    
    def get_pair_news(self, symbol, hours=24):
        """Get news relevant to a specific pair"""
        collection = self.db['news']
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return list(collection.find({
            'relevant_pairs': symbol,
            'published_at': {'$gte': cutoff_time}
        }).sort('impact_score', DESCENDING).limit(10))
    
    def get_recent_news(self, hours=24, limit=20):
        """Get all recent news - returns most recent articles regardless of age"""
        collection = self.db['news']
        
        # Simply get the most recent articles by published_at date
        # This ensures we always return articles if they exist, without filtering by cutoff time
        results = list(collection.find({}).sort('published_at', DESCENDING).limit(limit))
        
        return results
    
    def cleanup_old_news(self, days_to_keep=7):
        """Remove news older than specified days"""
        collection = self.db['news']
        
        cutoff_time = datetime.utcnow() - timedelta(days=days_to_keep)
        
        result = collection.delete_many({
            'published_at': {'$lt': cutoff_time}
        })
        
        return result.deleted_count
    
    # ==================== SYSTEM METADATA ====================
    
    def update_last_run(self, task_name):
        """Record when a task last ran"""
        collection = self.db['system_metadata']
        
        collection.update_one(
            {'task': task_name},
            {'$set': {
                'task': task_name,
                'last_run': datetime.utcnow()
            }},
            upsert=True
        )
    
    def get_last_run(self, task_name):
        """Get when a task last ran"""
        collection = self.db['system_metadata']
        
        record = collection.find_one({'task': task_name})
        
        return record['last_run'] if record else None
    
    def get_system_stats(self):
        """Get overview statistics"""
        stats = {
            'total_pairs': self.db['pairs_analysis'].count_documents({}),
            'crypto_pairs': self.db['pairs_analysis'].count_documents({'type': 'crypto'}),
            'forex_pairs': self.db['pairs_analysis'].count_documents({'type': 'forex'}),
            'high_confidence_signals': self.db['pairs_analysis'].count_documents({
                'signal.confidence': {'$gte': 75}
            }),
            'news_articles': self.db['news'].count_documents({}),
            'price_points': self.db['price_history'].count_documents({}),
            'last_update': None
        }
        
        # Get most recent update
        latest = self.db['pairs_analysis'].find_one(
            sort=[('updated_at', DESCENDING)]
        )
        
        if latest and 'updated_at' in latest:
            stats['last_update'] = latest['updated_at']
        
        return stats


# Helper function for serverless functions
def get_db():
    """Get database instance with connection"""
    db = TradingDatabase()
    if db.connect():
        return db
    return None
