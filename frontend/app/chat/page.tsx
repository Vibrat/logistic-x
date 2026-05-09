"use client";

import { useEffect, useRef, useState } from "react";
import { api, AskResponse, ChatMessage } from "@/lib/api";
import ChartRenderer from "@/components/ChartRenderer";
import ExplainPanel from "@/components/ExplainPanel";
import DataTable from "@/components/DataTable";

const SUGGESTIONS = [
  "Which carrier has the highest delay rate?",
  "Show total orders by region",
  "What is the on-time delivery rate by carrier?",
  "Show delayed orders by month",
  "Predict demand for CRAYON-0008 for the next 4 months",
  "Which product category has the most delayed orders?",
];

type ThreadEntry =
  | { kind: "user"; text: string }
  | { kind: "assistant"; response: AskResponse };

export default function ChatPage() {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [thread, setThread] = useState<ThreadEntry[]>([]);
  const [expandedTable, setExpandedTable] = useState<Set<number>>(new Set());
  const bottomRef = useRef<HTMLDivElement>(null);

  // Build the history array for the API from the current thread
  function buildHistory(): ChatMessage[] {
    const history: ChatMessage[] = [];
    for (const entry of thread) {
      if (entry.kind === "user") {
        history.push({ role: "user", content: entry.text });
      } else {
        history.push({ role: "assistant", content: entry.response.answer });
      }
    }
    return history;
  }

  async function handleSubmit(q?: string) {
    const text = (q ?? input).trim();
    if (!text || loading) return;

    setInput("");
    const userEntry: ThreadEntry = { kind: "user", text };
    setThread((prev) => [...prev, userEntry]);
    setLoading(true);

    try {
      const history = buildHistory();
      const res = await api.ask(text, history);
      setThread((prev) => [...prev, { kind: "assistant", response: res }]);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Something went wrong.";
      setThread((prev) => [
        ...prev,
        {
          kind: "assistant",
          response: {
            answer: msg,
            needs_clarification: false,
            chart_type: null,
            chart_data: null,
            explanation: null,
            filters_used: {},
            raw_data: [],
            inventory_recommendation: null,
          },
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function toggleTable(idx: number) {
    setExpandedTable((prev) => {
      const next = new Set(prev);
      next.has(idx) ? next.delete(idx) : next.add(idx);
      return next;
    });
  }

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [thread, loading]);

  const isEmpty = thread.length === 0;

  return (
    <div className="flex flex-col h-[calc(100vh-80px)] max-w-3xl mx-auto">
      {/* Header */}
      <div className="pb-4 pt-2 shrink-0">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">Ask AI</h1>
        <p className="text-sm text-gray-500">
          Ask any logistics question in plain English. The AI will clarify if it needs more information.
        </p>
      </div>

      {/* Thread */}
      <div className="flex-1 overflow-y-auto space-y-4 pb-4">
        {/* Suggestions — shown only on empty thread */}
        {isEmpty && !loading && (
          <div className="flex flex-wrap gap-2 pt-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => handleSubmit(s)}
                className="text-xs px-3 py-1.5 rounded-full border border-gray-200 bg-white hover:bg-gray-50 text-gray-600 transition"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {thread.map((entry, idx) => {
          if (entry.kind === "user") {
            return (
              <div key={idx} className="flex justify-end">
                <div className="max-w-[80%] bg-blue-600 text-white rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm leading-relaxed shadow-sm">
                  {entry.text}
                </div>
              </div>
            );
          }

          const res = entry.response;
          return (
            <div key={idx} className="flex justify-start">
              <div className="max-w-[90%] space-y-3">
                {/* Answer bubble */}
                <div
                  className={`rounded-2xl rounded-tl-sm px-4 py-3 text-sm leading-relaxed shadow-sm border ${
                    res.needs_clarification
                      ? "bg-amber-50 border-amber-200 text-amber-900"
                      : "bg-white border-gray-200 text-gray-800"
                  }`}
                >
                  {res.needs_clarification && (
                    <p className="text-xs font-semibold uppercase tracking-wider text-amber-600 mb-1">
                      Needs clarification
                    </p>
                  )}
                  <p>{res.answer}</p>
                  {res.inventory_recommendation && (
                    <p className="mt-2 text-sm text-amber-700 bg-amber-50 border border-amber-100 rounded-lg px-3 py-2">
                      📦 {res.inventory_recommendation}
                    </p>
                  )}
                </div>

                {/* Chart */}
                {res.chart_type && res.chart_data && (
                  <ChartRenderer chartType={res.chart_type} chartData={res.chart_data} />
                )}

                {/* Explanation */}
                {res.explanation && (
                  <ExplainPanel explanation={res.explanation} filtersUsed={res.filters_used} />
                )}

                {/* Raw data toggle */}
                {res.raw_data.length > 0 && (
                  <div>
                    <button
                      onClick={() => toggleTable(idx)}
                      className="text-xs text-blue-600 hover:underline"
                    >
                      {expandedTable.has(idx) ? "Hide" : "Show"} underlying data ({res.raw_data.length} rows)
                    </button>
                    {expandedTable.has(idx) && (
                      <div className="mt-2">
                        <DataTable rows={res.raw_data} />
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {/* Loading bubble */}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
              <div className="flex gap-1 items-center h-4">
                <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce [animation-delay:-0.3s]" />
                <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce [animation-delay:-0.15s]" />
                <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input bar — pinned to bottom */}
      <div className="shrink-0 pt-3 border-t border-gray-100">
        {thread.length > 0 && (
          <button
            onClick={() => { setThread([]); setExpandedTable(new Set()); }}
            className="text-xs text-gray-400 hover:text-gray-600 mb-2 hover:underline"
          >
            Clear conversation
          </button>
        )}
        <form
          onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}
          className="flex gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a follow-up or a new question…"
            disabled={loading}
            className="flex-1 rounded-lg border border-gray-300 px-4 py-2.5 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-5 py-2.5 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Thinking…" : "Send"}
          </button>
        </form>
      </div>
    </div>
  );
}
