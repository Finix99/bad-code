"""
Prediction router — blends XGBoost (ML) + Monte Carlo (Poisson) probabilities.

Blend logic:
  - If XGB model is available: 60% XGB + 40% Monte Carlo
  - Fallback to Monte Carlo only if model not trained yet

This gives the statistical rigour of Poisson simulation plus the
pattern-recognition of XGBoost over historical features.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.database import get_db, Match, TeamStats
from services.prediction_engine import monte_carlo, score_matrix, expected_score
from services.features import calculate_form, calculate_xg_features
from services.llm import build_match_prompt
from services.xgb_model import XGBPredictor, MODEL_PATH
import pandas as pd
import os

router = APIRouter(tags=["predictions"])

_xgb: XGBPredictor | None = None


def get_xgb() -> XGBPredictor | None:
    global _xgb
    if _xgb is None and os.path.exists(MODEL_PATH):
        try:
            _xgb = XGBPredictor.load(MODEL_PATH)
        except Exception:
            pass
    return _xgb


def blend(mc: dict, xgb: dict, xgb_weight: float = 0.6) -> dict:
    w = xgb_weight
    return {
        "home_win": round(w * xgb["home_win"] + (1 - w) * mc["home_win"], 4),
        "draw":     round(w * xgb["draw"]     + (1 - w) * mc["draw"],     4),
        "away_win": round(w * xgb["away_win"] + (1 - w) * mc["away_win"], 4),
    }


@router.get("/predict")
def predict_match(home_team: str, away_team: str, db: Session = Depends(get_db)):
    home = db.query(TeamStats).filter(TeamStats.team_name == home_team).first()
    away = db.query(TeamStats).filter(TeamStats.team_name == away_team).first()

    if not home or not away:
        raise HTTPException(404, "One or both teams not found in database.")

    home_xg = home.avg_xg or 1.2
    away_xg = away.avg_xg or 1.0

    mc_probs  = monte_carlo(home_xg, away_xg)
    matrix    = score_matrix(home_xg, away_xg)
    exp_score = expected_score(home_xg, away_xg)

    matches_df = pd.read_sql("SELECT * FROM matches ORDER BY match_date", db.bind)
    home_form  = calculate_form(matches_df, home_team)
    away_form  = calculate_form(matches_df, away_team)
    home_xg_f  = calculate_xg_features(matches_df, home_team)
    away_xg_f  = calculate_xg_features(matches_df, away_team)

    home_stats = {**home_form, **home_xg_f, "elo": home.elo_rating}
    away_stats = {**away_form, **away_xg_f, "elo": away.elo_rating}

    model        = get_xgb()
    xgb_probs    = None
    final_probs  = mc_probs
    model_source = "monte_carlo"

    if model and model.trained:
        try:
            xgb_probs   = model.predict(home_team, away_team)
            final_probs = blend(mc_probs, xgb_probs)
            model_source = "blend_xgb_mc"
        except Exception:
            pass

    prompt = build_match_prompt(home_team, away_team, final_probs, home_stats, away_stats)

    return {
        "match":            {"home_team": home_team, "away_team": away_team},
        "probabilities":    final_probs,
        "monte_carlo":      mc_probs,
        "xgboost":          xgb_probs,
        "model_source":     model_source,
        "expected_score":   exp_score,
        "score_matrix":     matrix,
        "home_stats":       home_stats,
        "away_stats":       away_stats,
        "llm_prompt":       prompt,
    }


@router.get("/model/importance")
def feature_importance():
    model = get_xgb()
    if not model:
        raise HTTPException(404, "No trained model found. Run train_model.py first.")
    return model.feature_importance()


@router.get("/model/status")
def model_status():
    model = get_xgb()
    return {
        "trained": model is not None and model.trained,
        "path":    MODEL_PATH,
        "exists":  os.path.exists(MODEL_PATH),
    }
