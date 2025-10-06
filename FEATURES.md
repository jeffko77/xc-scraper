# XC Scraper Features

## Core Features

### 1. Multi-Format Scraper
Automatically detects and parses three different MileSplit result formats:
- **Format 1**: "Mens/Womens Meters" (e.g., "Mens 5,000 Meters Varsity Boys")
- **Format 2**: "Event N" with structured tables (e.g., "Event 1 Boys 5k Run CC Varsity")
- **Format 3**: Simple race names with flexible ordering (e.g., "Freshman Girls 5k", "Girls Varsity 5k")

Supports:
- Any distance (3k, 5k, 10k, etc.)
- Auto-conversion from `/formatted/` to `/raw` URLs
- Team scores and individual results
- Multiple races per meet

### 2. PostgreSQL Storage
- Structured database with optimized indexes
- Eager loading to prevent N+1 queries
- Automatic driver detection (psycopg3 compatible)
- Meet, Race, TeamScore, and IndividualResult models

### 3. Streamlit Web Interface

#### Import Results Page
- Paste MileSplit URL to scrape
- Preview before saving
- Verbose mode for debugging
- Automatic meet detection and update

#### Name Lookup Page
- Search athletes across all meets
- Filter by gender (Boys/Girls/All)
- View all performances
- See personal best automatically

#### Leaderboard Page
- Top times across all meets
- Filter by gender and team
- Adjustable result limit
- CSV export

#### Class/District Rankings Page ⭐ NEW
- Rankings by MSHSAA classification
- Filter by Class (1-5) and District
- Based on `reference/missouri_schools.csv`
- Separate Boys/Girls/All tabs
- Only includes non-excluded meets
- Automatic school matching

#### Meet History Page
- View all imported meets
- See race counts and dates
- **Exclude/Include toggle** ⭐ NEW
  - Mark meets to exclude from rankings
  - Visual status indicators (✓/🚫)
  - Affects all ranking pages

### 4. School Classification System
Uses Missouri high school classifications from CSV:
- 419 schools organized by Class (1-5) and District
- Automatic team-to-school matching
- Fuzzy matching for variations in team names

### 5. Ranking Exclusion System ⭐ NEW
- Tag individual meets to exclude from rankings
- Useful for:
  - Practice meets
  - Invitational "fun" races
  - Out-of-state meets
  - Early season time trials
- Exclusion applies to:
  - Class/District Rankings
  - Overall Leaderboard (if needed)

## Database Schema

### Tables
```
meets
  - id (PK)
  - name
  - date
  - url (unique)
  - created_at
  - exclude_from_rankings ⭐ NEW

races
  - id (PK)
  - meet_id (FK)
  - name
  - gender (M/F)
  - race_type (Varsity/JV/etc)

team_scores
  - id (PK)
  - race_id (FK)
  - place
  - team_name
  - points

individual_results
  - id (PK)
  - race_id (FK)
  - place
  - athlete_name
  - year_grade
  - team
  - time
  - time_seconds (for sorting)
```

### Indexes
Optimized for:
- Athlete name searches
- Team name filtering
- Time-based rankings
- Class/District queries

## CLI Tools

### Batch Import
```bash
python batch_import.py urls.txt
```
Import multiple meets from a text file.

### Database Migration
```bash
python migrate_add_exclusion.py
```
Adds `exclude_from_rankings` column to existing databases.

### Test Scraper
```bash
python test_scraper.py
```
Tests scraper with example URLs.

## Supported URL Formats

All tested and working:
1. Frank Schultz Invitational (Format 1)
2. Parkway West Dale Shepherd (Format 2)
3. Forest Park XC Festival - Multiple races (Format 3)
   - 5k races
   - 3k races
   - Varsity/JV variations

## Future Enhancements

Potential additions:
- Personal record (PR) tracking
- Season progression charts
- Team scoring calculator
- Export to Excel
- Email notifications for new results
- Multi-state support
