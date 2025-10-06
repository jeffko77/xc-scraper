#!/usr/bin/env python3
"""
Batch import utility for importing multiple MileSplit URLs
"""
import sys
import argparse
from pathlib import Path
from scraper import MileSplitScraper
from database import Database


def main():
    parser = argparse.ArgumentParser(description='Batch import MileSplit results')
    parser.add_argument('file', help='Text file with one URL per line')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--skip-errors', action='store_true', help='Continue on errors')

    args = parser.parse_args()

    # Check file exists
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File '{args.file}' not found")
        sys.exit(1)

    # Read URLs
    urls = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                urls.append(line)

    if not urls:
        print("No URLs found in file")
        sys.exit(1)

    print(f"Found {len(urls)} URL(s) to import")

    # Initialize
    scraper = MileSplitScraper(verbose=args.verbose)
    db = Database()
    db.create_tables()

    # Process each URL
    success_count = 0
    error_count = 0

    for idx, url in enumerate(urls, 1):
        print(f"\n[{idx}/{len(urls)}] Processing: {url}")

        try:
            # Scrape
            races = scraper.scrape_url(url)
            print(f"  ✓ Scraped {len(races)} race(s)")

            # Save
            meet_id = db.save_results(url, races)
            print(f"  ✓ Saved to database (Meet ID: {meet_id})")

            success_count += 1

        except Exception as e:
            error_count += 1
            print(f"  ✗ Error: {str(e)}")

            if not args.skip_errors:
                print("\nStopping due to error (use --skip-errors to continue)")
                sys.exit(1)

    # Summary
    print(f"\n{'='*50}")
    print(f"Batch import complete")
    print(f"  Success: {success_count}")
    print(f"  Errors: {error_count}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
