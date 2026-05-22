# Sports AI v2 — XGBoost + WebSocket live engine

This package adds two major features on top of the v1 scaffold:

---

## 1. XGBoost prediction model

### Train
```bash
cd backend
python train_model.py
```

Requires at least 50 completed matches in the database (run the ETL first).
Prints accuracy, per-class precision/recall, and top feature importances.

### How it works

21 features per match — rolling 5-match and 10-match windows for:
- xG for / against
- Goals for / against
- Form points
- ELO rating
- Derived: xG ratio, ELO diff, form diff

Trained XGBClassifier (300 trees, depth 5) on 80% of historical data.
Evaluated on the held-out 20%.

### Blending with Monte Carlo

The `/api/predict` endpoint automatically blends both models:
- **60% XGBoost** (pattern-matching over historical features)
- **40% Monte Carlo** (statistical Poisson simulation)

If the XGBoost model hasn't been trained yet, it falls back to Monte Carlo only.
The `model_source` field in the response tells you which was used.

### New endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/model/status` | Is the model trained? |
| GET | `/api/model/importance` | Feature importance scores |

---

## 2. WebSocket live match simulation

### Connect
```
ws://localhost:8000/ws/live?home_team=Arsenal&away_team=Chelsea
ws://localhost:8000/ws/live?home_xg=1.8&away_xg=1.1
ws://localhost:8000/ws/live?home_xg=1.8&away_xg=1.1&speed=0.05&stride=3
```

Parameters:
- `home_team` / `away_team` — look up xG from database
- `home_xg` / `away_xg` — supply xG directly
- `speed` — seconds per simulated minute (default 0.35 → ~30s real time for 90 mins)
- `stride` — simulated minutes per tick (default 1; set 3 to fast-forward)

### Message schema
```json
{
  "type":          "kickoff | tick | event | final",
  "minute":        45,
  "home_goals":    1,
  "away_goals":    0,
  "home_win_prob": 0.62,
  "draw_prob":     0.24,
  "away_win_prob": 0.14,
  "event":         { "type": "goal", "team": "home", "minute": 34 },
  "momentum":      0.65,
  "home_red":      0,
  "away_red":      0
}
```

Event types: `goal`, `red_card`

The `final` message additionally contains an `events` array with every event in the match.

### React integration

```jsx
import { useLiveMatch } from "./hooks/useLiveMatch";
import LiveSimulation  from "./components/LiveSimulation";

// In your dashboard:
<LiveSimulation homeTeam="Arsenal" awayTeam="Chelsea" />

// Or with direct xG:
<LiveSimulation homeXg={1.8} awayXg={1.1} />
```

---

## Files added in v2

```
backend/
  services/xgb_model.py      XGBoost feature engineering + classifier
  services/live_engine.py    Minute-by-minute simulation engine
  routers/predictions.py     Updated — blends XGB + MC, adds model endpoints
  routers/live.py            WebSocket endpoint
  train_model.py             CLI training script
  main.py                    Updated — registers live router

frontend/src/
  hooks/useLiveMatch.js      WebSocket React hook
  components/LiveSimulation.jsx  Live match component with probability chart
```
