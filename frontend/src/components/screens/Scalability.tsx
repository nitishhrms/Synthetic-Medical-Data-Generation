import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Activity,
  Zap,
  Users,
  TrendingUp,
  Loader2,
  CheckCircle2,
  XCircle,
  BarChart3,
  Database
} from "lucide-react";
import { dataGenerationApi } from "@/services/api";
import type {
  ComprehensiveStudyResponse,
  BenchmarkResponse,
  StressTestResponse,
  PortfolioAnalytics
} from "@/types";

export function Scalability() {
  // Comprehensive Study State
  const [comprehensiveLoading, setComprehensiveLoading] = useState(false);
  const [comprehensiveResult, setComprehensiveResult] = useState<ComprehensiveStudyResponse | null>(null);
  const [comprehensiveParams, setComprehensiveParams] = useState({
    indication: "hypertension",
    phase: "Phase 3",
    n_per_arm: 50,
    target_effect: -5.0,
    method: "mvn" as "mvn" | "bootstrap" | "rules",
    seed: 42,
  });

  // Benchmark State
  const [benchmarkLoading, setBenchmarkLoading] = useState(false);
  const [benchmarkResult, setBenchmarkResult] = useState<BenchmarkResponse | null>(null);
  const [benchmarkParams, setBenchmarkParams] = useState({
    n_per_arm: 50,
    methods: "mvn,bootstrap,rules",
    indication: "hypertension",
    phase: "Phase 3",
  });

  // Stress Test State
  const [stressTestLoading, setStressTestLoading] = useState(false);
  const [stressTestResult, setStressTestResult] = useState<StressTestResponse | null>(null);
  const [stressTestParams, setStressTestParams] = useState({
    n_concurrent_requests: 10,
    n_per_arm: 50,
    indication: "hypertension",
    phase: "Phase 3",
  });

  // Portfolio Analytics State
  const [portfolioLoading, setPortfolioLoading] = useState(false);
  const [portfolioResult, setPortfolioResult] = useState<PortfolioAnalytics | null>(null);

  // Comprehensive Study Generation
  const handleComprehensiveStudy = async () => {
    try {
      setComprehensiveLoading(true);
      const result = await dataGenerationApi.generateComprehensiveStudy(comprehensiveParams);
      setComprehensiveResult(result);
    } catch (error) {
      console.error("Comprehensive study generation failed:", error);
      alert(error instanceof Error ? error.message : "Failed to generate comprehensive study");
    } finally {
      setComprehensiveLoading(false);
    }
  };

  // Performance Benchmark
  const handleBenchmark = async () => {
    try {
      setBenchmarkLoading(true);
      const result = await dataGenerationApi.benchmarkPerformance(benchmarkParams);
      setBenchmarkResult(result);
    } catch (error) {
      console.error("Benchmark failed:", error);
      alert(error instanceof Error ? error.message : "Failed to run benchmark");
    } finally {
      setBenchmarkLoading(false);
    }
  };

  // Stress Test
  const handleStressTest = async () => {
    try {
      setStressTestLoading(true);
      const result = await dataGenerationApi.stressTestConcurrent(stressTestParams);
      setStressTestResult(result);
    } catch (error) {
      console.error("Stress test failed:", error);
      alert(error instanceof Error ? error.message : "Failed to run stress test");
    } finally {
      setStressTestLoading(false);
    }
  };

  // Portfolio Analytics
  const handlePortfolioAnalytics = async () => {
    try {
      setPortfolioLoading(true);
      const result = await dataGenerationApi.getPortfolioAnalytics();
      setPortfolioResult(result);
    } catch (error) {
      console.error("Portfolio analytics failed:", error);
      alert(error instanceof Error ? error.message : "Failed to fetch portfolio analytics");
    } finally {
      setPortfolioLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Scalability Features</h2>
        <p className="text-muted-foreground mt-2">
          Demonstrate realistic scalability scenarios: comprehensive study generation, performance benchmarking,
          concurrent user stress testing, and portfolio analytics.
        </p>
      </div>

      {/* Comprehensive Study Generation */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg">
              <Database className="h-5 w-5 text-white" />
            </div>
            <div>
              <CardTitle>Comprehensive Study Generation</CardTitle>
              <CardDescription>
                Generate complete trial dataset (vitals + demographics + labs + adverse events) in one API call
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Indication</Label>
              <Input
                value={comprehensiveParams.indication}
                onChange={(e) => setComprehensiveParams({ ...comprehensiveParams, indication: e.target.value })}
                placeholder="hypertension"
              />
            </div>
            <div className="space-y-2">
              <Label>Phase</Label>
              <Input
                value={comprehensiveParams.phase}
                onChange={(e) => setComprehensiveParams({ ...comprehensiveParams, phase: e.target.value })}
                placeholder="Phase 3"
              />
            </div>
            <div className="space-y-2">
              <Label>Subjects per Arm</Label>
              <Input
                type="number"
                value={comprehensiveParams.n_per_arm}
                onChange={(e) => setComprehensiveParams({ ...comprehensiveParams, n_per_arm: parseInt(e.target.value) })}
              />
            </div>
            <div className="space-y-2">
              <Label>Method</Label>
              <select
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={comprehensiveParams.method}
                onChange={(e) => setComprehensiveParams({ ...comprehensiveParams, method: e.target.value as "mvn" | "bootstrap" | "rules" })}
              >
                <option value="mvn">MVN (Multivariate Normal)</option>
                <option value="bootstrap">Bootstrap</option>
                <option value="rules">Rules-Based</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label>Target Effect (mmHg)</Label>
              <Input
                type="number"
                step="0.1"
                value={comprehensiveParams.target_effect}
                onChange={(e) => setComprehensiveParams({ ...comprehensiveParams, target_effect: parseFloat(e.target.value) })}
              />
            </div>
            <div className="space-y-2">
              <Label>Random Seed</Label>
              <Input
                type="number"
                value={comprehensiveParams.seed}
                onChange={(e) => setComprehensiveParams({ ...comprehensiveParams, seed: parseInt(e.target.value) })}
              />
            </div>
          </div>

          <Button
            onClick={handleComprehensiveStudy}
            disabled={comprehensiveLoading}
            className="w-full"
          >
            {comprehensiveLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generating Complete Study...
              </>
            ) : (
              <>
                <Database className="mr-2 h-4 w-4" />
                Generate Comprehensive Study
              </>
            )}
          </Button>

          {comprehensiveResult && (
            <div className="mt-4 p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg border">
              <h3 className="font-semibold mb-3 flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-green-600" />
                Study Generated Successfully
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Vitals Records</p>
                  <p className="text-2xl font-bold">{comprehensiveResult.vitals.length}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Demographics</p>
                  <p className="text-2xl font-bold">{comprehensiveResult.demographics.length}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Lab Results</p>
                  <p className="text-2xl font-bold">{comprehensiveResult.labs.length}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Adverse Events</p>
                  <p className="text-2xl font-bold">{comprehensiveResult.adverse_events.length}</p>
                </div>
              </div>
              <div className="mt-4 flex items-center gap-4">
                <Badge variant="outline">
                  Total: {comprehensiveResult.metadata.total_records} records
                </Badge>
                <Badge variant="outline">
                  Subjects: {comprehensiveResult.metadata.n_subjects}
                </Badge>
                <Badge variant="outline">
                  Time: {comprehensiveResult.metadata.generation_time_ms.toFixed(0)} ms
                </Badge>
                {comprehensiveResult.metadata.aact_enhanced && (
                  <Badge className="bg-gradient-to-r from-purple-500 to-pink-500 text-white">
                    AACT Enhanced
                  </Badge>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Performance Benchmark */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-lg">
              <Zap className="h-5 w-5 text-white" />
            </div>
            <div>
              <CardTitle>Performance Benchmark</CardTitle>
              <CardDescription>
                Compare generation speed across MVN, Bootstrap, and Rules methods
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Subjects per Arm</Label>
              <Input
                type="number"
                value={benchmarkParams.n_per_arm}
                onChange={(e) => setBenchmarkParams({ ...benchmarkParams, n_per_arm: parseInt(e.target.value) })}
              />
            </div>
            <div className="space-y-2">
              <Label>Methods (comma-separated)</Label>
              <Input
                value={benchmarkParams.methods}
                onChange={(e) => setBenchmarkParams({ ...benchmarkParams, methods: e.target.value })}
                placeholder="mvn,bootstrap,rules"
              />
            </div>
          </div>

          <Button
            onClick={handleBenchmark}
            disabled={benchmarkLoading}
            className="w-full"
          >
            {benchmarkLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Running Benchmark...
              </>
            ) : (
              <>
                <Zap className="mr-2 h-4 w-4" />
                Run Performance Benchmark
              </>
            )}
          </Button>

          {benchmarkResult && (
            <div className="mt-4 p-4 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-lg border">
              <h3 className="font-semibold mb-3 flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-blue-600" />
                Benchmark Results (3 runs averaged)
              </h3>
              <div className="space-y-3">
                {benchmarkResult.ranking.map((item, index) => {
                  const result = benchmarkResult.benchmark_results[item.method];
                  return (
                    <div key={item.method} className="flex items-center justify-between p-3 bg-white rounded-lg">
                      <div className="flex items-center gap-3">
                        <Badge variant={index === 0 ? "default" : "outline"}>
                          {index + 1}
                        </Badge>
                        <div>
                          <p className="font-semibold capitalize">{item.method}</p>
                          <p className="text-sm text-muted-foreground">
                            {result.records_generated} records
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-bold">{result.avg_time_ms} ms</p>
                        <p className="text-sm text-muted-foreground">
                          {result.records_per_second.toFixed(0)} rec/sec
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
              {benchmarkResult.fastest_method && (
                <div className="mt-3 text-center">
                  <Badge className="bg-gradient-to-r from-blue-500 to-cyan-500 text-white">
                    Fastest: {benchmarkResult.fastest_method.toUpperCase()}
                  </Badge>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Grid for Stress Test and Portfolio Analytics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Stress Test */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <div className="p-2 bg-gradient-to-r from-orange-500 to-red-500 rounded-lg">
                <Activity className="h-5 w-5 text-white" />
              </div>
              <div>
                <CardTitle>Concurrent Stress Test</CardTitle>
                <CardDescription>
                  Simulate multiple researchers generating data simultaneously
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Concurrent Requests</Label>
              <Input
                type="number"
                value={stressTestParams.n_concurrent_requests}
                onChange={(e) => setStressTestParams({ ...stressTestParams, n_concurrent_requests: parseInt(e.target.value) })}
              />
            </div>
            <div className="space-y-2">
              <Label>Subjects per Request</Label>
              <Input
                type="number"
                value={stressTestParams.n_per_arm}
                onChange={(e) => setStressTestParams({ ...stressTestParams, n_per_arm: parseInt(e.target.value) })}
              />
            </div>

            <Button
              onClick={handleStressTest}
              disabled={stressTestLoading}
              className="w-full"
            >
              {stressTestLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Running Stress Test...
                </>
              ) : (
                <>
                  <Activity className="mr-2 h-4 w-4" />
                  Run Stress Test
                </>
              )}
            </Button>

            {stressTestResult && (
              <div className="mt-4 p-4 bg-gradient-to-r from-orange-50 to-red-50 rounded-lg border">
                <h3 className="font-semibold mb-3 flex items-center gap-2">
                  {stressTestResult.pass_criteria.passed ? (
                    <CheckCircle2 className="h-5 w-5 text-green-600" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-600" />
                  )}
                  {stressTestResult.pass_criteria.passed ? "PASSED" : "FAILED"}
                </h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Total Requests:</span>
                    <span className="font-semibold">{stressTestResult.stress_test_results.total_requests}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Successful:</span>
                    <span className="font-semibold text-green-600">
                      {stressTestResult.stress_test_results.successful_requests}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Failed:</span>
                    <span className="font-semibold text-red-600">
                      {stressTestResult.stress_test_results.failed_requests}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Total Time:</span>
                    <span className="font-semibold">{stressTestResult.stress_test_results.total_time_seconds}s</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Throughput:</span>
                    <span className="font-semibold">
                      {stressTestResult.stress_test_results.aggregate_throughput_records_per_second.toFixed(0)} rec/sec
                    </span>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Portfolio Analytics */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <div className="p-2 bg-gradient-to-r from-green-500 to-emerald-500 rounded-lg">
                <TrendingUp className="h-5 w-5 text-white" />
              </div>
              <div>
                <CardTitle>Portfolio Analytics</CardTitle>
                <CardDescription>
                  Organization-wide trial generation statistics
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button
              onClick={handlePortfolioAnalytics}
              disabled={portfolioLoading}
              className="w-full"
            >
              {portfolioLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Loading Analytics...
                </>
              ) : (
                <>
                  <TrendingUp className="mr-2 h-4 w-4" />
                  View Portfolio Analytics
                </>
              )}
            </Button>

            {portfolioResult && (
              <div className="mt-4 p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border">
                <h3 className="font-semibold mb-3 flex items-center gap-2">
                  <Users className="h-5 w-5 text-green-600" />
                  Portfolio Summary
                </h3>
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-white p-3 rounded">
                      <p className="text-sm text-muted-foreground">Total Studies</p>
                      <p className="text-2xl font-bold">{portfolioResult.portfolio_summary.total_studies}</p>
                    </div>
                    <div className="bg-white p-3 rounded">
                      <p className="text-sm text-muted-foreground">Total Subjects</p>
                      <p className="text-2xl font-bold">{portfolioResult.portfolio_summary.total_subjects}</p>
                    </div>
                  </div>
                  <div className="bg-white p-3 rounded">
                    <p className="text-sm text-muted-foreground mb-2">By Indication</p>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      {Object.entries(portfolioResult.portfolio_summary.studies_by_indication).map(([indication, count]) => (
                        <div key={indication} className="flex justify-between">
                          <span className="capitalize">{indication}:</span>
                          <span className="font-semibold">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="bg-white p-3 rounded">
                    <p className="text-sm text-muted-foreground">Quality Score</p>
                    <p className="text-lg font-bold">
                      {(portfolioResult.quality_metrics.average_quality_score * 100).toFixed(1)}%
                    </p>
                  </div>
                </div>
                {portfolioResult.note && (
                  <p className="mt-3 text-xs text-muted-foreground italic">{portfolioResult.note}</p>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
