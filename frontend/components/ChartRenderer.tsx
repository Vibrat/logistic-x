"use client";

import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import { AskResponse } from "@/lib/api";

type ChartDataProp = NonNullable<AskResponse["chart_data"]>;

interface Props {
  chartType: "bar" | "line" | "pie";
  chartData: ChartDataProp;
  title?: string;
}

const COLORS = ["#3b82f6", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6", "#ec4899", "#06b6d4"];

function toPlotData(chartData: ChartDataProp) {
  return chartData.labels.map((label, i) => {
    const point: Record<string, unknown> = { name: label };
    chartData.datasets.forEach((ds) => {
      point[ds.label] = ds.data[i] ?? null;
    });
    return point;
  });
}

export default function ChartRenderer({ chartType, chartData, title }: Props) {
  const data = toPlotData(chartData);

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
      {title && <h3 className="text-sm font-semibold text-gray-700 mb-4">{title}</h3>}
      <ResponsiveContainer width="100%" height={280}>
        {chartType === "line" ? (
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="name" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Legend />
            {chartData.datasets.map((ds, i) => (
              <Line
                key={ds.label}
                type="monotone"
                dataKey={ds.label}
                stroke={ds.borderColor ?? COLORS[i % COLORS.length]}
                strokeDasharray={ds.borderDash?.join(" ")}
                dot={false}
                connectNulls={ds.label === "Forecast"}
              />
            ))}
          </LineChart>
        ) : chartType === "pie" ? (
          <PieChart>
            <Pie data={data} dataKey={chartData.datasets[0]?.label ?? "value"} nameKey="name" cx="50%" cy="50%" outerRadius={100} label>
              {data.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        ) : (
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="name" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Legend />
            {chartData.datasets.map((ds, i) => (
              <Bar
                key={ds.label}
                dataKey={ds.label}
                fill={ds.backgroundColor ?? COLORS[i % COLORS.length]}
              />
            ))}
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
