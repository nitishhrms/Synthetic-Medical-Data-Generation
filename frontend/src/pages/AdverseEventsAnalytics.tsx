import { useState } from "react";
import { analyticsApi } from "../services/api";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Alert, AlertDescription } from "../components/ui/alert";
import { Badge } from "../components/ui/badge";
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { AlertCircle, Activity, PieChartIcon, Download } from "lucide-react";

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884d8", "#82ca9d", "#ffc658", "#ff7c7c"];

export function AdverseEventsAnalytics() {
  const [activeTab, setActiveTab] = useState("summary");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // State for each analysis type
  const [summaryData, setSummaryData] = useState<any>(null);
  const [teaeData, setTeaeData] = useState<any>(null);
  const [socData, setSocData] = useState<any>(null);
  const [qualityData, setQualityData] = useState<any>(null);

  // Sample AE data
  const sampleAEData = [
    {
      SubjectID: "S001",
      SOC: "Gastrointestinal disorders",
      PT: "Nausea",
      Severity: "Mild",
      Relationship: "Possibly Related",
      Serious: "No",
      OnsetDate: "2025-01-15",
      TreatmentArm: "Active"
    },
    {
      SubjectID: "S002",
      SOC: "Nervous system disorders",
      PT: "Headache",
      Severity: "Moderate",
      Relationship: "Not Related",
      Serious: "No",
      OnsetDate: "2025-01-20",
      TreatmentArm: "Placebo"
    },
    {
      SubjectID: "S003",
      SOC: "General disorders and administration site conditions",
      PT: "Fatigue",
      Severity: "Mild",
      Relationship: "Possibly Related",
      Serious: "No",
      OnsetDate: "2025-01-18",
      TreatmentArm: "Active"
    },
    {
      SubjectID: "S001",
      SOC: "Gastrointestinal disorders",
      PT: "Diarrhea",
      Severity: "Moderate",
      Relationship: "Probably Related",
      Serious: "No",
      OnsetDate: "2025-01-22",
      TreatmentArm: "Active"
    },
  ];

  const loadAESummary = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await analyticsApi.getAESummary(sampleAEData);
      setSummaryData(result);
    } catch (err: any) {
      setError(err.message || "Failed to load AE summary");
    } finally {
      setLoading(false);
    }
  };

  const loadTEAEAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await analyticsApi.analyzeTreatmentEmergentAEs(sampleAEData, "2025-01-01");
      setTeaeData(result);
    } catch (err: any) {
      setError(err.message || "Failed to load TEAE analysis");
    } finally {
      setLoading(false);
    }
  };

  const loadSOCAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await analyticsApi.analyzeSOCDistribution(sampleAEData);
      setSocData(result);
    } catch (err: any) {
      setError(err.message || "Failed to load SOC analysis");
    } finally {
      setLoading(false);
    }
  };

  const loadQualityComparison = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await analyticsApi.compareAEQuality(sampleAEData, sampleAEData);
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
      const result = await analyticsApi.exportAESDTM(sampleAEData);
      const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "ae_sdtm.json";
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
          <h1 className="text-3xl font-bold">Adverse Events Analytics</h1>
          <p className="text-muted-foreground mt-2">
            Analyze adverse events, treatment-emergent AEs, and safety profiles
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
          <TabsTrigger value="summary">
            <AlertCircle className="mr-2 h-4 w-4" />
            Summary
          </TabsTrigger>
          <TabsTrigger value="teae">
            <Activity className="mr-2 h-4 w-4" />
            TEAE
          </TabsTrigger>
          <TabsTrigger value="soc">
            <PieChartIcon className="mr-2 h-4 w-4" />
            SOC Analysis
          </TabsTrigger>
          <TabsTrigger value="quality">Quality</TabsTrigger>
        </TabsList>

        {/* Summary Tab */}
        <TabsContent value="summary" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Adverse Events Summary</CardTitle>
              <CardDescription>
                Overall adverse event incidence rates and summary statistics
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!summaryData ? (
                <div className="text-center py-12">
                  <AlertCircle className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <Button onClick={loadAESummary} disabled={loading}>
                    {loading ? "Loading..." : "Load AE Summary"}
                  </Button>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Overall Statistics */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Total AEs</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold">{summaryData.total_aes || 0}</div>
                        <p className="text-sm text-muted-foreground mt-2">All adverse events</p>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Subjects with AEs</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold">{summaryData.subjects_with_aes || 0}</div>
                        <p className="text-sm text-muted-foreground mt-2">
                          {((summaryData.incidence_rate || 0) * 100).toFixed(1)}% incidence
                        </p>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Serious AEs</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-red-600">{summaryData.serious_aes || 0}</div>
                        <Badge variant="destructive" className="mt-2">SAE</Badge>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Related AEs</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-orange-600">{summaryData.related_aes || 0}</div>
                        <p className="text-sm text-muted-foreground mt-2">
                          {((summaryData.related_rate || 0) * 100).toFixed(1)}% related
                        </p>
                      </CardContent>
                    </Card>
                  </div>

                  {/* AE by Treatment Arm */}
                  {summaryData.by_treatment_arm && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">AEs by Treatment Arm</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {Object.entries(summaryData.by_treatment_arm).map(([arm, data]: [string, any]) => (
                          <Card key={arm}>
                            <CardHeader>
                              <CardTitle className="text-lg">{arm}</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-2">
                              <div className="flex justify-between">
                                <span className="text-muted-foreground">Total AEs:</span>
                                <span className="font-semibold">{data.total_aes}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-muted-foreground">Subjects with AEs:</span>
                                <span className="font-semibold">{data.subjects_with_aes}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-muted-foreground">Serious AEs:</span>
                                <span className="font-semibold text-red-600">{data.serious_aes}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-muted-foreground">Related AEs:</span>
                                <span className="font-semibold text-orange-600">{data.related_aes}</span>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* AE by Severity Chart */}
                  {summaryData.by_severity && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">AEs by Severity</h3>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={summaryData.by_severity}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="severity" />
                          <YAxis />
                          <Tooltip />
                          <Legend />
                          <Bar dataKey="count" fill="#8884d8" name="Number of AEs" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  )}

                  {/* Top AEs Table */}
                  {summaryData.top_aes && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">Most Common Adverse Events</h3>
                      <div className="overflow-x-auto">
                        <table className="w-full border-collapse border border-gray-200">
                          <thead>
                            <tr className="bg-gray-50">
                              <th className="border border-gray-200 px-4 py-2 text-left">Preferred Term</th>
                              <th className="border border-gray-200 px-4 py-2 text-center">Count</th>
                              <th className="border border-gray-200 px-4 py-2 text-center">Incidence Rate</th>
                            </tr>
                          </thead>
                          <tbody>
                            {summaryData.top_aes.map((ae: any, idx: number) => (
                              <tr key={idx}>
                                <td className="border border-gray-200 px-4 py-2 font-medium">{ae.pt}</td>
                                <td className="border border-gray-200 px-4 py-2 text-center">{ae.count}</td>
                                <td className="border border-gray-200 px-4 py-2 text-center">
                                  {(ae.incidence_rate * 100).toFixed(1)}%
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* TEAE Tab */}
        <TabsContent value="teae" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Treatment-Emergent Adverse Events (TEAE)</CardTitle>
              <CardDescription>
                AEs occurring after treatment initiation (onset ≥ 2025-01-01)
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!teaeData ? (
                <div className="text-center py-12">
                  <Activity className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <Button onClick={loadTEAEAnalysis} disabled={loading}>
                    {loading ? "Loading..." : "Load TEAE Analysis"}
                  </Button>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* TEAE Summary */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Total TEAEs</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold">{teaeData.total_teaes || 0}</div>
                        <p className="text-sm text-muted-foreground mt-2">
                          {((teaeData.teae_rate || 0) * 100).toFixed(1)}% of all AEs
                        </p>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Subjects with TEAEs</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold">{teaeData.subjects_with_teaes || 0}</div>
                        <p className="text-sm text-muted-foreground mt-2">
                          {((teaeData.teae_incidence_rate || 0) * 100).toFixed(1)}% incidence
                        </p>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Serious TEAEs</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-red-600">{teaeData.serious_teaes || 0}</div>
                        <Badge variant="destructive" className="mt-2">Serious TEAE</Badge>
                      </CardContent>
                    </Card>
                  </div>

                  {/* TEAE by Treatment Arm */}
                  {teaeData.by_treatment_arm && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">TEAEs by Treatment Arm</h3>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart
                          data={Object.entries(teaeData.by_treatment_arm).map(([arm, data]: [string, any]) => ({
                            arm,
                            teaes: data.total_teaes,
                            serious: data.serious_teaes,
                          }))}
                        >
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="arm" />
                          <YAxis />
                          <Tooltip />
                          <Legend />
                          <Bar dataKey="teaes" fill="#8884d8" name="Total TEAEs" />
                          <Bar dataKey="serious" fill="#ff8042" name="Serious TEAEs" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  )}

                  {/* Most Common TEAEs */}
                  {teaeData.top_teaes && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">Most Common TEAEs</h3>
                      <div className="overflow-x-auto">
                        <table className="w-full border-collapse border border-gray-200">
                          <thead>
                            <tr className="bg-gray-50">
                              <th className="border border-gray-200 px-4 py-2 text-left">Preferred Term</th>
                              <th className="border border-gray-200 px-4 py-2 text-center">Active</th>
                              <th className="border border-gray-200 px-4 py-2 text-center">Placebo</th>
                              <th className="border border-gray-200 px-4 py-2 text-center">Risk Ratio</th>
                            </tr>
                          </thead>
                          <tbody>
                            {teaeData.top_teaes.slice(0, 10).map((ae: any, idx: number) => (
                              <tr key={idx}>
                                <td className="border border-gray-200 px-4 py-2 font-medium">{ae.pt}</td>
                                <td className="border border-gray-200 px-4 py-2 text-center">{ae.active_count}</td>
                                <td className="border border-gray-200 px-4 py-2 text-center">{ae.placebo_count}</td>
                                <td className="border border-gray-200 px-4 py-2 text-center">
                                  <Badge variant={ae.risk_ratio > 1.5 ? "destructive" : "secondary"}>
                                    {ae.risk_ratio?.toFixed(2)}
                                  </Badge>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Risk Ratio Interpretation */}
                  {teaeData.interpretation && (
                    <Alert>
                      <AlertDescription>{teaeData.interpretation}</AlertDescription>
                    </Alert>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* SOC Analysis Tab */}
        <TabsContent value="soc" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>System Organ Class (SOC) Analysis</CardTitle>
              <CardDescription>
                MedDRA System Organ Class distribution and analysis
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!socData ? (
                <div className="text-center py-12">
                  <PieChartIcon className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <Button onClick={loadSOCAnalysis} disabled={loading}>
                    {loading ? "Loading..." : "Load SOC Analysis"}
                  </Button>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* SOC Summary */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Total SOCs</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold">{socData.total_socs || 0}</div>
                        <p className="text-sm text-muted-foreground mt-2">Unique system organ classes</p>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Most Affected SOC</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-xl font-bold">{socData.most_common_soc || "N/A"}</div>
                        <p className="text-sm text-muted-foreground mt-2">
                          {socData.most_common_soc_count || 0} AEs
                        </p>
                      </CardContent>
                    </Card>
                  </div>

                  {/* SOC Distribution Pie Chart */}
                  {socData.soc_distribution && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">AE Distribution by SOC</h3>
                      <ResponsiveContainer width="100%" height={400}>
                        <PieChart>
                          <Pie
                            data={socData.soc_distribution}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            label={(entry) => `${entry.soc}: ${entry.count}`}
                            outerRadius={120}
                            fill="#8884d8"
                            dataKey="count"
                          >
                            {socData.soc_distribution.map((entry: any, index: number) => (
                              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  )}

                  {/* SOC by Treatment Arm */}
                  {socData.soc_by_arm && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">SOC Distribution by Treatment Arm</h3>
                      <div className="overflow-x-auto">
                        <table className="w-full border-collapse border border-gray-200">
                          <thead>
                            <tr className="bg-gray-50">
                              <th className="border border-gray-200 px-4 py-2 text-left">System Organ Class</th>
                              <th className="border border-gray-200 px-4 py-2 text-center">Active</th>
                              <th className="border border-gray-200 px-4 py-2 text-center">Placebo</th>
                              <th className="border border-gray-200 px-4 py-2 text-center">Total</th>
                            </tr>
                          </thead>
                          <tbody>
                            {socData.soc_by_arm?.map((soc: any, idx: number) => (
                              <tr key={idx}>
                                <td className="border border-gray-200 px-4 py-2 font-medium">{soc.soc}</td>
                                <td className="border border-gray-200 px-4 py-2 text-center">{soc.active_count}</td>
                                <td className="border border-gray-200 px-4 py-2 text-center">{soc.placebo_count}</td>
                                <td className="border border-gray-200 px-4 py-2 text-center font-semibold">{soc.total_count}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Top PTs within Each SOC */}
                  {socData.top_pts_by_soc && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">Top Preferred Terms within Each SOC</h3>
                      {Object.entries(socData.top_pts_by_soc).slice(0, 3).map(([soc, pts]: [string, any]) => (
                        <div key={soc} className="mb-4">
                          <h4 className="font-semibold mb-2">{soc}</h4>
                          <div className="pl-4 space-y-1">
                            {pts.map((pt: any, idx: number) => (
                              <div key={idx} className="flex justify-between items-center">
                                <span className="text-sm">{pt.pt}</span>
                                <Badge variant="secondary">{pt.count}</Badge>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Quality Tab */}
        <TabsContent value="quality" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>AE Data Quality Comparison</CardTitle>
              <CardDescription>
                Compare real vs. synthetic adverse event data quality
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!qualityData ? (
                <div className="text-center py-12">
                  <Activity className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <Button onClick={loadQualityComparison} disabled={loading}>
                    {loading ? "Loading..." : "Load Quality Comparison"}
                  </Button>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Quality Metrics */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Overall Quality</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold">{(qualityData.overall_quality * 100)?.toFixed(1)}%</div>
                        <Badge className="mt-2" variant={qualityData.overall_quality > 0.85 ? "default" : "secondary"}>
                          {qualityData.quality_grade}
                        </Badge>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">SOC Match</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold">{(qualityData.soc_similarity * 100)?.toFixed(1)}%</div>
                        <p className="text-sm text-muted-foreground mt-2">System Organ Class</p>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">PT Match</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold">{(qualityData.pt_similarity * 100)?.toFixed(1)}%</div>
                        <p className="text-sm text-muted-foreground mt-2">Preferred Term</p>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Quality Metrics Chart */}
                  {qualityData.quality_metrics && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">Quality Metrics Comparison</h3>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={qualityData.quality_metrics}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="metric" />
                          <YAxis />
                          <Tooltip />
                          <Legend />
                          <Bar dataKey="score" fill="#82ca9d" name="Quality Score" />
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
