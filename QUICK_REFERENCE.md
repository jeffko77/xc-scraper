# Quick Reference Guide

## Starting the App

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`

## Common Workflows

### 1. Import a New Meet

1. Go to **Import Results** page
2. Paste MileSplit URL (raw or formatted)
3. Click **Import Results**
4. Review preview
5. Data automatically saved to database

### 2. Exclude a Meet from Rankings

1. Go to **Meet History** page
2. Find the meet you want to exclude
3. Click **Exclude** button
4. Status changes to 🚫 (excluded)
5. Click **Include** to re-enable

**Why exclude?**
- Practice meets
- Time trials
- Out-of-state invites
- Early season "shakeout" races

### 3. View Class/District Rankings

1. Go to **Class/District Rankings** page
2. Select Class (e.g., "Class 5")
3. Select District (e.g., "District 1")
4. Choose gender tab (Boys/Girls/All)
5. Adjust "Top N" limit
6. View rankings table

### 4. Search for an Athlete

1. Go to **Name Lookup** page
2. Enter athlete name
3. Select gender filter
4. View all performances
5. See best time highlighted

### 5. View Overall Leaderboard

1. Go to **Leaderboard** page
2. Select gender
3. Select team (optional)
4. Set result limit
5. Download CSV if needed

## Database Management

### First Time Setup

```bash
# 1. Create .env file
echo "DB_URL=postgresql://user:pass@localhost:5432/xc_results" > .env

# 2. Run migration (if upgrading from old version)
python migrate_add_exclusion.py
```

### Backup Database

```bash
# PostgreSQL backup
pg_dump -U user xc_results > backup.sql

# Restore
psql -U user xc_results < backup.sql
```

## Team Name Matching

The app automatically matches team names to schools in `reference/missouri_schools.csv`.

**Examples:**
- "Parkway West" → Class 5, District 1
- "St. Louis University" → Matched to "S.L.U.H." in Class 5
- "Rockhurst" → Class 5, District 1

**Note:** Team names must match exactly or be close to CSV entries. If a team isn't matched, it won't appear in Class/District rankings.

## Troubleshooting

### Meet not showing in rankings?
- Check if it's excluded in **Meet History**
- Verify teams are in `missouri_schools.csv`

### Athlete not found?
- Try partial name search (e.g., "Smith" instead of "John Smith")
- Check gender filter is correct
- Verify meet was imported successfully

### Database connection error?
- Check `.env` file exists
- Verify `DB_URL` is correct
- Ensure PostgreSQL is running

### Import fails?
- Verify URL is from MileSplit
- Try changing `/formatted/` to `/raw`
- Enable verbose mode to see detailed logs

## File Structure

```
xc-scraper/
├── app.py                      # Main Streamlit app
├── database.py                 # Database models & queries
├── scraper.py                  # MileSplit scraper
├── batch_import.py             # CLI batch importer
├── migrate_add_exclusion.py    # Database migration
├── test_scraper.py             # Test script
├── reference/
│   └── missouri_schools.csv    # School classifications
├── .env                        # Database URL (create this)
├── requirements.txt            # Python dependencies
└── README.md                   # Full documentation
```

## Tips & Best Practices

1. **Import regularly** - Get results soon after meets for freshness
2. **Exclude carefully** - Only exclude meets you don't want in official rankings
3. **Check team names** - Review imported data to ensure team matching
4. **Export rankings** - Use CSV export to share with coaches
5. **Backup database** - Periodically backup your PostgreSQL database

## Support

For issues:
1. Check CHANGELOG.md for recent changes
2. Review README.md for detailed docs
3. See FEATURES.md for capability overview
4. Run test_scraper.py to verify setup
