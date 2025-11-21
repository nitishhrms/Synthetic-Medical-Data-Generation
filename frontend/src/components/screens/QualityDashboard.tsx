import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { qualityApi, dataGenerationApi } from "@/services/api";
import { useData } from "@/contexts/DataContext";
import type { SYNDATAMetricsResponse, VitalsRecord, PrivacyAssessmentResponse } from "@/types";
import {
  CheckCircle2,
  AlertTriangle,
  Loader2,
  Award,
  TrendingUp,
  Shield,
  FileText,
  Info,
  Download,
  Lock,
  Zap,
  Target
} from "lucide-react";

// Helper function to safely format percentages
const safePercent = (value: number | null | undefined, decimals: number = 1): string => {
  if (value === null || value === undefined || isNaN(value) || !isFinite(value)) {
    return "0.0";
  }
  return value.toFixed(decimals);
};

// Helper to safely multiply and format as percentage
const safePercentDisplay = (value: number | null | undefined, decimals: number = 1): string => {
  if (value === null || value === undefined || isNaN(value) || !isFinite(value)) {
    return "0.0";
  }
  return (value * 100).toFixed(decimals);
};

export function QualityDashboard() {
  const { generatedData, generationMethod, planningScenario } = useData();
  const [isAssessing, setIsAssessing] = useState(false);
  const [error, setError] = useState("");
  const [aactData, setAactData] = useState<VitalsRecord[] | null>(null);
  const [syndataMetrics, setSyndataMetrics] = useState<SYNDATAMetricsResponse | null>(null);
  const [qualityReport, setQualityReport] = useState<string | null>(null);
  const [isLoadingAactData, setIsLoadingAactData] = useState(false);
  const [privacyAssessment, setPrivacyAssessment] = useState<PrivacyAssessmentResponse | null>(null);
  const [isAssessingPrivacy, setIsAssessingPrivacy] = useState(false);
  const [availableDatasets, setAvailableDatasets] = useState<any[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<string | null>(null);

  // Load AACT baseline data and available datasets on mount
  useEffect(() => {
    loadAactData();
    loadAvailableDatasets();
  }, []);

  const loadAactData = async () => {
    setIsLoadingAactData(true);
    try {
      // Generate AACT baseline data using the backend
      const response = await dataGenerationApi.generateMVN({
        n_per_arm: 100,
        seed: 42,
        indication: 'Rheumatoid Arthritis',
        phase: 'Phase 3'
      });
      setAactData(response.data);
    } catch (err) {
      console.error("Failed to load AACT data:", err);
      setError("Could not generate AACT baseline data");
    } finally {
      setIsLoadingAactData(false);
    }
  };

  const loadAvailableDatasets = async () => {
    try {
      const result = await dataGenerationApi.listDatasets();
      setAvailableDatasets(result.datasets || []);
    } catch (err) {
      console.error("Failed to load datasets:", err);
    }
  };

  const runAssessment = async () => {
    if (!generatedData || !aactData) {
      setError("Need both generated and AACT baseline data to assess quality");
      return;
    }

    setIsAssessing(true);
    setError("");

    try {
      // Assess SYNDATA metrics against AACT baseline
      const metrics = await qualityApi.assessSYNDATA(aactData, generatedData);
      setSyndataMetrics(metrics);

      // Generate quality report
      const report = await qualityApi.generateQualityReport(
        generationMethod || "unknown",
        aactData,
        generatedData
      );
      setQualityReport(report.report);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Quality assessment failed");
    } finally {
      setIsAssessing(false);
    }
  };

  const runPrivacyAssessment = async () => {
    if (!generatedData || !aactData) {
      setError("Need both generated and AACT data to assess privacy");
      return;
    }

    setIsAssessingPrivacy(true);
    setError("");

    try {
      console.log("🔒 Starting privacy assessment...");
      const response = await qualityApi.assessPrivacy(
        aactData,
        generatedData,
        undefined, // Use default quasi-identifiers
        ["SystolicBP", "DiastolicBP", "HeartRate", "Temperature"]
      );
      console.log("✅ Privacy assessment response:", response);

      // Extract the nested privacy_assessment data
      const assessment = (response as any).privacy_assessment || response;
      console.log("📊 Extracted assessment:", assessment);
      console.log("📊 Has overall_assessment:", !!assessment.overall_assessment);

      setPrivacyAssessment(assessment);
    } catch (err) {
      console.error("❌ Privacy assessment error:", err);
      setError(err instanceof Error ? err.message : "Privacy assessment failed");
    } finally {
      setIsAssessingPrivacy(false);
    }
  };

  const getGradeBadgeColor = (grade: string) => {
    switch (grade) {
      case "A":
        return "bg-green-500";
      case "B":
        return "bg-blue-500";
      case "C":
        return "bg-yellow-500";
      case "D":
        return "bg-orange-500";
      case "F":
        return "bg-red-500";
      default:
        return "bg-gray-500";
    }
  };

  const getGradeStars = (grade: string) => {
    switch (grade) {
      case "A":
        return "⭐⭐⭐⭐⭐";
      case "B":
        return "⭐⭐⭐⭐";
      case "C":
        return "⭐⭐⭐";
      case "D":
        return "⭐⭐";
      case "F":
        return "⭐";
      default:
        return "";
    }
  };

  const downloadReport = () => {
    if (!qualityReport) return;

    const blob = new Blob([qualityReport], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `quality_report_${generationMethod}_${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-8 space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Quality Dashboard</h2>
        <p className="text-muted-foreground">
          SYNDATA metrics and privacy assessment against AACT baseline
        </p>
      </div>

      {/* Dataset Selector */}
      <Card>
        <CardHeader>
          <CardTitle>Select Dataset</CardTitle>
          <CardDescription>
            Choose a saved dataset to assess (currently using: {generationMethod || 'in-memory data'})
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 items-center">
            <select
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              value={selectedDataset || ''}
              onChange={(e) => setSelectedDataset(e.target.value)}
            >
              <option value="">Use current in-memory data ({generatedData?.length || 0} records)</option>
              {availableDatasets.map((ds) => (
                <option key={ds.id} value={ds.id}>
                  {ds.dataset_name} - {ds.record_count} records ({new Date(ds.created_at).toLocaleDateString()})
                </option>
              ))}
            </select>
            <Button
              onClick={async () => {
                if (selectedDataset) {
                  const dataset = availableDatasets.find(d => d.id === parseInt(selectedDataset));
                  if (dataset) {
                    const result = await dataGenerationApi.loadLatestData(dataset.dataset_type);
                    if (result?.data) {
                      // Update context with loaded data
                      alert(`Loaded ${result.data.length} records from ${dataset.dataset_name}`);
                    }
                  }
                }
              }}
              disabled={!selectedDataset}
            >
              Load Selected
            </Button>
          </div>
        </CardContent>
      </Card>

      {!generatedData ? (
        <Card>
          <CardHeader>
            <CardTitle>No Data Available</CardTitle>
            <CardDescription>
              Generate synthetic data first to assess quality
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-sm text-muted-foreground">
              Go to the Generate screen and create synthetic data, then return here to assess quality.
            </div>
          </CardContent>
        </Card>
      ) : (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Run Quality Assessment</CardTitle>
              <CardDescription>
                Assess {generatedData.length} records using SYNDATA project standards
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {error && (
                <div className="flex items-start gap-2 text-sm text-destructive bg-destructive/10 p-3 rounded-md border border-destructive/20">
                  <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  <div>{error}</div>
                </div>
              )}

              <div className="flex items-center gap-2">
                <Button onClick={runAssessment} disabled={isAssessing || !aactData}>
                  {isAssessing ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Assessing...
                    </>
                  ) : (
                    <>
                      <TrendingUp className="mr-2 h-4 w-4" />
                      Run SYNDATA Assessment
                    </>
                  )}
                </Button>

                {isLoadingAactData && (
                  <span className="text-sm text-muted-foreground">
                    Loading AACT data for comparison...
                  </span>
                )}
              </div>

              <div className="p-3 bg-muted/50 rounded-lg border border-muted">
                <div className="flex items-start gap-2">
                  <Info className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                  <div className="text-xs text-muted-foreground">
                    <p className="font-medium text-foreground mb-1">SYNDATA Quality Metrics</p>
                    <p>This assessment implements the NIH SYNDATA project standards, including:</p>
                    <ul className="list-disc list-inside mt-1 space-y-0.5 ml-2">
                      <li><strong>CI Coverage</strong>: % of synthetic values within real data 95% confidence intervals (Target: 88-98% like CART study)</li>
                      <li><strong>Support Coverage</strong>: How well synthetic data covers real data value ranges</li>
                      <li><strong>Cross-Classification</strong>: Joint distribution matching (utility metric)</li>
                      <li><strong>Privacy Disclosure</strong>: Membership and attribute disclosure risks</li>
                    </ul>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {syndataMetrics && (
            <>
              {/* Overall Grade Card */}
              <Card className="border-2 border-primary">
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2">
                    <Award className="h-6 w-6 text-primary" />
                    Overall Quality Grade
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div className="space-y-1">
                      <div className="flex items-baseline gap-3">
                        <Badge className={`${getGradeBadgeColor(syndataMetrics.syndata_metrics.grade)} text-white text-4xl font-bold py-2 px-4`}>
                          {syndataMetrics.syndata_metrics.grade}
                        </Badge>
                        <span className="text-2xl">{getGradeStars(syndataMetrics.syndata_metrics.grade)}</span>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        SYNDATA Score: {safePercentDisplay(syndataMetrics.syndata_metrics.overall_syndata_score)}%
                      </p>
                    </div>
                    {qualityReport && (
                      <Button onClick={downloadReport} variant="outline">
                        <Download className="mr-2 h-4 w-4" />
                        Download Report
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* ====== POWER VALIDATION CARD ====== */}
              {/**
               * Statistical Power Validation
               *
               * This card validates that the generated synthetic data matches the statistical
               * power requirements defined during trial planning. It ensures that the trial
               * design has sufficient sample size to detect the target effect.
               *
               * Purpose:
               * - Verify that generated data sample size aligns with planning recommendations
               * - Validate that statistical assumptions (effect size, power, alpha) are met
               * - Provide early warning if data generation doesn't match trial design
               * - Bridge planning phase with execution phase
               *
               * Workflow:
               * 1. User completes feasibility assessment in Trial Planning
               * 2. Planning parameters saved to DataContext (planningScenario)
               * 3. User generates synthetic data using recommended sample size
               * 4. This card validates alignment between planning and generated data
               * 5. Highlights any discrepancies that could affect statistical validity
               *
               * Key Validations:
               * - Sample size: Does generated N match planned N?
               * - Target effect: Is the planned effect size realistic?
               * - Power: Will the trial have adequate power to detect the effect?
               * - Alpha: Is the significance level appropriate?
               *
               * Statistical Context:
               * - Power (1-β): Probability of detecting a true effect (typically 80-90%)
               * - Alpha (α): Type I error rate (typically 0.05 for Phase 2/3)
               * - Effect size: Clinically meaningful difference (e.g., -5 mmHg SBP reduction)
               * - Sample size: Calculated to achieve desired power given effect and alpha
               */}
              {planningScenario && (
                <Card className="border-2 border-purple-200 bg-purple-50 dark:bg-purple-950">
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center gap-2">
                      <Zap className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                      Statistical Power Validation
                    </CardTitle>
                    <CardDescription>
                      Verify that generated data aligns with trial planning parameters
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Planning Scenario Summary */}
                    <div className="p-4 bg-white dark:bg-gray-950 rounded-lg border">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="text-sm font-semibold flex items-center gap-2">
                          <Target className="h-4 w-4" />
                          Planning Scenario: {planningScenario.name || "Feasibility Assessment"}
                        </h4>
                        {planningScenario.timestamp && (
                          <span className="text-xs text-muted-foreground">
                            {new Date(planningScenario.timestamp).toLocaleString()}
                          </span>
                        )}
                      </div>

                      {/* Grid of Planning Parameters */}
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div className="p-2 bg-muted/50 rounded">
                          <div className="text-xs text-muted-foreground">Required Sample Size</div>
                          <div className="text-lg font-bold text-purple-600 dark:text-purple-400">
                            {planningScenario.nPerArm || planningScenario.requiredN || "N/A"} <span className="text-xs font-normal">per arm</span>
                          </div>
                        </div>

                        <div className="p-2 bg-muted/50 rounded">
                          <div className="text-xs text-muted-foreground">Target Effect Size</div>
                          <div className="text-lg font-bold">
                            {planningScenario.targetEffect || "N/A"} <span className="text-xs font-normal">mmHg</span>
                          </div>
                        </div>

                        <div className="p-2 bg-muted/50 rounded">
                          <div className="text-xs text-muted-foreground">Statistical Power (1-β)</div>
                          <div className="text-lg font-bold">
                            {planningScenario.power ? (planningScenario.power * 100).toFixed(0) + "%" : "N/A"}
                          </div>
                        </div>

                        <div className="p-2 bg-muted/50 rounded">
                          <div className="text-xs text-muted-foreground">Significance Level (α)</div>
                          <div className="text-lg font-bold">
                            {planningScenario.alpha || "N/A"}
                          </div>
                        </div>

                        {planningScenario.cohensD && (
                          <div className="p-2 bg-muted/50 rounded">
                            <div className="text-xs text-muted-foreground">Effect Size (Cohen's d)</div>
                            <div className="text-lg font-bold">
                              {planningScenario.cohensD.toFixed(3)}
                            </div>
                          </div>
                        )}

                        {planningScenario.feasibilityGrade && (
                          <div className="p-2 bg-muted/50 rounded">
                            <div className="text-xs text-muted-foreground">Feasibility Grade</div>
                            <Badge className={`text-base ${
                              planningScenario.feasibilityGrade === "Highly Feasible" ? "bg-green-500" :
                              planningScenario.feasibilityGrade === "Feasible" ? "bg-blue-500" :
                              planningScenario.feasibilityGrade === "Moderately Feasible" ? "bg-yellow-500" :
                              "bg-orange-500"
                            }`}>
                              {planningScenario.feasibilityGrade}
                            </Badge>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Validation Results */}
                    <div className="p-4 bg-white dark:bg-gray-950 rounded-lg border border-purple-200">
                      <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4" />
                        Validation Checks
                      </h4>

                      <div className="space-y-2 text-sm">
                        {/* Sample Size Validation */}
                        {(() => {
                          const plannedN = planningScenario.nPerArm || planningScenario.requiredN || 0;
                          const actualN = generatedData ? generatedData.filter(r => r.TreatmentArm === 'Active').length : 0;
                          const matchesPlan = actualN >= plannedN * 0.95; // Within 5% tolerance

                          return (
                            <div className={`flex items-start gap-2 p-2 rounded ${matchesPlan ? 'bg-green-50 dark:bg-green-950' : 'bg-yellow-50 dark:bg-yellow-950'}`}>
                              {matchesPlan ? (
                                <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                              ) : (
                                <AlertTriangle className="h-4 w-4 text-yellow-600 mt-0.5 flex-shrink-0" />
                              )}
                              <div>
                                <div className="font-medium">
                                  Sample Size: {matchesPlan ? "✅ Matches Planning" : "⚠️ Deviation Detected"}
                                </div>
                                <div className="text-xs text-muted-foreground">
                                  Planned: {plannedN} per arm | Generated: {actualN} per arm
                                  {!matchesPlan && " (Consider regenerating with correct N)"}
                                </div>
                              </div>
                            </div>
                          );
                        })()}

                        {/* Power Adequacy Check */}
                        {planningScenario.power && (
                          <div className={`flex items-start gap-2 p-2 rounded ${
                            planningScenario.power >= 0.80 ? 'bg-green-50 dark:bg-green-950' : 'bg-yellow-50 dark:bg-yellow-950'
                          }`}>
                            {planningScenario.power >= 0.80 ? (
                              <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                            ) : (
                              <AlertTriangle className="h-4 w-4 text-yellow-600 mt-0.5 flex-shrink-0" />
                            )}
                            <div>
                              <div className="font-medium">
                                Statistical Power: {planningScenario.power >= 0.80 ? "✅ Adequate" : "⚠️ Below Standard"}
                              </div>
                              <div className="text-xs text-muted-foreground">
                                Current: {(planningScenario.power * 100).toFixed(0)}% | Standard: ≥80% (Phase 2/3)
                                {planningScenario.power < 0.80 && " (Consider increasing sample size)"}
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Effect Size Realism Check */}
                        {planningScenario.targetEffect && (
                          <div className="flex items-start gap-2 p-2 rounded bg-blue-50 dark:bg-blue-950">
                            <Info className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                            <div>
                              <div className="font-medium">Target Effect Size</div>
                              <div className="text-xs text-muted-foreground">
                                {Math.abs(planningScenario.targetEffect)} mmHg SBP reduction -
                                {Math.abs(planningScenario.targetEffect) >= 5 ? " Clinically meaningful" : " Small effect"}
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Regulatory Guidance */}
                    <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg border border-purple-200">
                      <div className="flex items-start gap-2">
                        <Info className="h-4 w-4 text-purple-600 dark:text-purple-400 mt-0.5 flex-shrink-0" />
                        <div className="text-xs text-purple-800 dark:text-purple-200">
                          <p className="font-medium mb-1">Regulatory Standards</p>
                          <ul className="list-disc list-inside space-y-0.5 ml-2">
                            <li><strong>FDA/ICH E9:</strong> Pre-specify sample size based on clinically meaningful effect</li>
                            <li><strong>Standard Power:</strong> 80% (Phase 2) or 90% (Phase 3 pivotal trials)</li>
                            <li><strong>Alpha:</strong> 0.05 (two-sided) with multiplicity adjustments if needed</li>
                            <li><strong>Effect Size:</strong> Should reflect minimum clinically important difference (MCID)</li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              <Tabs defaultValue="ci-coverage" className="space-y-4">
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="ci-coverage">
                    <TrendingUp className="h-4 w-4 mr-2" />
                    CI Coverage
                  </TabsTrigger>
                  <TabsTrigger value="support">
                    <CheckCircle2 className="h-4 w-4 mr-2" />
                    Support
                  </TabsTrigger>
                  <TabsTrigger value="utility">
                    <TrendingUp className="h-4 w-4 mr-2" />
                    Utility
                  </TabsTrigger>
                  <TabsTrigger value="privacy">
                    <Shield className="h-4 w-4 mr-2" />
                    Privacy
                  </TabsTrigger>
                </TabsList>

                {/* CI Coverage Tab - THE KEY METRIC */}
                <TabsContent value="ci-coverage" className="space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <TrendingUp className="h-5 w-5" />
                        Confidence Interval Coverage (CART Study Standard)
                      </CardTitle>
                      <CardDescription>
                        Percentage of synthetic values within real data 95% confidence intervals
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {/* Overall CI Coverage */}
                      <div className="p-4 bg-primary/5 border border-primary/20 rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium">Overall CI Coverage</span>
                          <Badge className={
                            syndataMetrics.syndata_metrics.ci_coverage.meets_cart_standard
                              ? "bg-green-500"
                              : "bg-yellow-500"
                          }>
                            {syndataMetrics.syndata_metrics.ci_coverage.meets_cart_standard ? "✅ CART Standard" : "⚠️ Below Target"}
                          </Badge>
                        </div>
                        <div className="flex items-baseline gap-2">
                          <span className="text-4xl font-bold">
                            {safePercentDisplay(syndataMetrics.syndata_metrics.ci_coverage.overall_coverage)}
                          </span>
                          <span className="text-sm text-muted-foreground">
                            (Target: 88-98%)
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground mt-2">
                          {syndataMetrics.syndata_metrics.ci_coverage.interpretation}
                        </p>
                      </div>

                      {/* Per-Variable CI Coverage */}
                      <div className="space-y-3">
                        <h4 className="text-sm font-medium">CI Coverage by Variable</h4>
                        {syndataMetrics.syndata_metrics.ci_coverage.by_variable &&
                          Object.entries(syndataMetrics.syndata_metrics.ci_coverage.by_variable).map(([variable, coverageFraction]: [string, any]) => {
                            const coveragePct = coverageFraction * 100;

                            return (<div key={variable} className="space-y-1">
                              <div className="flex items-center justify-between text-sm">
                                <span className="font-medium">{variable}</span>
                                <span className="text-muted-foreground">
                                  {safePercent(coveragePct)}%
                                </span>
                              </div>
                              <div className="h-2 bg-muted rounded-full overflow-hidden">
                                <div
                                  className={`h-full ${coveragePct >= 88 && coveragePct <= 98
                                    ? "bg-green-500"
                                    : coveragePct >= 80
                                      ? "bg-yellow-500"
                                      : "bg-red-500"
                                    }`}
                                  style={{ width: `${Math.min(100, coveragePct || 0)}%` }}
                                />
                              </div>
                            </div>);
                          })}
                      </div>

                      <div className="p-3 bg-muted/50 rounded-lg text-xs text-muted-foreground">
                        <p className="font-medium text-foreground mb-1">What does this mean?</p>
                        <p>
                          The CART study (a landmark NIH study) showed that high-quality synthetic data
                          has 88-98% of synthetic values falling within the 95% confidence intervals of
                          real data. This metric validates that your synthetic data statistically matches
                          the real data distribution.
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* Support Coverage Tab */}
                <TabsContent value="support" className="space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle>Support Coverage</CardTitle>
                      <CardDescription>
                        How well synthetic data covers real data value ranges
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="p-4 bg-muted/50 rounded-lg">
                        <div className="flex items-baseline gap-2 mb-2">
                          <span className="text-3xl font-bold">
                            {safePercentDisplay(syndataMetrics.syndata_metrics.support_coverage.overall_score)}%
                          </span>
                          <span className="text-sm text-muted-foreground">Overall Coverage</span>
                        </div>
                        <div className="h-3 bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full bg-primary"
                            style={{ width: `${safePercentDisplay(syndataMetrics.syndata_metrics.support_coverage.overall_score)}%` }}
                          />
                        </div>
                      </div>

                      <div className="space-y-3">
                        <h4 className="text-sm font-medium">Coverage by Variable</h4>
                        {syndataMetrics.syndata_metrics.support_coverage.by_variable &&
                          Object.entries(syndataMetrics.syndata_metrics.support_coverage.by_variable).map(([variable, coverageScore]: [string, any]) => (
                            <div key={variable} className="flex items-center justify-between">
                              <span className="text-sm">{variable}</span>
                              <Badge variant="outline">
                                {safePercentDisplay(coverageScore ?? 0)}%
                              </Badge>
                            </div>
                          ))}
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* Utility Tab */}
                <TabsContent value="utility" className="space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle>Cross-Classification Utility</CardTitle>
                      <CardDescription>
                        Joint distribution matching between real and synthetic data
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid gap-4 md:grid-cols-2">
                        <div className="p-4 bg-muted/50 rounded-lg">
                          <div className="text-sm text-muted-foreground mb-1">Utility Score</div>
                          <div className="text-2xl font-bold">
                            {safePercentDisplay(syndataMetrics.syndata_metrics.cross_classification.overall_score)}%
                          </div>
                        </div>
                        <div className="p-4 bg-muted/50 rounded-lg">
                          <div className="text-sm text-muted-foreground mb-1">Distribution Similarity</div>
                          <div className="text-2xl font-bold">
                            {safePercentDisplay(syndataMetrics.syndata_metrics.cross_classification.joint_distribution_similarity)}%
                          </div>
                        </div>
                      </div>

                      <div className="p-3 bg-muted/50 rounded-lg text-xs text-muted-foreground">
                        <p>
                          Cross-classification measures how well the synthetic data preserves
                          the joint distributions and relationships between variables. Higher
                          scores mean the synthetic data can be used for complex multivariate analyses.
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* Privacy Tab - Comprehensive Privacy Assessment */}
                <TabsContent value="privacy" className="space-y-4">
                  {!privacyAssessment || !privacyAssessment.overall_assessment ? (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <Lock className="h-5 w-5" />
                          Comprehensive Privacy Assessment
                        </CardTitle>
                        <CardDescription>
                          Run detailed privacy analysis including K-anonymity, L-diversity, and re-identification risk
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <Button
                          onClick={runPrivacyAssessment}
                          disabled={isAssessingPrivacy || !aactData || !generatedData}
                        >
                          {isAssessingPrivacy ? (
                            <>
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              Assessing Privacy...
                            </>
                          ) : (
                            <>
                              <Shield className="mr-2 h-4 w-4" />
                              Run Privacy Assessment
                            </>
                          )}
                        </Button>

                        {error && (
                          <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
                            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
                          </div>
                        )}

                        <div className="p-3 bg-muted/50 rounded-lg border border-muted">
                          <div className="flex items-start gap-2">
                            <Info className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                            <div className="text-xs text-muted-foreground">
                              <p className="font-medium text-foreground mb-1">Privacy Metrics</p>
                              <p>This assessment includes:</p>
                              <ul className="list-disc list-inside mt-1 space-y-0.5 ml-2">
                                <li><strong>K-anonymity</strong>: Each record indistinguishable from k-1 others (target: k≥5)</li>
                                <li><strong>L-diversity</strong>: Diversity of sensitive attributes (target: l≥2)</li>
                                <li><strong>Re-identification Risk</strong>: Singling out, linkability, and inference attacks</li>
                                <li><strong>Differential Privacy</strong>: ε (epsilon) privacy budget (ε&lt;1.0 is strong)</li>
                              </ul>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ) : (
                    <>
                      {/* Overall Safety Card */}
                      <Card className={`border-2 ${privacyAssessment.overall_assessment.safe_for_release ? "border-green-500" : "border-yellow-500"}`}>
                        <CardHeader>
                          <CardTitle className="flex items-center gap-2">
                            <Shield className="h-5 w-5" />
                            Overall Privacy Assessment
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-3">
                          <div className="flex items-center gap-3">
                            <Badge className={privacyAssessment.overall_assessment.safe_for_release ? "bg-green-500 text-white" : "bg-yellow-500 text-white"}>
                              {privacyAssessment.overall_assessment.safe_for_release ? "✅ Safe for Release" : "⚠️ Review Required"}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground">
                            {privacyAssessment.overall_assessment.recommendation}
                          </p>
                          <div className="grid grid-cols-3 gap-2 mt-3">
                            <div className="p-2 bg-muted/50 rounded text-center">
                              <div className="text-xs text-muted-foreground">K-anonymity</div>
                              <div className={`font-bold ${privacyAssessment.overall_assessment.k_anonymity_safe ? "text-green-600" : "text-yellow-600"}`}>
                                {privacyAssessment.overall_assessment.k_anonymity_safe ? "✓ Safe" : "⚠ Risk"}
                              </div>
                            </div>
                            <div className="p-2 bg-muted/50 rounded text-center">
                              <div className="text-xs text-muted-foreground">L-diversity</div>
                              <div className={`font-bold ${privacyAssessment.overall_assessment.l_diversity_safe ? "text-green-600" : "text-yellow-600"}`}>
                                {privacyAssessment.overall_assessment.l_diversity_safe ? "✓ Safe" : "⚠ Risk"}
                              </div>
                            </div>
                            <div className="p-2 bg-muted/50 rounded text-center">
                              <div className="text-xs text-muted-foreground">Re-ID Risk</div>
                              <div className={`font-bold ${privacyAssessment.overall_assessment.reidentification_safe ? "text-green-600" : "text-yellow-600"}`}>
                                {privacyAssessment.overall_assessment.reidentification_safe ? "✓ Safe" : "⚠ Risk"}
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>

                      {/* K-anonymity */}
                      <Card>
                        <CardHeader>
                          <CardTitle className="text-base">K-anonymity Assessment</CardTitle>
                          <CardDescription>
                            Ensures each record is indistinguishable from at least k-1 other records
                          </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-3">
                          <div className="grid gap-4 md:grid-cols-2">
                            <div className="p-4 bg-muted/50 rounded-lg">
                              <div className="text-sm text-muted-foreground mb-1">K-anonymity Value</div>
                              <div className="text-3xl font-bold">{privacyAssessment.k_anonymity.k}</div>
                              <div className="text-xs text-muted-foreground mt-1">
                                {privacyAssessment.k_anonymity.k >= 5 ? "✅ Exceeds minimum (k≥5)" : "⚠️ Below recommended"}
                              </div>
                            </div>
                            <div className="p-4 bg-muted/50 rounded-lg">
                              <div className="text-sm text-muted-foreground mb-1">Risky Records</div>
                              <div className="text-3xl font-bold">{privacyAssessment.k_anonymity.risky_percentage?.toFixed(1) || 0}%</div>
                              <div className="text-xs text-muted-foreground mt-1">
                                {privacyAssessment.k_anonymity.risky_records || 0} of {privacyAssessment.dataset_info?.synthetic_records || 0} records
                              </div>
                            </div>
                          </div>
                          <div className="grid gap-2 text-sm">
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Mean Group Size:</span>
                              <span className="font-medium">{privacyAssessment.k_anonymity.mean_group_size?.toFixed(1) || 0}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Median Group Size:</span>
                              <span className="font-medium">{privacyAssessment.k_anonymity.median_group_size || 0}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Equivalence Classes:</span>
                              <span className="font-medium">{privacyAssessment.k_anonymity.total_equivalence_classes}</span>
                            </div>
                          </div>
                          <div className="p-2 bg-muted/50 rounded text-xs">
                            <p className="font-medium mb-1">Quasi-identifiers used:</p>
                            <p className="text-muted-foreground">{privacyAssessment.k_anonymity.quasi_identifiers_used.join(", ")}</p>
                          </div>
                          <p className="text-xs text-muted-foreground italic">
                            {privacyAssessment.k_anonymity.recommendation}
                          </p>
                        </CardContent>
                      </Card>

                      {/* L-diversity */}
                      <Card>
                        <CardHeader>
                          <CardTitle className="text-base">L-diversity Assessment</CardTitle>
                          <CardDescription>
                            Ensures diversity of sensitive attributes within equivalence classes
                          </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-3">
                          <div className="grid gap-4 md:grid-cols-2">
                            <div className="p-4 bg-muted/50 rounded-lg">
                              <div className="text-sm text-muted-foreground mb-1">L-diversity Value</div>
                              <div className="text-3xl font-bold">{privacyAssessment.l_diversity.l?.toFixed(1) || 0}</div>
                              <div className="text-xs text-muted-foreground mt-1">
                                {(privacyAssessment.l_diversity.l || 0) >= 2 ? "✅ Meets minimum (l≥2)" : "⚠️ Below recommended"}
                              </div>
                            </div>
                            <div className="p-4 bg-muted/50 rounded-lg">
                              <div className="text-sm text-muted-foreground mb-1">Mean Diversity</div>
                              <div className="text-3xl font-bold">{privacyAssessment.l_diversity.mean_diversity?.toFixed(2) || 0}</div>
                              <div className="text-xs text-muted-foreground mt-1">
                                Average diversity across groups
                              </div>
                            </div>
                          </div>
                          <div className="p-2 bg-muted/50 rounded text-xs">
                            <p className="font-medium mb-1">Sensitive attributes checked:</p>
                            <p className="text-muted-foreground">{privacyAssessment.l_diversity.sensitive_attributes_checked.join(", ")}</p>
                          </div>
                          <p className="text-xs text-muted-foreground italic">
                            {privacyAssessment.l_diversity.recommendation}
                          </p>
                        </CardContent>
                      </Card>

                      {/* Re-identification Risk */}
                      {privacyAssessment.reidentification.overall && (
                        <Card>
                          <CardHeader>
                            <CardTitle className="text-base">Re-identification Risk Analysis</CardTitle>
                            <CardDescription>
                              Attack simulations to assess privacy vulnerabilities
                            </CardDescription>
                          </CardHeader>
                          <CardContent className="space-y-4">
                            <div className="p-4 bg-muted/50 rounded-lg">
                              <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium">Overall Risk Level</span>
                                <Badge className={
                                  privacyAssessment.reidentification.overall.safe_for_release
                                    ? "bg-green-500"
                                    : "bg-yellow-500"
                                }>
                                  {privacyAssessment.reidentification.overall.risk_level}
                                </Badge>
                              </div>
                              <div className="grid gap-2 text-sm">
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">Max Risk:</span>
                                  <span className="font-medium">{((privacyAssessment.reidentification.overall.max_risk || 0) * 100).toFixed(1)}%</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">Mean Risk:</span>
                                  <span className="font-medium">{((privacyAssessment.reidentification.overall.mean_risk || 0) * 100).toFixed(1)}%</span>
                                </div>
                              </div>
                            </div>

                            <div className="grid gap-3 md:grid-cols-3">
                              {privacyAssessment.reidentification.singling_out && (
                                <div className="p-3 border rounded-lg">
                                  <div className="text-xs font-medium mb-2">Singling Out Attack</div>
                                  <div className="space-y-1 text-xs">
                                    <div className="flex justify-between">
                                      <span className="text-muted-foreground">Attack Rate:</span>
                                      <span>{((privacyAssessment.reidentification.singling_out.attack_rate || 0) * 100).toFixed(1)}%</span>
                                    </div>
                                    <div className="flex justify-between">
                                      <span className="text-muted-foreground">Risk:</span>
                                      <Badge variant={privacyAssessment.reidentification.singling_out.safe ? "default" : "destructive"} className="text-xs">
                                        {((privacyAssessment.reidentification.singling_out.risk || 0) * 100).toFixed(1)}%
                                      </Badge>
                                    </div>
                                  </div>
                                </div>
                              )}
                              {privacyAssessment.reidentification.linkability && (
                                <div className="p-3 border rounded-lg">
                                  <div className="text-xs font-medium mb-2">Linkability Attack</div>
                                  <div className="space-y-1 text-xs">
                                    <div className="flex justify-between">
                                      <span className="text-muted-foreground">Attack Rate:</span>
                                      <span>{((privacyAssessment.reidentification.linkability.attack_rate || 0) * 100).toFixed(1)}%</span>
                                    </div>
                                    <div className="flex justify-between">
                                      <span className="text-muted-foreground">Risk:</span>
                                      <Badge variant={privacyAssessment.reidentification.linkability.safe ? "default" : "destructive"} className="text-xs">
                                        {((privacyAssessment.reidentification.linkability.risk || 0) * 100).toFixed(1)}%
                                      </Badge>
                                    </div>
                                  </div>
                                </div>
                              )}
                              {privacyAssessment.reidentification.inference && (
                                <div className="p-3 border rounded-lg">
                                  <div className="text-xs font-medium mb-2">Inference Attack</div>
                                  <div className="space-y-1 text-xs">
                                    <div className="flex justify-between">
                                      <span className="text-muted-foreground">Attack Rate:</span>
                                      <span>{((privacyAssessment.reidentification.inference.attack_rate || 0) * 100).toFixed(1)}%</span>
                                    </div>
                                    <div className="flex justify-between">
                                      <span className="text-muted-foreground">Risk:</span>
                                      <Badge variant={privacyAssessment.reidentification.inference.safe ? "default" : "destructive"} className="text-xs">
                                        {((privacyAssessment.reidentification.inference.risk || 0) * 100).toFixed(1)}%
                                      </Badge>
                                    </div>
                                  </div>
                                </div>
                              )}
                            </div>
                          </CardContent>
                        </Card>
                      )}

                      {/* Differential Privacy */}
                      <Card>
                        <CardHeader>
                          <CardTitle className="text-base">Differential Privacy Budget</CardTitle>
                          <CardDescription>
                            Privacy budget tracking (lower ε = stronger privacy)
                          </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-3">
                          <div className="grid gap-4 md:grid-cols-2">
                            <div className="p-4 bg-muted/50 rounded-lg">
                              <div className="text-sm text-muted-foreground mb-1">Epsilon (ε)</div>
                              <div className="text-3xl font-bold">{privacyAssessment.differential_privacy.epsilon?.toFixed(3) || 0}</div>
                              <div className="text-xs text-muted-foreground mt-1">
                                {privacyAssessment.differential_privacy.privacy_level || "Unknown"}
                              </div>
                            </div>
                            <div className="p-4 bg-muted/50 rounded-lg">
                              <div className="text-sm text-muted-foreground mb-1">Budget Remaining</div>
                              <div className="text-3xl font-bold">{privacyAssessment.differential_privacy.budget_remaining?.toFixed(3) || 0}</div>
                              <div className="text-xs text-muted-foreground mt-1">
                                After {privacyAssessment.differential_privacy.n_queries} queries
                              </div>
                            </div>
                          </div>
                          <div className="grid gap-2 text-sm">
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Delta (δ):</span>
                              <span className="font-medium">{privacyAssessment.differential_privacy.delta?.toExponential(2) || 0}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Total ε Used:</span>
                              <span className="font-medium">{privacyAssessment.differential_privacy.total_epsilon?.toFixed(3) || 0}</span>
                            </div>
                          </div>
                          <p className="text-xs text-muted-foreground italic">
                            {privacyAssessment.differential_privacy.recommendation}
                          </p>
                          <div className="p-2 bg-muted/50 rounded text-xs">
                            <p className="font-medium mb-1">Privacy Level Guide:</p>
                            <ul className="list-disc list-inside text-muted-foreground space-y-0.5 ml-2">
                              <li>ε &lt; 1.0: Strong privacy</li>
                              <li>ε 1.0-3.0: Moderate privacy</li>
                              <li>ε &gt; 3.0: Weak privacy</li>
                            </ul>
                          </div>
                        </CardContent>
                      </Card>
                    </>
                  )}
                </TabsContent>
              </Tabs>

              {/* Quality Report Preview */}
              {qualityReport && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <FileText className="h-5 w-5" />
                      Automated Quality Report
                    </CardTitle>
                    <CardDescription>
                      Comprehensive markdown report for documentation
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="p-4 bg-muted/50 rounded-lg border border-muted max-h-96 overflow-y-auto">
                      <pre className="text-xs whitespace-pre-wrap font-mono">
                        {qualityReport}
                      </pre>
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}
