"""
Live match simulation engine.

Simulates a 90-minute match in real-time via WebSocket.
After each in-match event (goal, red card, etc.) probabilities are
recalculated using Monte Carlo on the remaining expected goals.

WebSocket message shape (server → client):
{
  "type": "tick" | "event" | "final",
  "minute": 45,
  "home_goals": 1,
  "away_goals": 0,
  "home_win_prob": 0.62,
  "draw_prob": 0.24,
  "away_win_prob": 0.14,
  "event": {"type": "goal", "team": "home", "minute": 34} | null,
  "momentum": 0.65   // 0=away dominant, 1=home dominant
}
"""
import asyncio
import json
import numpy as np
from dataclasses import dataclass, field, asdict
from typing import Callable, Awaitable


@dataclass
class MatchState:
    home_team:    str
    away_team:    str
    base_home_xg: float
    base_away_xg: float
    minute:       int   = 0
    home_goals:   int   = 0
    away_goals:   int   = 0
    home_red:     int   = 0
    away_red:     int   = 0
    events:       list  = field(default_factory=list)


def _remaining_xg(base_xg: float, elapsed: int, red_cards: int) -> float:
    """Scale expected goals by fraction of match remaining, adjusted for red cards."""
    remaining_frac = max(0, (90 - elapsed) / 90)
    red_penalty    = 0.15 * red_cards
    return max(0.05, base_xg * remaining_frac * (1 - red_penalty))


def _win_probs(state: MatchState, simulations: int = 5000) -> tuple[float, float, float]:
    """Re-estimate win/draw/loss from current scoreline + remaining xG."""
    h_rem = _remaining_xg(state.base_home_xg, state.minute, state.home_red)
    a_rem = _remaining_xg(state.base_away_xg, state.minute, state.away_red)

    hw = draws = aw = 0
    for _ in range(simulations):
        h_add = np.random.poisson(h_rem)
        a_add = np.random.poisson(a_rem)
        h_fin = state.home_goals + h_add
        a_fin = state.away_goals + a_add
        if h_fin > a_fin:
            hw += 1
        elif h_fin == a_fin:
            draws += 1
        else:
            aw += 1

    n = simulations
    return round(hw / n, 4), round(draws / n, 4), round(aw / n, 4)


def _maybe_event(state: MatchState) -> dict | None:
    """
    Stochastically generate in-match events.
    Per-minute probabilities (rough real-world approximations):
      goal:     ~2.5 goals/game → 2.5/90 ≈ 0.028 per minute
      red card: ~0.15/game      → 0.15/90 ≈ 0.0017 per minute
    """
    total_xg = state.base_home_xg + state.base_away_xg
    goal_prob    = (total_xg / 90) * 1.1
    red_prob     = 0.0017

    if np.random.random() < goal_prob:
        is_home = np.random.random() < (state.base_home_xg / max(total_xg, 0.1))
        if is_home:
            state.home_goals += 1
        else:
            state.away_goals += 1
        return {"type": "goal", "team": "home" if is_home else "away", "minute": state.minute}

    if np.random.random() < red_prob:
        is_home = np.random.random() < 0.5
        if is_home:
            state.home_red += 1
        else:
            state.away_red += 1
        return {"type": "red_card", "team": "home" if is_home else "away", "minute": state.minute}

    return None


def _momentum(state: MatchState) -> float:
    """
    Simple momentum score: 0 = away dominant, 1 = home dominant.
    Based on scoreline, recent goals, and red cards.
    """
    score_diff  = (state.home_goals - state.away_goals) * 0.15
    red_diff    = (state.away_red   - state.home_red)   * 0.1
    base        = 0.5 + score_diff + red_diff
    return round(min(1.0, max(0.0, base)), 3)


async def simulate_live_match(
    state: MatchState,
    send: Callable[[dict], Awaitable[None]],
    tick_seconds: float = 0.35,
    minutes_per_tick: int = 1,
):
    """
    Drive a simulated match minute-by-minute.
    Calls `send(payload)` after every tick and after every event.

    tick_seconds:    real wall-clock time per simulated minute (0.35s → ~30s for 90 mins)
    minutes_per_tick: simulated minutes advanced per tick (increase to fast-forward)
    """
    hw, dr, aw = _win_probs(state)

    await send({
        "type":          "kickoff",
        "minute":        0,
        "home_goals":    0,
        "away_goals":    0,
        "home_win_prob": hw,
        "draw_prob":     dr,
        "away_win_prob": aw,
        "event":         None,
        "momentum":      0.5,
    })

    while state.minute < 90:
        await asyncio.sleep(tick_seconds)
        state.minute = min(state.minute + minutes_per_tick, 90)

        event = _maybe_event(state)
        if event:
            state.events.append(event)

        hw, dr, aw = _win_probs(state)
        payload = {
            "type":          "event" if event else "tick",
            "minute":        state.minute,
            "home_goals":    state.home_goals,
            "away_goals":    state.away_goals,
            "home_win_prob": hw,
            "draw_prob":     dr,
            "away_win_prob": aw,
            "event":         event,
            "momentum":      _momentum(state),
            "home_red":      state.home_red,
            "away_red":      state.away_red,
        }
        await send(payload)

    await send({
        "type":          "final",
        "minute":        90,
        "home_goals":    state.home_goals,
        "away_goals":    state.away_goals,
        "home_win_prob": 1.0 if state.home_goals > state.away_goals else 0.0,
        "draw_prob":     1.0 if state.home_goals == state.away_goals else 0.0,
        "away_win_prob": 1.0 if state.home_goals < state.away_goals else 0.0,
        "event":         None,
        "momentum":      _momentum(state),
        "events":        state.events,
    })
