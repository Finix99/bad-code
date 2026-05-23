from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
import os

# ---------------------------------------------------
# DATABASE URL
# ---------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

# Local fallback (prevents Railway startup crash)
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./sports_ai.db"
    print("WARNING: Using SQLite fallback database")

# Railway compatibility fix
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql://",
        1
    )

# ---------------------------------------------------
# ENGINE
# ---------------------------------------------------

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)

# ---------------------------------------------------
# BASE
# ---------------------------------------------------

class Base(DeclarativeBase):
    pass

# ---------------------------------------------------
# MATCHES TABLE
# ---------------------------------------------------

class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True)

    home_team = Column(String(255))
    away_team = Column(String(255))

    home_goals = Column(Integer)
    away_goals = Column(Integer)

    home_xg = Column(Float, nullable=True)
    away_xg = Column(Float, nullable=True)

    match_date = Column(DateTime)

    league = Column(String(255))
    season = Column(String(50))

# ---------------------------------------------------
# TEAM STATS TABLE
# ---------------------------------------------------

class TeamStats(Base):
    __tablename__ = "team_stats"

    id = Column(Integer, primary_key=True)

    team_name = Column(String(255), unique=True)

    avg_goals = Column(Float)
    avg_xg = Column(Float)
    avg_xg_against = Column(Float)

    avg_possession = Column(Float)

    defensive_rating = Column(Float)

    elo_rating = Column(Float, default=1500.0)

# ---------------------------------------------------
# PLAYER STATS TABLE
# ---------------------------------------------------

class PlayerStats(Base):
    __tablename__ = "player_stats"

    id = Column(Integer, primary_key=True)

    player_name = Column(String(255))
    team_name = Column(String(255))

    goals = Column(Integer)
    assists = Column(Integer)

    xg = Column(Float)
    xa = Column(Float)

    rating = Column(Float)

# ---------------------------------------------------
# DATABASE SESSION
# ---------------------------------------------------

def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()

# ---------------------------------------------------
# CREATE TABLES
# ---------------------------------------------------

def create_tables():
    Base.metadata.create_all(bind=engine)
