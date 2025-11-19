import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { qualityApi, analyticsApi, dataGenerationApi } from "@/services/api";
import { useData } from "@/contexts/DataContext";
import type { ValidationResponse, QualityAssessmentResponse, VitalsRecord } from "@/types";
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Loader2,
  Shield,
  Wrench,
  BarChart3,
  Activity,
  TrendingUp,
  Download,
  RefreshCw
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from "recharts";

export function Quality() {
  const {
    generatedData,
    setGeneratedData,
    repairedData,
    setRepairedData,
    pilotData,
    setPilotData,
    qualityMetrics,
    setQualityMetrics,
    validationResults,
    setValidationResults
  } = useData();

  const [isValidating, setIsValidating] = useState(false);
  const [isRepairing, setIsRepairing] = useState(false);
  const [isLoadingQuality, setIsLoadingQuality] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  // Auto-load pilot data on mount
  useEffect(() => {
    if (!pilotData) {
      loadPilotData();
    }
  }, []);

  // Auto-run quality assessment when data is generated
  useEffect(() => {
    if (generatedData && pilotData && !qualityMetrics) {
      runQualityAssessment();
    }
  }, [generatedData, pilotData]);

  const loadPilotData = async () => {
    try {
      const data = await dataGenerationApi.getPilotData();
      setPilotData(data);
    } catch (err) {
      console.error("Failed to load pilot data:", err);
    }
  };

  const runValidation = async () => {
    if (!generatedData) {
      setError("No generated data available. Please generate data first from the Generate screen.");
      return;
    }

    setIsValidating(true);
    setError("");

    try {
      const results = await qualityApi.validateVitals(generatedData);
      setValidationResults(results);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Validation failed");
    } finally {
      setIsValidating(false);
    }
  };

  const runQualityAssessment = async () => {
    if (!generatedData) {
      setError("No generated data available. Please generate data first.");
      return;
    }

    if (!pilotData) {
      setError("Loading pilot data for comparison...");
      await loadPilotData();
      return;
    }

    setIsLoadingQuality(true);
    setError("");

    try {
      const assessment = await analyticsApi.comprehensiveQuality(pilotData, generatedData, 5);
      setQualityMetrics(assessment);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Quality assessment failed");
    } finally {
      setIsLoadingQuality(false);
    }
  };

  const repairData = async () => {
    if (!generatedData) {
      setError("No generated data available to repair.");
      return;
    }

    setIsRepairing(true);
    setError("");
    setSuccessMessage("");

    try {
      const result = await qualityApi.repairVitals(generatedData);
      setRepairedData(result.repaired_records);
      setValidationResults(result.validation_after);
      setSuccessMessage(
        `✅ Successfully repaired ${result.repaired_records.length} records! Validation score improved to ${(result.validation_after.quality_score * 100).toFixed(1)}%`
      );

      // Optionally replace generated data with repaired data
      // setGeneratedData(result.repaired_records);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Data repair failed");
    } finally {
      setIsRepairing(false);
    }
  };

  const useRepairedData = () => {
    if (repairedData) {
      setGeneratedData(repairedData);
      setSuccessMessage("✅ Repaired data is now active. You can use it for analytics and export.");
      // Re-run quality assessment on repaired data
      setTimeout(() => runQualityAssessment(), 500);
    }
  };

  const downloadData = (data: VitalsRecord[], filename: string) => {
    const csv = [
      Object.keys(data[0]).join(','),
      ...data.map(row => Object.values(row).join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getQualityBadge = (score: number) => {
    if (score >= 0.85) return { variant: "default" as const, label: "Excellent", color: "bg-green-500" };
    if (score >= 0.70) return { variant: "secondary" as const, label: "Good", color: "bg-yellow-500" };
    return { variant: "destructive" as const, label: "Needs Improvement", color: "bg-red-500" };
  };

  return (
    <div className="p-8 space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Quality Assessment & Data Repair</h2>
        <p className="text-muted-foreground">
          Comprehensive quality validation, statistical comparison, and automated data repair
        </p>
      </div>

      {/* Status Messages */}
      {error && (
        <div className="text-sm text-destructive bg-destructive/10 p-4 rounded-md flex items-start gap-2 border border-destructive/20">
          <AlertTriangle className="h-5 w-5 mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {successMessage && (
        <div className="text-sm text-green-700 bg-green-50 dark:bg-green-900/20 p-4 rounded-md flex items-start gap-2 border border-green-200 dark:border-green-800">
          <CheckCircle2 className="h-5 w-5 mt-0.5 flex-shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      {!generatedData ? (
        <Card>
          <CardHeader>
            <CardTitle>No Data Available</CardTitle>
            <CardDescription>
              Please generate synthetic data first from the Generate screen
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-sm text-muted-foreground">
              Go to the <strong>Generate</strong> screen and create some synthetic data to assess quality.
            </div>
          </CardContent>
        </Card>
      ) : (
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">
              <Activity className="h-4 w-4 mr-2" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="quality">
              <BarChart3 className="h-4 w-4 mr-2" />
              Quality Metrics
            </TabsTrigger>
            <TabsTrigger value="validation">
              <Shield className="h-4 w-4 mr-2" />
              Validation
            </TabsTrigger>
            <TabsTrigger value="repair">
              <Wrench className="h-4 w-4 mr-2" />
              Repair
            </TabsTrigger>
          </TabsList>

          {/* ====== OVERVIEW TAB ====== */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid gap-4 md:grid-cols-3">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">Generated Records</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{generatedData.length}</div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {new Set(generatedData.map(r => r.SubjectID)).size} unique subjects
                  </p>
                </CardContent>
              </Card>

              {qualityMetrics && (
                <>
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-medium">Overall Quality Score</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold">
                        {(qualityMetrics.overall_quality_score * 100).toFixed(0)}%
                      </div>
                      <Badge {...getQualityBadge(qualityMetrics.overall_quality_score)} className="mt-2">
                        {getQualityBadge(qualityMetrics.overall_quality_score).label}
                      </Badge>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-medium">K-NN Imputation Score</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold">
                        {qualityMetrics.knn_imputation_score.toFixed(3)}
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        Nearest neighbor match quality
                      </p>
                    </CardContent>
                  </Card>
                </>
              )}
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
                <CardDescription>
                  Common quality assessment and repair operations
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex flex-wrap gap-3">
                  <Button onClick={runQualityAssessment} disabled={isLoadingQuality}>
                    {isLoadingQuality ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <TrendingUp className="mr-2 h-4 w-4" />
                        Run Quality Assessment
                      </>
                    )}
                  </Button>

                  <Button variant="outline" onClick={runValidation} disabled={isValidating}>
                    {isValidating ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Validating...
                      </>
                    ) : (
                      <>
                        <Shield className="mr-2 h-4 w-4" />
                        Validate Data
                      </>
                    )}
                  </Button>

                  <Button variant="outline" onClick={repairData} disabled={isRepairing}>
                    {isRepairing ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Repairing...
                      </>
                    ) : (
                      <>
                        <Wrench className="mr-2 h-4 w-4" />
                        Auto-Repair Data
                      </>
                    )}
                  </Button>

                  <Button
                    variant="outline"
                    onClick={() => downloadData(generatedData, 'synthetic_data.csv')}
                  >
                    <Download className="mr-2 h-4 w-4" />
                    Download CSV
                  </Button>
                </div>

                {repairedData && (
                  <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                    <p className="text-sm font-medium mb-2">Repaired data is available!</p>
                    <div className="flex gap-2">
                      <Button size="sm" onClick={useRepairedData}>
                        <RefreshCw className="mr-2 h-4 w-4" />
                        Use Repaired Data
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => downloadData(repairedData, 'repaired_data.csv')}
                      >
                        <Download className="mr-2 h-4 w-4" />
                        Download Repaired
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {qualityMetrics && (
              <Card>
                <CardHeader>
                  <CardTitle>Quality Summary</CardTitle>
                  <CardDescription>
                    Statistical assessment based on comparison with real pilot data (n={pilotData?.length || 0})
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm mb-4">{qualityMetrics.summary}</p>

                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="p-3 border rounded-lg">
                      <p className="text-xs text-muted-foreground mb-1">Correlation Preservation</p>
                      <div className="flex items-center gap-3">
                        <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div
                            className="bg-gradient-to-r from-blue-500 to-indigo-500 h-2 rounded-full"
                            style={{ width: `${qualityMetrics.correlation_preservation * 100}%` }}
                          ></div>
                        </div>
                        <span className="text-sm font-semibold">{(qualityMetrics.correlation_preservation * 100).toFixed(1)}%</span>
                      </div>
                    </div>

                    <div className="p-3 border rounded-lg">
                      <p className="text-xs text-muted-foreground mb-1">Mean Euclidean Distance</p>
                      <p className="text-2xl font-bold">{qualityMetrics.euclidean_distances.mean_distance.toFixed(2)}</p>
                      <p className="text-xs text-muted-foreground">Lower is better</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* ====== QUALITY METRICS TAB ====== */}
          <TabsContent value="quality" className="space-y-6">
            {qualityMetrics ? (
              <>
                <Card>
                  <CardHeader>
                    <CardTitle>Wasserstein Distance (Distribution Similarity)</CardTitle>
                    <CardDescription>
                      Measures how closely synthetic data matches real data distributions. Lower is better (excellent &lt; 5, good &lt; 10).
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart
                        data={Object.entries(qualityMetrics.wasserstein_distances).map(([vital, distance]) => ({
                          vital: vital.replace(/([A-Z])/g, ' $1').trim(),
                          Distance: Number(distance.toFixed(2)),
                        }))}
                        margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                          dataKey="vital"
                          angle={-45}
                          textAnchor="end"
                          height={80}
                          tick={{ fontSize: 12 }}
                        />
                        <YAxis label={{ value: 'Wasserstein Distance (Lower = Better)', angle: -90, position: 'insideLeft' }} />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="Distance" name="Distribution Distance">
                          {Object.entries(qualityMetrics.wasserstein_distances).map((entry, index) => {
                            const distance = entry[1];
                            const color = distance < 5 ? '#10b981' : distance < 10 ? '#f59e0b' : '#ef4444';
                            return <Cell key={`cell-${index}`} fill={color} />;
                          })}
                        </Bar>
                        <ReferenceLine y={5} stroke="#10b981" strokeDasharray="3 3" label="Excellent" />
                        <ReferenceLine y={10} stroke="#f59e0b" strokeDasharray="3 3" label="Good" />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>K-NN Imputation RMSE by Vital Sign</CardTitle>
                    <CardDescription>
                      Root Mean Square Error for K-nearest neighbor predictions (K=5). Lower indicates better local similarity.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart
                        data={Object.entries(qualityMetrics.rmse_by_column).map(([vital, rmse]) => ({
                          vital: vital.replace(/([A-Z])/g, ' $1').trim(),
                          RMSE: Number(rmse.toFixed(2)),
                        }))}
                        margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                          dataKey="vital"
                          angle={-45}
                          textAnchor="end"
                          height={80}
                          tick={{ fontSize: 12 }}
                        />
                        <YAxis label={{ value: 'RMSE (Lower = Better)', angle: -90, position: 'insideLeft' }} />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="RMSE" name="Imputation Error (RMSE)">
                          {Object.entries(qualityMetrics.rmse_by_column).map((entry, index) => {
                            const rmse = entry[1];
                            const color = rmse < 5 ? '#10b981' : rmse < 10 ? '#f59e0b' : '#ef4444';
                            return <Cell key={`cell-${index}`} fill={color} />;
                          })}
                        </Bar>
                        <ReferenceLine y={5} stroke="#10b981" strokeDasharray="3 3" label="Excellent" />
                        <ReferenceLine y={10} stroke="#f59e0b" strokeDasharray="3 3" label="Good" />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                <div className="grid gap-4 md:grid-cols-3">
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm">Avg Wasserstein</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-blue-600">
                        {(Object.values(qualityMetrics.wasserstein_distances).reduce((a, b) => a + b, 0) /
                          Object.values(qualityMetrics.wasserstein_distances).length).toFixed(2)}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm">Avg RMSE</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-green-600">
                        {(Object.values(qualityMetrics.rmse_by_column).reduce((a, b) => a + b, 0) /
                          Object.values(qualityMetrics.rmse_by_column).length).toFixed(2)}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm">Median Distance</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-orange-600">
                        {qualityMetrics.euclidean_distances.median_distance.toFixed(2)}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </>
            ) : (
              <Card>
                <CardHeader>
                  <CardTitle>Run Quality Assessment</CardTitle>
                  <CardDescription>
                    Comprehensive statistical comparison with real pilot data
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Button onClick={runQualityAssessment} disabled={isLoadingQuality}>
                    {isLoadingQuality ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <TrendingUp className="mr-2 h-4 w-4" />
                        Run Quality Assessment
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* ====== VALIDATION TAB ====== */}
          <TabsContent value="validation" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Run Data Validation</CardTitle>
                <CardDescription>
                  Validate {generatedData.length} records against quality rules
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button onClick={runValidation} disabled={isValidating}>
                  {isValidating ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Validating...
                    </>
                  ) : (
                    <>
                      <Shield className="mr-2 h-4 w-4" />
                      Run Quality Checks
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            {validationResults && (
              <>
                <div className="grid gap-4 md:grid-cols-4">
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-medium">Total Records</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{validationResults.total_records}</div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-medium">Checks Run</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{validationResults.total_checks}</div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-medium">Quality Score</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">
                        {(validationResults.quality_score * 100).toFixed(0)}%
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-medium">Validation Status</CardTitle>
                    </CardHeader>
                    <CardContent>
                      {validationResults.passed ? (
                        <Badge className="bg-green-500">
                          <CheckCircle2 className="mr-1 h-3 w-3" />
                          Passed
                        </Badge>
                      ) : (
                        <Badge variant="destructive">
                          <XCircle className="mr-1 h-3 w-3" />
                          Failed
                        </Badge>
                      )}
                    </CardContent>
                  </Card>
                </div>

                {validationResults.violations && validationResults.violations.length > 0 ? (
                  <Card>
                    <CardHeader>
                      <CardTitle>Validation Violations</CardTitle>
                      <CardDescription>
                        {validationResults.violations.length} violations found - use Auto-Repair to fix them
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {validationResults.violations.slice(0, 10).map((violation: any, idx: number) => (
                          <div
                            key={idx}
                            className="flex items-start gap-3 p-3 border rounded-lg hover:bg-accent/50 transition-colors"
                          >
                            <XCircle className="h-4 w-4 text-destructive mt-0.5" />
                            <div className="flex-1 space-y-1">
                              <div className="flex items-center gap-2">
                                <span className="font-mono text-sm font-medium">
                                  {violation.record}
                                </span>
                                <Badge variant="destructive">{violation.severity}</Badge>
                                <Badge variant="outline" className="text-xs">
                                  {violation.rule}
                                </Badge>
                              </div>
                              <p className="text-sm text-muted-foreground">{violation.message}</p>
                            </div>
                          </div>
                        ))}
                        {validationResults.violations.length > 10 && (
                          <div className="text-sm text-muted-foreground text-center pt-2">
                            Showing first 10 of {validationResults.violations.length} violations
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ) : validationResults.passed ? (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-green-600">
                        <CheckCircle2 className="h-5 w-5" />
                        All Checks Passed
                      </CardTitle>
                      <CardDescription>
                        No validation violations found in the generated data
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                        <p className="text-sm text-green-800 dark:text-green-200">
                          The generated data passed all {validationResults.total_checks} quality checks successfully.
                          The data meets all validation rules and is ready for use.
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                ) : null}
              </>
            )}
          </TabsContent>

          {/* ====== REPAIR TAB ====== */}
          <TabsContent value="repair" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Automated Data Repair</CardTitle>
                <CardDescription>
                  Automatically fix constraint violations and improve data quality
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                  <h4 className="font-medium mb-2">Repair Actions Applied:</h4>
                  <ul className="text-sm space-y-1 list-disc list-inside">
                    <li>Clip values to valid clinical ranges (BP: 95-200/55-130, HR: 50-120, Temp: 35-40°C)</li>
                    <li>Ensure blood pressure differential (SBP &gt; DBP by at least 5 mmHg)</li>
                    <li>Fix fever patterns (ensure fever rows have elevated heart rate ≥ 67 bpm)</li>
                    <li>Adjust Week-12 treatment effect to target (-5 mmHg for Active vs Placebo)</li>
                    <li>Remove duplicate records and fill missing values</li>
                  </ul>
                </div>

                <Button onClick={repairData} disabled={isRepairing} size="lg">
                  {isRepairing ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Repairing Data...
                    </>
                  ) : (
                    <>
                      <Wrench className="mr-2 h-4 w-4" />
                      Auto-Repair All Violations
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            {repairedData && (
              <>
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-green-600">
                      <CheckCircle2 className="h-5 w-5" />
                      Repair Completed Successfully
                    </CardTitle>
                    <CardDescription>
                      {repairedData.length} records have been repaired and validated
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid gap-4 md:grid-cols-3">
                      <div className="p-4 border rounded-lg">
                        <p className="text-sm text-muted-foreground mb-1">Records Repaired</p>
                        <p className="text-2xl font-bold">{repairedData.length}</p>
                      </div>

                      {validationResults && (
                        <>
                          <div className="p-4 border rounded-lg">
                            <p className="text-sm text-muted-foreground mb-1">Validation Score</p>
                            <p className="text-2xl font-bold text-green-600">
                              {(validationResults.quality_score * 100).toFixed(0)}%
                            </p>
                          </div>

                          <div className="p-4 border rounded-lg">
                            <p className="text-sm text-muted-foreground mb-1">Violations</p>
                            <p className="text-2xl font-bold">
                              {validationResults.violations?.length || 0}
                            </p>
                          </div>
                        </>
                      )}
                    </div>

                    <div className="flex gap-3">
                      <Button onClick={useRepairedData}>
                        <RefreshCw className="mr-2 h-4 w-4" />
                        Use Repaired Data as Active
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => downloadData(repairedData, 'repaired_data.csv')}
                      >
                        <Download className="mr-2 h-4 w-4" />
                        Download Repaired Data
                      </Button>
                    </div>

                    <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                      <p className="text-sm font-medium mb-2">✅ Repair Benefits:</p>
                      <ul className="text-sm space-y-1 list-disc list-inside">
                        <li><strong>Reduced trial re-runs</strong> - No need to regenerate data</li>
                        <li><strong>Maintained statistical power</strong> - Complete datasets for analysis</li>
                        <li><strong>Cost savings</strong> - Avoid expensive data re-collection</li>
                        <li><strong>Regulatory compliance</strong> - Validated repair methodology</li>
                      </ul>
                    </div>
                  </CardContent>
                </Card>
              </>
            )}
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}
