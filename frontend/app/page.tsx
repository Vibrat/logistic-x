import { api } from "@/lib/api";
import KPICard from "@/components/KPICard";
import ChartRenderer from "@/components/ChartRenderer";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const [kpis, charts] = await Promise.all([
    api.getKPIs().catch(() => []),
    api.getCharts().catch(() => null),
  ]);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-1">Logistics Dashboard</h1>
        <p className="text-sm text-gray-500">Live analytics from the unified order dataset.</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {kpis.map((kpi) => (
          <KPICard key={kpi.id} kpi={kpi} />
        ))}
      </div>

      {/* Charts */}
      {charts && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <ChartRenderer
            title="Order Volume by Month"
            chartType="bar"
            chartData={{
              labels: charts.order_volume_by_month.map((r) => r.dimension),
              datasets: [{
                label: "Orders",
                data: charts.order_volume_by_month.map((r) => r.value),
                backgroundColor: "rgba(59,130,246,0.6)",
                borderColor: "#3b82f6",
              }],
            }}
          />

          <ChartRenderer
            title="On-Time Delivery Rate by Region"
            chartType="bar"
            chartData={{
              labels: charts.on_time_rate_by_region.map((r) => r.dimension),
              datasets: [{
                label: "On-Time Rate (%)",
                data: charts.on_time_rate_by_region.map((r) => r.value),
                backgroundColor: "rgba(16,185,129,0.6)",
                borderColor: "#10b981",
              }],
            }}
          />

          <ChartRenderer
            title="Delayed Orders by Carrier"
            chartType="bar"
            chartData={{
              labels: charts.delayed_orders_by_carrier.map((r) => r.dimension),
              datasets: [{
                label: "Delayed Orders",
                data: charts.delayed_orders_by_carrier.map((r) => r.value),
                backgroundColor: "rgba(239,68,68,0.6)",
                borderColor: "#ef4444",
              }],
            }}
          />
        </div>
      )}

      <p className="text-xs text-gray-400">
        All KPI formulas are defined in <code>backend/config/kpi.json</code>.
      </p>
    </div>
  );
}
