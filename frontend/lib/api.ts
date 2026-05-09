const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface KPI {
  id: string;
  label: string;
  value: number;
  format: "integer" | "percent" | "days";
}

export interface ChartRow {
  dimension: string;
  value: number;
}

export interface DashboardCharts {
  order_volume_by_month: ChartRow[];
  on_time_rate_by_region: ChartRow[];
  delayed_orders_by_carrier: ChartRow[];
}

export interface ExplanationDetail {
  metric: string;
  group_by: string | null;
  filters_applied: Record<string, string>;
  query_plan: string | null;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface AskResponse {
  answer: string;
  needs_clarification: boolean;
  chart_type: "bar" | "line" | "pie" | null;
  chart_data: {
    labels: string[];
    datasets: {
      label: string;
      data: (number | null)[];
      backgroundColor?: string;
      borderColor?: string;
      borderDash?: number[];
    }[];
  } | null;
  explanation: ExplanationDetail | null;
  filters_used: Record<string, string>;
  raw_data: Record<string, unknown>[];
  inventory_recommendation?: string | null;
}

export interface ForecastResponse {
  historical: { month: string; quantity: number }[];
  forecast: { month: string; quantity: number; lower: number; upper: number }[];
  inventory_recommendation: string;
  methodology: string;
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "API error");
  }
  return res.json();
}

export const api = {
  getKPIs: () => apiFetch<KPI[]>("/api/dashboard/kpis"),

  getCharts: () => apiFetch<DashboardCharts>("/api/dashboard/charts"),

  ask: (question: string, history: ChatMessage[] = []) =>
    apiFetch<AskResponse>("/api/ask", {
      method: "POST",
      body: JSON.stringify({ question, history }),
    }),

  forecast: (params: {
    group_by: string;
    group_value: string;
    horizon_months: number;
    method?: string;
  }) =>
    apiFetch<ForecastResponse>("/api/forecast", {
      method: "POST",
      body: JSON.stringify(params),
    }),
};
