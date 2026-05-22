K_FACTOR = 32


def expected_result(rating_a: float, rating_b: float) -> float:
    """Expected score for team A against team B."""
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))


def update_elo(old_rating: float, expected: float, actual: float) -> float:
    """Return updated ELO rating after a match."""
    return round(old_rating + K_FACTOR * (actual - expected), 2)


def match_actual(home_goals: int, away_goals: int) -> tuple[float, float]:
    """Convert scoreline to ELO outcome scores (1 = win, 0.5 = draw, 0 = loss)."""
    if home_goals > away_goals:
        return 1.0, 0.0
    elif home_goals == away_goals:
        return 0.5, 0.5
    else:
        return 0.0, 1.0


def process_match_elo(home_rating: float, away_rating: float,
                      home_goals: int, away_goals: int) -> tuple[float, float]:
    """Return new ELO ratings for both teams after a match."""
    exp_home = expected_result(home_rating, away_rating)
    exp_away = 1 - exp_home
    act_home, act_away = match_actual(home_goals, away_goals)
    new_home = update_elo(home_rating, exp_home, act_home)
    new_away = update_elo(away_rating, exp_away, act_away)
    return new_home, new_away
