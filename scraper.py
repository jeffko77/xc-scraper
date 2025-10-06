"""
MileSplit cross country results scraper
"""
import re
import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TeamScore:
    """Team score information"""
    place: int
    team_name: str
    points: int


@dataclass
class IndividualResult:
    """Individual athlete result"""
    place: int
    athlete_name: str
    year_grade: str
    team: str
    time: str

    def time_to_seconds(self) -> Optional[float]:
        """Convert time string MM:SS.SS to seconds"""
        try:
            parts = self.time.split(':')
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
        except (ValueError, AttributeError):
            pass
        return None


@dataclass
class RaceResults:
    """Complete race results"""
    race_name: str
    meet_name: Optional[str] = None
    meet_date: Optional[str] = None
    team_scores: List[TeamScore] = field(default_factory=list)
    individual_results: List[IndividualResult] = field(default_factory=list)

    @property
    def gender(self) -> Optional[str]:
        """Extract gender from race name"""
        race_lower = self.race_name.lower()
        if 'women' in race_lower or 'girls' in race_lower:
            return 'F'
        elif 'men' in race_lower or 'boys' in race_lower:
            return 'M'
        return None

    @property
    def race_type(self) -> Optional[str]:
        """Extract race type (Varsity/JV) from race name"""
        race_lower = self.race_name.lower()
        if 'varsity' in race_lower:
            return 'Varsity'
        elif 'jv' in race_lower or 'junior varsity' in race_lower:
            return 'JV'
        return None


class MileSplitScraper:
    """Scraper for MileSplit cross country results"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def log(self, message: str):
        """Print log message if verbose mode is enabled"""
        if self.verbose:
            print(f"[LOG] {message}")

    def convert_to_raw_url(self, url: str) -> str:
        """Convert formatted URL to raw URL"""
        if '/formatted/' in url:
            url = url.replace('/formatted/', '/raw')
            self.log(f"Converted to raw URL: {url}")
        return url

    def fetch_page(self, url: str) -> str:
        """Fetch the page content"""
        try:
            self.log(f"Fetching URL: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            self.log(f"Successfully fetched page ({len(response.text)} bytes)")
            return response.text
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch URL: {str(e)}")

    def parse_meet_info(self, content: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract meet name and date from page content"""
        meet_name = None
        meet_date = None

        # Try to extract meet name from title or header
        title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
        if title_match:
            meet_name = title_match.group(1).strip()
            # Clean up common patterns
            meet_name = re.sub(r'\s*-\s*MileSplit.*$', '', meet_name)

        return meet_name, meet_date

    def parse_raw_results(self, content: str) -> List[RaceResults]:
        """Parse raw results from MileSplit page"""
        races = []
        meet_name, meet_date = self.parse_meet_info(content)

        # Try Format 1: "Mens 5,000 Meters Varsity Boys" pattern
        race_pattern_1 = r'((?:Mens|Womens)\s+[\d,]+\s+Meters.*?)(?=(?:Mens|Womens)\s+[\d,]+\s+Meters|$)'
        race_sections = re.findall(race_pattern_1, content, re.DOTALL | re.IGNORECASE)

        if race_sections:
            self.log(f"Using Format 1 (Mens/Womens Meters pattern)")
            for section in race_sections:
                race = self._parse_race_section(section, meet_name, meet_date)
                if race:
                    races.append(race)
        else:
            # Try Format 2: "Event N  Boys/Girls 5k Run CC" pattern
            self.log(f"Trying Format 2 (Event N pattern)")
            race_pattern_2 = r'Event\s+\d+\s+(?:Boys|Girls).*?(?=Event\s+\d+|$)'
            race_sections = re.findall(race_pattern_2, content, re.DOTALL | re.IGNORECASE)

            if race_sections:
                for section in race_sections:
                    race = self._parse_event_section(section, meet_name, meet_date)
                    if race:
                        races.append(race)
            else:
                # Try Format 3: Simple race name pattern
                # Examples: "Freshman Girls 5k Run Results", "Girls JV 3k Run White Results", "Girls Varsity 5k Run Green Results"
                self.log(f"Trying Format 3 (Simple race name pattern)")
                # Support various patterns:
                # - "Freshman Girls 5k Run Results"
                # - "Girls JV 3k Run White Results"
                # - "Girls Varsity 5k Run Green Results"
                # Pattern: [Type]? Boys/Girls [Type]? [Distance]k Run [Color]? Results
                race_pattern_3 = r'(?:Freshman|Sophomore|Junior|Senior|Varsity|JV|Junior Varsity)?\s*(?:Boys|Girls|Men|Women)\s+(?:Freshman|Sophomore|Junior|Senior|Varsity|JV|Junior Varsity)?\s*(?:3k|5k|[\d\.]+k)\s+Run\s+(?:\w+\s+)?Results.*?(?=(?:Freshman|Sophomore|Junior|Senior|Varsity|JV)?\s*(?:Boys|Girls|Men|Women)\s+(?:Freshman|Sophomore|Junior|Senior|Varsity|JV)?\s*(?:3k|5k|[\d\.]+k)\s+Run\s+(?:\w+\s+)?Results|$)'
                race_sections = re.findall(race_pattern_3, content, re.DOTALL | re.IGNORECASE)

                for section in race_sections:
                    race = self._parse_simple_section(section, meet_name, meet_date)
                    if race:
                        races.append(race)

        self.log(f"Parsed {len(races)} races")
        return races

    def _parse_race_section(self, section: str, meet_name: Optional[str],
                           meet_date: Optional[str]) -> Optional[RaceResults]:
        """Parse a single race section"""
        lines = section.strip().split('\n')
        if not lines:
            return None

        # First line should be the race name
        race_name = lines[0].strip()
        self.log(f"Parsing race: {race_name}")

        race = RaceResults(race_name=race_name, meet_name=meet_name, meet_date=meet_date)

        i = 1
        while i < len(lines):
            line = lines[i].strip()

            # Check for "Team Scores" section
            if 'Team Scores' in line:
                i += 1
                i = self._parse_team_scores(lines, i, race)

            # Check for individual results (after team scores or standalone)
            elif line.startswith('Pl') and 'Athlete' in line:
                i += 1
                i = self._parse_individual_results(lines, i, race)
            else:
                i += 1

        return race

    def _parse_team_scores(self, lines: List[str], start_idx: int,
                          race: RaceResults) -> int:
        """Parse team scores section"""
        idx = start_idx

        # Skip header and separator lines
        while idx < len(lines) and ('===' in lines[idx] or 'Pl' in lines[idx]):
            idx += 1

        # Parse team score lines
        while idx < len(lines):
            line = lines[idx].strip()

            # Stop at empty line or next section
            if not line or '===' in line or line.startswith('Pl'):
                break

            # Parse team score: "1 Rockhurst 40"
            match = re.match(r'^(\d+)\s+(.+?)\s+(\d+)$', line)
            if match:
                place = int(match.group(1))
                team_name = match.group(2).strip()
                points = int(match.group(3))
                race.team_scores.append(TeamScore(place, team_name, points))
                self.log(f"  Team: {place}. {team_name} - {points} pts")

            idx += 1

        return idx

    def _parse_individual_results(self, lines: List[str], start_idx: int,
                                  race: RaceResults) -> int:
        """Parse individual results section"""
        idx = start_idx

        # Skip separator lines
        while idx < len(lines) and '===' in lines[idx]:
            idx += 1

        # Parse individual result lines
        while idx < len(lines):
            line = lines[idx].strip()

            # Stop at empty line or next major section
            if not line or ('Team Scores' in line and idx > start_idx):
                break

            # Parse result: "1 Alex Cravens 12 Rockhurst 15:54.29"
            # Handle various formats including DNF, DNS, etc.
            match = re.match(r'^(\d+)\s+(.+?)\s+(\d+|SR|JR|SO|FR)\s+(.+?)\s+([\d:\.]+|DNF|DNS|DQ)$', line)
            if match:
                place = int(match.group(1))
                athlete = match.group(2).strip()
                year_grade = match.group(3).strip()
                team = match.group(4).strip()
                time = match.group(5).strip()

                race.individual_results.append(
                    IndividualResult(place, athlete, year_grade, team, time)
                )
                self.log(f"  Result: {place}. {athlete} ({team}) - {time}")

            idx += 1

        return idx

    def _parse_event_section(self, section: str, meet_name: Optional[str],
                            meet_date: Optional[str]) -> Optional[RaceResults]:
        """Parse Event N format section (alternate MileSplit format)"""
        lines = section.strip().split('\n')
        if not lines:
            return None

        # First line should be the event name: "Event 1  Boys 5k Run CC Varsity"
        race_name = lines[0].strip()
        self.log(f"Parsing race: {race_name}")

        race = RaceResults(race_name=race_name, meet_name=meet_name, meet_date=meet_date)

        i = 1
        while i < len(lines):
            line = lines[i].strip()

            # Check for "Team Scores" section
            if 'Team Scores' in line or (line.startswith('Rank') and 'Team' in line):
                i += 1
                i = self._parse_event_team_scores(lines, i, race)

            # Check for individual results header: "Name                    Year School"
            elif 'Name' in line and 'Year' in line and 'School' in line:
                i += 1
                i = self._parse_event_individual_results(lines, i, race)
            else:
                i += 1

        return race

    def _parse_event_team_scores(self, lines: List[str], start_idx: int,
                                 race: RaceResults) -> int:
        """Parse team scores in Event format"""
        idx = start_idx

        # Skip header and separator lines
        while idx < len(lines) and ('===' in lines[idx] or 'Rank' in lines[idx]):
            idx += 1

        # Parse team score lines
        # Format: "   1 Parkway West                 35    1    4    7   10   13   18   29"
        while idx < len(lines):
            line = lines[idx].strip()

            # Stop at empty line or next section
            if not line or '===' in line or line.startswith('Event') or 'Name' in line:
                break

            # Skip lines with "Total Time" or "Average"
            if 'Total Time' in line or 'Average' in line:
                idx += 1
                continue

            # Parse team score: rank, team name, total points
            match = re.match(r'^\s*(\d+)\s+(.+?)\s+(\d+)\s+', line)
            if match:
                place = int(match.group(1))
                team_name = match.group(2).strip()
                points = int(match.group(3))
                race.team_scores.append(TeamScore(place, team_name, points))
                self.log(f"  Team: {place}. {team_name} - {points} pts")

            idx += 1

        return idx

    def _parse_event_individual_results(self, lines: List[str], start_idx: int,
                                       race: RaceResults) -> int:
        """Parse individual results in Event format"""
        idx = start_idx

        # Skip separator lines
        while idx < len(lines) and '===' in lines[idx]:
            idx += 1

        # Parse individual result lines
        # Format: "  1 Patten, Wade              12 Parkway West          16:15.54    1"
        while idx < len(lines):
            line = lines[idx].strip()

            # Stop at empty line or next major section
            if not line or line.startswith('Event') or 'Team Scores' in line:
                break

            # Skip separator lines
            if '===' in line or line.startswith('Rank'):
                idx += 1
                continue

            # Parse result: place, name (Last, First), year, school, time, points
            match = re.match(r'^\s*(\d+)\s+(.+?)\s+(\d+|SR|JR|SO|FR)\s+(.+?)\s+([\d:\.]+|DNF|DNS|DQ)', line)
            if match:
                place = int(match.group(1))
                athlete = match.group(2).strip()
                year_grade = match.group(3).strip()
                team = match.group(4).strip()
                time = match.group(5).strip()

                race.individual_results.append(
                    IndividualResult(place, athlete, year_grade, team, time)
                )
                self.log(f"  Result: {place}. {athlete} ({team}) - {time}")

            idx += 1

        return idx

    def _parse_simple_section(self, section: str, meet_name: Optional[str],
                             meet_date: Optional[str]) -> Optional[RaceResults]:
        """Parse simple format section (e.g., 'Freshman Girls 5k Run Results')"""
        lines = section.strip().split('\n')
        if not lines:
            return None

        # First line should be the race name
        race_name = lines[0].strip()
        self.log(f"Parsing race: {race_name}")

        race = RaceResults(race_name=race_name, meet_name=meet_name, meet_date=meet_date)

        i = 1
        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines and separator lines
            if not line or '===' in line:
                i += 1
                continue

            # Skip header line
            if 'Pl' in line and 'Athlete' in line and 'Team' in line:
                i += 1
                continue

            # Parse individual result line
            # Format: "   1 Macailyn TOWNSEND         FR Liberty (Wentzville)                       22:06.6"
            match = re.match(r'^\s*(\d+)\s+(.+?)\s+(FR|SO|JR|SR|\d+)\s+(.+?)\s+([\d:\.]+|DNF|DNS|DQ)\s*$', line)
            if match:
                place = int(match.group(1))
                athlete = match.group(2).strip()
                year_grade = match.group(3).strip()
                team = match.group(4).strip()
                time = match.group(5).strip()

                race.individual_results.append(
                    IndividualResult(place, athlete, year_grade, team, time)
                )
                self.log(f"  Result: {place}. {athlete} ({team}) - {time}")

            i += 1

        return race

    def scrape_url(self, url: str) -> List[RaceResults]:
        """Main method to scrape a MileSplit URL"""
        # Convert to raw URL if needed
        url = self.convert_to_raw_url(url)

        # Fetch the page
        content = self.fetch_page(url)

        # Parse results
        races = self.parse_raw_results(content)

        if not races:
            raise Exception("No race results found on page")

        return races


def validate_time_format(time_str: str) -> bool:
    """Validate time format MM:SS.SS"""
    pattern = r'^\d{1,2}:\d{2}\.\d{2}$'
    return bool(re.match(pattern, time_str))
