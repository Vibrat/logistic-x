import { KPI } from "@/lib/api";
import clsx from "clsx";

interface Props {
  kpi: KPI;
}

function formatValue(value: number, format: KPI["format"]): string {
  if (format === "percent") return `${value}%`;
  if (format === "days") return `${value} days`;
  return value.toLocaleString();
}

const formatColors: Record<KPI["format"], string> = {
  integer: "text-blue-600",
  percent: "text-green-600",
  days: "text-amber-600",
};

export default function KPICard({ kpi }: Props) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wider text-gray-500 mb-1">
        {kpi.label}
      </p>
      <p className={clsx("text-3xl font-bold", formatColors[kpi.format])}>
        {formatValue(kpi.value, kpi.format)}
      </p>
    </div>
  );
}
