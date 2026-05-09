import Link from "next/link";
import { api } from "@/lib/api";
import KPICard from "@/components/KPICard";
import ChartRenderer from "@/components/ChartRenderer";

export const dynamic = "force-dynamic";

const KPI_REGISTRY = [
  { id: "total_orders",          label: "Total Orders",          description: "COUNT(*)",                                         format: "integer" },
  { id: "delivered_orders",      label: "Delivered Orders",      description: "COUNT(*) WHERE status = delivered",                format: "integer" },
  { id: "delayed_orders",        label: "Delayed Orders",        description: "COUNT(*) WHERE status = delayed",                  format: "integer" },
  { id: "on_time_delivery_rate", label: "On-Time Delivery Rate", description: "delivered ÷ total orders × 100",                   format: "percent" },
  { id: "avg_delivery_days",     label: "Avg Delivery Time",     description: "AVG(delivery_date − order_date) for delivered",    format: "days"    },
];

const AI_EXAMPLES = [
  { q: "Which carrier has the highest delay rate?",            hint: "AI picks the right metric + grouping automatically" },
  { q: "Show on-time delivery rate by region",                 hint: "Breaks down any KPI by any dimension" },
  { q: "Forecast demand for CRAYON-0008 for the next 6 months", hint: "Runs Holt-Winters or linear regression" },
  { q: "How many delayed orders does FedEx have this year?",   hint: "Applies carrier + date filters for you" },
  { q: "Predict demand for the paper category",                hint: "AI explores the DB to find the exact category name" },
];

export default async function DashboardPage() {
  const [kpis, charts] = await Promise.all([
    api.getKPIs().catch(() => []),
    api.getCharts().catch(() => null),
  ]);

  return (
    <div className="space-y-12">

      {/* ── Header ──────────────────────────────────────────────────────────── */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-1">Logistics Dashboard</h1>
        <p className="text-sm text-gray-500">Live analytics from the unified order dataset.</p>
      </div>

      {/* ── KPI Cards ───────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {kpis.map((kpi) => (
          <KPICard key={kpi.id} kpi={kpi} />
        ))}
      </div>

      {/* ── Charts ──────────────────────────────────────────────────────────── */}
      {charts && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <ChartRenderer
            title="Order Volume by Month"
            chartType="bar"
            chartData={{
              labels: charts.order_volume_by_month.map((r) => r.dimension),
              datasets: [{ label: "Orders", data: charts.order_volume_by_month.map((r) => r.value), backgroundColor: "rgba(59,130,246,0.6)", borderColor: "#3b82f6" }],
            }}
          />
          <ChartRenderer
            title="On-Time Delivery Rate by Region"
            chartType="bar"
            chartData={{
              labels: charts.on_time_rate_by_region.map((r) => r.dimension),
              datasets: [{ label: "On-Time Rate (%)", data: charts.on_time_rate_by_region.map((r) => r.value), backgroundColor: "rgba(16,185,129,0.6)", borderColor: "#10b981" }],
            }}
          />
          <ChartRenderer
            title="Delayed Orders by Carrier"
            chartType="bar"
            chartData={{
              labels: charts.delayed_orders_by_carrier.map((r) => r.dimension),
              datasets: [{ label: "Delayed Orders", data: charts.delayed_orders_by_carrier.map((r) => r.value), backgroundColor: "rgba(239,68,68,0.6)", borderColor: "#ef4444" }],
            }}
          />
        </div>
      )}

      {/* ── Ask AI Guide ────────────────────────────────────────────────────── */}
      <section className="rounded-2xl border border-blue-100 bg-blue-50 p-6 space-y-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-blue-900">Ask AI — Natural Language Analytics</h2>
            <p className="text-sm text-blue-700 mt-1">
              Type any logistics question in plain English. The AI reasons about what you need,
              queries the database, and renders the result as a chart + explanation — no SQL required.
            </p>
          </div>
          <Link
            href="/chat"
            className="shrink-0 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition"
          >
            Open Ask AI →
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {AI_EXAMPLES.map(({ q, hint }) => (
            <div key={q} className="bg-white rounded-xl border border-blue-100 px-4 py-3 space-y-1">
              <p className="text-sm font-medium text-gray-800">"{q}"</p>
              <p className="text-xs text-gray-400">{hint}</p>
            </div>
          ))}
        </div>

        <div className="rounded-xl border border-blue-200 bg-white px-5 py-4 space-y-3 text-sm text-gray-700">
          <p className="font-semibold text-gray-800">How the AI reasons</p>
          <ol className="list-decimal list-inside space-y-1.5 text-sm text-gray-600">
            <li><span className="font-medium text-gray-700">Interpret</span> — the AI reads your question and decides whether it needs more information.</li>
            <li><span className="font-medium text-gray-700">Explore</span> — if a value is ambiguous (e.g. "SKU X"), it runs a <code className="text-xs bg-gray-100 px-1 rounded">SELECT DISTINCT</code> against the database to find matching real values.</li>
            <li><span className="font-medium text-gray-700">Clarify</span> — if multiple matches exist, it asks you to pick one. If one exact match is found, it proceeds automatically.</li>
            <li><span className="font-medium text-gray-700">Compute</span> — once all values are confirmed, it calls the right KPI formula or forecasting engine and builds a chart.</li>
          </ol>
        </div>
      </section>

      {/* ── KPI Registry ────────────────────────────────────────────────────── */}
      <section className="space-y-5">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">KPI Registry</h2>
          <p className="text-sm text-gray-500 mt-1">
            All metrics are declared in{" "}
            <code className="text-xs bg-gray-100 border border-gray-200 rounded px-1.5 py-0.5">backend/config/kpi.json</code>.
            The AI is constrained to only these IDs — it can never invent metrics or write SQL.
          </p>
        </div>

        <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-500 text-xs uppercase tracking-wider">ID</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500 text-xs uppercase tracking-wider">Label</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500 text-xs uppercase tracking-wider">Formula</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500 text-xs uppercase tracking-wider">Format</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {KPI_REGISTRY.map((kpi) => (
                <tr key={kpi.id} className="hover:bg-gray-50 transition">
                  <td className="px-4 py-3 font-mono text-xs text-blue-700">{kpi.id}</td>
                  <td className="px-4 py-3 font-medium text-gray-800">{kpi.label}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{kpi.description}</td>
                  <td className="px-4 py-3">
                    <span className="inline-block text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 font-mono">{kpi.format}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* How to add a KPI */}
        <div className="rounded-xl border border-gray-200 bg-white p-5 space-y-3">
          <p className="font-semibold text-gray-800">Adding a new KPI</p>
          <p className="text-sm text-gray-500">
            Append a new entry to <code className="text-xs bg-gray-100 border border-gray-200 rounded px-1.5 py-0.5">backend/config/kpi.json</code>.
            The AI automatically picks it up on the next request — no code changes needed.
          </p>
          <pre className="overflow-x-auto rounded-lg bg-gray-950 text-gray-100 text-xs p-4 leading-relaxed">{`{
  "id": "exception_rate",
  "label": "Exception Rate",
  "description": "Percentage of orders with status = exception",
  "aggregation": "ratio",
  "numerator":   { "field": "*", "filters": { "status": "exception" } },
  "denominator": { "field": "*", "filters": {} },
  "format": "percent"
}`}</pre>
          <p className="text-xs text-gray-400">
            Supported <span className="font-medium">aggregation</span> types:{" "}
            <code className="bg-gray-100 px-1 rounded text-xs">count</code>{" · "}
            <code className="bg-gray-100 px-1 rounded text-xs">sum</code>{" · "}
            <code className="bg-gray-100 px-1 rounded text-xs">avg</code>{" · "}
            <code className="bg-gray-100 px-1 rounded text-xs">ratio</code>{" · "}
            <code className="bg-gray-100 px-1 rounded text-xs">avg_date_diff</code>.
            Any column in the <code className="bg-gray-100 px-1 rounded text-xs">orders</code> table can be used as a field or filter.
          </p>
        </div>
      </section>

    </div>
  );
}
