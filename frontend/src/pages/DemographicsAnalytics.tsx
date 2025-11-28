import { useState, useEffect } from "react";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Alert, AlertDescription } from "../components/ui/alert";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from "recharts";
import { Upload, Download, Users, BarChart3, Scale, RefreshCw, FileUp, AlertCircle } from "lucide-react";
import { analyticsApi } from "@/services/api";

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884d8", "#82ca9d"];

interface DemographicRecord {
  SubjectID: string;
  Age: number;
  Gender: string;
  Race: string;
  Ethnicity: string;
  Weight: number;
  Height: number;
  BMI: number;
  TreatmentArm: string;
}

export function DemographicsAnalytics() {
  const [activeTab, setActiveTab] = useState("baseline");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // State for demographics data
  const [demographicsData, setDemographicsData] = useState<DemographicRecord[]>([]);
  const [syntheticData, setSyntheticData] = useState<DemographicRecord[]>([]);

  // State for each analysis type
  const [baselineData, setBaselineData] = useState<any>(null);
  const [summaryData, setSummaryData] = useState<any>(null);
  const [balanceData, setBalanceData] = useState<any>(null);
  const [qualityData, setQualityData] = useState<any>(null);

  // Generate sample demographics data on mount
  useEffect(() => {
    generateSampleData();
  }, []);

  const generateSampleData = () => {
    const sampleData: DemographicRecord[] = [];
    const genders = ["Male", "Female"];
    const races = ["White", "Black", "Asian", "Other"];
    const ethnicities = ["Hispanic or Latino", "Not Hispanic or Latino"];
    const arms = ["Active", "Placebo"];

    for (let i = 1; i <= 100; i++) {
      const height = 150 + Math.random() * 40; // 150-190 cm
      const weight = 50 + Math.random() * 50; // 50-100 kg
      const bmi = weight / Math.pow(height / 100, 2);

      sampleData.push({
        SubjectID: `S${String(i).padStart(3, "0")}`,
        Age: Math.floor(18 + Math.random() * 62), // 18-80 years
        Gender: genders[Math.floor(Math.random() * genders.length)],
        Race: races[Math.floor(Math.random() * races.length)],
        Ethnicity: ethnicities[Math.floor(Math.random() * ethnicities.length)],
        Weight: Math.round(weight * 10) / 10,
        Height: Math.round(height * 10) / 10,
        BMI: Math.round(bmi * 10) / 10,
        TreatmentArm: arms[i % 2], // Alternate between Active and Placebo
      });
    }

    setDemographicsData(sampleData);
  };

  const loadBaselineCharacteristics = async () => {
    if (demographicsData.length === 0) {
      setError("No demographics data available. Please load data first.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const result = await analyticsApi.getBaselineCharacteristics(demographicsData);
      setBaselineData(result);
    } catch (err: any) {
      setError(err.message || "Failed to load baseline characteristics");
    } finally {
      setLoading(false);
    }
  };

  const loadSummaryStatistics = async () => {
    if (demographicsData.length === 0) {
      setError("No demographics data available. Please load data first.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const result = await analyticsApi.getDemographicSummary(demographicsData);
      setSummaryData(result);
    } catch (err: any) {
      setError(err.message || "Failed to load summary statistics");
    } finally {
      setLoading(false);
    }
  };

  const loadBalanceAssessment = async () => {
    if (demographicsData.length === 0) {
      setError("No demographics data available. Please load data first.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const result = await analyticsApi.assessDemographicBalance(demographicsData);
      setBalanceData(result);
    } catch (err: any) {
      setError(err.message || "Failed to load balance assessment");
    } finally {
      setLoading(false);
    }
  };

  const loadQualityComparison = async () => {
    if (demographicsData.length === 0 || syntheticData.length === 0) {
      setError("Both real and synthetic data required for quality comparison.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const result = await analyticsApi.compareDemographicsQuality(demographicsData, syntheticData);
      setQualityData(result);
    } catch (err: any) {
      setError(err.message || "Failed to load quality comparison");
    } finally {
      setLoading(false);
    }
  };

  const generateSyntheticData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Generate synthetic demographics using the existing API
      // Note: You may need to add this method to analyticsApi
      const result = await analyticsApi.compareDemographicsQuality(demographicsData, demographicsData);
      // For now, use the same data as placeholder
      setSyntheticData(demographicsData.map(d => ({ ...d, SubjectID: `SYN-${d.SubjectID}` })));
    } catch (err: any) {
      setError(err.message || "Failed to generate synthetic data");
    } finally {
      setLoading(false);
    }
  };

  const exportSDTM = async () => {
    if (demographicsData.length === 0) {
      setError("No demographics data available to export.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const result = await analyticsApi.exportDemographicsSDTM(demographicsData);

      // Download as JSON file
      const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `demographics_sdtm_${new Date().toISOString().split("T")[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.message || "Failed to export SDTM data");
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const json = JSON.parse(e.target?.result as string);
        if (Array.isArray(json)) {
          setDemographicsData(json);
          setError(null);
        } else {
          setError("Invalid file format. Expected JSON array.");
        }
      } catch (err) {
        setError("Failed to parse JSON file.");
      }
    };
    reader.readAsText(file);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <Users className="h-8 w-8 text-blue-600" />
            Demographics Analytics
          </h1>
          <p className="text-gray-500 mt-1">
            Analyze baseline characteristics, treatment balance, and data quality ({demographicsData.length} subjects)
          </p>
        </div>
        <div className="flex gap-2">
          <div>
            <Input
              id="file-upload"
              type="file"
              accept=".json"
              onChange={handleFileUpload}
              className="hidden"
            />
            <Button variant="outline" onClick={() => document.getElementById("file-upload")?.click()} disabled={loading}>
              <FileUp className="h-4 w-4 mr-2" />
              Upload Data
            </Button>
          </div>
          <Button variant="outline" onClick={generateSampleData} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
            Generate Sample
          </Button>
          <Button variant="outline" onClick={generateSyntheticData} disabled={loading || demographicsData.length === 0}>
            <BarChart3 className="h-4 w-4 mr-2" />
            Generate Synthetic
          </Button>
          <Button variant="outline" onClick={exportSDTM} disabled={loading || demographicsData.length === 0}>
            <Download className="h-4 w-4 mr-2" />
            Export SDTM
          </Button>
        </div>
      </div>

      {/* Data Status Cards */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">Real Data</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{demographicsData.length}</div>
            <p className="text-xs text-gray-500 mt-1">subjects loaded</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">Synthetic Data</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{syntheticData.length}</div>
            <p className="text-xs text-gray-500 mt-1">synthetic subjects</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">Treatment Arms</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {demographicsData.filter((d) => d.TreatmentArm === "Active").length} / {demographicsData.filter((d) => d.TreatmentArm === "Placebo").length}
            </div>
            <p className="text-xs text-gray-500 mt-1">Active / Placebo</p>
          </CardContent>
        </Card>
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
            <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
            <p className="text-gray-600">Processing demographics analysis...</p>
          </CardContent>
        </Card>
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
                          {balanceData.balance_tests && Array.isArray(balanceData.balance_tests) ? (
                            balanceData.balance_tests.map((test: any, idx: number) => (
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
                            ))
                          ) : (
                            <tr>
                              <td colSpan={4} className="border border-gray-200 px-4 py-2 text-center">
                                No balance test data available
                              </td>
                            </tr>
                          )}
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
