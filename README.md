# Sports AI — prediction platform

Full-stack football analytics platform: Poisson modelling, Monte Carlo simulation, ELO ratings, xG features, FastAPI backend, React frontend, AI insights.

---

## Quick start (Docker — recommended)

```bash
cd docker
docker compose up
```

Then open http://localhost:3000

---

## Manual setup

### 1. PostgreSQL

Create a database named `sports_ai` and update `DATABASE_URL` in your environment.

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

API runs at http://localhost:8000  
Docs at http://localhost:8000/docs

### 3. Load data (no API key needed)

Download a free CSV from https://www.football-data.co.uk/englandm.php  
(e.g. E0.csv = Premier League)

```bash
cd data
python etl.py --file E0.csv --league "Premier League" --season "2023-24"
```

Or use StatsBomb open data (richer xG data):
```bash
git clone https://github.com/statsbomb/open-data
python etl_statsbomb.py --dir open-data/data/matches/2/44
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Project structure

```
sports-ai/
├── backend/
│   ├── main.py                        # FastAPI app
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── routers/
│   │   ├── predictions.py             # GET /api/predict
│   │   ├── teams.py                   # GET /api/teams
│   │   └── fixtures.py                # GET /api/fixtures
│   ├── services/
│   │   ├── prediction_engine.py       # Poisson + Monte Carlo
│   │   ├── elo.py                     # ELO rating system
│   │   ├── features.py                # Form + xG feature engineering
│   │   └── llm.py                     # Prompt builder
│   └── models/
│       └── database.py                # SQLAlchemy models
├── frontend/
│   └── src/
│       ├── api.js                     # Axios client
│       ├── pages/Dashboard.jsx        # Main dashboard
│       └── components/
│           ├── PredictionGauge.jsx    # Win/draw/loss bar
│           ├── TeamFormChart.jsx      # xG trend (Recharts)
│           └── AIInsightPanel.jsx     # LLM-powered analysis
├── data/
│   └── etl.py                         # CSV ingestion script
└── docker/
    └── docker-compose.yml
```

---

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/predict?home_team=X&away_team=Y` | Full prediction with probabilities, score matrix, features |
| GET | `/api/teams` | All teams with ELO + xG stats |
| GET | `/api/teams/{name}` | Single team detail |
| GET | `/api/fixtures?limit=20` | Recent matches |
| GET | `/health` | Health check |

---

## Adding AI insights (optional)

The `AIInsightPanel` calls the Anthropic API directly from the frontend.  
Set your API key in the browser — or proxy through the FastAPI backend:

```python
# In routers/predictions.py, after building the prompt:
import anthropic
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
msg = client.messages.create(model="claude-sonnet-4-20250514", max_tokens=400,
                              messages=[{"role":"user","content": prompt}])
insight = msg.content[0].text
```

---

## Roadmap

- [ ] XGBoost classifier for improved predictions
- [ ] WebSocket live match probability updates
- [ ] Player impact modelling
- [ ] Multi-league support
- [ ] Betting odds comparison
