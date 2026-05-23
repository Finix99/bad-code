from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import predictions, teams, fixtures, live
from models.database import create_tables

app = FastAPI(
    title="Sports AI API v2",
    version="2.0.0"
)

# ---------------------------------------------------
# STARTUP
# ---------------------------------------------------

@app.on_event("startup")
def startup():

    try:
        create_tables()
        print("Database tables ready")

    except Exception as e:
        print(f"Database startup error: {e}")

# ---------------------------------------------------
# CORS
# ---------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------
# ROUTERS
# ---------------------------------------------------

app.include_router(predictions.router, prefix="/api")
app.include_router(teams.router, prefix="/api")
app.include_router(fixtures.router, prefix="/api")
app.include_router(live.router)

# ---------------------------------------------------
# ROOT
# ---------------------------------------------------

@app.get("/")
def root():

    return {
        "message": "Sports AI API Running",
        "docs": "/docs",
        "health": "/health"
    }

# ---------------------------------------------------
# HEALTH
# ---------------------------------------------------

@app.get("/health")
def health():

    return {
        "status": "ok",
        "version": "2.0.0"
    }
