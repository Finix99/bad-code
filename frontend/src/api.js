import axios from "axios";

const api = axios.create({ baseURL: "http://localhost:8000/api" });

export const getTeams      = ()                          => api.get("/teams");
export const getPrediction = (homeTeam, awayTeam)        => api.get("/predict", { params: { home_team: homeTeam, away_team: awayTeam } });
export const getFixtures   = (limit = 20)                => api.get("/fixtures", { params: { limit } });
