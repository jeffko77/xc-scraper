# Deployment Guide

## Streamlit Cloud Deployment

### Prerequisites

1. **GitHub Repository**
   - Push all code to GitHub
   - Ensure `reference/missouri_schools.csv` is included

2. **PostgreSQL Database**
   - Set up a cloud PostgreSQL database (Railway, Supabase, ElephantSQL, etc.)
   - Note the connection URL

### Deployment Steps

#### 1. Prepare Files

Ensure these files exist in your repository:

- ✅ `app.py` - Main Streamlit application
- ✅ `scraper.py` - MileSplit scraper module
- ✅ `database.py` - Database models
- ✅ `requirements.txt` - Python dependencies
- ✅ `packages.txt` - System packages (for PostgreSQL)
- ✅ `.streamlit/config.toml` - Streamlit configuration
- ✅ `reference/missouri_schools.csv` - School classifications
- ✅ `.gitignore` - Git ignore rules (excludes .env)

#### 2. Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Select your repository
5. Set:
   - **Main file path**: `app.py`
   - **Branch**: `main` (or your branch name)
   - **Python version**: 3.13 (or latest)

#### 3. Configure Secrets

In Streamlit Cloud dashboard, go to **Settings** → **Secrets** and add:

```toml
DB_URL = "postgresql://user:password@host:5432/database"
```

**Example Database URLs:**

Railway:
```
postgresql://postgres:pass@containers-us-west-123.railway.app:5432/railway
```

Supabase:
```
postgresql://postgres:pass@db.abc123.supabase.co:5432/postgres
```

ElephantSQL:
```
postgresql://user:pass@name.db.elephantsql.com:5432/database
```

#### 4. Deploy

Click **Deploy!**

Streamlit will:
1. Install system packages from `packages.txt`
2. Install Python packages from `requirements.txt`
3. Run `app.py`

#### 5. Verify Deployment

Once deployed:
1. Check the app loads
2. Try importing a test meet
3. Verify database connection works
4. Test all pages

### Troubleshooting

#### Import Error: "KeyError: 'scraper'"

**Fixed in app.py** - We added path insertion at the top:
```python
import sys
import os
if os.path.dirname(__file__) not in sys.path:
    sys.path.insert(0, os.path.dirname(__file__))
```

#### Database Connection Error

- Check `DB_URL` is set in Streamlit secrets
- Verify PostgreSQL database is accessible from internet
- Ensure database exists
- Test connection string locally first

#### Missing CSV File

- Ensure `reference/missouri_schools.csv` is committed to git
- Check file path in repository matches code expectations

#### Import Errors

- Check `requirements.txt` has all dependencies
- Verify Python version compatibility (3.8+)
- Check `packages.txt` has system dependencies

## Local Development

### Setup

```bash
# 1. Create virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up .env file
echo "DB_URL=postgresql://user:pass@localhost:5432/xc_results" > .env

# 4. Run migrations (if upgrading)
python migrate_add_exclusion.py

# 5. Start app
streamlit run app.py
```

### Database Setup (Local)

#### Option 1: Local PostgreSQL

```bash
# Install PostgreSQL
# Then create database
createdb xc_results

# Set .env
DB_URL=postgresql://postgres:password@localhost:5432/xc_results
```

#### Option 2: Cloud Database (Same as Production)

Use Railway, Supabase, etc. and use the same DB_URL locally.

## Post-Deployment

### Initial Data Load

1. Go to **Import Results** page
2. Import your first meet
3. Verify data appears in other pages
4. Check **Meet History** shows the meet

### Manage Rankings

1. Go to **Meet History**
2. Use **Exclude** button for practice meets
3. Verify excluded meets don't appear in **Class/District Rankings**

## Updating the App

### Push Updates

```bash
git add .
git commit -m "Update description"
git push
```

Streamlit Cloud will automatically redeploy on push to main branch.

### Database Migrations

If you update the database schema:
1. Create migration script (like `migrate_add_exclusion.py`)
2. Run locally first to test
3. Document in CHANGELOG.md
4. Users run migration manually after deployment

## Monitoring

### Streamlit Cloud Dashboard

- View logs
- Monitor resource usage
- Check errors
- Restart app if needed

### Database Monitoring

- Check connection pool
- Monitor query performance
- Review storage usage
- Set up backups

## Backup Strategy

### Database Backups

```bash
# Export (PostgreSQL)
pg_dump -U user -h host -d database > backup.sql

# Import
psql -U user -h host -d database < backup.sql
```

### Code Backups

- Git repository serves as code backup
- Tag releases: `git tag v1.0.0`
- Keep CHANGELOG.md updated

## Security

### Secrets Management

- ✅ Never commit `.env` files
- ✅ Use Streamlit secrets for DB_URL
- ✅ Use read-only database user if possible
- ✅ Enable SSL for database connections

### Database Security

- Use strong passwords
- Whitelist IP addresses if possible
- Regular backups
- Monitor for suspicious activity

## Performance

### Optimization Tips

1. Database indexes (already implemented)
2. Eager loading (already implemented)
3. Limit query results
4. Cache expensive operations
5. Monitor slow queries

### Streamlit Caching

Already implemented for database connection.
Consider adding `@st.cache_data` for other expensive operations.

## Support

For deployment issues:
- Check Streamlit Cloud docs: https://docs.streamlit.io/streamlit-community-cloud
- Review error logs in dashboard
- Test locally first
- Check this repository's Issues page
