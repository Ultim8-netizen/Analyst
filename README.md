# Trading Intelligence System

AI-powered trading analysis system using real technical indicators, pattern recognition, and automated data processing.

## Features

- **Real Technical Analysis**: RSI, MACD, Bollinger Bands, ATR, Support/Resistance
- **Smart Signal Generation**: Confidence-based trading signals (LONG/SHORT/NEUTRAL)
- **Risk Management**: Calculated TP/SL for $5 max risk on 0.01 lots
- **Multi-Timeframe**: Analysis based on 4-hour and 1-hour charts
- **News Integration**: Pair-specific news with sentiment analysis
- **Automated Updates**: GitHub Actions runs analysis every 4 hours
- **11 Trading Pairs**: 5 Crypto + 6 Forex pairs

## Trading Pairs

**Cryptocurrency:**
- BTC/USDT, ETH/USDT, ETC/USDT, SOL/USDT, DOGE/USDT

**Forex:**
- EUR/USD, GBP/USD, USD/JPY, GBP/JPY, AUD/USD, USD/CAD

## Architecture

```
Frontend (GitHub Pages)
    ↓ REST API calls
Backend (Vercel Serverless Functions)
    ↓ Processes & analyzes data
Database (MongoDB Atlas)
    ↑ Stores results
Automation (GitHub Actions)
    ↑ Triggers updates every 4 hours
```

## Technology Stack

**Backend:**
- Python 3.9
- Pandas & NumPy for data processing
- TA-Lib for technical indicators
- PyMongo for database operations
- Vercel serverless functions

**Frontend:**
- Vanilla JavaScript (no frameworks)
- Modern CSS with animations
- Responsive design

**Data Sources:**
- CoinGecko API (cryptocurrency)
- Polygon API (forex)
- EODHD API (forex backup)
- Alpha Vantage API (forex fallback)
- NewsAPI (market news)

**Infrastructure:**
- MongoDB Atlas (database)
- Vercel (serverless hosting)
- GitHub Actions (automation)

## Project Structure

```
├── api/                    # Backend serverless functions
│   ├── utils/              # Shared utilities
│   │   ├── database.py     # MongoDB operations
│   │   ├── technical.py    # Technical analysis
│   │   └── fetchers.py     # API data fetching
│   ├── analyze-pair.py     # Single pair analysis
│   ├── fetch-news.py       # News processing
│   ├── update-all.py       # Bulk update endpoint
│   └── get-analysis.py     # Serve data to frontend
├── .github/workflows/      # GitHub Actions automation
│   └── update-data.yml     # Scheduled update workflow
├── public/                 # Frontend files
│   └── index.html          # Main interface
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules
├── requirements.txt        # Python dependencies
├── vercel.json             # Vercel configuration
└── README.md               # This file
```

## How It Works

### 1. Data Collection
- GitHub Actions triggers every 4 hours
- Calls `/api/update-all` endpoint with authentication
- Fetches current prices from multiple APIs
- Stores historical OHLCV data in MongoDB

### 2. Technical Analysis
- Calculates 14-period RSI
- Computes MACD (12, 26, 9)
- Generates Bollinger Bands (20, 2)
- Finds support/resistance levels
- Calculates Average True Range (ATR)
- Determines trend direction

### 3. Signal Generation
- Combines multiple indicators
- Assigns confidence score (0-100%)
- Generates trading direction (LONG/SHORT/NEUTRAL)
- Calculates entry, TP, SL based on:
  - ATR for volatility
  - 2.5:1 risk/reward ratio
  - $5 maximum risk on 0.01 lots

### 4. News Processing
- Fetches recent market news
- Analyzes sentiment (positive/negative/neutral)
- Matches news to relevant trading pairs
- Assigns impact score (0-10)

### 5. Frontend Display
- Calls `/api/get-analysis` endpoint
- Displays analysis cards for each pair
- Shows technical indicators
- Provides detailed modal on click
- Updates performance metrics

## API Endpoints

### GET `/api/get-analysis`
Returns all trading pairs with analysis

**Response:**
```json
{
  "pairs": [...],
  "high_confidence": [...],
  "stats": {
    "total_pairs": 11,
    "high_confidence_signals": 3,
    "last_update": "2025-09-30T12:00:00Z"
  }
}
```

### GET `/api/get-analysis?symbol=BTCUSDT`
Returns specific pair analysis

### POST `/api/analyze-pair`
Analyze single pair on demand

**Request:**
```json
{
  "symbol": "EURUSD"
}
```

### POST `/api/update-all`
Bulk update all pairs (requires authorization)

**Headers:**
```
Authorization: Bearer your-secret-key
```

### GET `/api/fetch-news`
Fetch and process latest news

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment instructions.

**Quick Start:**
1. Set up MongoDB Atlas
2. Add API keys to Vercel environment variables
3. Push to GitHub
4. Deploy to Vercel
5. Configure GitHub Actions
6. Run first update manually

## Environment Variables

Required in Vercel dashboard:

```
MONGODB_URI=mongodb+srv://...
ALPHA_VANTAGE_KEY=your_key
POLYGON_KEY=your_key
EODHD_KEY=your_key
NEWSAPI_KEY=your_key
UPDATE_SECRET_KEY=random_string
```

## Cost

**$0/month** - Uses only free tiers:
- MongoDB Atlas: 512MB free
- Vercel: 100GB bandwidth free
- GitHub Actions: 2000 minutes/month free
- All APIs: Free tier plans

## API Rate Limits

- **CoinGecko**: No limit (used for crypto)
- **Polygon**: 5 calls/minute (forex)
- **EODHD**: 20 calls/day (forex backup)
- **Alpha Vantage**: 25 calls/day (forex fallback)
- **NewsAPI**: 100 calls/day

System uses ~72 total API calls per day across all services.

## Data Retention

- **Price History**: 30 days
- **News Articles**: 7 days
- **Analysis Results**: Indefinite (updated every 4 hours)

## Limitations

1. **Historical Data**: Limited to 7 days for most indicators
2. **Real-Time Updates**: 4-hour lag by design (suitable for 1hr+ timeframes)
3. **Free API Constraints**: Some forex pairs may occasionally fail
4. **No Backtesting**: Current version doesn't track historical accuracy
5. **Simulation**: Not connected to live trading accounts

## Warning

This system is for **educational and analysis purposes only**. It does not:
- Execute trades automatically
- Guarantee profitable signals
- Replace professional financial advice
- Provide real-time data (4-hour lag)

**Trading involves substantial risk of loss.** Always:
- Use proper risk management
- Start with demo accounts
- Never risk more than you can afford to lose
- Consider this tool as ONE input among many

## Future Enhancements

Potential improvements:
- [ ] Backtesting engine with historical accuracy tracking
- [ ] Machine learning for pattern recognition
- [ ] Multiple timeframe analysis (15m, 1h, 4h, 1d)
- [ ] Email/SMS alerts for high-confidence signals
- [ ] Portfolio tracking
- [ ] More sophisticated sentiment analysis (NLP)
- [ ] Additional technical indicators (Ichimoku, Fibonacci, etc.)

## Contributing

This is a personal project. If you fork it:
1. Replace all API keys with your own
2. Update MongoDB connection string
3. Change UPDATE_SECRET_KEY
4. Modify trading pairs as desired

## License

MIT License - Use at your own risk

## Disclaimer

The creator of this system is not a financial advisor. This software is provided "as is" without warranty of any kind. Past performance does not indicate future results. Trading cryptocurrencies and forex carries significant risk and may not be suitable for all investors.

---

**Created:** 2025
**Purpose:** Educational trading analysis
**Status:** Active Development