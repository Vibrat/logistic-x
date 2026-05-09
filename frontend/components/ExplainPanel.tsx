import { ExplanationDetail } from "@/lib/api";

interface Props {
  explanation: ExplanationDetail;
  filtersUsed: Record<string, string>;
}

export default function ExplainPanel({ explanation, filtersUsed }: Props) {
  const hasFilters = Object.keys(filtersUsed).length > 0;

  return (
    <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 text-sm space-y-2">
      <p className="font-semibold text-blue-800 text-xs uppercase tracking-wider">Query Explanation</p>

      <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-gray-700">
        <span className="text-gray-500">Metric</span>
        <span className="font-mono text-xs">{explanation.metric}</span>

        {explanation.group_by && (
          <>
            <span className="text-gray-500">Grouped by</span>
            <span className="font-mono text-xs">{explanation.group_by}</span>
          </>
        )}

        <span className="text-gray-500">Filters</span>
        <span className="font-mono text-xs">
          {hasFilters ? Object.entries(filtersUsed).map(([k, v]) => `${k}=${v}`).join(", ") : "none"}
        </span>

        {explanation.query_plan && (
          <>
            <span className="text-gray-500">Formula</span>
            <span className="font-mono text-xs text-blue-700 break-all">{explanation.query_plan}</span>
          </>
        )}
      </div>
    </div>
  );
}
