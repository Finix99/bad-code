from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import predictions, teams, fixtures, live

app = FastAPI(title="Sports AI API v2", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predictions.router, prefix="/api")
app.include_router(teams.router,       prefix="/api")
app.include_router(fixtures.router,    prefix="/api")
app.include_router(live.router)


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}
