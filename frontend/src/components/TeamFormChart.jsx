import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from "recharts";

export default function TeamFormChart({ homeXgTrend, awayXgTrend, homeTeam, awayTeam }) {
  if (!homeXgTrend?.length) return null;

  const data = homeXgTrend.map((v, i) => ({
    match:   `M-${homeXgTrend.length - i}`,
    [homeTeam]: v,
    [awayTeam]: awayXgTrend?.[i] ?? null,
  }));

  return (
    <div className="bg-white border border-gray-100 rounded-xl p-5">
      <h3 className="text-sm font-medium text-gray-500 mb-4">xG trend — last {data.length} matches</h3>
      <ResponsiveContainer width="100%" height={180}>
        <LineChart data={data}>
          <XAxis dataKey="match" tick={{ fontSize: 11 }} />
          <YAxis domain={[0, 3]} tick={{ fontSize: 11 }} width={28} />
          <Tooltip formatter={(v) => v?.toFixed(2)} />
          <Legend iconType="plainline" iconSize={16} wrapperStyle={{ fontSize: 12 }} />
          <Line type="monotone" dataKey={homeTeam}  stroke="#3B82F6" strokeWidth={2} dot={{ r: 3 }} />
          <Line type="monotone" dataKey={awayTeam}  stroke="#8B5CF6" strokeWidth={2} strokeDasharray="5 4" dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
