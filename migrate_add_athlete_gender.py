#!/usr/bin/env python3
"""
Migration script to add athlete_gender column to individual_results table
and populate it with the race gender as a starting point.
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def migrate():
    db_url = os.getenv('DB_URL')
    if not db_url:
        print("Error: DB_URL environment variable not set")
        return

    # Convert to psycopg if needed
    if db_url.startswith('postgresql://'):
        db_url = db_url.replace('postgresql://', 'postgresql+psycopg://', 1)
    elif db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql+psycopg://', 1)

    engine = create_engine(db_url)

    try:
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='individual_results' AND column_name='athlete_gender'
            """))

            if result.fetchone():
                print("Column 'athlete_gender' already exists. No migration needed.")
                return

            # Add the column
            print("Adding 'athlete_gender' column to individual_results table...")
            conn.execute(text("""
                ALTER TABLE individual_results
                ADD COLUMN athlete_gender VARCHAR(1)
            """))

            # Populate with race gender as starting point
            print("Populating athlete_gender from race.gender...")
            conn.execute(text("""
                UPDATE individual_results
                SET athlete_gender = races.gender
                FROM races
                WHERE individual_results.race_id = races.id
            """))

            # Create index for faster queries
            print("Creating index on athlete_gender...")
            conn.execute(text("""
                CREATE INDEX idx_athlete_gender ON individual_results(athlete_gender)
            """))

            conn.commit()
            print("Migration completed successfully!")
            print("Note: Run clean_gender_outliers.py to identify and clean misclassified records.")

    except Exception as e:
        print(f"Error during migration: {e}")
        raise

if __name__ == "__main__":
    migrate()
