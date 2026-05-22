from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from models.database import get_db, Match

router = APIRouter(tags=["fixtures"])


@router.get("/fixtures")
def recent_fixtures(limit: int = 20, db: Session = Depends(get_db)):
    matches = (
        db.query(Match)
        .order_by(desc(Match.match_date))
        .limit(limit)
        .all()
    )
    return [
        {
            "id":         m.id,
            "home_team":  m.home_team,
            "away_team":  m.away_team,
            "home_goals": m.home_goals,
            "away_goals": m.away_goals,
            "home_xg":    m.home_xg,
            "away_xg":    m.away_xg,
            "date":       m.match_date.isoformat() if m.match_date else None,
            "league":     m.league,
        }
        for m in matches
    ]
