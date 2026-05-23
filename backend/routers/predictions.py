"""
Prediction router — blends XGBoost (ML) + Monte Carlo (Poisson) probabilities.

Blend logic:
  - If XGB model is available: 60% XGB + 40% Monte Carlo
  - Fallback to Monte Carlo only if model not trained yet
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
import numpy as np

router = APIRouter(tags=["predictions"])

_xgb: XGBPredictor | None = None


def get_xgb() -> XGBPredictor | None:
    global _xgb

    if _xgb is None and os.path.exists(MODEL_PATH):
        try:
            _xgb = XGBPredictor.load(MODEL_PATH)
        except Exception as e:
            print(f"XGB load error: {e}")
            _xgb = None

    return _xgb


def blend(mc: dict, xgb: dict, xgb_weight: float = 0.6) -> dict:
    w = xgb_weight

    return {
        "home_win": round(
            w * float(xgb["home_win"]) +
            (1 - w) * float(mc["home_win"]),
            4
        ),
        "draw": round(
            w * float(xgb["draw"]) +
            (1 - w) * float(mc["draw"]),
            4
        ),
        "away_win": round(
            w * float(xgb["away_win"]) +
            (1 - w) * float(mc["away_win"]),
            4
        ),
    }


def sanitize(obj):
    """
    Converts NumPy/Pandas objects into JSON-safe Python types.
    """

    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}

    elif isinstance(obj, list):
        return [sanitize(v) for v in obj]

    elif isinstance(obj, tuple):
        return tuple(sanitize(v) for v in obj)

    elif isinstance(obj, np.ndarray):
        return obj.tolist()

    elif isinstance(obj, (np.integer,)):
        return int(obj)

    elif isinstance(obj, (np.floating,)):
        return float(obj)

    elif pd.isna(obj):
        return None

    return obj


@router.get("/predict")
def predict_match(
    home_team: str,
    away_team: str,
    db: Session = Depends(get_db)
):

    try:
        # ---------------------------------------------------
        # TEAM LOOKUP
        # ---------------------------------------------------

        home = (
            db.query(TeamStats)
            .filter(TeamStats.team_name == home_team)
            .first()
        )

        away = (
            db.query(TeamStats)
            .filter(TeamStats.team_name == away_team)
            .first()
        )

        if not home or not away:
            raise HTTPException(
                status_code=404,
                detail="One or both teams not found in database."
            )

        # ---------------------------------------------------
        # BASE XG VALUES
        # ---------------------------------------------------

        home_xg = float(home.avg_xg or 1.2)
        away_xg = float(away.avg_xg or 1.0)

        # ---------------------------------------------------
        # MONTE CARLO + SCORE MATRIX
        # ---------------------------------------------------

        mc_probs = monte_carlo(home_xg, away_xg)

        matrix = score_matrix(home_xg, away_xg)

        exp_score = expected_score(home_xg, away_xg)

        # ---------------------------------------------------
        # MATCH HISTORY
        # ---------------------------------------------------

        try:
            matches_df = pd.read_sql(
                "SELECT * FROM matches ORDER BY match_date",
                db.bind
            )

        except Exception as e:
            return {
                "error": "Failed to load matches table",
                "details": str(e)
            }

        # ---------------------------------------------------
        # FEATURE ENGINEERING
        # ---------------------------------------------------

        try:
            home_form = calculate_form(matches_df, home_team)
            away_form = calculate_form(matches_df, away_team)

            home_xg_f = calculate_xg_features(matches_df, home_team)
            away_xg_f = calculate_xg_features(matches_df, away_team)

        except Exception as e:
            return {
                "error": "Feature engineering failed",
                "details": str(e)
            }

        # ---------------------------------------------------
        # TEAM FEATURE PACKS
        # ---------------------------------------------------

        home_stats = {
            **home_form,
            **home_xg_f,
            "elo": float(home.elo_rating or 1500)
        }

        away_stats = {
            **away_form,
            **away_xg_f,
            "elo": float(away.elo_rating or 1500)
        }

        # ---------------------------------------------------
        # XGBOOST MODEL
        # ---------------------------------------------------

        model = get_xgb()

        xgb_probs = None
        final_probs = mc_probs
        model_source = "monte_carlo"

        if model and model.trained:

            try:
                xgb_probs = model.predict(home_team, away_team)

                final_probs = blend(mc_probs, xgb_probs)

                model_source = "blend_xgb_mc"

            except Exception as e:
                print(f"XGB prediction failed: {e}")

        # ---------------------------------------------------
        # LLM PROMPT
        # ---------------------------------------------------

        try:
            prompt = build_match_prompt(
                home_team,
                away_team,
                final_probs,
                home_stats,
                away_stats
            )

        except Exception as e:
            prompt = f"Prompt generation failed: {e}"

        # ---------------------------------------------------
        # FINAL RESPONSE
        # ---------------------------------------------------

        response = {
            "match": {
                "home_team": home_team,
                "away_team": away_team
            },

            "probabilities": sanitize(final_probs),

            "monte_carlo": sanitize(mc_probs),

            "xgboost": sanitize(xgb_probs),

            "model_source": model_source,

            "expected_score": sanitize(exp_score),

            "score_matrix": sanitize(matrix),

            "home_stats": sanitize(home_stats),

            "away_stats": sanitize(away_stats),

            "llm_prompt": prompt
        }

        return response

    except HTTPException:
        raise

    except Exception as e:
        return {
            "error": "Prediction engine crashed",
            "details": str(e),
            "type": str(type(e))
        }


@router.get("/model/importance")
def feature_importance():

    try:
        model = get_xgb()

        if not model:
            raise HTTPException(
                status_code=404,
                detail="No trained model found."
            )

        return sanitize(model.feature_importance())

    except Exception as e:
        return {
            "error": str(e)
        }


@router.get("/model/status")
def model_status():

    model = get_xgb()

    return {
        "trained": bool(model is not None and model.trained),
        "path": MODEL_PATH,
        "exists": os.path.exists(MODEL_PATH)
    }
