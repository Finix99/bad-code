import { useLiveMatch } from "../hooks/useLiveMatch";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

const EVENT_ICONS = { goal: "⚽", red_card: "🟥" };
const STATUS_LABEL = {
  idle:       "Ready",
  connecting: "Connecting…",
  running:    "Live",
  finished:   "Full time",
  error:      "Connection error",
};

export default function LiveSimulation({ homeTeam, awayTeam, homeXg, awayXg }) {
  const { state, history, status, start, reset } = useLiveMatch({
    homeTeam, awayTeam, homeXg, awayXg, speed: 0.35, stride: 1,
  });

  const events = history.filter((t) => t.event);

  const chartData = history
    .filter((_, i) => i % 3 === 0)
    .map((t) => ({
      min:  t.minute,
      home: +(t.home_win_prob * 100).toFixed(1),
      draw: +(t.draw_prob     * 100).toFixed(1),
      away: +(t.away_win_prob * 100).toFixed(1),
    }));

  const isRunning  = status === "running" || status === "connecting";
  const isFinished = status === "finished";

  return (
    <div className="bg-white border border-gray-100 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-500">Live simulation</h3>
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium
          ${status === "running"  ? "bg-green-50 text-green-700" :
            status === "finished" ? "bg-gray-100 text-gray-500"  :
            status === "error"    ? "bg-red-50 text-red-600"     :
                                    "bg-gray-50 text-gray-400"}`}>
          {STATUS_LABEL[status]}
        </span>
      </div>

      {state && (
        <>
          <div className="flex items-center justify-between mb-3">
            <div className="text-center flex-1">
              <div className="text-2xl font-medium">{state.home_goals}</div>
              <div className="text-xs text-gray-400">{homeTeam || "Home"}</div>
            </div>
            <div className="text-gray-300 text-sm px-3">{state.minute}'</div>
            <div className="text-center flex-1">
              <div className="text-2xl font-medium">{state.away_goals}</div>
              <div className="text-xs text-gray-400">{awayTeam || "Away"}</div>
            </div>
          </div>

          <div className="mb-1 flex justify-between text-xs text-gray-400">
            <span>Home {(state.home_win_prob * 100).toFixed(0)}%</span>
            <span>Draw {(state.draw_prob     * 100).toFixed(0)}%</span>
            <span>Away {(state.away_win_prob * 100).toFixed(0)}%</span>
          </div>
          <div className="flex gap-1 h-2 mb-4">
            <div className="bg-blue-500 rounded-l-full transition-all duration-300"
                 style={{ width: `${(state.home_win_prob * 100).toFixed(0)}%` }} />
            <div className="bg-gray-300 transition-all duration-300"
                 style={{ width: `${(state.draw_prob * 100).toFixed(0)}%` }} />
            <div className="bg-purple-500 rounded-r-full transition-all duration-300"
                 style={{ width: `${(state.away_win_prob * 100).toFixed(0)}%` }} />
          </div>

          <div className="mb-1">
            <div className="flex justify-between text-xs text-gray-400 mb-1">
              <span>Away</span><span>Momentum</span><span>Home</span>
            </div>
            <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <div className="h-full bg-blue-400 transition-all duration-500 rounded-full"
                   style={{ width: `${(state.momentum * 100).toFixed(0)}%` }} />
            </div>
          </div>
        </>
      )}

      {chartData.length > 2 && (
        <div className="mt-4">
          <ResponsiveContainer width="100%" height={120}>
            <LineChart data={chartData}>
              <XAxis dataKey="min" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
              <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} width={24} />
              <Tooltip formatter={(v) => `${v}%`} labelFormatter={(v) => `${v}'`} />
              <Line type="monotone" dataKey="home" stroke="#3B82F6" strokeWidth={1.5} dot={false} />
              <Line type="monotone" dataKey="draw" stroke="#9CA3AF" strokeWidth={1} dot={false} strokeDasharray="3 3" />
              <Line type="monotone" dataKey="away" stroke="#8B5CF6" strokeWidth={1.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {events.length > 0 && (
        <div className="mt-3 space-y-1 max-h-24 overflow-y-auto">
          {[...events].reverse().map((t, i) => (
            <div key={i} className="flex items-center gap-2 text-xs text-gray-600">
              <span>{EVENT_ICONS[t.event.type] || "•"}</span>
              <span className="font-medium">{t.minute}'</span>
              <span className="capitalize">{t.event.team} {t.event.type.replace("_", " ")}</span>
            </div>
          ))}
        </div>
      )}

      <div className="flex gap-2 mt-4">
        {!isRunning && !isFinished && (
          <button onClick={start} className="flex-1 text-sm border border-gray-200 rounded-lg px-4 py-2 hover:bg-gray-50">
            <i className="ti ti-player-play" aria-hidden="true" /> Simulate match
          </button>
        )}
        {isRunning && (
          <button disabled className="flex-1 text-sm border border-gray-200 rounded-lg px-4 py-2 opacity-50 cursor-not-allowed">
            Simulating…
          </button>
        )}
        {(isFinished || isRunning) && (
          <button onClick={reset} className="text-sm border border-gray-200 rounded-lg px-4 py-2 hover:bg-gray-50">
            <i className="ti ti-refresh" aria-hidden="true" /> Reset
          </button>
        )}
      </div>
    </div>
  );
}
