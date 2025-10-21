# Data Cleaning Guide

## Overview

The xc-scraper now includes a robust data cleaning system to handle gender misclassifications in cross-country results. This system identifies and removes boys' times that appear in girls' races (and vice versa) using time-based outlier detection.

## New Features

### 1. Athlete-Level Gender Column

**What changed:**
- Added `athlete_gender` column to `individual_results` table
- Gender is now tracked at the individual athlete level, not just the race level
- All leaderboard queries now use `athlete_gender` instead of `race.gender`

**Benefits:**
- Individual athletes can be correctly classified even if the race was mislabeled
- More accurate leaderboards and rankings
- Easier to identify and fix data quality issues

### 2. Automated Outlier Detection

**What it does:**
- Identifies suspiciously fast times in girls' races (likely boys)
- Identifies suspiciously slow times in boys' races (possibly girls)
- Uses configurable time thresholds for 5K races

**Default thresholds:**
- Girls' races: times < 16:00 (960 seconds) flagged as likely boys
- Boys' races: times > 24:00 (1440 seconds) flagged as possibly girls

## How to Use

### Step 1: Run the Database Migration

Before using the new features, you must migrate your database to add the `athlete_gender` column:

```bash
uv run python migrate_add_athlete_gender.py
```

This will:
1. Add the `athlete_gender` column to `individual_results`
2. Populate it with values from `race.gender` as a starting point
3. Create an index on `athlete_gender` for faster queries

### Step 2: Analyze Your Data for Outliers

Run the cleaning script in **dry-run mode** (default) to see what would be cleaned:

```bash
uv run python clean_gender_outliers.py
```

This will show:
- Number of outliers found in girls' races
- Number of outliers found in boys' races
- Top 20 examples of each type
- Total count of records that would be deleted

**Example output:**
```
================================================================================
GENDER OUTLIER ANALYSIS
================================================================================

🔍 Searching for suspiciously FAST times in GIRLS' races (< 16.00 min)...
Found 45 outliers

Top 20 fastest (likely boys in girls' races):
--------------------------------------------------------------------------------
 1. John Smith                   | Central High School       | 15:23.45 | Girls Varsity 5K
 2. Mike Johnson                 | North High School         | 15:45.67 | Girls JV 5K
...

🔍 Searching for suspiciously SLOW times in BOYS' races (> 24.00 min)...
Found 12 outliers

================================================================================
SUMMARY
================================================================================
Boys' times in girls' races: 45
Girls' times in boys' races: 12
Total outliers found: 57
================================================================================

🔍 DRY RUN: Would delete 57 records
   Run with --execute to actually delete these records
```

### Step 3: Export Outliers for Review (Optional)

If you want to manually review the outliers before deleting them:

```bash
uv run python clean_gender_outliers.py --export outliers.csv
```

This creates a CSV file with all flagged records for manual review.

### Step 4: Clean the Data

Once you're confident in the outliers identified, run the cleaning script with `--execute`:

```bash
uv run python clean_gender_outliers.py --execute
```

This will **permanently delete** the outlier records from your database.

### Step 5: Adjust Thresholds (Optional)

If the default thresholds don't work well for your data, you can customize them:

```bash
# More aggressive cleaning (wider thresholds)
uv run python clean_gender_outliers.py --girls-threshold 990 --boys-threshold 1380 --execute

# More conservative cleaning (narrower thresholds)
uv run python clean_gender_outliers.py --girls-threshold 930 --boys-threshold 1500 --execute
```

**Time conversion reference:**
- 15:30 = 930 seconds
- 16:00 = 960 seconds
- 16:30 = 990 seconds
- 23:00 = 1380 seconds
- 24:00 = 1440 seconds
- 25:00 = 1500 seconds

## Advanced Usage

### Custom Threshold Examples

**Very aggressive cleaning** (removes more data, higher confidence):
```bash
uv run python clean_gender_outliers.py --girls-threshold 1020 --boys-threshold 1320 --execute
# Girls < 17:00 and Boys > 22:00
```

**Very conservative cleaning** (removes less data, lower confidence):
```bash
uv run python clean_gender_outliers.py --girls-threshold 900 --boys-threshold 1560 --execute
# Girls < 15:00 and Boys > 26:00
```

### Workflow for Large Datasets

1. **Start conservative:** Use tighter thresholds to remove only obvious misclassifications
2. **Review results:** Check leaderboards and rankings for quality
3. **Iterate:** Gradually adjust thresholds based on results
4. **Export before deleting:** Always use `--export` first for safety

### Re-running After New Imports

After importing new meet data:

```bash
# Check for new outliers
uv run python clean_gender_outliers.py

# Clean if needed
uv run python clean_gender_outliers.py --execute
```

## Technical Details

### Database Schema Changes

**Before:**
- Gender stored only in `races.gender` (M/F)
- Queries joined `races` table for gender filtering
- All athletes in a race inherited the same gender

**After:**
- Gender stored in both `races.gender` AND `individual_results.athlete_gender`
- Queries use `individual_results.athlete_gender` directly (faster)
- Individual athletes can have different genders than their race
- New index: `idx_athlete_gender` for performance

### New Files

1. **`clean_gender_outliers.py`** - Main cleaning script
2. **`migrate_add_athlete_gender.py`** - Database migration
3. **`DATA_CLEANING_GUIDE.md`** - This documentation

### Modified Files

1. **`database.py`**
   - Added `athlete_gender` column to `IndividualResult` model
   - Updated queries to use `athlete_gender` instead of `race.gender`
   - Added `athlete_gender` to saved results

2. **`app.py`**
   - Updated gender mapping to use `athlete_gender`
   - Simplified queries (no longer need to join Race for gender)

## Troubleshooting

### "DB_URL environment variable not set"

Make sure your `.env` file exists and contains:
```
DB_URL=postgresql://user:password@host:port/database
```

### "Column 'athlete_gender' already exists"

Migration already ran successfully. Skip to Step 2.

### Database connection issues

If you see connection errors, check:
1. Database URL is correct in `.env`
2. Database is accessible from your environment
3. Network connectivity to database host

### Too many/too few outliers found

Adjust the time thresholds using `--girls-threshold` and `--boys-threshold` flags.

## Best Practices

1. **Always start with dry-run mode** - Never use `--execute` on first run
2. **Export before deleting** - Use `--export` to create a backup CSV
3. **Review the top 20 examples** - Make sure the flagged records actually look wrong
4. **Start conservative** - Use tighter thresholds initially
5. **Document your thresholds** - Keep track of what values work for your dataset
6. **Regular maintenance** - Run cleaning after each batch of new imports

## Support

For issues or questions:
- Check the main README.md
- Review existing GitHub issues
- Create a new issue with details about your problem
