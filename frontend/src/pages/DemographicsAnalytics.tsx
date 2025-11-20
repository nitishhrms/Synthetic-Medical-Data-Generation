import { useState } from "react";
import { analyticsApi } from "../services/api";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Alert, AlertDescription } from "../components/ui/alert";
import { Badge } from "../components/ui/badge";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { Upload, Download, Users, BarChart3, Scale } from "lucide-react";

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884d8", "#82ca9d"];

export function DemographicsAnalytics() {
  const [activeTab, setActiveTab] = useState("baseline");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // State for each analysis type
  const [baselineData, setBaselineData] = useState<any>(null);
  const [summaryData, setSummaryData] = useState<any>(null);
  const [balanceData, setBalanceData] = useState<any>(null);
  const [qualityData, setQualityData] = useState<any>(null);

  // Sample demographics data for testing
  const sampleDemographics = [
    {
      SubjectID: "S001", Age: 45, Gender: "Male", Race: "White", Ethnicity: "Not Hispanic",
      Weight: 75.0, Height: 175.0, BMI: 24.5, TreatmentArm: "Active"
    },
    {
      SubjectID: "S002", Age: 52, Gender: "Female", Race: "Asian", Ethnicity: "Not Hispanic",
      Weight: 68.0, Height: 165.0, BMI: 25.0, TreatmentArm: "Placebo"
    },
    {
      SubjectID: "S003", Age: 38, Gender: "Male", Race: "Black", Ethnicity: "Hispanic",
      Weight: 82.0, Height: 180.0, BMI: 25.3, TreatmentArm: "Active"
    },
    {
      SubjectID: "S004", Age: 61, Gender: "Female", Race: "White", Ethnicity: "Not Hispanic",
      Weight: 71.0, Height: 168.0, BMI: 25.1, TreatmentArm: "Placebo"
    },
  ];

  const loadBaselineCharacteristics = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await analyticsApi.getBaselineCharacteristics(sampleDemographics);
      setBaselineData(result);
    } catch (err: any) {
      setError(err.message || "Failed to load baseline characteristics");
    } finally {
      setLoading(false);
    }
  };

  const loadSummaryStatistics = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await analyticsApi.getDemographicSummary(sampleDemographics);
      setSummaryData(result);
    } catch (err: any) {
      setError(err.message || "Failed to load summary statistics");
    } finally {
      setLoading(false);
    }
  };

  const loadBalanceAssessment = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await analyticsApi.assessDemographicBalance(sampleDemographics);
      setBalanceData(result);
    } catch (err: any) {
      setError(err.message || "Failed to load balance assessment");
    } finally {
      setLoading(false);
    }
  };

  const loadQualityComparison = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await analyticsApi.compareDemographicsQuality(
        sampleDemographics,
        sampleDemographics // Using same data for demo
      );
      setQualityData(result);
    } catch (err: any) {
      setError(err.message || "Failed to load quality comparison");
    } finally {
      setLoading(false);
    }
  };

  const exportSDTM = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await analyticsApi.exportDemographicsSDTM(sampleDemographics);
      // Download as JSON file
      const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "demographics_sdtm.json";
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.message || "Failed to export SDTM data");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Demographics Analytics</h1>
          <p className="text-muted-foreground mt-2">
            Analyze baseline characteristics, treatment balance, and data quality
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={exportSDTM} disabled={loading}>
            <Download className="mr-2 h-4 w-4" />
            Export SDTM
          </Button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="baseline">
            <Users className="mr-2 h-4 w-4" />
            Baseline
          </TabsTrigger>
          <TabsTrigger value="summary">
            <BarChart3 className="mr-2 h-4 w-4" />
            Summary
          </TabsTrigger>
          <TabsTrigger value="balance">
            <Scale className="mr-2 h-4 w-4" />
            Balance
          </TabsTrigger>
          <TabsTrigger value="quality">Quality</TabsTrigger>
        </TabsList>

        {/* Baseline Characteristics Tab */}
        <TabsContent value="baseline" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Baseline Characteristics</CardTitle>
              <CardDescription>
                Demographic and baseline characteristics by treatment arm
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!baselineData ? (
                <div className="text-center py-12">
                  <Users className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <Button onClick={loadBaselineCharacteristics} disabled={loading}>
                    {loading ? "Loading..." : "Load Baseline Characteristics"}
                  </Button>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Demographics Table */}
                  <div>
                    <h3 className="text-lg font-semibold mb-4">Patient Characteristics</h3>
                    <div className="overflow-x-auto">
                      <table className="w-full border-collapse border border-gray-200">
                        <thead>
                          <tr className="bg-gray-50">
                            <th className="border border-gray-200 px-4 py-2 text-left">Characteristic</th>
                            <th className="border border-gray-200 px-4 py-2 text-center">Active (n={baselineData.treatment_groups?.Active?.n || 0})</th>
                            <th className="border border-gray-200 px-4 py-2 text-center">Placebo (n={baselineData.treatment_groups?.Placebo?.n || 0})</th>
                          </tr>
                        </thead>
                        <tbody>
                          {baselineData.characteristics?.map((char: any, idx: number) => (
                            <tr key={idx}>
                              <td className="border border-gray-200 px-4 py-2 font-medium">{char.characteristic}</td>
                              <td className="border border-gray-200 px-4 py-2 text-center">{char.active_value}</td>
                              <td className="border border-gray-200 px-4 py-2 text-center">{char.placebo_value}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Age Distribution Chart */}
                  {baselineData.treatment_groups && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">Age Distribution</h3>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart
                          data={[
                            {
                              name: "Active",
                              Age: baselineData.treatment_groups.Active?.mean_age || 0,
                            },
                            {
                              name: "Placebo",
                              Age: baselineData.treatment_groups.Placebo?.mean_age || 0,
                            },
                          ]}
                        >
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="name" />
                          <YAxis label={{ value: "Mean Age (years)", angle: -90, position: "insideLeft" }} />
                          <Tooltip />
                          <Legend />
                          <Bar dataKey="Age" fill="#8884d8" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Summary Statistics Tab */}
        <TabsContent value="summary" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Summary Statistics</CardTitle>
              <CardDescription>
                Detailed summary statistics by treatment arm
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!summaryData ? (
                <div className="text-center py-12">
                  <BarChart3 className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <Button onClick={loadSummaryStatistics} disabled={loading}>
                    {loading ? "Loading..." : "Load Summary Statistics"}
                  </Button>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Treatment Arms Summary */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {Object.entries(summaryData.treatment_arms || {}).map(([arm, data]: [string, any]) => (
                      <Card key={arm}>
                        <CardHeader>
                          <CardTitle className="text-lg">{arm}</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-2">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">N:</span>
                            <span className="font-semibold">{data.n}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Mean Age:</span>
                            <span className="font-semibold">{data.mean_age?.toFixed(1)} years</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Mean BMI:</span>
                            <span className="font-semibold">{data.mean_bmi?.toFixed(1)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Male:</span>
                            <span className="font-semibold">{data.male_count} ({data.male_percent?.toFixed(1)}%)</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Female:</span>
                            <span className="font-semibold">{data.female_count} ({data.female_percent?.toFixed(1)}%)</span>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>

                  {/* Gender Distribution Pie Chart */}
                  {summaryData.treatment_arms && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">Gender Distribution</h3>
                      <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                          <Pie
                            data={[
                              { name: "Male (Active)", value: summaryData.treatment_arms.Active?.male_count || 0 },
                              { name: "Female (Active)", value: summaryData.treatment_arms.Active?.female_count || 0 },
                              { name: "Male (Placebo)", value: summaryData.treatment_arms.Placebo?.male_count || 0 },
                              { name: "Female (Placebo)", value: summaryData.treatment_arms.Placebo?.female_count || 0 },
                            ]}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            label={(entry) => `${entry.name}: ${entry.value}`}
                            outerRadius={80}
                            fill="#8884d8"
                            dataKey="value"
                          >
                            {[0, 1, 2, 3].map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Balance Assessment Tab */}
        <TabsContent value="balance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Treatment Arm Balance</CardTitle>
              <CardDescription>
                Statistical tests for baseline balance between treatment arms
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!balanceData ? (
                <div className="text-center py-12">
                  <Scale className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <Button onClick={loadBalanceAssessment} disabled={loading}>
                    {loading ? "Loading..." : "Load Balance Assessment"}
                  </Button>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Overall Balance Status */}
                  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div>
                      <h3 className="text-lg font-semibold">Overall Balance Status</h3>
                      <p className="text-sm text-muted-foreground">
                        {balanceData.overall_balanced ? "Treatment arms are well balanced" : "Treatment arms show imbalance"}
                      </p>
                    </div>
                    <Badge variant={balanceData.overall_balanced ? "default" : "destructive"}>
                      {balanceData.overall_balanced ? "Balanced" : "Imbalanced"}
                    </Badge>
                  </div>

                  {/* Statistical Tests Table */}
                  <div>
                    <h3 className="text-lg font-semibold mb-4">Statistical Tests</h3>
                    <div className="overflow-x-auto">
                      <table className="w-full border-collapse border border-gray-200">
                        <thead>
                          <tr className="bg-gray-50">
                            <th className="border border-gray-200 px-4 py-2 text-left">Variable</th>
                            <th className="border border-gray-200 px-4 py-2 text-center">Test</th>
                            <th className="border border-gray-200 px-4 py-2 text-center">p-value</th>
                            <th className="border border-gray-200 px-4 py-2 text-center">Balanced</th>
                          </tr>
                        </thead>
                        <tbody>
                          {balanceData.balance_tests?.map((test: any, idx: number) => (
                            <tr key={idx}>
                              <td className="border border-gray-200 px-4 py-2 font-medium">{test.variable}</td>
                              <td className="border border-gray-200 px-4 py-2 text-center">{test.test_name}</td>
                              <td className="border border-gray-200 px-4 py-2 text-center">{test.p_value?.toFixed(4)}</td>
                              <td className="border border-gray-200 px-4 py-2 text-center">
                                <Badge variant={test.balanced ? "default" : "destructive"}>
                                  {test.balanced ? "Yes" : "No"}
                                </Badge>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Interpretation */}
                  {balanceData.interpretation && (
                    <Alert>
                      <AlertDescription>{balanceData.interpretation}</AlertDescription>
                    </Alert>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Quality Comparison Tab */}
        <TabsContent value="quality" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Data Quality Comparison</CardTitle>
              <CardDescription>
                Compare real vs. synthetic demographics data quality
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!qualityData ? (
                <div className="text-center py-12">
                  <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <Button onClick={loadQualityComparison} disabled={loading}>
                    {loading ? "Loading..." : "Load Quality Comparison"}
                  </Button>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Overall Quality Score */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Overall Quality</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold">{(qualityData.overall_quality_score * 100)?.toFixed(1)}%</div>
                        <Badge className="mt-2" variant={qualityData.overall_quality_score > 0.85 ? "default" : "secondary"}>
                          {qualityData.quality_grade}
                        </Badge>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Distribution Match</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold">{(qualityData.distribution_similarity * 100)?.toFixed(1)}%</div>
                        <p className="text-sm text-muted-foreground mt-2">Wasserstein distance</p>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Category Match</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold">{(qualityData.category_similarity * 100)?.toFixed(1)}%</div>
                        <p className="text-sm text-muted-foreground mt-2">Gender, Race, Ethnicity</p>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Quality Metrics Chart */}
                  {qualityData.quality_metrics && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">Quality Metrics by Variable</h3>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={qualityData.quality_metrics}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="variable" />
                          <YAxis label={{ value: "Quality Score", angle: -90, position: "insideLeft" }} />
                          <Tooltip />
                          <Legend />
                          <Bar dataKey="quality_score" fill="#82ca9d" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  )}

                  {/* Summary */}
                  {qualityData.summary && (
                    <Alert>
                      <AlertDescription>{qualityData.summary}</AlertDescription>
                    </Alert>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
