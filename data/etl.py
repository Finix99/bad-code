"""
ETL: ingest Football-Data.co.uk CSV files into PostgreSQL.

Usage:
    python etl.py --file data/E0.csv --league "Premier League" --season "2023-24"
"""

import argparse
import os
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

# ---------------------------------------------------
# PATH FIX (SAFE IMPORTS)
# ---------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from models.database import Match, TeamStats, Base  # FIXED IMPORT

# ---------------------------------------------------
# DATABASE (RAILWAY SAFE)
# ---------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set (Railway Postgres missing)")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# ---------------------------------------------------
# COLUMN MAP
# ---------------------------------------------------

COLUMN_MAP = {
    "HomeTeam": "home_team",
    "AwayTeam": "away_team",
    "FTHG": "home_goals",
    "FTAG": "away_goals",
    "Date": "match_date",
}

# ---------------------------------------------------
# LOAD CSV
# ---------------------------------------------------

def load_csv(path: str, league: str, season: str):

    df = pd.read_csv(path)
    df = df.rename(columns=COLUMN_MAP)

    # xG handling (optional)
    if "xG" in df.columns:
        df["home_xg"] = df["xG"]
        df["away_xg"] = df["xGA"] if "xGA" in df.columns else None
    else:
        df["home_xg"] = None
        df["away_xg"] = None

    df["match_date"] = pd.to_datetime(df["match_date"], dayfirst=True, errors="coerce")

    df["league"] = league
    df["season"] = season

    df = df.dropna(subset=["home_team", "away_team", "home_goals", "away_goals"])

    return df

# ---------------------------------------------------
# TEAM STATS
# ---------------------------------------------------

def compute_team_stats(df: pd.DataFrame):

    stats = {}

    for team in pd.concat([df["home_team"], df["away_team"]]).unique():

        home = df[df["home_team"] == team]
        away = df[df["away_team"] == team]

        gf = list(home["home_goals"]) + list(away["away_goals"])
        ga = list(home["away_goals"]) + list(away["home_goals"])

        xg_for = list(home["home_xg"].dropna()) + list(away["away_xg"].dropna())
        xg_against = list(home["away_xg"].dropna()) + list(away["home_xg"].dropna())

        stats[team] = {
            "avg_goals": round(sum(gf) / len(gf), 3) if gf else 0,
            "avg_xg": round(sum(xg_for) / len(xg_for), 3) if xg_for else 0,
            "avg_xg_against": round(sum(xg_against) / len(xg_against), 3) if xg_against else 0,
            "avg_possession": 0.0,
            "defensive_rating": round(1 - (sum(ga) / len(ga) / 3), 3) if ga else 0.5,
            "elo_rating": 1500.0,
        }

    return stats

# ---------------------------------------------------
# MAIN INGESTION
# ---------------------------------------------------

def ingest(path: str, league: str, season: str):

    Base.metadata.create_all(bind=engine)

    df = load_csv(path, league, season)

    print(f"Loaded {len(df)} matches")

    with Session(engine) as session:

        # ---------------------------------------------------
        # INSERT MATCHES (WITH DUPLICATE CHECK)
        # ---------------------------------------------------

        inserted = 0

        for _, row in df.iterrows():

            exists = session.query(Match).filter_by(
                home_team=row["home_team"],
                away_team=row["away_team"],
                match_date=row["match_date"]
            ).first()

            if exists:
                continue

            match = Match(
                home_team=row["home_team"],
                away_team=row["away_team"],
                home_goals=int(row["home_goals"]),
                away_goals=int(row["away_goals"]),
                home_xg=float(row["home_xg"]) if pd.notna(row["home_xg"]) else None,
                away_xg=float(row["away_xg"]) if pd.notna(row["away_xg"]) else None,
                match_date=row["match_date"],
                league=league,
                season=season,
            )

            session.add(match)
            inserted += 1

        session.commit()

        print(f"Inserted {inserted} new matches")

        # ---------------------------------------------------
        # UPSERT TEAM STATS
        # ---------------------------------------------------

        team_stats = compute_team_stats(df)

        for name, s in team_stats.items():

            existing = session.query(TeamStats).filter_by(team_name=name).first()

            if existing:
                for k, v in s.items():
                    setattr(existing, k, v)
            else:
                session.add(TeamStats(team_name=name, **s))

        session.commit()

        print(f"Upserted {len(team_stats)} teams")

# ---------------------------------------------------
# CLI
# ---------------------------------------------------

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("--file", required=True)
    parser.add_argument("--league", default="Unknown")
    parser.add_argument("--season", default="2023-24")

    args = parser.parse_args()

    ingest(args.file, args.league, args.season)
