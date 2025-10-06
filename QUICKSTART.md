# Quick Start Guide

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Set up PostgreSQL Database

### Option A: Local PostgreSQL
Install PostgreSQL and create a database:

```sql
CREATE DATABASE xc_results;
```

### Option B: Cloud PostgreSQL
Use a service like:
- **Railway**: https://railway.app/
- **Supabase**: https://supabase.com/
- **ElephantSQL**: https://www.elephantsql.com/
- **AWS RDS**: https://aws.amazon.com/rds/postgresql/

## 3. Configure Environment

Create a `.env` file:

```bash
DB_URL=postgresql://user:password@localhost:5432/xc_results
```

**Example formats:**
- Local: `postgresql://postgres:mypassword@localhost:5432/xc_results`
- Railway: `postgresql://user:pass@containers-us-west-1.railway.app:5432/railway`
- Heroku: `postgres://user:pass@host.compute.amazonaws.com:5432/dbname`

## 4. Test the Scraper

```bash
python test_scraper.py
```

This will test scraping the example MileSplit URL.

## 5. Run the App

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

## 6. Import Your First Meet

1. Go to the "Import Results" page
2. Paste a MileSplit URL (e.g., `https://mo.milesplit.com/meets/703864-frank-schultz-invitational-2025/results/1221124/raw`)
3. Click "Import Results"
4. Wait for the scraping and database import to complete

## 7. Explore the Data

- **Name Lookup**: Search for athletes across all meets
- **Leaderboard**: View top times by gender/team
- **Meet History**: See all imported meets

## Troubleshooting

### Database Connection Error
- Check that PostgreSQL is running
- Verify DB_URL in `.env` is correct
- Ensure database exists

### Import Fails
- Check URL is from MileSplit
- Try converting `/formatted/` to `/raw`
- Check internet connection

### Windows Encoding Issues
If you see encoding errors, the app handles them automatically. For console scripts, UTF-8 encoding is enforced.

## Example URLs to Try

Missouri MileSplit:
- `https://mo.milesplit.com/meets/703864-frank-schultz-invitational-2025/results/1221124/raw`

Other states: Replace `mo.` with your state code (e.g., `ca.`, `tx.`, `ny.`)
