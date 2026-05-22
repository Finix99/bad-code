def build_match_prompt(home_team: str, away_team: str, prediction: dict,
                        home_stats: dict, away_stats: dict) -> str:
    return f"""You are a football analytics expert. Analyse this upcoming match concisely.

Match: {home_team} (home) vs {away_team} (away)

Prediction probabilities:
- Home win: {prediction['home_win']*100:.1f}%
- Draw:     {prediction['draw']*100:.1f}%
- Away win: {prediction['away_win']*100:.1f}%

{home_team} stats:
- xG (avg):        {home_stats.get('avg_xg_for', 'N/A')}
- xGA (avg):       {home_stats.get('avg_xg_against', 'N/A')}
- Recent form:     {', '.join(home_stats.get('results', []))}
- ELO rating:      {home_stats.get('elo', 'N/A')}

{away_team} stats:
- xG (avg):        {away_stats.get('avg_xg_for', 'N/A')}
- xGA (avg):       {away_stats.get('avg_xg_against', 'N/A')}
- Recent form:     {', '.join(away_stats.get('results', []))}
- ELO rating:      {away_stats.get('elo', 'N/A')}

Write 3 short paragraphs covering: (1) attacking strength comparison, 
(2) defensive stability, (3) key tactical factors affecting this prediction.
Be specific to the numbers. Do not repeat the probabilities verbatim.
"""


def build_team_prompt(team_name: str, stats: dict) -> str:
    return f"""Summarise {team_name}'s current form and playing style based on these stats:

xG for (avg):     {stats.get('avg_xg_for')}
xG against (avg): {stats.get('avg_xg_against')}
Recent results:   {', '.join(stats.get('results', []))}
ELO rating:       {stats.get('elo')}

Give a 2-sentence scout report."""
