"""
Database models and operations for XC results
"""
import os
from datetime import datetime
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session, joinedload
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

Base = declarative_base()


class Meet(Base):
    """Meet information"""
    __tablename__ = 'meets'

    id = Column(Integer, primary_key=True)
    name = Column(String(500))
    date = Column(String(100))
    url = Column(String(1000), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    exclude_from_rankings = Column(Integer, default=0)  # 0 = include, 1 = exclude

    races = relationship("Race", back_populates="meet", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Meet(name='{self.name}', date='{self.date}')>"


class Race(Base):
    """Race information"""
    __tablename__ = 'races'

    id = Column(Integer, primary_key=True)
    meet_id = Column(Integer, ForeignKey('meets.id'), nullable=False)
    name = Column(String(500), nullable=False)
    gender = Column(String(1))  # M or F
    race_type = Column(String(50))  # Varsity, JV, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

    meet = relationship("Meet", back_populates="races")
    team_scores = relationship("TeamScore", back_populates="race", cascade="all, delete-orphan")
    individual_results = relationship("IndividualResult", back_populates="race", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Race(name='{self.name}', gender='{self.gender}')>"


class TeamScore(Base):
    """Team scores for a race"""
    __tablename__ = 'team_scores'

    id = Column(Integer, primary_key=True)
    race_id = Column(Integer, ForeignKey('races.id'), nullable=False)
    place = Column(Integer, nullable=False)
    team_name = Column(String(500), nullable=False)
    points = Column(Integer, nullable=False)

    race = relationship("Race", back_populates="team_scores")

    # Index for faster queries
    __table_args__ = (
        Index('idx_team_name', 'team_name'),
        Index('idx_race_team', 'race_id', 'team_name'),
    )

    def __repr__(self):
        return f"<TeamScore(place={self.place}, team='{self.team_name}', points={self.points})>"


class IndividualResult(Base):
    """Individual athlete results"""
    __tablename__ = 'individual_results'

    id = Column(Integer, primary_key=True)
    race_id = Column(Integer, ForeignKey('races.id'), nullable=False)
    place = Column(Integer, nullable=False)
    athlete_name = Column(String(500), nullable=False)
    year_grade = Column(String(10))
    team = Column(String(500), nullable=False)
    time = Column(String(20), nullable=False)
    time_seconds = Column(Float)  # Time converted to seconds for sorting

    race = relationship("Race", back_populates="individual_results")

    # Indexes for faster queries
    __table_args__ = (
        Index('idx_athlete_name', 'athlete_name'),
        Index('idx_team', 'team'),
        Index('idx_race_athlete', 'race_id', 'athlete_name'),
        Index('idx_time_seconds', 'time_seconds'),
    )

    def __repr__(self):
        return f"<IndividualResult(place={self.place}, athlete='{self.athlete_name}', time='{self.time}')>"


class Database:
    """Database operations manager"""

    def __init__(self, db_url: Optional[str] = None):
        """Initialize database connection"""
        self.db_url = db_url or os.getenv('DB_URL')
        if not self.db_url:
            raise ValueError("DB_URL environment variable not set")

        # Convert postgresql:// to postgresql+psycopg:// for psycopg3
        if self.db_url.startswith('postgresql://'):
            self.db_url = self.db_url.replace('postgresql://', 'postgresql+psycopg://', 1)
        elif self.db_url.startswith('postgres://'):
            self.db_url = self.db_url.replace('postgres://', 'postgresql+psycopg://', 1)

        self.engine = create_engine(self.db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()

    def save_results(self, url: str, races_data: List) -> int:
        """
        Save scraped results to database
        Returns the meet_id
        """
        session = self.get_session()
        try:
            # Check if meet already exists
            meet = session.query(Meet).filter_by(url=url).first()

            if meet:
                # Update existing meet
                if races_data and races_data[0].meet_name:
                    meet.name = races_data[0].meet_name
                if races_data and races_data[0].meet_date:
                    meet.date = races_data[0].meet_date

                # Delete old races (cascade will delete related data)
                for race in meet.races:
                    session.delete(race)
            else:
                # Create new meet
                meet_name = races_data[0].meet_name if races_data else "Unknown Meet"
                meet_date = races_data[0].meet_date if races_data else None

                meet = Meet(
                    name=meet_name,
                    date=meet_date,
                    url=url
                )
                session.add(meet)
                session.flush()  # Get meet.id

            # Add races
            for race_data in races_data:
                race = Race(
                    meet_id=meet.id,
                    name=race_data.race_name,
                    gender=race_data.gender,
                    race_type=race_data.race_type
                )
                session.add(race)
                session.flush()  # Get race.id

                # Add team scores
                for ts in race_data.team_scores:
                    team_score = TeamScore(
                        race_id=race.id,
                        place=ts.place,
                        team_name=ts.team_name,
                        points=ts.points
                    )
                    session.add(team_score)

                # Add individual results
                for ir in race_data.individual_results:
                    result = IndividualResult(
                        race_id=race.id,
                        place=ir.place,
                        athlete_name=ir.athlete_name,
                        year_grade=ir.year_grade,
                        team=ir.team,
                        time=ir.time,
                        time_seconds=ir.time_to_seconds()
                    )
                    session.add(result)

            session.commit()
            return meet.id

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def search_athlete(self, name: str, gender: Optional[str] = None) -> List[IndividualResult]:
        """Search for athlete by name"""
        session = self.get_session()
        try:
            query = session.query(IndividualResult).options(
                joinedload(IndividualResult.race).joinedload(Race.meet)
            ).filter(
                IndividualResult.athlete_name.ilike(f'%{name}%')
            )

            if gender:
                query = query.join(Race).filter(Race.gender == gender)

            results = query.all()
            return results
        finally:
            session.close()

    def get_leaderboard(self, gender: Optional[str] = None, team: Optional[str] = None,
                       limit: int = 100) -> List[IndividualResult]:
        """Get top times leaderboard"""
        session = self.get_session()
        try:
            query = session.query(IndividualResult).options(
                joinedload(IndividualResult.race).joinedload(Race.meet)
            ).join(Race)

            if gender:
                query = query.filter(Race.gender == gender)

            if team:
                query = query.filter(IndividualResult.team.ilike(f'%{team}%'))

            # Filter out invalid times
            query = query.filter(IndividualResult.time_seconds.isnot(None))

            # Order by time
            query = query.order_by(IndividualResult.time_seconds.asc())

            results = query.limit(limit).all()
            return results
        finally:
            session.close()

    def get_all_teams(self) -> List[str]:
        """Get list of all unique team names"""
        session = self.get_session()
        try:
            teams = session.query(IndividualResult.team).distinct().order_by(IndividualResult.team).all()
            return [team[0] for team in teams]
        finally:
            session.close()

    def get_meets(self) -> List[Meet]:
        """Get all meets"""
        session = self.get_session()
        try:
            meets = session.query(Meet).options(
                joinedload(Meet.races)
            ).order_by(Meet.created_at.desc()).all()
            return meets
        finally:
            session.close()

    def toggle_meet_exclusion(self, meet_id: int) -> bool:
        """Toggle meet exclusion from rankings. Returns new exclusion state."""
        session = self.get_session()
        try:
            meet = session.query(Meet).filter_by(id=meet_id).first()
            if meet:
                meet.exclude_from_rankings = 1 if meet.exclude_from_rankings == 0 else 0
                session.commit()
                return bool(meet.exclude_from_rankings)
            return False
        finally:
            session.close()

    def get_rankings_by_class_district(self, class_name: str, district: str,
                                       gender: Optional[str] = None,
                                       limit: int = 50) -> List[IndividualResult]:
        """Get rankings for a specific class and district"""
        import csv
        import os

        # Load school classifications
        csv_path = os.path.join(os.path.dirname(__file__), 'reference', 'missouri_schools.csv')
        schools_in_district = []

        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Class'] == class_name and row['District'] == district:
                        schools_in_district.append(row['School'])
        except FileNotFoundError:
            pass  # If CSV not found, return empty list

        if not schools_in_district:
            return []

        session = self.get_session()
        try:
            query = session.query(IndividualResult).options(
                joinedload(IndividualResult.race).joinedload(Race.meet)
            ).join(Race).join(Meet)

            # Filter by gender
            if gender:
                query = query.filter(Race.gender == gender)

            # Exclude meets marked for exclusion
            query = query.filter(Meet.exclude_from_rankings == 0)

            # Filter by schools in this district
            query = query.filter(IndividualResult.team.in_(schools_in_district))

            # Filter out invalid times
            query = query.filter(IndividualResult.time_seconds.isnot(None))

            # Order by time
            query = query.order_by(IndividualResult.time_seconds.asc())

            results = query.limit(limit).all()
            return results
        finally:
            session.close()
