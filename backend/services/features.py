import pandas as pd


def calculate_form(matches: pd.DataFrame, team_name: str, last_n: int = 5) -> dict:
    """
    Calculate recent form for a team.
    Returns points total, results list, and goal stats over last N matches.
    """
    team_matches = matches[
        (matches["home_team"] == team_name) |
        (matches["away_team"] == team_name)
    ].sort_values("match_date", ascending=False).head(last_n)

    points = 0
    results = []
    goals_for = []
    goals_against = []

    for _, row in team_matches.iterrows():
        is_home = row["home_team"] == team_name
        gf = row["home_goals"] if is_home else row["away_goals"]
        ga = row["away_goals"] if is_home else row["home_goals"]
        goals_for.append(gf)
        goals_against.append(ga)

        if gf > ga:
            points += 3
            results.append("W")
        elif gf == ga:
            points += 1
            results.append("D")
        else:
            results.append("L")

    return {
        "points": points,
        "results": results,
        "avg_goals_for": round(sum(goals_for) / len(goals_for), 2) if goals_for else 0,
        "avg_goals_against": round(sum(goals_against) / len(goals_against), 2) if goals_against else 0,
    }


def calculate_xg_features(matches: pd.DataFrame, team_name: str, last_n: int = 8) -> dict:
    """
    Calculate xG-based features from recent matches.
    Expects columns: home_xg, away_xg (added by ETL from data source).
    """
    if "home_xg" not in matches.columns:
        return {"avg_xg_for": None, "avg_xg_against": None, "xg_trend": []}

    team_matches = matches[
        (matches["home_team"] == team_name) |
        (matches["away_team"] == team_name)
    ].sort_values("match_date", ascending=False).head(last_n)

    xg_for = []
    xg_against = []

    for _, row in team_matches.iterrows():
        is_home = row["home_team"] == team_name
        xg_for.append(row["home_xg"] if is_home else row["away_xg"])
        xg_against.append(row["away_xg"] if is_home else row["home_xg"])

    return {
        "avg_xg_for": round(sum(xg_for) / len(xg_for), 3) if xg_for else 0,
        "avg_xg_against": round(sum(xg_against) / len(xg_against), 3) if xg_against else 0,
        "xg_trend": [round(x, 2) for x in reversed(xg_for)],
    }
