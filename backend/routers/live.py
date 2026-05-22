"""
WebSocket endpoint for live match simulation.

Connect:
    ws://localhost:8000/ws/live?home_team=Arsenal&away_team=Chelsea
    ws://localhost:8000/ws/live?home_xg=1.8&away_xg=1.1   (direct xG input)

The server streams JSON tick messages until minute 90, then sends a
"final" message and closes the connection.

Optional query params:
    speed   float  tick_seconds per simulated minute (default 0.35)
    stride  int    simulated minutes per tick (default 1)

Example (fast mode for testing):
    ws://localhost:8000/ws/live?home_xg=1.8&away_xg=1.1&speed=0.05&stride=3
"""
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.orm import Session
from models.database import get_db, TeamStats
from services.live_engine import MatchState, simulate_live_match

router = APIRouter(tags=["live"])


@router.websocket("/ws/live")
async def live_match(
    websocket: WebSocket,
    home_team: str  = Query(None),
    away_team: str  = Query(None),
    home_xg:  float = Query(None),
    away_xg:  float = Query(None),
    speed:    float = Query(0.35),
    stride:   int   = Query(1),
    db: Session = Depends(get_db),
):
    await websocket.accept()

    try:
        h_xg = home_xg
        a_xg = away_xg

        if home_team and away_team and (h_xg is None or a_xg is None):
            h = db.query(TeamStats).filter(TeamStats.team_name == home_team).first()
            a = db.query(TeamStats).filter(TeamStats.team_name == away_team).first()
            if not h or not a:
                await websocket.send_json({"error": "Team not found."})
                await websocket.close()
                return
            h_xg = h.avg_xg or 1.2
            a_xg = a.avg_xg or 1.0

        if h_xg is None or a_xg is None:
            await websocket.send_json({"error": "Provide home_xg/away_xg or valid team names."})
            await websocket.close()
            return

        state = MatchState(
            home_team    = home_team or "Home",
            away_team    = away_team or "Away",
            base_home_xg = h_xg,
            base_away_xg = a_xg,
        )

        async def send(payload: dict):
            await websocket.send_text(json.dumps(payload))

        await simulate_live_match(state, send, tick_seconds=speed, minutes_per_tick=stride)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"error": str(e)})
        except Exception:
            pass
