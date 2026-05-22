from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/sports_ai")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class Match(Base):
    __tablename__ = "matches"
    id         = Column(Integer, primary_key=True)
    home_team  = Column(String(255))
    away_team  = Column(String(255))
    home_goals = Column(Integer)
    away_goals = Column(Integer)
    home_xg    = Column(Float, nullable=True)
    away_xg    = Column(Float, nullable=True)
    match_date = Column(DateTime)
    league     = Column(String(255))
    season     = Column(String(50))


class TeamStats(Base):
    __tablename__ = "team_stats"
    id               = Column(Integer, primary_key=True)
    team_name        = Column(String(255), unique=True)
    avg_goals        = Column(Float)
    avg_xg           = Column(Float)
    avg_xg_against   = Column(Float)
    avg_possession   = Column(Float)
    defensive_rating = Column(Float)
    elo_rating       = Column(Float, default=1500.0)


class PlayerStats(Base):
    __tablename__ = "player_stats"
    id          = Column(Integer, primary_key=True)
    player_name = Column(String(255))
    team_name   = Column(String(255))
    goals       = Column(Integer)
    assists     = Column(Integer)
    xg          = Column(Float)
    xa          = Column(Float)
    rating      = Column(Float)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    Base.metadata.create_all(bind=engine)
