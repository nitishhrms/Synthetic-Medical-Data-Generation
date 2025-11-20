import { useState, useEffect } from "react";
import { analyticsApi, dataGenerationApi } from "@/services/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from "recharts";
import { Activity, TrendingDown, Download, AlertCircle } from "lucide-react";

export default function SurvivalAnalysis() {
  const [demographicsData, setDemographicsData] = useState<any[] | null>(null);
  const [indication, setIndication] = useState("oncology");
  const [medianSurvivalActive, setMedianSurvivalActive] = useState(18.0);
  const [medianSurvivalPlacebo, setMedianSurvivalPlacebo] = useState(12.0);

  const [pilotData, setPilotData] = useState<any[] | null>(null);
  const [isPilotLoading, setIsPilotLoading] = useState(false);
  const [survivalResults, setSurvivalResults] = useState<any>(null);
  const [isAnalysisLoading, setIsAnalysisLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch pilot data on mount
  useEffect(() => {
    const fetchPilotData = async () => {
      setIsPilotLoading(true);
      try {
        const data = await dataGenerationApi.getPilotData();
        setPilotData(data);
      } catch (err: any) {
        setError(err.message || "Failed to fetch pilot data");
      } finally {
        setIsPilotLoading(false);
      }
    };

    fetchPilotData();
  }, []);

  // Run survival analysis when demographics data changes
  useEffect(() => {
    const runSurvivalAnalysis = async () => {
      if (!demographicsData || demographicsData.length === 0) {
        setSurvivalResults(null);
        return;
      }

      setIsAnalysisLoading(true);
      setError(null);
      try {
        const result = await analyticsApi.comprehensiveSurvivalAnalysis({
          demographics_data: demographicsData,
          indication,
          median_survival_active: medianSurvivalActive,
          median_survival_placebo: medianSurvivalPlacebo,
          seed: 42,
        });
        setSurvivalResults(result);
      } catch (err: any) {
        setError(err.message || "Failed to run survival analysis");
      } finally {
        setIsAnalysisLoading(false);
      }
    };

    runSurvivalAnalysis();
  }, [demographicsData, indication, medianSurvivalActive, medianSurvivalPlacebo]);

  const handleGenerateDemographics = () => {
    if (pilotData) {
      // Extract demographics from pilot data
      const demographics = pilotData.map((record: any, index: number) => ({
        SubjectID: record.SubjectID || `SUB-${String(index + 1).padStart(3, "0")}`,
        TreatmentArm: index % 2 === 0 ? "Active" : "Placebo",
        Age: 55 + Math.floor(Math.random() * 20),
        Gender: Math.random() > 0.5 ? "Male" : "Female",
        Race: "White",
      }));

      // Take unique subjects
      const uniqueSubjects = Array.from(
        new Map(demographics.map((d: any) => [d.SubjectID, d])).values()
      );

      setDemographicsData(uniqueSubjects.slice(0, 100));
    }
  };

  const handleDownloadSDTM = () => {
    if (survivalResults?.sdtm_tte) {
      const blob = new Blob([JSON.stringify(survivalResults.sdtm_tte, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "survival_sdtm_tte.json";
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  const isLoading = isPilotLoading || isAnalysisLoading;

  // Prepare Kaplan-Meier curve data
  const kmCurveData = survivalResults?.kaplan_meier ? [
    ...(survivalResults.kaplan_meier.active?.km_curve?.map((point: any) => ({
      time: point.time,
      Active: point.survival_prob,
      active_lower: point.ci_lower,
      active_upper: point.ci_upper,
    })) || []),
  ].map((point, index) => ({
    ...point,
    Placebo: survivalResults.kaplan_meier.placebo?.km_curve?.[index]?.survival_prob,
    placebo_lower: survivalResults.kaplan_meier.placebo?.km_curve?.[index]?.ci_lower,
    placebo_upper: survivalResults.kaplan_meier.placebo?.km_curve?.[index]?.ci_upper,
  })) : [];

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Survival Analysis</h1>
          <p className="text-muted-foreground">
            Kaplan-Meier curves, log-rank test, hazard ratios for time-to-event analysis
          </p>
        </div>
        <Activity className="h-8 w-8 text-primary" />
      </div>

      {/* Configuration Panel */}
      <Card>
        <CardHeader>
          <CardTitle>Analysis Configuration</CardTitle>
          <CardDescription>
            Configure survival analysis parameters for oncology trials
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Indication</label>
              <select
                value={indication}
                onChange={(e) => setIndication(e.target.value)}
                className="w-full border rounded px-3 py-2"
              >
                <option value="oncology">Oncology</option>
                <option value="cardiovascular">Cardiovascular</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">
                Median Survival Active (months)
              </label>
              <input
                type="number"
                value={medianSurvivalActive}
                onChange={(e) => setMedianSurvivalActive(parseFloat(e.target.value))}
                className="w-full border rounded px-3 py-2"
                step="0.1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">
                Median Survival Placebo (months)
              </label>
              <input
                type="number"
                value={medianSurvivalPlacebo}
                onChange={(e) => setMedianSurvivalPlacebo(parseFloat(e.target.value))}
                className="w-full border rounded px-3 py-2"
                step="0.1"
              />
            </div>
            <div className="flex items-end">
              <Button
                onClick={handleGenerateDemographics}
                disabled={isPilotLoading}
                className="w-full"
              >
                {isPilotLoading ? "Loading..." : "Generate Analysis"}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {isLoading && (
        <Card>
          <CardContent className="py-8">
            <div className="flex items-center justify-center space-x-2">
              <Activity className="h-6 w-6 animate-spin text-primary" />
              <p className="text-muted-foreground">Running survival analysis...</p>
            </div>
          </CardContent>
        </Card>
      )}

      {survivalResults && (
        <Tabs defaultValue="kaplan-meier" className="space-y-4">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="kaplan-meier">Kaplan-Meier</TabsTrigger>
            <TabsTrigger value="log-rank">Log-Rank Test</TabsTrigger>
            <TabsTrigger value="hazard-ratio">Hazard Ratio</TabsTrigger>
            <TabsTrigger value="summary">Summary</TabsTrigger>
          </TabsList>

          {/* Kaplan-Meier Tab */}
          <TabsContent value="kaplan-meier" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Kaplan-Meier Survival Curves</CardTitle>
                <CardDescription>
                  Survival probability over time by treatment arm
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <LineChart data={kmCurveData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="time"
                      label={{ value: "Time (months)", position: "insideBottom", offset: -5 }}
                    />
                    <YAxis
                      domain={[0, 1]}
                      label={{ value: "Survival Probability", angle: -90, position: "insideLeft" }}
                    />
                    <Tooltip />
                    <Legend />
                    <ReferenceLine y={0.5} stroke="#888" strokeDasharray="3 3" />
                    <Line
                      type="stepAfter"
                      dataKey="Active"
                      stroke="#8b5cf6"
                      strokeWidth={2}
                      dot={false}
                      name="Active Arm"
                    />
                    <Line
                      type="stepAfter"
                      dataKey="Placebo"
                      stroke="#ef4444"
                      strokeWidth={2}
                      dot={false}
                      name="Placebo Arm"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>Active Arm</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Median Survival:</span>
                    <span className="font-semibold">
                      {survivalResults.kaplan_meier.active?.median_survival?.toFixed(1) || "N/A"} months
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">95% CI:</span>
                    <span>
                      ({survivalResults.kaplan_meier.active?.median_ci_lower?.toFixed(1) || "N/A"},
                      {survivalResults.kaplan_meier.active?.median_ci_upper?.toFixed(1) || "N/A"})
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Total Subjects:</span>
                    <span>{survivalResults.kaplan_meier.active?.n_subjects || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Events:</span>
                    <span>{survivalResults.kaplan_meier.active?.n_events || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Censored:</span>
                    <span>{survivalResults.kaplan_meier.active?.n_censored || 0}</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Placebo Arm</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Median Survival:</span>
                    <span className="font-semibold">
                      {survivalResults.kaplan_meier.placebo?.median_survival?.toFixed(1) || "N/A"} months
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">95% CI:</span>
                    <span>
                      ({survivalResults.kaplan_meier.placebo?.median_ci_lower?.toFixed(1) || "N/A"},
                      {survivalResults.kaplan_meier.placebo?.median_ci_upper?.toFixed(1) || "N/A"})
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Total Subjects:</span>
                    <span>{survivalResults.kaplan_meier.placebo?.n_subjects || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Events:</span>
                    <span>{survivalResults.kaplan_meier.placebo?.n_events || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Censored:</span>
                    <span>{survivalResults.kaplan_meier.placebo?.n_censored || 0}</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Log-Rank Test Tab */}
          <TabsContent value="log-rank" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Log-Rank Test Results</CardTitle>
                <CardDescription>
                  Statistical comparison of survival curves between treatment arms
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-3">
                    <h3 className="font-semibold text-lg">Test Statistics</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Chi-Square Statistic:</span>
                        <span className="font-mono">
                          {survivalResults.log_rank_test?.test_statistic?.toFixed(4) || "N/A"}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">P-Value:</span>
                        <span className="font-mono font-semibold">
                          {survivalResults.log_rank_test?.p_value?.toFixed(4) || "N/A"}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Significance (α=0.05):</span>
                        <Badge variant={survivalResults.log_rank_test?.significant ? "default" : "secondary"}>
                          {survivalResults.log_rank_test?.significant ? "Significant" : "Not Significant"}
                        </Badge>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <h3 className="font-semibold text-lg">Event Counts</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Active Arm Events:</span>
                        <span>{survivalResults.log_rank_test?.arm1_events || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Placebo Arm Events:</span>
                        <span>{survivalResults.log_rank_test?.arm2_events || 0}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <Alert>
                  <TrendingDown className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Interpretation:</strong> {survivalResults.log_rank_test?.interpretation || "N/A"}
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Hazard Ratio Tab */}
          <TabsContent value="hazard-ratio" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Hazard Ratio Analysis</CardTitle>
                <CardDescription>
                  Relative risk of event occurrence between treatment arms
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-3">
                    <h3 className="font-semibold text-lg">Hazard Ratio</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">HR (Active vs Placebo):</span>
                        <span className="font-mono text-xl font-semibold">
                          {survivalResults.hazard_ratio?.hazard_ratio?.toFixed(3) || "N/A"}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">95% Confidence Interval:</span>
                        <span className="font-mono">
                          ({survivalResults.hazard_ratio?.ci_lower?.toFixed(3) || "N/A"},
                          {survivalResults.hazard_ratio?.ci_upper?.toFixed(3) || "N/A"})
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Clinical Benefit:</span>
                        <Badge
                          variant={
                            survivalResults.hazard_ratio?.clinical_benefit === "Favors treatment"
                              ? "default"
                              : "secondary"
                          }
                        >
                          {survivalResults.hazard_ratio?.clinical_benefit || "N/A"}
                        </Badge>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <h3 className="font-semibold text-lg">Event Counts</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Treatment Events:</span>
                        <span>{survivalResults.hazard_ratio?.treatment_events || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Reference Events:</span>
                        <span>{survivalResults.hazard_ratio?.reference_events || 0}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <Alert>
                  <TrendingDown className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Interpretation:</strong> {survivalResults.hazard_ratio?.interpretation || "N/A"}
                  </AlertDescription>
                </Alert>

                <div className="pt-4">
                  <h3 className="font-semibold mb-2">Understanding Hazard Ratio</h3>
                  <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
                    <li>HR &lt; 1: Treatment reduces risk (favors treatment)</li>
                    <li>HR = 1: No difference between treatments</li>
                    <li>HR &gt; 1: Treatment increases risk (favors control)</li>
                    <li>95% CI not including 1.0 indicates statistical significance</li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Summary Tab */}
          <TabsContent value="summary" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Analysis Summary</CardTitle>
                <CardDescription>
                  Comprehensive overview of survival analysis results
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-medium">Study Details</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Indication:</span>
                        <Badge>{survivalResults.summary?.indication || "N/A"}</Badge>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Total Subjects:</span>
                        <span className="font-semibold">{survivalResults.summary?.total_subjects || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Total Events:</span>
                        <span>{survivalResults.summary?.total_events || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Total Censored:</span>
                        <span>{survivalResults.summary?.total_censored || 0}</span>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-medium">Median Survival</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Active Arm:</span>
                        <span className="font-semibold">
                          {survivalResults.summary?.median_survival_active?.toFixed(1) || "N/A"} mo
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Placebo Arm:</span>
                        <span className="font-semibold">
                          {survivalResults.summary?.median_survival_placebo?.toFixed(1) || "N/A"} mo
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Difference:</span>
                        <span className="font-semibold text-green-600">
                          {((survivalResults.summary?.median_survival_active || 0) -
                            (survivalResults.summary?.median_survival_placebo || 0)).toFixed(1)} mo
                        </span>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-medium">Statistical Significance</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Hazard Ratio:</span>
                        <span className="font-semibold">
                          {survivalResults.summary?.hazard_ratio?.toFixed(3) || "N/A"}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">P-Value:</span>
                        <span className="font-mono">
                          {survivalResults.summary?.p_value?.toFixed(4) || "N/A"}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Significant:</span>
                        <Badge variant={survivalResults.summary?.significant ? "default" : "secondary"}>
                          {survivalResults.summary?.significant ? "Yes" : "No"}
                        </Badge>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                <div className="flex justify-end pt-4">
                  <Button onClick={handleDownloadSDTM} variant="outline">
                    <Download className="h-4 w-4 mr-2" />
                    Download SDTM TTE Data
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}
