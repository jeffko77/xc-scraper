"""
Streamlit app for MileSplit XC Results
"""
import streamlit as st
import os
from typing import Optional
from scraper import MileSplitScraper
from database import Database, IndividualResult, Race
from sqlalchemy.orm import joinedload
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="XC Results Manager",
    page_icon="🏃",
    layout="wide"
)


def init_database():
    """Initialize database connection"""
    try:
        db = Database()
        db.create_tables()
        return db
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
        st.info("Make sure DB_URL environment variable is set correctly")
        return None


def main():
    """Main application"""
    st.title("🏃 Cross Country Results Manager")

    # Initialize database
    db = init_database()
    if not db:
        return

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["Import Results", "Name Lookup", "Leaderboard", "Meet History", "Class/District Rankings"]
    )

    if page == "Import Results":
        import_page(db)
    elif page == "Name Lookup":
        name_lookup_page(db)
    elif page == "Leaderboard":
        leaderboard_page(db)
    elif page == "Meet History":
        meet_history_page(db)
    elif page == "Class/District Rankings":
        class_district_rankings_page(db)


def import_page(db: Database):
    """Page for importing results from MileSplit"""
    st.header("Import Results from MileSplit")

    st.markdown("""
    Enter a MileSplit results URL to scrape and import the data.

    **Supported formats:**
    - `/raw` URLs: `https://mo.milesplit.com/meets/.../results/.../raw`
    - `/formatted/` URLs (will be auto-converted): `https://mo.milesplit.com/meets/.../results/.../formatted/`
    """)

    # URL input
    url = st.text_input(
        "MileSplit URL",
        placeholder="https://mo.milesplit.com/meets/703864-frank-schultz-invitational-2025/results/1221124/raw"
    )

    # Verbose mode
    verbose = st.checkbox("Verbose mode (show detailed logging)")

    # Import button
    if st.button("Import Results", type="primary"):
        if not url:
            st.error("Please enter a URL")
            return

        with st.spinner("Scraping results..."):
            try:
                # Scrape the results
                scraper = MileSplitScraper(verbose=verbose)
                races = scraper.scrape_url(url)

                st.success(f"Successfully scraped {len(races)} race(s)")

                # Display preview
                st.subheader("Preview")
                for race in races:
                    with st.expander(f"📊 {race.race_name}"):
                        col1, col2 = st.columns(2)

                        with col1:
                            st.markdown("**Team Scores**")
                            if race.team_scores:
                                team_df = pd.DataFrame([
                                    {"Place": ts.place, "Team": ts.team_name, "Points": ts.points}
                                    for ts in race.team_scores
                                ])
                                st.dataframe(team_df, hide_index=True)
                            else:
                                st.info("No team scores")

                        with col2:
                            st.markdown("**Individual Results (Top 10)**")
                            if race.individual_results:
                                results_df = pd.DataFrame([
                                    {
                                        "Place": ir.place,
                                        "Athlete": ir.athlete_name,
                                        "Team": ir.team,
                                        "Time": ir.time
                                    }
                                    for ir in race.individual_results[:10]
                                ])
                                st.dataframe(results_df, hide_index=True)
                            else:
                                st.info("No individual results")

                # Save to database
                with st.spinner("Saving to database..."):
                    meet_id = db.save_results(url, races)
                    st.success(f"✅ Results saved to database (Meet ID: {meet_id})")

            except Exception as e:
                st.error(f"Error: {str(e)}")


def name_lookup_page(db: Database):
    """Page for looking up athletes by name"""
    st.header("Athlete Name Lookup")

    col1, col2 = st.columns([3, 1])

    with col1:
        search_name = st.text_input("Search for athlete", placeholder="Enter athlete name")

    with col2:
        gender_filter = st.selectbox("Gender", ["All", "Boys", "Girls"])

    if search_name:
        gender = None
        if gender_filter == "Boys":
            gender = "M"
        elif gender_filter == "Girls":
            gender = "F"

        results = db.search_athlete(search_name, gender)

        if results:
            st.success(f"Found {len(results)} result(s)")

            # Create dataframe
            data = []
            for result in results:
                data.append({
                    "Athlete": result.athlete_name,
                    "Team": result.team,
                    "Time": result.time,
                    "Place": result.place,
                    "Grade": result.year_grade,
                    "Race": result.race.name,
                    "Meet": result.race.meet.name
                })

            df = pd.DataFrame(data)
            st.dataframe(df, hide_index=True, use_container_width=True)

            # Best time
            if any((r.time_seconds is not None) for r in results):
                best_result = min((r for r in results if r.time_seconds is not None), key=lambda x: x.time_seconds)
                st.info(f"🏆 Best time: **{best_result.time}** at {best_result.race.meet.name}")

        else:
            st.warning("No results found")


def leaderboard_page(db: Database):
    """Page for viewing leaderboards"""
    st.header("Leaderboard")

    # Filters
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        gender = st.selectbox("Gender", ["Boys", "Girls", "All"])

    with col2:
        teams = ["All Teams"] + db.get_all_teams()
        team_filter = st.selectbox("Team", teams)

    with col3:
        limit = st.number_input("Top", min_value=10, max_value=500, value=50, step=10)

    # Convert filters
    gender_code = None
    if gender == "Boys":
        gender_code = "M"
    elif gender == "Girls":
        gender_code = "F"

    team = None if team_filter == "All Teams" else team_filter

    # Get leaderboard
    results = db.get_leaderboard(gender=gender_code, team=team, limit=limit)

    if results:
        st.success(f"Showing top {len(results)} times")

        # Create dataframe
        data = []
        for idx, result in enumerate(results, 1):
            data.append({
                "Rank": idx,
                "Athlete": result.athlete_name,
                "Team": result.team,
                "Time": result.time,
                "Grade": result.year_grade,
                "Race": result.race.name,
                "Meet": result.race.meet.name
            })

        df = pd.DataFrame(data)
        st.dataframe(df, hide_index=True, use_container_width=True)

        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"leaderboard_{gender}_{team_filter}.csv",
            mime="text/csv"
        )

    else:
        st.warning("No results found")


def meet_history_page(db: Database):
    """Page for viewing imported meets"""
    st.header("Meet History")

    meets = db.get_meets()

    if meets:
        st.success(f"Total meets imported: {len(meets)}")

        data = []
        for meet in meets:
            race_count = len(meet.races)
            data.append({
                "Meet": meet.name,
                "Date": meet.date or "N/A",
                "Races": race_count,
                "URL": meet.url,
                "Imported": meet.created_at.strftime("%Y-%m-%d %H:%M")
            })

        df = pd.DataFrame(data)
        st.dataframe(df, hide_index=True, use_container_width=True)

    else:
        st.info("No meets imported yet. Go to 'Import Results' to add data.")


def load_school_reference(path: str = "reference/missouri_schools.csv"):
    """Load the school reference CSV and return a mapping from school name -> (class, district)"""
    import csv
    mapping = {}
    try:
        with open(path, newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                school = row.get('School') or row.get('school')
                cls = row.get('Class') or row.get('class')
                district = row.get('District') or row.get('district')
                if school:
                    mapping[school.strip().lower()] = (cls.strip() if cls else None, district.strip() if district else None)
    except FileNotFoundError:
        return {}
    return mapping


def map_team_to_class(team_name: str, mapping: dict):
    """Try to map a team name to its class and district using the mapping.

    This does a case-insensitive exact or substring match to be forgiving of naming differences.
    Returns (class, district) or (None, None) if unknown.
    """
    if not team_name:
        return (None, None)

    key = team_name.strip().lower()

    # Exact match first
    if key in mapping:
        return mapping[key]

    # Try simplified forms: remove common suffixes like 'high school' or parentheticals
    import re
    simplified = re.sub(r"\s*\([^)]*\)", "", key)
    simplified = simplified.replace('high school', '').replace('hs', '').strip()
    if simplified in mapping:
        return mapping[simplified]

    # Try substring match (team contains school name)
    for school_key, val in mapping.items():
        if school_key in key or key in school_key:
            return val

    return (None, None)


def class_district_rankings_page(db: Database):
    """Page to show rankings of runners by Class and District"""
    st.header("Class & District Rankings")

    # Load reference
    ref_map = load_school_reference()
    if not ref_map:
        st.warning("School reference file not found at 'reference/missouri_schools.csv'. Rankings will be unavailable.")
        return

    # Filters
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        class_filter = st.selectbox("Class", ["All"] + sorted({v[0] for v in ref_map.values() if v[0]}))
    with col2:
        district_filter = st.selectbox("District", ["All"] + sorted({v[1] for v in ref_map.values() if v[1]}))
    with col3:
        top_n = st.number_input("Top N", min_value=5, max_value=200, value=25, step=5)

    # Gender tabs
    tab_boys, tab_girls, tab_all = st.tabs(["Boys", "Girls", "All"])

    # Get all individual results with valid times
    session = db.get_session()
    try:
        results = session.query(IndividualResult).join(Race).filter(
            IndividualResult.time_seconds.isnot(None)
        ).options(
            # eager load race and meet
            joinedload(IndividualResult.race).joinedload(Race.meet)
        ).all()
    except Exception as e:
        st.error(f"Database error: {e}")
        session.close()
        return

    # Build list with mapped class/district
    rows = []
    for r in results:
        team = str(r.team or "")
        cls, dist = map_team_to_class(team, ref_map)
        rows.append({
            "athlete": r.athlete_name,
            "team": team,
            "time": r.time,
            "time_seconds": r.time_seconds,
            "class": cls,
            "district": dist,
            "grade": r.year_grade,
            "race": r.race.name if r.race else None,
            "meet": r.race.meet.name if (r.race and r.race.meet) else None
        })

    session.close()

    import pandas as pd
    df = pd.DataFrame(rows)

    if df.empty:
        st.info("No individual results with valid times found in the database.")
        return

    # Apply filters
    if class_filter != "All":
        df = df[df['class'] == class_filter]
    if district_filter != "All":
        df = df[df['district'] == district_filter]

    if df.empty:
        st.warning("No results match the selected class/district filters.")
        return

    def show_filtered(df_in, gender_label: str):
        df_filtered = df_in
        if gender_label == 'Boys':
            df_filtered = df_filtered[df_filtered.get('gender', 'M') == 'M'] if 'gender' in df_filtered.columns else df_filtered[df_in.get('gender', 'M') == 'M']
        elif gender_label == 'Girls':
            df_filtered = df_filtered[df_filtered.get('gender', 'F') == 'F'] if 'gender' in df_filtered.columns else df_filtered[df_in.get('gender', 'F') == 'F']

        if df_filtered.empty:
            st.info(f"No {gender_label} results match the selected filters.")
            return

        df_sorted = df_filtered.sort_values('time_seconds', ascending=True).head(top_n)

        st.subheader(f"Top {top_n} Runners — {gender_label}")
        st.dataframe(df_sorted[['athlete', 'team', 'class', 'district', 'time', 'grade', 'race', 'meet']].reset_index(drop=True), hide_index=True, use_container_width=True)

        csv = df_sorted[['athlete', 'team', 'class', 'district', 'time', 'grade', 'race', 'meet']].to_csv(index=False)
        st.download_button(label=f"📥 Download {gender_label} CSV", data=csv, file_name=f"class_district_rankings_{gender_label}_{class_filter}_{district_filter}.csv", mime='text/csv')

    # Inject gender into df rows if available by querying Race.gender earlier; we didn't include it before — create it now
    # Note: results were loaded from ORM where Race.gender exists; we must ensure the dataframe has the 'gender' column
    if 'gender' not in df.columns:
        # Re-query to get genders mapped per row (lightweight mapping using race names)
        # Build a mapping from (team, athlete, time_seconds) -> gender by reusing the original results list
        # Re-run a light DB pass to attach genders
        session2 = db.get_session()
        try:
            orm_results = session2.query(IndividualResult).join(Race).filter(IndividualResult.time_seconds.isnot(None)).options(joinedload(IndividualResult.race)).all()
            gender_map = {}
            for r in orm_results:
                key = (str(r.athlete_name), str(r.team or ''), str(r.time_seconds) if r.time_seconds is not None else None)
                gender_map[key] = r.race.gender if r.race else None
        finally:
            session2.close()

        # Apply genders where possible
        def pick_gender(row):
            time_key = str(row['time_seconds']) if pd.notnull(row['time_seconds']) else None
            key = (str(row['athlete']), str(row['team']), time_key)
            return gender_map.get(key)

        genders = []
        for _, row in df.iterrows():
            genders.append(pick_gender(row))
        df['gender'] = genders

    with tab_boys:
        show_filtered(df, 'Boys')
    with tab_girls:
        show_filtered(df, 'Girls')
    with tab_all:
        show_filtered(df, 'All')


if __name__ == "__main__":
    main()
