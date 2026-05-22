import numpy as np
from scipy.stats import poisson


def monte_carlo(home_xg: float, away_xg: float, simulations: int = 10_000) -> dict:
    """
    Run Monte Carlo simulation using Poisson-distributed goal sampling.
    Returns win/draw/loss probabilities.
    """
    home_wins = draws = away_wins = 0

    for _ in range(simulations):
        h = np.random.poisson(home_xg)
        a = np.random.poisson(away_xg)
        if h > a:
            home_wins += 1
        elif h == a:
            draws += 1
        else:
            away_wins += 1

    return {
        "home_win": round(home_wins / simulations, 4),
        "draw":     round(draws     / simulations, 4),
        "away_win": round(away_wins / simulations, 4),
    }


def score_matrix(home_xg: float, away_xg: float, max_goals: int = 6) -> list[list[float]]:
    """
    Build a (max_goals × max_goals) probability matrix using Poisson PMF.
    matrix[i][j] = P(home scores i, away scores j)
    """
    matrix = []
    for h in range(max_goals):
        row = []
        for a in range(max_goals):
            row.append(round(
                float(poisson.pmf(h, home_xg) * poisson.pmf(a, away_xg)), 6
            ))
        matrix.append(row)
    return matrix


def expected_score(home_xg: float, away_xg: float) -> dict:
    """Most likely scoreline from the probability matrix."""
    matrix = score_matrix(home_xg, away_xg)
    best_prob = -1
    best_h = best_a = 0
    for h, row in enumerate(matrix):
        for a, p in enumerate(row):
            if p > best_prob:
                best_prob, best_h, best_a = p, h, a
    return {"home": best_h, "away": best_a, "probability": round(best_prob, 4)}
