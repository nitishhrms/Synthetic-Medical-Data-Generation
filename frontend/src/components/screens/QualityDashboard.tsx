import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { qualityApi, dataGenerationApi } from "@/services/api";
import { useData } from "@/contexts/DataContext";
import type { SYNDATAMetricsResponse, VitalsRecord } from "@/types";
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Loader2,
  Award,
  TrendingUp,
  Shield,
  FileText,
  Info,
  Download
} from "lucide-react";

export function QualityDashboard() {
  const { generatedData, generationMethod } = useData();
  const [isAssessing, setIsAssessing] = useState(false);
  const [error, setError] = useState("");
  const [realData, setRealData] = useState<VitalsRecord[] | null>(null);
  const [syndataMetrics, setSyndataMetrics] = useState<SYNDATAMetricsResponse | null>(null);
  const [qualityReport, setQualityReport] = useState<string | null>(null);
  const [isLoadingRealData, setIsLoadingRealData] = useState(false);

  // Load real data on mount
  useEffect(() => {
    loadRealData();
  }, []);

  const loadRealData = async () => {
    setIsLoadingRealData(true);
    try {
      const data = await dataGenerationApi.getPilotData();
      setRealData(data);
    } catch (err) {
      console.error("Failed to load real data:", err);
      setError("Could not load real pilot data for comparison");
    } finally {
      setIsLoadingRealData(false);
    }
  };

  const runAssessment = async () => {
    if (!generatedData || !realData) {
      setError("Need both generated and real data to assess quality");
      return;
    }

    setIsAssessing(true);
    setError("");

    try {
      // Assess SYNDATA metrics
      const metrics = await qualityApi.assessSYNDATA(realData, generatedData);
      setSyndataMetrics(metrics);

      // Generate quality report
      const report = await qualityApi.generateQualityReport(
        generationMethod || "unknown",
        realData,
        generatedData
      );
      setQualityReport(report.report);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Quality assessment failed");
    } finally {
      setIsAssessing(false);
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
        <h2 className="text-3xl font-bold tracking-tight">Quality Assessment Dashboard</h2>
        <p className="text-muted-foreground">
          SYNDATA-style metrics for synthetic data quality validation
        </p>
      </div>

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
                <Button
                  onClick={runAssessment}
                  disabled={isAssessing || isLoadingRealData || !realData}
                >
                  {isAssessing ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Assessing Quality...
                    </>
                  ) : (
                    <>
                      <Award className="mr-2 h-4 w-4" />
                      Run SYNDATA Assessment
                    </>
                  )}
                </Button>

                {isLoadingRealData && (
                  <span className="text-sm text-muted-foreground">
                    Loading real data for comparison...
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
                        SYNDATA Score: {(syndataMetrics.syndata_metrics.overall_syndata_score * 100).toFixed(1)}%
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
                            {(syndataMetrics.syndata_metrics.ci_coverage.overall_coverage * 100).toFixed(1)}%
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
                        {Object.entries(syndataMetrics.syndata_metrics.ci_coverage.by_variable).map(([variable, coverage]) => (
                          <div key={variable} className="space-y-1">
                            <div className="flex items-center justify-between text-sm">
                              <span className="font-medium">{variable}</span>
                              <span className="text-muted-foreground">
                                {(coverage * 100).toFixed(1)}%
                              </span>
                            </div>
                            <div className="h-2 bg-muted rounded-full overflow-hidden">
                              <div
                                className={`h-full ${
                                  coverage >= 0.88 && coverage <= 0.98
                                    ? "bg-green-500"
                                    : coverage >= 0.80
                                    ? "bg-yellow-500"
                                    : "bg-red-500"
                                }`}
                                style={{ width: `${coverage * 100}%` }}
                              />
                            </div>
                          </div>
                        ))}
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
                            {(syndataMetrics.syndata_metrics.support_coverage.overall_score * 100).toFixed(1)}%
                          </span>
                          <span className="text-sm text-muted-foreground">Overall Coverage</span>
                        </div>
                        <div className="h-3 bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full bg-primary"
                            style={{ width: `${syndataMetrics.syndata_metrics.support_coverage.overall_score * 100}%` }}
                          />
                        </div>
                      </div>

                      <div className="space-y-3">
                        <h4 className="text-sm font-medium">Coverage by Variable</h4>
                        {Object.entries(syndataMetrics.syndata_metrics.support_coverage.by_variable).map(([variable, score]) => (
                          <div key={variable} className="flex items-center justify-between">
                            <span className="text-sm">{variable}</span>
                            <Badge variant="outline">
                              {(score * 100).toFixed(1)}%
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
                            {(syndataMetrics.syndata_metrics.cross_classification.utility_score * 100).toFixed(1)}%
                          </div>
                        </div>
                        <div className="p-4 bg-muted/50 rounded-lg">
                          <div className="text-sm text-muted-foreground mb-1">Distribution Similarity</div>
                          <div className="text-2xl font-bold">
                            {(syndataMetrics.syndata_metrics.cross_classification.joint_distribution_similarity * 100).toFixed(1)}%
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

                {/* Privacy Tab */}
                <TabsContent value="privacy" className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">Membership Disclosure</CardTitle>
                        <CardDescription>
                          Can a classifier distinguish real from synthetic?
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm">Disclosure Risk</span>
                          <Badge variant={
                            syndataMetrics.syndata_metrics.membership_disclosure.safe
                              ? "default"
                              : "destructive"
                          }>
                            {syndataMetrics.syndata_metrics.membership_disclosure.safe ? "✅ Safe" : "⚠️ Risk"}
                          </Badge>
                        </div>
                        <div className="text-2xl font-bold">
                          {(syndataMetrics.syndata_metrics.membership_disclosure.disclosure_risk * 100).toFixed(1)}%
                        </div>
                        <div className="text-xs text-muted-foreground">
                          Classifier Accuracy: {(syndataMetrics.syndata_metrics.membership_disclosure.classifier_accuracy * 100).toFixed(1)}%
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">Attribute Disclosure</CardTitle>
                        <CardDescription>
                          Can sensitive attributes be predicted?
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm">Disclosure Risk</span>
                          <Badge variant={
                            syndataMetrics.syndata_metrics.attribute_disclosure.safe
                              ? "default"
                              : "destructive"
                          }>
                            {syndataMetrics.syndata_metrics.attribute_disclosure.safe ? "✅ Safe" : "⚠️ Risk"}
                          </Badge>
                        </div>
                        <div className="text-2xl font-bold">
                          {(syndataMetrics.syndata_metrics.attribute_disclosure.disclosure_risk * 100).toFixed(1)}%
                        </div>
                        <div className="text-xs text-muted-foreground">
                          Prediction Accuracy: {(syndataMetrics.syndata_metrics.attribute_disclosure.prediction_accuracy * 100).toFixed(1)}%
                        </div>
                      </CardContent>
                    </Card>
                  </div>
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
