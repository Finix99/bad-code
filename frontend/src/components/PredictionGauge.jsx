export default function PredictionGauge({ homeWin, draw, awayWin, homeTeam, awayTeam }) {
  const fmt = (v) => `${(v * 100).toFixed(0)}%`;

  return (
    <div className="bg-white border border-gray-100 rounded-xl p-5">
      <h3 className="text-sm font-medium text-gray-500 mb-3">Match outcome probability</h3>

      <div className="flex justify-between text-sm mb-1">
        <span className="font-medium text-blue-700">{homeTeam} {fmt(homeWin)}</span>
        <span className="text-gray-500">Draw {fmt(draw)}</span>
        <span className="font-medium text-purple-700">{awayTeam} {fmt(awayWin)}</span>
      </div>

      <div className="flex gap-1 h-2.5 rounded-full overflow-hidden">
        <div className="bg-blue-500 transition-all duration-500"  style={{ width: fmt(homeWin) }} />
        <div className="bg-gray-300 transition-all duration-500"  style={{ width: fmt(draw) }} />
        <div className="bg-purple-500 transition-all duration-500" style={{ width: fmt(awayWin) }} />
      </div>
    </div>
  );
}
