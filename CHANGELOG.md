# Changelog

## Latest Updates

### Meet Exclusion & Class/District Rankings (2025-10-06)

**Added:** Meet exclusion from rankings
- New `exclude_from_rankings` column in `meets` table
- Toggle button in Meet History page to include/exclude meets
- Excluded meets are filtered out from all ranking queries
- Visual indicators (✓/🚫) show exclusion status

**Added:** Class/District Rankings page
- New page showing rankings by MSHSAA class (1-5) and district
- Uses `reference/missouri_schools.csv` for school classifications
- Filters: Class, District, Gender (Boys/Girls/All)
- Only includes non-excluded meets
- Automatic team-to-school matching

**Migration:** Run `python migrate_add_exclusion.py` to add exclusion column to existing databases

### Database Fixes (2025-10-06)

**Fixed:** SQLAlchemy `DetachedInstanceError` issues
- Added eager loading with `joinedload` to all database query methods
- `search_athlete()`: Pre-loads `race` and `meet` relationships
- `get_leaderboard()`: Pre-loads `race` and `meet` relationships
- `get_meets()`: Pre-loads `races` relationship
- Prevents N+1 query problems and improves performance

### Scraper Enhancements (2025-10-06)

**Added:** Support for multiple MileSplit result formats
- **Format 1**: "Mens/Womens Meters" pattern (original)
- **Format 2**: "Event N" pattern with team scores table
- **Format 3**: Simple race name pattern with flexible ordering
  - Supports 3k, 5k, and any distance format
  - Handles "Freshman Girls 5k" (type before gender)
  - Handles "Girls Varsity 5k" (type after gender)
  - Supports division colors (White, Green, etc.)

**Tested URLs:**
- Frank Schultz Invitational (Format 1) ✓
- Parkway West Dale Shepherd (Format 2) ✓
- Forest Park XC Festival (Format 3 variations) ✓

### Database Connection (2025-10-06)

**Fixed:** PostgreSQL driver compatibility
- Automatically converts `postgresql://` to `postgresql+psycopg://`
- Supports both psycopg2 and psycopg3 drivers
- Works with Python 3.13+

### Dependencies (2025-10-06)

**Updated:** Python 3.13 compatibility
- pandas >= 2.2.3 (pre-built wheels)
- psycopg[binary] >= 3.2.0 (modern driver)
- sqlalchemy >= 2.0.36
- streamlit >= 1.39.0
- All dependencies tested on Python 3.13.1

## Known Issues

None currently! All tests passing.

## Future Enhancements

Potential features for future development:
- Batch URL import from CSV
- Export meets to Excel format
- Team comparison analytics
- PR (Personal Record) tracking
- Season progression charts
