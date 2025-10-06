#!/usr/bin/env python3
"""
Migration script to add exclude_from_rankings column to meets table
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
                WHERE table_name='meets' AND column_name='exclude_from_rankings'
            """))

            if result.fetchone():
                print("Column 'exclude_from_rankings' already exists. No migration needed.")
                return

            # Add the column
            print("Adding 'exclude_from_rankings' column to meets table...")
            conn.execute(text("""
                ALTER TABLE meets
                ADD COLUMN exclude_from_rankings INTEGER DEFAULT 0
            """))
            conn.commit()
            print("Migration completed successfully!")

    except Exception as e:
        print(f"Error during migration: {e}")
        raise

if __name__ == "__main__":
    migrate()
