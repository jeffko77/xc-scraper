#!/usr/bin/env python3
"""
Data cleaning script to identify and remove gender outliers based on time thresholds.

This script finds boys' times that ended up in girls' races (and vice versa) by analyzing
suspicious performance times that are statistically unlikely for the labeled gender.
"""

import os
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from database import Base, Race, IndividualResult
from typing import List, Tuple
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Time thresholds in seconds for 5K races
# These represent extremely fast/slow times that are likely misclassified
GIRLS_MIN_THRESHOLD = 930  # 15:30 - Extremely fast, likely boys
BOYS_MAX_THRESHOLD = 1500  # 25:00 - Very slow, possibly girls (less reliable)

# More aggressive thresholds for clear outliers
GIRLS_OBVIOUS_THRESHOLD = 960  # 16:00 - Obvious boys' times in girls' races
BOYS_OBVIOUS_THRESHOLD = 1440  # 24:00 - Obvious girls' times in boys' races


def get_database_session():
    """Create database session from environment"""
    db_url = os.environ.get('DB_URL')
    if not db_url:
        raise ValueError("DB_URL environment variable not set")

    # Convert to use psycopg3 driver (same as database.py)
    if db_url.startswith('postgresql://') and 'psycopg' not in db_url:
        db_url = db_url.replace('postgresql://', 'postgresql+psycopg://', 1)
    elif db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql+psycopg://', 1)

    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    return Session()


def find_girls_race_outliers(session, threshold: int = GIRLS_OBVIOUS_THRESHOLD) -> List[Tuple]:
    """Find suspiciously fast times in girls' races (likely boys)"""

    results = session.query(
        IndividualResult.id,
        IndividualResult.athlete_name,
        IndividualResult.team,
        IndividualResult.time,
        IndividualResult.time_seconds,
        Race.name.label('race_name'),
        Race.id.label('race_id')
    ).join(Race).filter(
        and_(
            Race.gender == 'F',  # Girls' races
            IndividualResult.time_seconds < threshold,  # Suspiciously fast
            IndividualResult.time_seconds.isnot(None)
        )
    ).order_by(IndividualResult.time_seconds).all()

    return results


def find_boys_race_outliers(session, threshold: int = BOYS_OBVIOUS_THRESHOLD) -> List[Tuple]:
    """Find suspiciously slow times in boys' races (possibly girls)"""

    results = session.query(
        IndividualResult.id,
        IndividualResult.athlete_name,
        IndividualResult.team,
        IndividualResult.time,
        IndividualResult.time_seconds,
        Race.name.label('race_name'),
        Race.id.label('race_id')
    ).join(Race).filter(
        and_(
            Race.gender == 'M',  # Boys' races
            IndividualResult.time_seconds > threshold,  # Suspiciously slow
            IndividualResult.time_seconds.isnot(None)
        )
    ).order_by(IndividualResult.time_seconds.desc()).all()

    return results


def analyze_outliers(session, girls_threshold: int = GIRLS_OBVIOUS_THRESHOLD, boys_threshold: int = BOYS_OBVIOUS_THRESHOLD):
    """Analyze and report on outliers without making changes"""

    print("\n" + "="*80)
    print("GENDER OUTLIER ANALYSIS")
    print("="*80)

    # Find girls' race outliers (boys' times)
    print(f"\n🔍 Searching for suspiciously FAST times in GIRLS' races (< {girls_threshold/60:.2f} min)...")
    girls_outliers = find_girls_race_outliers(session, girls_threshold)

    print(f"Found {len(girls_outliers)} outliers\n")

    if girls_outliers:
        print("Top 20 fastest (likely boys in girls' races):")
        print("-" * 80)
        for i, result in enumerate(girls_outliers[:20], 1):
            print(f"{i:2d}. {result.athlete_name:30s} | {result.team:25s} | {result.time:8s} | {result.race_name[:30]}")

    # Find boys' race outliers (girls' times) - less reliable
    print(f"\n🔍 Searching for suspiciously SLOW times in BOYS' races (> {boys_threshold/60:.2f} min)...")
    boys_outliers = find_boys_race_outliers(session, boys_threshold)

    print(f"Found {len(boys_outliers)} outliers\n")

    if boys_outliers:
        print("Top 20 slowest (possibly girls in boys' races):")
        print("-" * 80)
        for i, result in enumerate(boys_outliers[:20], 1):
            print(f"{i:2d}. {result.athlete_name:30s} | {result.team:25s} | {result.time:8s} | {result.race_name[:30]}")

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Boys' times in girls' races: {len(girls_outliers)}")
    print(f"Girls' times in boys' races: {len(boys_outliers)}")
    print(f"Total outliers found: {len(girls_outliers) + len(boys_outliers)}")
    print("="*80 + "\n")

    return girls_outliers, boys_outliers


def clean_outliers(session, girls_outliers: List, boys_outliers: List, dry_run: bool = True):
    """Delete outlier records from the database"""

    total_to_delete = len(girls_outliers) + len(boys_outliers)

    if total_to_delete == 0:
        print("✅ No outliers to clean!")
        return

    if dry_run:
        print(f"\n🔍 DRY RUN: Would delete {total_to_delete} records")
        print("   Run with --execute to actually delete these records")
        return

    print(f"\n⚠️  DELETING {total_to_delete} outlier records...")

    # Delete girls' race outliers
    if girls_outliers:
        outlier_ids = [r.id for r in girls_outliers]
        deleted = session.query(IndividualResult).filter(
            IndividualResult.id.in_(outlier_ids)
        ).delete(synchronize_session=False)
        print(f"   Deleted {deleted} boys' times from girls' races")

    # Delete boys' race outliers
    if boys_outliers:
        outlier_ids = [r.id for r in boys_outliers]
        deleted = session.query(IndividualResult).filter(
            IndividualResult.id.in_(outlier_ids)
        ).delete(synchronize_session=False)
        print(f"   Deleted {deleted} girls' times from boys' races")

    session.commit()
    print("✅ Database cleaned successfully!")


def export_outliers_csv(girls_outliers: List, boys_outliers: List, filename: str = "outliers_report.csv"):
    """Export outliers to CSV for manual review"""

    import csv

    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Type', 'ID', 'Athlete', 'Team', 'Time', 'Time (sec)', 'Race Name', 'Race ID'])

        for result in girls_outliers:
            writer.writerow([
                'Boys in Girls Race',
                result.id,
                result.athlete_name,
                result.team,
                result.time,
                result.time_seconds,
                result.race_name,
                result.race_id
            ])

        for result in boys_outliers:
            writer.writerow([
                'Girls in Boys Race',
                result.id,
                result.athlete_name,
                result.team,
                result.time,
                result.time_seconds,
                result.race_name,
                result.race_id
            ])

    print(f"\n📄 Exported outliers to {filename}")


def main():
    parser = argparse.ArgumentParser(
        description='Clean gender outliers from cross-country results database'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Actually delete records (default is dry-run)'
    )
    parser.add_argument(
        '--export',
        metavar='FILE',
        help='Export outliers to CSV file'
    )
    parser.add_argument(
        '--girls-threshold',
        type=int,
        default=GIRLS_OBVIOUS_THRESHOLD,
        help=f'Threshold for girls races in seconds (default: {GIRLS_OBVIOUS_THRESHOLD})'
    )
    parser.add_argument(
        '--boys-threshold',
        type=int,
        default=BOYS_OBVIOUS_THRESHOLD,
        help=f'Threshold for boys races in seconds (default: {BOYS_OBVIOUS_THRESHOLD})'
    )

    args = parser.parse_args()

    # Get database session
    session = get_database_session()

    try:
        # Analyze outliers with specified thresholds
        girls_outliers, boys_outliers = analyze_outliers(
            session,
            girls_threshold=args.girls_threshold,
            boys_threshold=args.boys_threshold
        )

        # Export if requested
        if args.export:
            export_outliers_csv(girls_outliers, boys_outliers, args.export)

        # Clean outliers
        clean_outliers(session, girls_outliers, boys_outliers, dry_run=not args.execute)

    finally:
        session.close()


if __name__ == '__main__':
    main()
