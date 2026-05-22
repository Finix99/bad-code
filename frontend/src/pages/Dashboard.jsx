import { useState, useEffect } from "react";
import { getTeams, getPrediction } from "../api";
import PredictionGauge from "../components/PredictionGauge";
import TeamFormChart   from "../components/TeamFormChart";
import AIInsightPanel  from "../components/AIInsightPanel";

export default function Dashboard() {
  const [teams, setTeams]           = useState([]);
  const [homeTeam, setHomeTeam]     = useState("");
  const [awayTeam, setAwayTeam]     = useState("");
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState(null);

  useEffect(() => {
    getTeams().then((r) => {
      setTeams(r.data);
      if (r.data.length >= 2) {
        setHomeTeam(r.data[0].name);
        setAwayTeam(r.data[1].name);
      }
    });
  }, []);

  async function handlePredict() {
    if (!homeTeam || !awayTeam || homeTeam === awayTeam) return;
    setLoading(true);
    setError(null);
    try {
      const r = await getPrediction(homeTeam, awayTeam);
      setPrediction(r.data);
    } catch (e) {
      setError("Prediction failed. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  const p = prediction;

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-medium mb-6">Match predictor</h1>

      <div className="grid grid-cols-2 gap-3 mb-4">
        <div>
          <label className="block text-xs text-gray-500 mb-1">Home team</label>
          <select value={homeTeam} onChange={(e) => setHomeTeam(e.target.value)}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm">
            {teams.map((t) => <option key={t.name} value={t.name}>{t.name}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Away team</label>
          <select value={awayTeam} onChange={(e) => setAwayTeam(e.target.value)}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm">
            {teams.map((t) => <option key={t.name} value={t.name}>{t.name}</option>)}
          </select>
        </div>
      </div>

      <button onClick={handlePredict} disabled={loading}
        className="w-full bg-blue-600 text-white rounded-lg py-2.5 text-sm font-medium mb-6 hover:bg-blue-700 disabled:opacity-50">
        {loading ? "Simulating…" : "Run prediction"}
      </button>

      {error && <p className="text-red-500 text-sm mb-4">{error}</p>}

      {p && (
        <div className="space-y-4">
          <PredictionGauge
            homeWin={p.probabilities.home_win}
            draw={p.probabilities.draw}
            awayWin={p.probabilities.away_win}
            homeTeam={p.match.home_team}
            awayTeam={p.match.away_team}
          />

          <div className="grid grid-cols-3 gap-3">
            {[
              { label: "Home xG",   value: p.home_stats.avg_xg_for?.toFixed(2)    ?? "—" },
              { label: "Away xG",   value: p.away_stats.avg_xg_for?.toFixed(2)    ?? "—" },
              { label: "Likely score", value: `${p.expected_score.home}–${p.expected_score.away}` },
            ].map(({ label, value }) => (
              <div key={label} className="bg-gray-50 rounded-lg p-3">
                <div className="text-xs text-gray-500">{label}</div>
                <div className="text-xl font-medium mt-0.5">{value}</div>
              </div>
            ))}
          </div>

          <TeamFormChart
            homeXgTrend={p.home_stats.xg_trend}
            awayXgTrend={p.away_stats.xg_trend}
            homeTeam={p.match.home_team}
            awayTeam={p.match.away_team}
          />

          <AIInsightPanel
            homeTeam={p.match.home_team}
            awayTeam={p.match.away_team}
            prediction={p}
            homeStats={p.home_stats}
            awayStats={p.away_stats}
          />
        </div>
      )}
    </div>
  );
}
