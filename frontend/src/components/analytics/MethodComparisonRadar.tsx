import { useMemo } from "react";
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend, ResponsiveContainer, Tooltip } from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp } from "lucide-react";

export interface MethodMetrics {
  method: string;
  distribution_similarity: number; // 0-1, higher is better
  correlation_preservation: number; // 0-1, higher is better
  statistical_utility: number; // 0-1, higher is better
  privacy_risk: number; // 0-1, lower is better (inverted for display)
  performance: number; // records/sec, normalized to 0-1
  overall_quality: number; // 0-1, weighted average
}

interface MethodComparisonRadarProps {
  methods: MethodMetrics[];
  selectedMethods?: string[]; // Optionally filter to show only certain methods
  showLegend?: boolean;
}

const METHOD_COLORS: Record<string, string> = {
  mvn: "#10b981", // green
  bootstrap: "#3b82f6", // blue
  rules: "#f59e0b", // amber
  llm: "#8b5cf6", // purple
  bayesian: "#ec4899", // pink
  mice: "#06b6d4", // cyan
};

const METHOD_NAMES: Record<string, string> = {
  mvn: "MVN",
  bootstrap: "Bootstrap",
  rules: "Rules-Based",
  llm: "LLM (GPT-4o-mini)",
  bayesian: "Bayesian Network",
  mice: "MICE",
};

export default function MethodComparisonRadar({
  methods,
  selectedMethods,
  showLegend = true,
}: MethodComparisonRadarProps) {
  // Transform data for radar chart
  const radarData = useMemo(() => {
    // Filter methods if selection provided
    const filteredMethods = selectedMethods
      ? methods.filter((m) => selectedMethods.includes(m.method))
      : methods;

    // Transform to radar chart format
    const metrics = [
      "Distribution Similarity",
      "Correlation Preservation",
      "Statistical Utility",
      "Privacy Protection", // Inverted privacy_risk
      "Performance",
      "Overall Quality",
    ];

    return metrics.map((metric) => {
      const dataPoint: any = { metric };

      filteredMethods.forEach((method) => {
        let value: number;
        switch (metric) {
          case "Distribution Similarity":
            value = method.distribution_similarity * 100;
            break;
          case "Correlation Preservation":
            value = method.correlation_preservation * 100;
            break;
          case "Statistical Utility":
            value = method.statistical_utility * 100;
            break;
          case "Privacy Protection":
            value = (1 - method.privacy_risk) * 100; // Invert so higher is better
            break;
          case "Performance":
            value = method.performance * 100;
            break;
          case "Overall Quality":
            value = method.overall_quality * 100;
            break;
          default:
            value = 0;
        }
        dataPoint[method.method] = value;
      });

      return dataPoint;
    });
  }, [methods, selectedMethods]);

  // Prepare filtered methods for rendering
  const displayMethods = useMemo(() => {
    return selectedMethods
      ? methods.filter((m) => selectedMethods.includes(m.method))
      : methods;
  }, [methods, selectedMethods]);

  // Get top method by overall quality
  const topMethod = useMemo(() => {
    const sorted = [...displayMethods].sort((a, b) => b.overall_quality - a.overall_quality);
    return sorted[0];
  }, [displayMethods]);

  return (
    <Card className="border-2 border-purple-200">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-purple-600" />
          Multi-Dimensional Quality Comparison
        </CardTitle>
        <CardDescription>
          Radar chart comparing generation methods across 6 quality dimensions (0-100 scale)
        </CardDescription>
        {topMethod && (
          <div className="flex items-center gap-2 mt-2">
            <Badge variant="outline" className="bg-green-50 text-green-700">
              Top Method: {METHOD_NAMES[topMethod.method]} (Quality: {(topMethod.overall_quality * 100).toFixed(1)}%)
            </Badge>
          </div>
        )}
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Radar Chart */}
        <ResponsiveContainer width="100%" height={400}>
          <RadarChart data={radarData}>
            <PolarGrid stroke="#cbd5e1" />
            <PolarAngleAxis
              dataKey="metric"
              tick={{ fill: "#475569", fontSize: 12 }}
              tickLine={{ stroke: "#94a3b8" }}
            />
            <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: "#64748b", fontSize: 10 }} />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  return (
                    <div className="bg-white p-3 border rounded-lg shadow-lg">
                      <div className="font-semibold mb-2">{payload[0]?.payload.metric}</div>
                      <div className="space-y-1 text-sm">
                        {payload.map((entry: any) => (
                          <div key={entry.name} className="flex items-center gap-2">
                            <div
                              className="w-3 h-3 rounded-full"
                              style={{ backgroundColor: METHOD_COLORS[entry.name] || "#94a3b8" }}
                            />
                            <span className="font-medium">{METHOD_NAMES[entry.name] || entry.name}:</span>
                            <span className="text-gray-700">{entry.value.toFixed(1)}%</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            {displayMethods.map((method) => (
              <Radar
                key={method.method}
                name={method.method}
                dataKey={method.method}
                stroke={METHOD_COLORS[method.method] || "#94a3b8"}
                fill={METHOD_COLORS[method.method] || "#94a3b8"}
                fillOpacity={0.15}
                strokeWidth={2}
              />
            ))}
            {showLegend && (
              <Legend
                formatter={(value) => METHOD_NAMES[value] || value}
                wrapperStyle={{ paddingTop: "20px" }}
              />
            )}
          </RadarChart>
        </ResponsiveContainer>

        {/* Interpretation Guide */}
        <div className="bg-gradient-to-r from-purple-50 to-pink-50 p-4 rounded-lg border border-purple-200">
          <h4 className="font-semibold text-purple-800 mb-2">Understanding the Radar Chart</h4>
          <div className="text-sm text-gray-700 space-y-2">
            <div className="flex items-start gap-2">
              <div className="w-2 h-2 rounded-full bg-purple-500 mt-1.5"></div>
              <div>
                <strong>Larger area = Better overall quality:</strong> Methods with larger coverage across all dimensions
                perform best
              </div>
            </div>
            <div className="flex items-start gap-2">
              <div className="w-2 h-2 rounded-full bg-purple-500 mt-1.5"></div>
              <div>
                <strong>Distribution Similarity:</strong> How closely synthetic data matches real data distributions
                (Wasserstein distance based)
              </div>
            </div>
            <div className="flex items-start gap-2">
              <div className="w-2 h-2 rounded-full bg-purple-500 mt-1.5"></div>
              <div>
                <strong>Correlation Preservation:</strong> How well the method preserves correlations between variables
              </div>
            </div>
            <div className="flex items-start gap-2">
              <div className="w-2 h-2 rounded-full bg-purple-500 mt-1.5"></div>
              <div>
                <strong>Statistical Utility:</strong> Usefulness for statistical analysis (K-NN RMSE based)
              </div>
            </div>
            <div className="flex items-start gap-2">
              <div className="w-2 h-2 rounded-full bg-purple-500 mt-1.5"></div>
              <div>
                <strong>Privacy Protection:</strong> Lower re-identification risk (higher is better on this chart)
              </div>
            </div>
            <div className="flex items-start gap-2">
              <div className="w-2 h-2 rounded-full bg-purple-500 mt-1.5"></div>
              <div>
                <strong>Performance:</strong> Generation speed (records per second, normalized)
              </div>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-3">
          {displayMethods.slice(0, 3).map((method) => (
            <div
              key={method.method}
              className="p-3 rounded-lg border"
              style={{
                borderColor: METHOD_COLORS[method.method] || "#94a3b8",
                backgroundColor: `${METHOD_COLORS[method.method]}10` || "#f1f5f910",
              }}
            >
              <div className="font-semibold text-sm mb-1" style={{ color: METHOD_COLORS[method.method] }}>
                {METHOD_NAMES[method.method]}
              </div>
              <div className="text-xs text-gray-600">
                Quality: <span className="font-medium">{(method.overall_quality * 100).toFixed(1)}%</span>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
