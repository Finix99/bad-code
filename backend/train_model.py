"""
Train (or retrain) the XGBoost model from the database.

Usage:
    python train_model.py
    python train_model.py --min-rows 100

The script loads all completed matches + team stats from PostgreSQL,
builds the feature matrix, trains XGBClassifier, prints eval metrics,
and saves the model to models/xgb_model.pkl.
"""
import argparse
import pandas as pd
from sqlalchemy import create_engine
import os, sys

sys.path.insert(0, os.path.dirname(__file__))
from services.xgb_model import XGBPredictor

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/sports_ai")


def main(min_rows: int):
    print("Connecting to database…")
    engine = create_engine(DATABASE_URL)

    matches    = pd.read_sql("SELECT * FROM matches ORDER BY match_date", engine)
    team_stats = pd.read_sql("SELECT * FROM team_stats", engine)

    print(f"Loaded {len(matches)} matches, {len(team_stats)} teams.")

    predictor = XGBPredictor()
    print("Building features and training model…")
    result = predictor.train(matches, team_stats, min_rows=min_rows)

    print(f"\nModel trained successfully.")
    print(f"  Train samples : {result['n_train']}")
    print(f"  Test samples  : {result['n_test']}")
    print(f"  Accuracy      : {result['accuracy']*100:.1f}%")
    print(f"\nPer-class metrics:")
    for cls, metrics in result["report"].items():
        if isinstance(metrics, dict):
            print(f"  {cls:12s}  precision={metrics['precision']:.2f}  "
                  f"recall={metrics['recall']:.2f}  f1={metrics['f1-score']:.2f}")

    print(f"\nTop features:")
    imp = predictor.feature_importance()
    for feat, score in sorted(imp.items(), key=lambda x: -x[1])[:8]:
        bar = "█" * int(score * 200)
        print(f"  {feat:15s} {score:.4f}  {bar}")

    print(f"\nModel saved to models/xgb_model.pkl")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-rows", type=int, default=50)
    args = parser.parse_args()
    main(args.min_rows)
