import { useState } from "react";

export default function AIInsightPanel({ homeTeam, awayTeam, prediction, homeStats, awayStats }) {
  const [insight, setInsight] = useState(null);
  const [loading, setLoading] = useState(false);

  async function fetchInsight() {
    if (!prediction) return;
    setLoading(true);

    const prompt = prediction.llm_prompt;

    try {
      const res = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 400,
          messages: [{ role: "user", content: prompt }],
        }),
      });
      const data = await res.json();
      setInsight(data.content?.[0]?.text ?? "No insight returned.");
    } catch (e) {
      setInsight("Could not fetch AI insight. Check your API key.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-white border border-gray-100 rounded-xl p-5">
      <h3 className="text-sm font-medium text-gray-500 mb-3">AI insight</h3>

      {!insight && !loading && (
        <button
          onClick={fetchInsight}
          className="text-sm border border-gray-200 rounded-lg px-4 py-2 hover:bg-gray-50"
        >
          Generate analysis
        </button>
      )}

      {loading && (
        <p className="text-sm text-gray-400 animate-pulse">Analysing match data…</p>
      )}

      {insight && (
        <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">{insight}</p>
      )}
    </div>
  );
}
