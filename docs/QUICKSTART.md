# Quick Start Checklist

Follow these steps in order. Check each box as you complete it.

## Phase 1: File Setup (15 minutes)

- [* ] Copy all code files to correct locations:
  - [ *] `/api/utils/database.py`
  - [ ] `/api/utils/technical.py`
  - [ ] `/api/utils/fetchers.py`
  - [ ] `/api/utils/__init__.py` (empty file)
  - [ ] `/api/analyze-pair.py`
  - [ ] `/api/fetch-news.py`
  - [ ] `/api/update-all.py`
  - [ ] `/api/get-analysis.py`
  - [ ] `/.github/workflows/update-data.yml`
  - [ ] `/public/index.html` (updated version)
  - [ ] `vercel.json`
  - [ ] `requirements.txt` (updated)
  - [ ] `.env.example`

- [* ] Create `.gitignore` with:
  ```
  venv/
  .env
  __pycache__/
  *.pyc
  ```

## Phase 2: MongoDB Setup (10 minutes)

- [ ] Go to mongodb.com/cloud/atlas
- [ ] Sign up for free account
- [ ] Create M0 Free cluster
- [ ] Create database user (save credentials!)
- [ ] Network Access → Add 0.0.0.0/0 (allow all IPs for Vercel)
- [ ] Get connection string:
  - Click "Connect" → "Connect your application"
  - Copy connection string
  - Replace `<password>` with your password
  - Add `/trading_intelligence` before the `?`
  
**Your connection string should look like:**
```
mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/trading_intelligence?retryWrites=true&w=majority
```

## Phase 3: Local Environment (5 minutes)

- [ ] Create `.env` file in project root
- [ ] Add all values to `.env`:
  ```
  MONGODB_URI=your_mongodb_string_from_above
  ALPHA_VANTAGE_KEY=6V27WZG29PZ7PAI7
  POLYGON_KEY=WVkKEGrCIxJnKQ7DHDNVWxVLfFypAbat
  EODHD_KEY=68d7afb6e1b3c6.52504006
  NEWSAPI_KEY=4409c461699a4b5287c4f8a46e8c69a7
  UPDATE_SECRET_KEY=generate_random_string_here
  ```

- [ ] Generate random secret key:
  - Visit random.org/strings OR
  - Use: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

## Phase 4: Git Commit (5 minutes)

```bash
git add .
git commit -m "Complete trading system implementation"
git push origin main
```

- [ ] Verify all files pushed to GitHub (check repository online)
- [ ] Confirm `.env` is NOT in GitHub (should be ignored)

## Phase 5: Vercel Deployment (15 minutes)

- [ ] Go to vercel.com
- [ ] Sign in with GitHub
- [ ] Click "Add New Project"
- [ ] Import your GitHub repository
- [ ] Framework: "Other"
- [ ] Click "Deploy"
- [ ] Wait for deployment to complete

### Add Environment Variables to Vercel

- [ ] Go to Project → Settings → Environment Variables
- [ ] Add each variable (copy from your local `.env`):
  - [ ] `MONGODB_URI`
  - [ ] `ALPHA_VANTAGE_KEY`
  - [ ] `POLYGON_KEY`
  - [ ] `EODHD_KEY`
  - [ ] `NEWSAPI_KEY`
  - [ ] `UPDATE_SECRET_KEY`

- [ ] Click "Redeploy" from Deployments tab
- [ ] Copy your Vercel URL (e.g., `https://analyst-proj.vercel.app`)

## Phase 6: Update Frontend (5 minutes)

- [ ] Open `public/index.html`
- [ ] Find line ~290: `const API_BASE_URL = 'https://your-project.vercel.app';`
- [ ] Replace with your actual Vercel URL
- [ ] Save file
- [ ] Commit and push:
  ```bash
  git add public/index.html
  git commit -m "Update API URL"
  git push origin main
  ```

## Phase 7: GitHub Actions Setup (5 minutes)

- [ ] Go to GitHub repository → Settings → Secrets and variables → Actions
- [ ] Click "New repository secret"
- [ ] Add `UPDATE_SECRET_KEY`:
  - Name: `UPDATE_SECRET_KEY`
  - Value: (same as in your `.env` and Vercel)
- [ ] Add `VERCEL_API_URL`:
  - Name: `VERCEL_API_URL`
  - Value: Your Vercel URL (no trailing slash)

## Phase 8: First Test (10 minutes)

### Test API Endpoint

- [ ] Open browser to: `https://your-vercel-url.vercel.app/api/get-analysis`
- [ ] Should see JSON response (might be empty initially - that's OK)

### Run First Data Update

**Option A: Manual GitHub Action**
- [ ] Go to GitHub → Actions tab
- [ ] Click "Update Trading Data"
- [ ] Click "Run workflow" → "Run workflow"
- [ ] Wait 3-5 minutes
- [ ] Check run completed successfully (green checkmark)

**Option B: API Call**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_SECRET_KEY" \
  https://your-vercel-url.vercel.app/api/update-all
```

### Verify Data in MongoDB

- [ ] Go to MongoDB Atlas dashboard
- [ ] Click "Browse Collections"
- [ ] Should see databases:
  - `pairs_analysis` (11 documents)
  - `price_history` (has entries)
  - `news` (has articles)
  - `system_metadata` (has update record)

### Test Frontend

- [ ] Open `public/index.html` in browser
- [ ] Click "Refresh Analysis"
- [ ] Should see 11 trading pair cards with data
- [ ] Click a card → Should open detailed modal
- [ ] Check news section shows articles

## Phase 9: Deploy Frontend to GitHub Pages (Optional, 5 minutes)

- [ ] GitHub repository → Settings → Pages
- [ ] Source: "Deploy from a branch"
- [ ] Branch: `main`, Folder: `/public`
- [ ] Click "Save"
- [ ] Wait 2 minutes
- [ ] Visit: `https://yourusername.github.io/repository-name/`

## Troubleshooting Checklist

If something doesn't work:

**Database connection failed:**
- [ ] Check MongoDB connection string format
- [ ] Verify password doesn't have special characters (or URL-encode them)
- [ ] Confirm IP whitelist is 0.0.0.0/0
- [ ] Check environment variable is set in Vercel

**No data showing:**
- [ ] Run GitHub Action manually first
- [ ] Check Vercel function logs (Deployments → Function Logs)
- [ ] Verify API_BASE_URL in HTML matches your Vercel URL
- [ ] Open browser console (F12) for JavaScript errors

**GitHub Action fails:**
- [ ] Verify both secrets are set: `UPDATE_SECRET_KEY` and `VERCEL_API_URL`
- [ ] Check UPDATE_SECRET_KEY matches between GitHub and Vercel
- [ ] Ensure VERCEL_API_URL has no trailing slash

**API returns errors:**
- [ ] Check Vercel environment variables are all set
- [ ] Verify MongoDB allows connections from anywhere
- [ ] Check function logs in Vercel dashboard

## Success Criteria

You've completed setup successfully when:

- [x] GitHub Actions runs without errors
- [x] MongoDB has data in all collections
- [x] API endpoint returns JSON with trading pairs
- [x] Frontend displays 11 trading cards
- [x] Clicking cards shows detailed analysis
- [x] News section shows recent articles
- [x] System updates automatically every 4 hours

## Next Steps After Successful Setup

1. **Monitor for 24 hours** - Let system collect more data
2. **Review signals** - Compare system predictions with actual market movements
3. **Adjust if needed** - Fine-tune confidence thresholds or indicators
4. **Set up notifications** - Consider adding email/SMS alerts for high-confidence signals

## Need Help?

Check these resources:
1. DEPLOYMENT.md - Detailed deployment instructions
2. README.md - System overview and architecture
3. Vercel function logs - Real-time error tracking
4. MongoDB logs - Database connection issues
5. GitHub Actions logs - Automation troubleshooting

---

**Estimated Total Time:** 1-1.5 hours for complete setup

**Cost:** $0/month (all free tiers)