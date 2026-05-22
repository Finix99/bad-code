from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.database import get_db, TeamStats, Match

router = APIRouter(tags=["teams"])


@router.get("/teams")
def list_teams(db: Session = Depends(get_db)):
    teams = db.query(TeamStats).all()
    return [
        {
            "name":            t.team_name,
            "elo":             t.elo_rating,
            "avg_xg":          t.avg_xg,
            "avg_xg_against":  t.avg_xg_against,
            "defensive_rating": t.defensive_rating,
        }
        for t in teams
    ]


@router.get("/teams/{team_name}")
def get_team(team_name: str, db: Session = Depends(get_db)):
    team = db.query(TeamStats).filter(TeamStats.team_name == team_name).first()
    if not team:
        raise HTTPException(404, "Team not found")
    return team
