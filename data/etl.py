"""
ETL: ingest Football-Data.co.uk CSV files into PostgreSQL.

Usage:
    python etl.py --file data/E0.csv --league "Premier League" --season "2023-24"

Free CSV download (no API key needed):
    https://www.football-data.co.uk/englandm.php
"""
import argparse
import os
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from backend.models.database import engine, create_tables, Match, TeamStats

COLUMN_MAP = {
    "HomeTeam": "home_team",
    "AwayTeam": "away_team",
    "FTHG":     "home_goals",
    "FTAG":     "away_goals",
    "Date":     "match_date",
}

XG_COLS = {"xG": ("home_xg", "xGA")}


def load_csv(path: str, league: str, season: str):
    df = pd.read_csv(path)
    df = df.rename(columns=COLUMN_MAP)

    if "xG" in df.columns:
        df["home_xg"] = df["xG"]
        df["away_xg"] = df["xGA"] if "xGA" in df.columns else None
    else:
        df["home_xg"] = None
        df["away_xg"] = None

    df["match_date"] = pd.to_datetime(df["match_date"], dayfirst=True, errors="coerce")
    df["league"]     = league
    df["season"]     = season

    keep = ["home_team", "away_team", "home_goals", "away_goals",
            "home_xg", "away_xg", "match_date", "league", "season"]
    df = df[[c for c in keep if c in df.columns]].dropna(
        subset=["home_team", "away_team", "home_goals", "away_goals"]
    )
    return df


def compute_team_stats(df: pd.DataFrame) -> dict:
    stats = {}
    for team in pd.concat([df["home_team"], df["away_team"]]).unique():
        home = df[df["home_team"] == team]
        away = df[df["away_team"] == team]

        gf = list(home["home_goals"]) + list(away["away_goals"])
        ga = list(home["away_goals"]) + list(away["home_goals"])
        xg_for  = list(home["home_xg"].dropna()) + list(away["away_xg"].dropna())
        xg_ag   = list(home["away_xg"].dropna()) + list(away["home_xg"].dropna())

        stats[team] = {
            "avg_goals":       round(sum(gf) / len(gf), 3) if gf else 0,
            "avg_xg":          round(sum(xg_for) / len(xg_for), 3) if xg_for else 0,
            "avg_xg_against":  round(sum(xg_ag) / len(xg_ag), 3) if xg_ag else 0,
            "avg_possession":  0.0,
            "defensive_rating": round(1 - (sum(ga) / len(ga) / 3), 3) if ga else 0.5,
            "elo_rating":      1500.0,
        }
    return stats


def ingest(path: str, league: str, season: str):
    create_tables()
    df = load_csv(path, league, season)
    print(f"Loaded {len(df)} matches from {path}")

    with Session(engine) as session:
        for _, row in df.iterrows():
            m = Match(**row.to_dict())
            session.add(m)
        session.commit()
        print("Matches inserted.")

        team_stats = compute_team_stats(df)
        for name, s in team_stats.items():
            existing = session.query(TeamStats).filter_by(team_name=name).first()
            if existing:
                for k, v in s.items():
                    setattr(existing, k, v)
            else:
                session.add(TeamStats(team_name=name, **s))
        session.commit()
        print(f"Team stats upserted for {len(team_stats)} teams.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file",   required=True, help="Path to CSV file")
    parser.add_argument("--league", default="Unknown League")
    parser.add_argument("--season", default="2023-24")
    args = parser.parse_args()
    ingest(args.file, args.league, args.season)
