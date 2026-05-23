"""
Train (or retrain) the XGBoost model from the database.

Usage:
    python train_model.py
    python train_model.py --min-rows 100
"""

import argparse
import pandas as pd
from sqlalchemy import create_engine
import os, sys

sys.path.insert(0, os.path.dirname(__file__))

from services.xgb_model import XGBPredictor


# ---------------------------------------------------
# DATABASE URL (FIXED FOR RAILWAY)
# ---------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL is not set. "
        "Make sure Railway PostgreSQL is attached."
    )

# Railway compatibility fix
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)


def main(min_rows: int):

    print("Connecting to database...")

    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True
    )

    # ---------------------------------------------------
    # LOAD DATA SAFELY
    # ---------------------------------------------------

    try:
        matches = pd.read_sql(
            "SELECT * FROM matches ORDER BY match_date",
            engine
        )
    except Exception as e:
        raise RuntimeError(f"Failed to load matches table: {e}")

    try:
        team_stats = pd.read_sql(
            "SELECT * FROM team_stats",
            engine
        )
    except Exception as e:
        raise RuntimeError(f"Failed to load team_stats table: {e}")

    print(f"Loaded {len(matches)} matches, {len(team_stats)} teams.")

    # ---------------------------------------------------
    # VALIDATION CHECK (VERY IMPORTANT)
    # ---------------------------------------------------

    if len(matches) < min_rows:
        raise ValueError(
            f"Not enough training data. "
            f"Found {len(matches)}, need at least {min_rows}"
        )

    # ---------------------------------------------------
    # TRAIN MODEL
    # ---------------------------------------------------

    predictor = XGBPredictor()

    print("Building features and training model...")

    result = predictor.train(
        matches,
        team_stats,
        min_rows=min_rows
    )

    # ---------------------------------------------------
    # OUTPUT RESULTS
    # ---------------------------------------------------

    print("\nModel trained successfully.")
    print(f"  Train samples : {result['n_train']}")
    print(f"  Test samples  : {result['n_test']}")
    print(f"  Accuracy      : {result['accuracy']*100:.1f}%")

    print("\nPer-class metrics:")

    for cls, metrics in result["report"].items():
        if isinstance(metrics, dict):
            print(
                f"  {cls:12s}  "
                f"precision={metrics['precision']:.2f}  "
                f"recall={metrics['recall']:.2f}  "
                f"f1={metrics['f1-score']:.2f}"
            )

    print("\nTop features:")

    imp = predictor.feature_importance()

    for feat, score in sorted(imp.items(), key=lambda x: -x[1])[:8]:
        bar = "█" * int(score * 200)
        print(f"  {feat:15s} {score:.4f}  {bar}")

    print("\nModel saved to models/xgb_model.pkl")


# ---------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--min-rows", type=int, default=50)

    args = parser.parse_args()

    main(args.min_rows)
