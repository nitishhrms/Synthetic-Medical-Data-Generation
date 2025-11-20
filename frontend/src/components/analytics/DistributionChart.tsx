import { useMemo, useState } from "react";
import {
  ComposedChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Line,
} from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { BarChart3, TrendingUp, Box } from "lucide-react";

interface DistributionChartProps {
  realData: number[];
  syntheticData: number[];
  variable: string;
  unit?: string;
  syntheticMethodName?: string;
  wassersteinDistance?: number;
  rmse?: number;
}

export default function DistributionChart({
  realData,
  syntheticData,
  variable,
  unit = "",
  syntheticMethodName = "Synthetic",
  wassersteinDistance,
  rmse,
}: DistributionChartProps) {
  const [chartType, setChartType] = useState<"histogram" | "boxplot" | "overlay">("histogram");

  // Calculate histogram bins
  const histogramData = useMemo(() => {
    const allValues = [...realData, ...syntheticData];
    const min = Math.min(...allValues);
    const max = Math.max(...allValues);
    const binCount = 20;
    const binWidth = (max - min) / binCount;

    const bins: { binStart: number; binEnd: number; real: number; synthetic: number }[] = [];

    for (let i = 0; i < binCount; i++) {
      const binStart = min + i * binWidth;
      const binEnd = binStart + binWidth;

      const realCount = realData.filter((v) => v >= binStart && v < binEnd).length;
      const syntheticCount = syntheticData.filter((v) => v >= binStart && v < binEnd).length;

      bins.push({
        binStart: Math.round(binStart * 10) / 10,
        binEnd: Math.round(binEnd * 10) / 10,
        real: realCount,
        synthetic: syntheticCount,
      });
    }

    return bins;
  }, [realData, syntheticData]);

  // Calculate summary statistics
  const stats = useMemo(() => {
    const calcStats = (data: number[]) => {
      const sorted = [...data].sort((a, b) => a - b);
      const n = data.length;
      const mean = data.reduce((sum, v) => sum + v, 0) / n;
      const variance = data.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / n;
      const std = Math.sqrt(variance);

      return {
        n,
        mean: Math.round(mean * 10) / 10,
        std: Math.round(std * 10) / 10,
        min: Math.round(sorted[0] * 10) / 10,
        q1: Math.round(sorted[Math.floor(n * 0.25)] * 10) / 10,
        median: Math.round(sorted[Math.floor(n * 0.5)] * 10) / 10,
        q3: Math.round(sorted[Math.floor(n * 0.75)] * 10) / 10,
        max: Math.round(sorted[n - 1] * 10) / 10,
      };
    };

    return {
      real: calcStats(realData),
      synthetic: calcStats(syntheticData),
    };
  }, [realData, syntheticData]);

  // Box plot data
  const boxPlotData = useMemo(() => {
    return [
      {
        name: "Real Data",
        min: stats.real.min,
        q1: stats.real.q1,
        median: stats.real.median,
        q3: stats.real.q3,
        max: stats.real.max,
      },
      {
        name: syntheticMethodName,
        min: stats.synthetic.min,
        q1: stats.synthetic.q1,
        median: stats.synthetic.median,
        q3: stats.synthetic.q3,
        max: stats.synthetic.max,
      },
    ];
  }, [stats, syntheticMethodName]);

  return (
    <Card className="border-2 border-blue-200">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-blue-600" />
              {variable} Distribution
            </CardTitle>
            <CardDescription>
              Comparing Real Pilot Data vs {syntheticMethodName} {unit && `(${unit})`}
            </CardDescription>
          </div>
          {wassersteinDistance !== undefined && (
            <div className="text-right">
              <div className="text-xs text-gray-500">Wasserstein Distance</div>
              <div className="text-lg font-bold text-blue-700">{wassersteinDistance.toFixed(2)}</div>
              {wassersteinDistance < 5 && <Badge variant="outline" className="bg-green-50 text-green-700">Excellent</Badge>}
              {wassersteinDistance >= 5 && wassersteinDistance < 10 && (
                <Badge variant="outline" className="bg-yellow-50 text-yellow-700">Good</Badge>
              )}
              {wassersteinDistance >= 10 && <Badge variant="outline" className="bg-red-50 text-red-700">Needs Review</Badge>}
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Chart Type Selector */}
        <Tabs value={chartType} onValueChange={(v) => setChartType(v as any)} className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="histogram" className="flex items-center gap-1">
              <BarChart3 className="h-4 w-4" />
              Histogram
            </TabsTrigger>
            <TabsTrigger value="overlay" className="flex items-center gap-1">
              <TrendingUp className="h-4 w-4" />
              Overlay
            </TabsTrigger>
            <TabsTrigger value="boxplot" className="flex items-center gap-1">
              <Box className="h-4 w-4" />
              Box Plot
            </TabsTrigger>
          </TabsList>

          {/* Histogram View */}
          <TabsContent value="histogram" className="mt-4">
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={histogramData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="binStart"
                  label={{ value: variable + (unit ? ` (${unit})` : ""), position: "insideBottom", offset: -5 }}
                />
                <YAxis label={{ value: "Frequency", angle: -90, position: "insideLeft" }} />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="bg-white p-3 border rounded shadow-lg">
                          <div className="font-semibold mb-2">
                            Range: {data.binStart} - {data.binEnd} {unit}
                          </div>
                          <div className="text-sm space-y-1">
                            <div className="text-green-700">Real: {data.real} records</div>
                            <div className="text-blue-700">{syntheticMethodName}: {data.synthetic} records</div>
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Legend />
                <Bar dataKey="real" fill="#10b981" name="Real Data" opacity={0.8} />
                <Bar dataKey="synthetic" fill="#3b82f6" name={syntheticMethodName} opacity={0.8} />
              </ComposedChart>
            </ResponsiveContainer>
          </TabsContent>

          {/* Overlay View */}
          <TabsContent value="overlay" className="mt-4">
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={histogramData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="binStart"
                  label={{ value: variable + (unit ? ` (${unit})` : ""), position: "insideBottom", offset: -5 }}
                />
                <YAxis label={{ value: "Frequency", angle: -90, position: "insideLeft" }} />
                <Tooltip />
                <Legend />
                <Bar dataKey="real" fill="#10b981" name="Real Data" opacity={0.4} />
                <Bar dataKey="synthetic" fill="#3b82f6" name={syntheticMethodName} opacity={0.4} />
                <Line type="monotone" dataKey="real" stroke="#059669" strokeWidth={2} name="Real Trend" dot={false} />
                <Line
                  type="monotone"
                  dataKey="synthetic"
                  stroke="#2563eb"
                  strokeWidth={2}
                  name="Synthetic Trend"
                  dot={false}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </TabsContent>

          {/* Box Plot View */}
          <TabsContent value="boxplot" className="mt-4">
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={boxPlotData} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" label={{ value: variable + (unit ? ` (${unit})` : ""), position: "insideBottom", offset: -5 }} />
                <YAxis dataKey="name" type="category" />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="bg-white p-3 border rounded shadow-lg">
                          <div className="font-semibold mb-2">{data.name}</div>
                          <div className="text-sm space-y-1">
                            <div>Min: {data.min} {unit}</div>
                            <div>Q1: {data.q1} {unit}</div>
                            <div className="font-bold">Median: {data.median} {unit}</div>
                            <div>Q3: {data.q3} {unit}</div>
                            <div>Max: {data.max} {unit}</div>
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                {/* This is a simplified box plot using error bars */}
                <Bar dataKey="median" fill="#8884d8" />
              </ComposedChart>
            </ResponsiveContainer>
          </TabsContent>
        </Tabs>

        {/* Summary Statistics */}
        <div className="grid grid-cols-2 gap-4 mt-4">
          <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-4 rounded-lg border border-green-200">
            <h4 className="font-semibold text-green-800 mb-3 flex items-center gap-2">
              Real Data Statistics
              <Badge variant="outline" className="bg-white">N={stats.real.n}</Badge>
            </h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-gray-600">Mean:</span>
                <span className="ml-2 font-medium">{stats.real.mean} {unit}</span>
              </div>
              <div>
                <span className="text-gray-600">SD:</span>
                <span className="ml-2 font-medium">{stats.real.std} {unit}</span>
              </div>
              <div>
                <span className="text-gray-600">Median:</span>
                <span className="ml-2 font-medium">{stats.real.median} {unit}</span>
              </div>
              <div>
                <span className="text-gray-600">Range:</span>
                <span className="ml-2 font-medium">
                  {stats.real.min}-{stats.real.max} {unit}
                </span>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-r from-blue-50 to-cyan-50 p-4 rounded-lg border border-blue-200">
            <h4 className="font-semibold text-blue-800 mb-3 flex items-center gap-2">
              {syntheticMethodName} Statistics
              <Badge variant="outline" className="bg-white">N={stats.synthetic.n}</Badge>
            </h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-gray-600">Mean:</span>
                <span className="ml-2 font-medium">{stats.synthetic.mean} {unit}</span>
              </div>
              <div>
                <span className="text-gray-600">SD:</span>
                <span className="ml-2 font-medium">{stats.synthetic.std} {unit}</span>
              </div>
              <div>
                <span className="text-gray-600">Median:</span>
                <span className="ml-2 font-medium">{stats.synthetic.median} {unit}</span>
              </div>
              <div>
                <span className="text-gray-600">Range:</span>
                <span className="ml-2 font-medium">
                  {stats.synthetic.min}-{stats.synthetic.max} {unit}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Quality Metrics */}
        {(wassersteinDistance !== undefined || rmse !== undefined) && (
          <div className="bg-gradient-to-r from-purple-50 to-pink-50 p-4 rounded-lg border border-purple-200">
            <h4 className="font-semibold text-purple-800 mb-3">Quality Metrics</h4>
            <div className="grid grid-cols-2 gap-4">
              {wassersteinDistance !== undefined && (
                <div>
                  <div className="text-xs text-gray-600 mb-1">Wasserstein Distance</div>
                  <div className="text-2xl font-bold text-purple-700">{wassersteinDistance.toFixed(2)}</div>
                  <div className="text-xs text-gray-500 mt-1">Lower is better (measures distribution similarity)</div>
                </div>
              )}
              {rmse !== undefined && (
                <div>
                  <div className="text-xs text-gray-600 mb-1">RMSE (K-NN)</div>
                  <div className="text-2xl font-bold text-pink-700">{rmse.toFixed(2)}</div>
                  <div className="text-xs text-gray-500 mt-1">Prediction error from K-nearest neighbors</div>
                </div>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
