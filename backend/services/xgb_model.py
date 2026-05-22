"""
XGBoost match outcome classifier.

Features per match:
  - home/away avg xG for & against (last 5, last 10)
  - home/away ELO rating
  - home/away form points (last 5)
  - home/away avg goals for & against
  - xG ratio, ELO diff, form diff
  - is_home advantage flag

Target: 0 = away win, 1 = draw, 2 = home win

Usage:
    from services.xgb_model import XGBPredictor
    model = XGBPredictor()
    model.train(matches_df, team_stats_df)
    probs = model.predict("Arsenal", "Chelsea")
    # {"home_win": 0.48, "draw": 0.27, "away_win": 0.25}
"""
import numpy as np
import pandas as pd
import pickle
import os
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report

MODEL_PATH = os.getenv("MODEL_PATH", "models/xgb_model.pkl")


def _rolling_stats(matches: pd.DataFrame, team: str, n: int) -> dict:
    tm = matches[
        (matches["home_team"] == team) | (matches["away_team"] == team)
    ].sort_values("match_date", ascending=False).head(n)

    if tm.empty:
        return {"xg_for": 1.2, "xg_against": 1.2, "goals_for": 1.2,
                "goals_against": 1.2, "points": n * 1.5}

    xg_for, xg_ag, gf, ga, pts = [], [], [], [], 0

    for _, r in tm.iterrows():
        home = r["home_team"] == team
        xg_for.append(r.get("home_xg" if home else "away_xg", 1.2) or 1.2)
        xg_ag.append(r.get("away_xg" if home else "home_xg", 1.2) or 1.2)
        gf.append(r["home_goals"] if home else r["away_goals"])
        ga.append(r["away_goals"] if home else r["home_goals"])
        g_f, g_a = gf[-1], ga[-1]
        pts += 3 if g_f > g_a else (1 if g_f == g_a else 0)

    return {
        "xg_for":       round(np.mean(xg_for), 3),
        "xg_against":   round(np.mean(xg_ag), 3),
        "goals_for":    round(np.mean(gf), 3),
        "goals_against": round(np.mean(ga), 3),
        "points":       pts,
    }


def build_features(matches: pd.DataFrame, team_stats: pd.DataFrame) -> pd.DataFrame:
    """
    Build a feature matrix from historical matches.
    Each row = one match with pre-match features + outcome label.
    """
    elo_map = {}
    if team_stats is not None and "elo_rating" in team_stats.columns:
        elo_map = dict(zip(team_stats["team_name"], team_stats["elo_rating"]))

    matches = matches.sort_values("match_date").reset_index(drop=True)
    rows = []

    for idx, row in matches.iterrows():
        ht, at = row["home_team"], row["away_team"]
        past = matches.iloc[:idx]

        h5  = _rolling_stats(past, ht, 5)
        h10 = _rolling_stats(past, ht, 10)
        a5  = _rolling_stats(past, at, 5)
        a10 = _rolling_stats(past, at, 10)

        h_elo = elo_map.get(ht, 1500)
        a_elo = elo_map.get(at, 1500)

        hg, ag = row["home_goals"], row["away_goals"]
        label = 2 if hg > ag else (1 if hg == ag else 0)

        rows.append({
            "h_xg5":       h5["xg_for"],
            "h_xga5":      h5["xg_against"],
            "h_xg10":      h10["xg_for"],
            "h_xga10":     h10["xg_against"],
            "h_gf5":       h5["goals_for"],
            "h_ga5":       h5["goals_against"],
            "h_pts5":      h5["points"],
            "h_pts10":     h10["points"],
            "h_elo":       h_elo,

            "a_xg5":       a5["xg_for"],
            "a_xga5":      a5["xg_against"],
            "a_xg10":      a10["xg_for"],
            "a_xga10":     a10["xg_against"],
            "a_gf5":       a5["goals_for"],
            "a_ga5":       a5["goals_against"],
            "a_pts5":      a5["points"],
            "a_pts10":     a10["points"],
            "a_elo":       a_elo,

            "xg_ratio":    round(h5["xg_for"] / max(a5["xg_for"], 0.1), 3),
            "elo_diff":    round(h_elo - a_elo, 1),
            "form_diff":   h5["points"] - a5["points"],

            "label": label,
        })

    return pd.DataFrame(rows)


class XGBPredictor:
    FEATURES = [
        "h_xg5", "h_xga5", "h_xg10", "h_xga10", "h_gf5", "h_ga5",
        "h_pts5", "h_pts10", "h_elo",
        "a_xg5", "a_xga5", "a_xg10", "a_xga10", "a_gf5", "a_ga5",
        "a_pts5", "a_pts10", "a_elo",
        "xg_ratio", "elo_diff", "form_diff",
    ]

    def __init__(self):
        self.model = XGBClassifier(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=5,
            subsample=0.8,
            colsample_bytree=0.8,
            use_label_encoder=False,
            eval_metric="mlogloss",
            random_state=42,
        )
        self._matches = None
        self._team_stats = None
        self.trained = False

    def train(self, matches: pd.DataFrame, team_stats: pd.DataFrame | None = None,
              min_rows: int = 50) -> dict:
        df = build_features(matches, team_stats)
        if len(df) < min_rows:
            raise ValueError(
                f"Need at least {min_rows} completed matches to train. Got {len(df)}."
            )

        X = df[self.FEATURES]
        y = df["label"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        self.model.fit(X_train, y_train)
        self._matches    = matches
        self._team_stats = team_stats
        self.trained     = True

        preds   = self.model.predict(X_test)
        acc     = accuracy_score(y_test, preds)
        report  = classification_report(y_test, preds,
                      target_names=["away_win", "draw", "home_win"],
                      output_dict=True)

        self.save()
        return {"accuracy": round(acc, 4), "report": report, "n_train": len(X_train), "n_test": len(X_test)}

    def predict(self, home_team: str, away_team: str) -> dict:
        if not self.trained:
            raise RuntimeError("Model not trained. Call .train() first.")

        h5  = _rolling_stats(self._matches, home_team, 5)
        h10 = _rolling_stats(self._matches, home_team, 10)
        a5  = _rolling_stats(self._matches, away_team, 5)
        a10 = _rolling_stats(self._matches, away_team, 10)

        elo_map = {}
        if self._team_stats is not None:
            elo_map = dict(zip(
                self._team_stats["team_name"], self._team_stats["elo_rating"]
            ))
        h_elo = elo_map.get(home_team, 1500)
        a_elo = elo_map.get(away_team, 1500)

        row = pd.DataFrame([{
            "h_xg5": h5["xg_for"],   "h_xga5": h5["xg_against"],
            "h_xg10": h10["xg_for"], "h_xga10": h10["xg_against"],
            "h_gf5": h5["goals_for"], "h_ga5": h5["goals_against"],
            "h_pts5": h5["points"],  "h_pts10": h10["points"],  "h_elo": h_elo,
            "a_xg5": a5["xg_for"],   "a_xga5": a5["xg_against"],
            "a_xg10": a10["xg_for"], "a_xga10": a10["xg_against"],
            "a_gf5": a5["goals_for"], "a_ga5": a5["goals_against"],
            "a_pts5": a5["points"],  "a_pts10": a10["points"],  "a_elo": a_elo,
            "xg_ratio": round(h5["xg_for"] / max(a5["xg_for"], 0.1), 3),
            "elo_diff": round(h_elo - a_elo, 1),
            "form_diff": h5["points"] - a5["points"],
        }])

        probs = self.model.predict_proba(row[self.FEATURES])[0]
        return {
            "away_win": round(float(probs[0]), 4),
            "draw":     round(float(probs[1]), 4),
            "home_win": round(float(probs[2]), 4),
            "source":   "xgboost",
        }

    def feature_importance(self) -> dict:
        if not self.trained:
            return {}
        return dict(zip(
            self.FEATURES,
            [round(float(s), 4) for s in self.model.feature_importances_]
        ))

    def save(self, path: str = MODEL_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path: str = MODEL_PATH) -> "XGBPredictor":
        with open(path, "rb") as f:
            return pickle.load(f)
