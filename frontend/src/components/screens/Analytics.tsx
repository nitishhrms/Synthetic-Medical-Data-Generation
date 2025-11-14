import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { analyticsApi, dataGenerationApi } from "@/services/api";
import { useData } from "@/contexts/DataContext";
import type { VitalsRecord, Week12StatsResponse, QualityAssessmentResponse } from "@/types";
import { BarChart3, CheckCircle, AlertCircle, Loader2, TrendingDown } from "lucide-react";

export function Analytics() {
  const {
    generatedData,
    pilotData,
    setPilotData,
    week12Stats,
    setWeek12Stats,
    qualityMetrics,
    setQualityMetrics,
  } = useData();

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  // Load pilot data on mount if not already loaded
  useEffect(() => {
    if (!pilotData) {
      loadPilotData();
    }
  }, []);

  const loadPilotData = async () => {
    try {
      const data = await dataGenerationApi.getPilotData();
      setPilotData(data);
    } catch (err) {
      console.error("Failed to load pilot data:", err);
    }
  };

  const runAnalysis = async () => {
    if (!generatedData) {
      setError("No generated data available. Please generate data first from the Generate screen.");
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      // Get week-12 statistics
      const statsResponse = await analyticsApi.getWeek12Stats({
        vitals_data: generatedData,
      });
      setWeek12Stats(statsResponse);

      // Load pilot data if not loaded
      if (!pilotData) {
        await loadPilotData();
      }

      // Get quality assessment if we have pilot data
      if (pilotData || await loadPilotData()) {
        const qualityResponse = await analyticsApi.comprehensiveQuality(
          pilotData!,
          generatedData,
          5
        );
        setQualityMetrics(qualityResponse);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setIsLoading(false);
    }
  };

  const getQualityBadge = (score: number) => {
    if (score >= 0.85) return { variant: "default" as const, label: "Excellent", color: "text-green-600" };
    if (score >= 0.70) return { variant: "secondary" as const, label: "Good", color: "text-yellow-600" };
    return { variant: "destructive" as const, label: "Needs Improvement", color: "text-red-600" };
  };

  return (
    <div className="p-8 space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Analytics</h2>
        <p className="text-muted-foreground">
          Statistical analysis and quality assessment of generated synthetic data
        </p>
      </div>

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
              Go to the Generate screen and create some synthetic data to analyze.
            </div>
          </CardContent>
        </Card>
      ) : (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Run Analysis</CardTitle>
              <CardDescription>
                Analyze {generatedData.length} generated records for statistical significance and quality
              </CardDescription>
            </CardHeader>
            <CardContent>
              {error && (
                <div className="text-sm text-destructive bg-destructive/10 p-3 rounded-md mb-4">
                  {error}
                </div>
              )}

              <Button onClick={runAnalysis} disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <TrendingDown className="mr-2 h-4 w-4" />
                    Run Statistical Analysis
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </>
      )}

      {week12Stats && (
        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Treatment Groups</CardTitle>
              <CardDescription>Week 12 Systolic BP Summary</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Active Arm</span>
                  <Badge>n = {week12Stats.treatment_groups.Active.n}</Badge>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <p className="text-muted-foreground">Mean SBP</p>
                    <p className="font-semibold">{week12Stats.treatment_groups.Active.mean_systolic.toFixed(1)} mmHg</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Std Dev</p>
                    <p className="font-semibold">{week12Stats.treatment_groups.Active.std_systolic.toFixed(1)}</p>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Placebo Arm</span>
                  <Badge variant="secondary">n = {week12Stats.treatment_groups.Placebo.n}</Badge>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <p className="text-muted-foreground">Mean SBP</p>
                    <p className="font-semibold">{week12Stats.treatment_groups.Placebo.mean_systolic.toFixed(1)} mmHg</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Std Dev</p>
                    <p className="font-semibold">{week12Stats.treatment_groups.Placebo.std_systolic.toFixed(1)}</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Treatment Effect</CardTitle>
              <CardDescription>Active vs Placebo Comparison</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Difference</span>
                  <span className="font-semibold">{week12Stats.treatment_effect.difference.toFixed(2)} mmHg</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">95% CI</span>
                  <span className="font-mono text-sm">
                    [{week12Stats.treatment_effect.ci_95_lower.toFixed(1)}, {week12Stats.treatment_effect.ci_95_upper.toFixed(1)}]
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">p-value</span>
                  <span className="font-semibold">{week12Stats.treatment_effect.p_value.toFixed(4)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Statistical Significance</span>
                  {week12Stats.interpretation.significant ? (
                    <Badge className="bg-green-500">
                      <CheckCircle className="mr-1 h-3 w-3" />
                      Significant (p &lt; 0.05)
                    </Badge>
                  ) : (
                    <Badge variant="secondary">
                      <AlertCircle className="mr-1 h-3 w-3" />
                      Not Significant
                    </Badge>
                  )}
                </div>
              </div>

              <div className="pt-4 border-t">
                <p className="text-sm font-medium mb-1">Interpretation</p>
                <p className="text-sm text-muted-foreground">
                  {week12Stats.interpretation.clinical_relevance}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {qualityMetrics && (
        <Card>
          <CardHeader>
            <CardTitle>Quality Assessment</CardTitle>
            <CardDescription>
              Comprehensive evaluation of synthetic data quality
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
              <div>
                <p className="text-sm font-medium">Overall Quality Score</p>
                <p className="text-2xl font-bold mt-1">{qualityMetrics.overall_quality_score.toFixed(3)}</p>
              </div>
              <Badge {...getQualityBadge(qualityMetrics.overall_quality_score)}>
                {getQualityBadge(qualityMetrics.overall_quality_score).label}
              </Badge>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-3">
                <h4 className="font-medium">Wasserstein Distances</h4>
                {Object.entries(qualityMetrics.wasserstein_distances).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">{key}</span>
                    <span className="font-mono">{value.toFixed(3)}</span>
                  </div>
                ))}
              </div>

              <div className="space-y-3">
                <h4 className="font-medium">RMSE by Column</h4>
                {Object.entries(qualityMetrics.rmse_by_column).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">{key}</span>
                    <span className="font-mono">{value.toFixed(3)}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <div className="p-3 border rounded-lg">
                <p className="text-sm text-muted-foreground">Correlation Preservation</p>
                <p className="text-lg font-semibold mt-1">
                  {(qualityMetrics.correlation_preservation * 100).toFixed(1)}%
                </p>
              </div>
              <div className="p-3 border rounded-lg">
                <p className="text-sm text-muted-foreground">K-NN Imputation Score</p>
                <p className="text-lg font-semibold mt-1">
                  {qualityMetrics.knn_imputation_score.toFixed(3)}
                </p>
              </div>
              <div className="p-3 border rounded-lg">
                <p className="text-sm text-muted-foreground">Mean Euclidean Distance</p>
                <p className="text-lg font-semibold mt-1">
                  {qualityMetrics.euclidean_distances.mean_distance.toFixed(2)}
                </p>
              </div>
            </div>

            <div className="p-4 bg-muted rounded-lg">
              <p className="text-sm font-medium mb-2">Summary</p>
              <p className="text-sm text-muted-foreground">{qualityMetrics.summary}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {generatedData && (
        <Card>
          <CardHeader>
            <CardTitle>Generated Dataset</CardTitle>
            <CardDescription>
              {generatedData.length} synthetic vitals records
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-2 md:grid-cols-4">
              <div className="p-3 border rounded-lg">
                <p className="text-sm text-muted-foreground">Total Records</p>
                <p className="text-2xl font-bold">{generatedData.length}</p>
              </div>
              <div className="p-3 border rounded-lg">
                <p className="text-sm text-muted-foreground">Subjects</p>
                <p className="text-2xl font-bold">
                  {new Set(generatedData.map(d => d.SubjectID)).size}
                </p>
              </div>
              <div className="p-3 border rounded-lg">
                <p className="text-sm text-muted-foreground">Active Arm</p>
                <p className="text-2xl font-bold">
                  {generatedData.filter(d => d.TreatmentArm === "Active").length}
                </p>
              </div>
              <div className="p-3 border rounded-lg">
                <p className="text-sm text-muted-foreground">Placebo Arm</p>
                <p className="text-2xl font-bold">
                  {generatedData.filter(d => d.TreatmentArm === "Placebo").length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
