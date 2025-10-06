#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for the MileSplit scraper
"""
import sys
import io
from scraper import MileSplitScraper, validate_time_format

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def test_scraper():
    """Test the scraper with example URL"""
    print("Testing MileSplit Scraper")
    print("=" * 50)

    # Test URL
    url = "https://mo.milesplit.com/meets/703864-frank-schultz-invitational-2025/results/1221124/raw"

    print(f"\nTesting with URL: {url}")

    # Create scraper
    scraper = MileSplitScraper(verbose=True)

    try:
        # Scrape results
        print("\n--- Scraping Results ---")
        races = scraper.scrape_url(url)

        print(f"\n✓ Successfully scraped {len(races)} race(s)\n")

        # Display results
        for idx, race in enumerate(races, 1):
            print(f"\n{'='*50}")
            print(f"Race {idx}: {race.race_name}")
            print(f"Gender: {race.gender or 'Unknown'}")
            print(f"Type: {race.race_type or 'Unknown'}")
            print(f"{'='*50}")

            # Team scores
            print(f"\nTeam Scores ({len(race.team_scores)} teams):")
            for ts in race.team_scores[:5]:  # Show top 5
                print(f"  {ts.place}. {ts.team_name} - {ts.points} pts")
            if len(race.team_scores) > 5:
                print(f"  ... and {len(race.team_scores) - 5} more teams")

            # Individual results
            print(f"\nIndividual Results ({len(race.individual_results)} athletes):")
            for ir in race.individual_results[:10]:  # Show top 10
                time_valid = validate_time_format(ir.time)
                time_seconds = ir.time_to_seconds()
                print(f"  {ir.place}. {ir.athlete_name} ({ir.year_grade}) - {ir.team} - {ir.time} "
                      f"[{time_seconds:.2f}s] {'✓' if time_valid else '✗'}")
            if len(race.individual_results) > 10:
                print(f"  ... and {len(race.individual_results) - 10} more results")

        print(f"\n{'='*50}")
        print("Test completed successfully! ✓")
        print(f"{'='*50}")

    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = test_scraper()
    exit(0 if success else 1)
