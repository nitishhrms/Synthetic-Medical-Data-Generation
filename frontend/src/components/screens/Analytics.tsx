import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { analyticsApi, dataGenerationApi } from "@/services/api";
import type { VitalsRecord, Week12StatsResponse, QualityAssessmentResponse } from "@/types";
import { BarChart3, CheckCircle, AlertCircle, Loader2 } from "lucide-react";

export function Analytics() {
  const [isLoading, setIsLoading] = useState(false);
  const [syntheticData, setSyntheticData] = useState<VitalsRecord[] | null>(null);
  const [realData, setRealData] = useState<VitalsRecord[] | null>(null);
  const [stats, setStats] = useState<Week12StatsResponse | null>(null);
  const [quality, setQuality] = useState<QualityAssessmentResponse | null>(null);
  const [error, setError] = useState("");

  const loadRealData = async () => {
    try {
      const data = await dataGenerationApi.getPilotData();
      setRealData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load real data");
    }
  };

  const generateAndAnalyze = async () => {
    setIsLoading(true);
    setError("");

    try {
      // Generate synthetic data
      const genResponse = await dataGenerationApi.generateMVN({
        n_per_arm: 50,
        target_effect: -5.0,
      });
      setSyntheticData(genResponse.data);

      // Get week-12 statistics
      const statsResponse = await analyticsApi.getWeek12Stats({
        vitals_data: genResponse.data,
      });
      setStats(statsResponse);

      // Load real data if not loaded
      if (!realData) {
        await loadRealData();
      }

      // Get quality assessment
      if (realData) {
        const qualityResponse = await analyticsApi.comprehensiveQuality(
          realData,
          genResponse.data,
          5
        );
        setQuality(qualityResponse);
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
        <h2 className="text-3xl font-bold tracking-tight">Analytics & Quality</h2>
        <p className="text-muted-foreground">
          Statistical analysis and quality assessment of synthetic data
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Quick Analysis</CardTitle>
          <CardDescription>
            Generate synthetic data and analyze quality in one click
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="text-sm text-destructive bg-destructive/10 p-3 rounded-md mb-4">
              {error}
            </div>
          )}

          <Button onClick={generateAndAnalyze} disabled={isLoading}>
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <BarChart3 className="mr-2 h-4 w-4" />
                Generate & Analyze
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {stats && (
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
                  <Badge>n = {stats.treatment_groups.Active.n}</Badge>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <p className="text-muted-foreground">Mean SBP</p>
                    <p className="font-semibold">{stats.treatment_groups.Active.mean_systolic.toFixed(1)} mmHg</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Std Dev</p>
                    <p className="font-semibold">{stats.treatment_groups.Active.std_systolic.toFixed(1)}</p>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Placebo Arm</span>
                  <Badge variant="secondary">n = {stats.treatment_groups.Placebo.n}</Badge>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <p className="text-muted-foreground">Mean SBP</p>
                    <p className="font-semibold">{stats.treatment_groups.Placebo.mean_systolic.toFixed(1)} mmHg</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Std Dev</p>
                    <p className="font-semibold">{stats.treatment_groups.Placebo.std_systolic.toFixed(1)}</p>
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
                  <span className="font-semibold">{stats.treatment_effect.difference.toFixed(2)} mmHg</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">95% CI</span>
                  <span className="font-mono text-sm">
                    [{stats.treatment_effect.ci_95_lower.toFixed(1)}, {stats.treatment_effect.ci_95_upper.toFixed(1)}]
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">p-value</span>
                  <span className="font-semibold">{stats.treatment_effect.p_value.toFixed(4)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Statistical Significance</span>
                  {stats.interpretation.significant ? (
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
                  {stats.interpretation.clinical_relevance}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {quality && (
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
                <p className="text-2xl font-bold mt-1">{quality.overall_quality_score.toFixed(3)}</p>
              </div>
              <Badge {...getQualityBadge(quality.overall_quality_score)}>
                {getQualityBadge(quality.overall_quality_score).label}
              </Badge>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-3">
                <h4 className="font-medium">Wasserstein Distances</h4>
                {Object.entries(quality.wasserstein_distances).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">{key}</span>
                    <span className="font-mono">{value.toFixed(3)}</span>
                  </div>
                ))}
              </div>

              <div className="space-y-3">
                <h4 className="font-medium">RMSE by Column</h4>
                {Object.entries(quality.rmse_by_column).map(([key, value]) => (
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
                  {(quality.correlation_preservation * 100).toFixed(1)}%
                </p>
              </div>
              <div className="p-3 border rounded-lg">
                <p className="text-sm text-muted-foreground">K-NN Imputation Score</p>
                <p className="text-lg font-semibold mt-1">
                  {quality.knn_imputation_score.toFixed(3)}
                </p>
              </div>
              <div className="p-3 border rounded-lg">
                <p className="text-sm text-muted-foreground">Mean Euclidean Distance</p>
                <p className="text-lg font-semibold mt-1">
                  {quality.euclidean_distances.mean_distance.toFixed(2)}
                </p>
              </div>
            </div>

            <div className="p-4 bg-muted rounded-lg">
              <p className="text-sm font-medium mb-2">Summary</p>
              <p className="text-sm text-muted-foreground">{quality.summary}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {syntheticData && (
        <Card>
          <CardHeader>
            <CardTitle>Generated Dataset</CardTitle>
            <CardDescription>
              {syntheticData.length} synthetic vitals records
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-2 md:grid-cols-4">
              <div className="p-3 border rounded-lg">
                <p className="text-sm text-muted-foreground">Total Records</p>
                <p className="text-2xl font-bold">{syntheticData.length}</p>
              </div>
              <div className="p-3 border rounded-lg">
                <p className="text-sm text-muted-foreground">Subjects</p>
                <p className="text-2xl font-bold">
                  {new Set(syntheticData.map(d => d.SubjectID)).size}
                </p>
              </div>
              <div className="p-3 border rounded-lg">
                <p className="text-sm text-muted-foreground">Active Arm</p>
                <p className="text-2xl font-bold">
                  {syntheticData.filter(d => d.TreatmentArm === "Active").length}
                </p>
              </div>
              <div className="p-3 border rounded-lg">
                <p className="text-sm text-muted-foreground">Placebo Arm</p>
                <p className="text-2xl font-bold">
                  {syntheticData.filter(d => d.TreatmentArm === "Placebo").length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
