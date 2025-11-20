import { useState, useEffect } from "react";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Alert, AlertDescription } from "../components/ui/alert";
import { Badge } from "../components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import { ScatterChart, Scatter, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { Zap, Award, Lightbulb, BarChart3, Download, RefreshCw, AlertCircle, CheckCircle2, TrendingUp } from "lucide-react";
import { analyticsApi } from "@/services/api";
import MethodComparisonRadar, { type MethodMetrics } from "@/components/analytics/MethodComparisonRadar";

interface BenchmarkResult {
  methods: MethodMetrics[];
  recommendations: {
    best_overall: string;
    best_for_speed: string;
    best_for_quality: string;
    best_for_privacy: string;
  };
  detailed_metrics: {
    [method: string]: {
      wasserstein_distances: {
        SystolicBP: number;
        DiastolicBP: number;
        HeartRate: number;
        Temperature: number;
      };
      generation_time_ms: number;
      records_per_second: number;
      correlation_matrix_diff: number;
    };
  };
}

const METHOD_INFO: Record<string, { name: string; description: string; icon: string }> = {
  mvn: {
    name: "MVN (Multivariate Normal)",
    description: "Statistical distribution-based generation preserving mean and covariance",
    icon: "📊",
  },
  bootstrap: {
    name: "Bootstrap",
    description: "Resampling from real data with Gaussian jitter",
    icon: "🔄",
  },
  rules: {
    name: "Rules-Based",
    description: "Deterministic generation using business rules",
    icon: "📋",
  },
  llm: {
    name: "LLM (GPT-4o-mini)",
    description: "AI-powered generation with context awareness",
    icon: "🤖",
  },
  bayesian: {
    name: "Bayesian Network",
    description: "Probabilistic graphical model capturing dependencies",
    icon: "🔗",
  },
  mice: {
    name: "MICE (Multiple Imputation)",
    description: "Chained equations with uncertainty quantification",
    icon: "🎲",
  },
};

export function MethodComparison() {
  const [activeTab, setActiveTab] = useState("overview");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [benchmarkData, setBenchmarkData] = useState<BenchmarkResult | null>(null);

  // Run benchmark comparison
  const runBenchmark = async () => {
    setLoading(true);
    setError(null);

    try {
      // Call the benchmark/performance endpoint
      const result = await analyticsApi.compareMethodPerformance({
        mvn: { generation_time_ms: 14, records_generated: 400, quality_score: 0.87, aact_similarity: 0.91 },
        bootstrap: { generation_time_ms: 3, records_generated: 400, quality_score: 0.92, aact_similarity: 0.88 },
        rules: { generation_time_ms: 5, records_generated: 400, quality_score: 0.83, aact_similarity: 0.85 },
        llm: { generation_time_ms: 2500, records_generated: 200, quality_score: 0.89, aact_similarity: 0.93 }
      });

      // Transform the result to match BenchmarkResult interface
      // Note: This is a placeholder - you'll need to adapt based on actual API response
      setBenchmarkData(result as any);
    } catch (err: any) {
      console.error("Benchmark error:", err);
      setError(err.message || "Failed to run benchmark comparison");
    } finally {
      setLoading(false);
    }
  };

  // Auto-run on mount
  useEffect(() => {
    runBenchmark();
  }, []);

  // Export results
  const exportResults = () => {
    if (!benchmarkData) return;

    const exportData = {
      timestamp: new Date().toISOString(),
      methods: benchmarkData.methods,
      recommendations: benchmarkData.recommendations,
      detailed_metrics: benchmarkData.detailed_metrics,
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `method-comparison-${new Date().toISOString().split("T")[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Get quality badge
  const getQualityBadge = (score: number) => {
    if (score >= 0.85) return <Badge className="bg-green-500 text-white">Excellent</Badge>;
    if (score >= 0.70) return <Badge className="bg-blue-500 text-white">Good</Badge>;
    if (score >= 0.50) return <Badge className="bg-yellow-500 text-white">Fair</Badge>;
    return <Badge className="bg-red-500 text-white">Poor</Badge>;
  };

  // Get performance badge
  const getPerformanceBadge = (recordsPerSec: number) => {
    if (recordsPerSec >= 50000) return <Badge className="bg-green-500 text-white">Ultra Fast</Badge>;
    if (recordsPerSec >= 10000) return <Badge className="bg-blue-500 text-white">Fast</Badge>;
    if (recordsPerSec >= 1000) return <Badge className="bg-yellow-500 text-white">Moderate</Badge>;
    return <Badge className="bg-orange-500 text-white">Slow</Badge>;
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <BarChart3 className="h-8 w-8 text-purple-600" />
            Method Comparison & Benchmarking
          </h1>
          <p className="text-gray-500 mt-1">
            Compare all 6 synthetic data generation methods across quality, performance, and utility dimensions
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={runBenchmark} disabled={loading} variant="outline">
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
            Re-run Benchmark
          </Button>
          <Button onClick={exportResults} disabled={!benchmarkData || loading}>
            <Download className="h-4 w-4 mr-2" />
            Export Results
          </Button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Loading State */}
      {loading && (
        <Card>
          <CardContent className="p-8 text-center">
            <RefreshCw className="h-8 w-8 animate-spin text-purple-600 mx-auto mb-4" />
            <p className="text-gray-600">Running comprehensive benchmark comparison...</p>
            <p className="text-sm text-gray-500 mt-2">This may take up to 30 seconds</p>
          </CardContent>
        </Card>
      )}

      {/* Main Content */}
      {!loading && benchmarkData && (
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="quality">Quality Metrics</TabsTrigger>
            <TabsTrigger value="performance">Performance</TabsTrigger>
            <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {/* Radar Chart */}
            <MethodComparisonRadar methods={benchmarkData.methods} />

            {/* Quick Comparison Matrix */}
            <Card>
              <CardHeader>
                <CardTitle>6-Method Comparison Matrix</CardTitle>
                <CardDescription>Overall quality scores and key characteristics</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Method</TableHead>
                      <TableHead>Overall Quality</TableHead>
                      <TableHead>Distribution</TableHead>
                      <TableHead>Correlation</TableHead>
                      <TableHead>Utility</TableHead>
                      <TableHead>Privacy</TableHead>
                      <TableHead>Speed</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {benchmarkData.methods
                      .sort((a, b) => b.overall_quality - a.overall_quality)
                      .map((method, index) => (
                        <TableRow key={method.method}>
                          <TableCell className="font-medium">
                            <div className="flex items-center gap-2">
                              <span className="text-xl">{METHOD_INFO[method.method]?.icon}</span>
                              <div>
                                <div>{METHOD_INFO[method.method]?.name}</div>
                                {index === 0 && (
                                  <Badge variant="outline" className="bg-green-50 text-green-700 text-xs mt-1">
                                    Best Overall
                                  </Badge>
                                )}
                              </div>
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-lg">
                                {(method.overall_quality * 100).toFixed(1)}%
                              </span>
                              {getQualityBadge(method.overall_quality)}
                            </div>
                          </TableCell>
                          <TableCell>{(method.distribution_similarity * 100).toFixed(1)}%</TableCell>
                          <TableCell>{(method.correlation_preservation * 100).toFixed(1)}%</TableCell>
                          <TableCell>{(method.statistical_utility * 100).toFixed(1)}%</TableCell>
                          <TableCell>{((1 - method.privacy_risk) * 100).toFixed(1)}%</TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <Zap className="h-4 w-4 text-yellow-500" />
                              <span className="font-medium">{(method.performance * 100).toFixed(1)}%</span>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Quality Metrics Tab */}
          <TabsContent value="quality" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Distribution Similarity (Wasserstein Distance)</CardTitle>
                <CardDescription>Lower values indicate better distribution matching</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Method</TableHead>
                      <TableHead>Systolic BP</TableHead>
                      <TableHead>Diastolic BP</TableHead>
                      <TableHead>Heart Rate</TableHead>
                      <TableHead>Temperature</TableHead>
                      <TableHead>Average</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {benchmarkData.methods.map((method) => {
                      const metrics = benchmarkData.detailed_metrics[method.method];
                      const avgDist = metrics
                        ? (metrics.wasserstein_distances.SystolicBP +
                            metrics.wasserstein_distances.DiastolicBP +
                            metrics.wasserstein_distances.HeartRate +
                            metrics.wasserstein_distances.Temperature) /
                          4
                        : 0;

                      return (
                        <TableRow key={method.method}>
                          <TableCell className="font-medium">{METHOD_INFO[method.method]?.name}</TableCell>
                          <TableCell>{metrics?.wasserstein_distances.SystolicBP.toFixed(2) || "N/A"}</TableCell>
                          <TableCell>{metrics?.wasserstein_distances.DiastolicBP.toFixed(2) || "N/A"}</TableCell>
                          <TableCell>{metrics?.wasserstein_distances.HeartRate.toFixed(2) || "N/A"}</TableCell>
                          <TableCell>{metrics?.wasserstein_distances.Temperature.toFixed(3) || "N/A"}</TableCell>
                          <TableCell className="font-bold">{avgDist.toFixed(2)}</TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Correlation Preservation</CardTitle>
                <CardDescription>How well each method preserves variable relationships</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {benchmarkData.methods
                    .sort((a, b) => b.correlation_preservation - a.correlation_preservation)
                    .map((method) => (
                      <div key={method.method} className="flex items-center gap-4">
                        <div className="w-48 font-medium">{METHOD_INFO[method.method]?.name}</div>
                        <div className="flex-1">
                          <div className="bg-gray-200 rounded-full h-6 overflow-hidden">
                            <div
                              className="bg-gradient-to-r from-blue-500 to-purple-600 h-full flex items-center justify-end px-2 text-white text-xs font-medium"
                              style={{ width: `${method.correlation_preservation * 100}%` }}
                            >
                              {(method.correlation_preservation * 100).toFixed(1)}%
                            </div>
                          </div>
                        </div>
                        {method.correlation_preservation >= 0.9 && <CheckCircle2 className="h-5 w-5 text-green-600" />}
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Performance Tab */}
          <TabsContent value="performance" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Generation Performance Metrics</CardTitle>
                <CardDescription>Speed and efficiency comparison</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Method</TableHead>
                      <TableHead>Generation Time</TableHead>
                      <TableHead>Records/Second</TableHead>
                      <TableHead>Performance Rating</TableHead>
                      <TableHead>Best Use Case</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {benchmarkData.methods
                      .sort((a, b) => {
                        const aSpeed = benchmarkData.detailed_metrics[a.method]?.records_per_second || 0;
                        const bSpeed = benchmarkData.detailed_metrics[b.method]?.records_per_second || 0;
                        return bSpeed - aSpeed;
                      })
                      .map((method) => {
                        const metrics = benchmarkData.detailed_metrics[method.method];
                        return (
                          <TableRow key={method.method}>
                            <TableCell className="font-medium">{METHOD_INFO[method.method]?.name}</TableCell>
                            <TableCell>{metrics?.generation_time_ms.toFixed(0) || "N/A"} ms</TableCell>
                            <TableCell className="font-bold">
                              {metrics?.records_per_second.toLocaleString() || "N/A"}
                            </TableCell>
                            <TableCell>
                              {metrics?.records_per_second
                                ? getPerformanceBadge(metrics.records_per_second)
                                : "N/A"}
                            </TableCell>
                            <TableCell className="text-sm text-gray-600">
                              {method.method === "bootstrap" && "Large-scale generation"}
                              {method.method === "mvn" && "Fast statistical analysis"}
                              {method.method === "rules" && "Deterministic scenarios"}
                              {method.method === "llm" && "Creative small datasets"}
                              {method.method === "bayesian" && "Complex dependencies"}
                              {method.method === "mice" && "Missing data scenarios"}
                            </TableCell>
                          </TableRow>
                        );
                      })}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Recommendations Tab */}
          <TabsContent value="recommendations" className="space-y-6">
            <div className="grid grid-cols-2 gap-6">
              {/* Best Overall */}
              <Card className="border-2 border-green-200">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 text-green-600" />
                    Best Overall Quality
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-center">
                    <div className="text-4xl mb-2">
                      {METHOD_INFO[benchmarkData.recommendations.best_overall]?.icon}
                    </div>
                    <div className="font-bold text-xl text-green-700">
                      {METHOD_INFO[benchmarkData.recommendations.best_overall]?.name}
                    </div>
                    <p className="text-sm text-gray-600 mt-2">
                      {METHOD_INFO[benchmarkData.recommendations.best_overall]?.description}
                    </p>
                  </div>
                </CardContent>
              </Card>

              {/* Best for Speed */}
              <Card className="border-2 border-blue-200">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Zap className="h-5 w-5 text-blue-600" />
                    Best for Speed
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-center">
                    <div className="text-4xl mb-2">
                      {METHOD_INFO[benchmarkData.recommendations.best_for_speed]?.icon}
                    </div>
                    <div className="font-bold text-xl text-blue-700">
                      {METHOD_INFO[benchmarkData.recommendations.best_for_speed]?.name}
                    </div>
                    <p className="text-sm text-gray-600 mt-2">
                      {METHOD_INFO[benchmarkData.recommendations.best_for_speed]?.description}
                    </p>
                  </div>
                </CardContent>
              </Card>

              {/* Best for Quality */}
              <Card className="border-2 border-purple-200">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-purple-600" />
                    Best for Quality
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-center">
                    <div className="text-4xl mb-2">
                      {METHOD_INFO[benchmarkData.recommendations.best_for_quality]?.icon}
                    </div>
                    <div className="font-bold text-xl text-purple-700">
                      {METHOD_INFO[benchmarkData.recommendations.best_for_quality]?.name}
                    </div>
                    <p className="text-sm text-gray-600 mt-2">
                      {METHOD_INFO[benchmarkData.recommendations.best_for_quality]?.description}
                    </p>
                  </div>
                </CardContent>
              </Card>

              {/* Best for Privacy */}
              <Card className="border-2 border-pink-200">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <AlertCircle className="h-5 w-5 text-pink-600" />
                    Best for Privacy
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-center">
                    <div className="text-4xl mb-2">
                      {METHOD_INFO[benchmarkData.recommendations.best_for_privacy]?.icon}
                    </div>
                    <div className="font-bold text-xl text-pink-700">
                      {METHOD_INFO[benchmarkData.recommendations.best_for_privacy]?.name}
                    </div>
                    <p className="text-sm text-gray-600 mt-2">
                      {METHOD_INFO[benchmarkData.recommendations.best_for_privacy]?.description}
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Selection Guide */}
            <Card>
              <CardHeader>
                <CardTitle>Method Selection Guide</CardTitle>
                <CardDescription>Choose the right method for your use case</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-start gap-3 p-3 bg-green-50 rounded-lg">
                    <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
                    <div>
                      <div className="font-semibold text-green-800">For Production Use:</div>
                      <div className="text-sm text-gray-700">
                        Choose <strong>{METHOD_INFO[benchmarkData.recommendations.best_overall]?.name}</strong> - Best
                        balance of quality, speed, and reliability
                      </div>
                    </div>
                  </div>

                  <div className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
                    <Zap className="h-5 w-5 text-blue-600 mt-0.5" />
                    <div>
                      <div className="font-semibold text-blue-800">For Large-Scale Generation:</div>
                      <div className="text-sm text-gray-700">
                        Choose <strong>{METHOD_INFO[benchmarkData.recommendations.best_for_speed]?.name}</strong> -
                        Fastest generation for million-scale datasets
                      </div>
                    </div>
                  </div>

                  <div className="flex items-start gap-3 p-3 bg-purple-50 rounded-lg">
                    <TrendingUp className="h-5 w-5 text-purple-600 mt-0.5" />
                    <div>
                      <div className="font-semibold text-purple-800">For Statistical Analysis:</div>
                      <div className="text-sm text-gray-700">
                        Choose <strong>{METHOD_INFO[benchmarkData.recommendations.best_for_quality]?.name}</strong> -
                        Highest statistical fidelity
                      </div>
                    </div>
                  </div>

                  <div className="flex items-start gap-3 p-3 bg-pink-50 rounded-lg">
                    <AlertCircle className="h-5 w-5 text-pink-600 mt-0.5" />
                    <div>
                      <div className="font-semibold text-pink-800">For Privacy-Sensitive Data:</div>
                      <div className="text-sm text-gray-700">
                        Choose <strong>{METHOD_INFO[benchmarkData.recommendations.best_for_privacy]?.name}</strong> -
                        Lowest re-identification risk
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}
