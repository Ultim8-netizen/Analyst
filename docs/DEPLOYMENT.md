# Trading Intelligence System - Deployment Guide

## Prerequisites Checklist

- [x] VS Code installed
- [x] Python installed
- [x] Git installed
- [x] Virtual environment created
- [x] All Python packages installed in venv
- [x] GitHub repository created

## Step 1: MongoDB Atlas Setup (5 minutes)

1. Go to [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Sign up for free account
3. Create a new cluster (Free M0 tier)
4. Click "Connect" → "Connect your application"
5. Copy the connection string:
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/
   ```
6. Replace `<username>` and `<password>` with your credentials
7. Add `/trading_intelligence` to the end before the `?` parameters

**Result:** You should have a connection string like:
```
mongodb+srv://myuser:mypass@cluster0.xxxxx.mongodb.net/trading_intelligence?retryWrites=true&w=majority
```

## Step 2: Organize Project Files

Your project structure should look like this:

```
ANALYST_PROJ/
├── .github/
│   └── workflows/
│       └── update-data.yml
├── api/
│   ├── utils/
│   │   ├── __init__.py (empty file)
│   │   ├── database.py
│   │   ├── technical.py
│   │   └── fetchers.py
│   ├── analyze-pair.py
│   ├── fetch-news.py
│   ├── update-all.py
│   └── get-analysis.py
├── public/
│   └── index.html
├── venv/ (don't commit this)
├── .env (don't commit this)
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
└── vercel.json
```

### Create __init__.py

In `/api/utils/` folder, create an empty file named `__init__.py`. This tells Python it's a package.

**Windows Command Prompt:**
```cmd
cd api\utils
type nul > __init__.py
```

**PowerShell:**
```powershell
cd api\utils
New-Item __init__.py
```

## Step 3: Update .gitignore

Make sure your `.gitignore` contains:

```
venv/
env/
.env
__pycache__/
*.pyc
.DS_Store
```

## Step 4: Create .env File (Local Testing)

Create `.env` in your project root with your actual values:

```
MONGODB_URI=your_mongodb_connection_string_here
ALPHA_VANTAGE_KEY=6V27WZG29PZ7PAI7
POLYGON_KEY=WVkKEGrCIxJnKQ7DHDNVWxVLfFypAbat
EODHD_KEY=68d7afb6e1b3c6.52504006
NEWSAPI_KEY=4409c461699a4b5287c4f8a46e8c69a7
UPDATE_SECRET_KEY=make-this-a-random-string-12345
```

**Generate a secure UPDATE_SECRET_KEY:**
- Visit: https://www.random.org/strings/
- Or use: `openssl rand -base64 32` in terminal

## Step 5: Commit to GitHub

```bash
# Navigate to your project folder
cd path/to/ANALYST_PROJ

# Add all files
git add .

# Commit
git commit -m "Complete trading intelligence system backend"

# Push to GitHub
git push origin main
```

## Step 6: Deploy to Vercel (10 minutes)

1. Go to [vercel.com](https://vercel.com)
2. Sign up/login with GitHub
3. Click "Add New" → "Project"
4. Import your GitHub repository
5. **Framework Preset:** Select "Other"
6. **Root Directory:** Leave as `.` (project root)
7. Click "Deploy"

### Configure Environment Variables in Vercel

1. After first deployment, go to your project dashboard
2. Click "Settings" → "Environment Variables"
3. Add each variable:
   - `MONGODB_URI` → Your MongoDB connection string
   - `ALPHA_VANTAGE_KEY` → `6V27WZG29PZ7PAI7`
   - `POLYGON_KEY` → `WVkKEGrCIxJnKQ7DHDNVWxVLfFypAbat`
   - `EODHD_KEY` → `68d7afb6e1b3c6.52504006`
   - `NEWSAPI_KEY` → `4409c461699a4b5287c4f8a46e8c69a7`
   - `UPDATE_SECRET_KEY` → Your random secret key

4. Click "Redeploy" to apply environment variables

## Step 7: Get Your Vercel URL

After deployment completes:
1. Copy your Vercel URL (e.g., `https://analyst-proj.vercel.app`)
2. Test your API endpoints:
   - `https://your-url.vercel.app/api/get-analysis`
   - Should return JSON (might be empty initially)

## Step 8: Update Frontend HTML

1. Open `public/index.html`
2. Find this line (around line 290):
   ```javascript
   const API_BASE_URL = 'https://your-project.vercel.app';
   ```
3. Replace with your actual Vercel URL
4. Commit and push changes:
   ```bash
   git add public/index.html
   git commit -m "Update API URL"
   git push origin main
   ```

## Step 9: Configure GitHub Actions

1. Go to your GitHub repository
2. Click "Settings" → "Secrets and variables" → "Actions"
3. Add these secrets:
   - `UPDATE_SECRET_KEY` → Same value as in Vercel
   - `VERCEL_API_URL` → Your Vercel deployment URL (without trailing slash)

## Step 10: Test the System

### Test API Endpoints

```bash
# Test get-analysis (should work immediately)
curl https://your-url.vercel.app/api/get-analysis

# Test update-all (requires authorization)
curl -X POST \
  -H "Authorization: Bearer your-secret-key" \
  https://your-url.vercel.app/api/update-all
```

### Trigger First Data Update

**Option 1: Manual GitHub Action**
1. Go to GitHub repo → "Actions" tab
2. Click "Update Trading Data" workflow
3. Click "Run workflow" → "Run workflow"
4. Wait 2-3 minutes

**Option 2: Call API directly**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_SECRET_KEY" \
  -H "Content-Type: application/json" \
  https://your-url.vercel.app/api/update-all
```

### View Your Frontend

1. Open `public/index.html` in a browser
2. OR deploy to GitHub Pages:
   - GitHub repo → Settings → Pages
   - Source: Deploy from branch `main`, folder `/public`
   - Your site will be at: `https://username.github.io/repo-name/`

## Step 11: Verify Everything Works

**Check MongoDB:**
1. Go to MongoDB Atlas dashboard
2. Click "Browse Collections"
3. Should see collections: `pairs_analysis`, `price_history`, `news`, `system_metadata`

**Check Frontend:**
1. Open your HTML page
2. Click "Refresh Analysis"
3. Should see trading pairs with real data

**Check GitHub Actions:**
1. GitHub repo → Actions tab
2. Should see workflow runs every 4 hours

## Troubleshooting

### "Database connection failed"
- Check MongoDB connection string in Vercel env vars
- Ensure IP whitelist allows connections (set to 0.0.0.0/0 in MongoDB Atlas)

### "No data showing in frontend"
- Run GitHub Action manually first to populate database
- Check browser console for errors (F12)
- Verify API_BASE_URL is correct in HTML

### "API returns 500 error"
- Check Vercel deployment logs: Project → Deployments → Click latest → "Function Logs"
- Ensure all environment variables are set

### "GitHub Action fails"
- Check you set both secrets: `UPDATE_SECRET_KEY` and `VERCEL_API_URL`
- Verify UPDATE_SECRET_KEY matches between GitHub and Vercel

## Expected Behavior

**After successful deployment:**
- GitHub Actions runs every 4 hours
- Updates all 11 trading pairs (5 crypto + 6 forex)
- Fetches and processes news
- Stores everything in MongoDB
- Frontend displays real-time analysis
- Each pair shows:
  - Current price
  - Technical indicators (RSI, MACD, Bollinger Bands)
  - Trading signal (LONG/SHORT/NEUTRAL)
  - Confidence percentage
  - Entry, TP, SL levels calculated for $5 max risk
  - Support/Resistance levels

## Maintenance

**Weekly:**
- Check MongoDB storage usage (free tier: 512MB)
- Review GitHub Actions logs for failures

**Monthly:**
- Clean old data if approaching storage limits
- Review API usage (most APIs track monthly/daily limits)

**API Call Estimates per Update Cycle:**
- Crypto: 5 calls (CoinGecko - unlimited free)
- Forex: 6 calls (spread across Polygon/EODHD/Alpha Vantage)
- News: 1 call (NewsAPI)
- **Total per cycle:** ~12 API calls

**Daily totals (6 cycles at 4-hour intervals):**
- ~72 API calls spread across multiple services
- Well within all free tier limits

## Cost: $0/month

Everything uses free tiers:
- MongoDB Atlas: Free (512MB)
- Vercel: Free (100GB bandwidth)
- GitHub Actions: Free (2000 minutes/month)
- All APIs: Free tiers

## Support

If you encounter issues:
1. Check Vercel function logs
2. Check MongoDB connection
3. Verify all environment variables are set
4. Test API endpoints individually
5. Review GitHub Actions run logs

## Next Steps

Once deployed and working:
1. Let the system run for 24-48 hours to collect data
2. Monitor accuracy of signals
3. Consider adjusting confidence thresholds
4. Fine-tune technical indicator parameters if needed

## Security Notes

- Never commit `.env` file
- Change UPDATE_SECRET_KEY to a strong random value
- MongoDB should have IP whitelist set to 0.0.0.0/0 for Vercel
- Consider adding authentication to frontend if making it public