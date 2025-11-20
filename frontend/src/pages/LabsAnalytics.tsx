import { useState } from "react";
import { analyticsApi } from "../services/api";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Alert, AlertDescription } from "../components/ui/alert";
import { Badge } from "../components/ui/badge";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { Activity, AlertTriangle, TrendingUp, Table as TableIcon, Download } from "lucide-react";

export function LabsAnalytics() {
  const [activeTab, setActiveTab] = useState("summary");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // State for each analysis type
  const [summaryData, setSummaryData] = useState<any>(null);
  const [abnormalData, setAbnormalData] = useState<any>(null);
  const [shiftData, setShiftData] = useState<any>(null);
  const [safetySignals, setSafetySignals] = useState<any>(null);
  const [longitudinalData, setLongitudinalData] = useState<any>(null);

  // Sample labs data in long format
  const sampleLabsData = [
    { SubjectID: "S001", VisitName: "Baseline", VisitNum: 1, TestName: "ALT", TestValue: 25, TreatmentArm: "Active" },
    { SubjectID: "S001", VisitName: "Baseline", VisitNum: 1, TestName: "AST", TestValue: 30, TreatmentArm: "Active" },
    { SubjectID: "S001", VisitName: "Baseline", VisitNum: 1, TestName: "Bilirubin", TestValue: 0.8, TreatmentArm: "Active" },
    { SubjectID: "S001", VisitName: "Baseline", VisitNum: 1, TestName: "Creatinine", TestValue: 0.9, TreatmentArm: "Active" },
    { SubjectID: "S001", VisitName: "Week 4", VisitNum: 2, TestName: "ALT", TestValue: 28, TreatmentArm: "Active" },
    { SubjectID: "S001", VisitName: "Week 4", VisitNum: 2, TestName: "AST", TestValue: 32, TreatmentArm: "Active" },
    { SubjectID: "S001", VisitName: "Week 4", VisitNum: 2, TestName: "Bilirubin", TestValue: 0.9, TreatmentArm: "Active" },
    { SubjectID: "S001", VisitName: "Week 4", VisitNum: 2, TestName: "Creatinine", TestValue: 0.95, TreatmentArm: "Active" },
    { SubjectID: "S002", VisitName: "Baseline", VisitNum: 1, TestName: "ALT", TestValue: 22, TreatmentArm: "Placebo" },
    { SubjectID: "S002", VisitName: "Baseline", VisitNum: 1, TestName: "AST", TestValue: 28, TreatmentArm: "Placebo" },
    { SubjectID: "S002", VisitName: "Baseline", VisitNum: 1, TestName: "Bilirubin", TestValue: 0.7, TreatmentArm: "Placebo" },
    { SubjectID: "S002", VisitName: "Baseline", VisitNum: 1, TestName: "Creatinine", TestValue: 0.85, TreatmentArm: "Placebo" },
  ];

  const loadLabsSummary = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await analyticsApi.getLabsSummary(sampleLabsData);
      setSummaryData(result);
    } catch (err: any) {
      setError(err.message || "Failed to load labs summary");
    } finally {
      setLoading(false);
    }
  };

  const loadAbnormalLabs = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await analyticsApi.detectAbnormalLabs(sampleLabsData);
      setAbnormalData(result);
    } catch (err: any) {
      setError(err.message || "Failed to detect abnormal labs");
    } finally {
      setLoading(false);
    }
  };

  const loadShiftTables = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await analyticsApi.generateShiftTables(sampleLabsData);
      setShiftData(result);
    } catch (err: any) {
      setError(err.message || "Failed to generate shift tables");
    } finally {
      setLoading(false);
    }
  };

  const loadSafetySignals = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await analyticsApi.detectSafetySignals(sampleLabsData);
      setSafetySignals(result);
    } catch (err: any) {
      setError(err.message || "Failed to detect safety signals");
    } finally {
      setLoading(false);
    }
  };

  const loadLongitudinalAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await analyticsApi.analyzeLabsLongitudinal(sampleLabsData);
      setLongitudinalData(result);
    } catch (err: any) {
      setError(err.message || "Failed to load longitudinal analysis");
    } finally {
      setLoading(false);
    }
  };

  const exportSDTM = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await analyticsApi.exportLabsSDTM(sampleLabsData);
      const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "labs_sdtm.json";
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
          <h1 className="text-3xl font-bold">Laboratory Analytics</h1>
          <p className="text-muted-foreground mt-2">
            Analyze lab results, detect safety signals, and monitor trends
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
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="summary">
            <Activity className="mr-2 h-4 w-4" />
            Summary
          </TabsTrigger>
          <TabsTrigger value="abnormal">
            <AlertTriangle className="mr-2 h-4 w-4" />
            Abnormal
          </TabsTrigger>
          <TabsTrigger value="shift">
            <TableIcon className="mr-2 h-4 w-4" />
            Shift Tables
          </TabsTrigger>
          <TabsTrigger value="safety">Safety Signals</TabsTrigger>
          <TabsTrigger value="longitudinal">
            <TrendingUp className="mr-2 h-4 w-4" />
            Trends
          </TabsTrigger>
        </TabsList>

        {/* Summary Tab */}
        <TabsContent value="summary" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Laboratory Summary Statistics</CardTitle>
              <CardDescription>
                Descriptive statistics for all lab tests by treatment arm and visit
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!summaryData ? (
                <div className="text-center py-12">
                  <Activity className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <Button onClick={loadLabsSummary} disabled={loading}>
                    {loading ? "Loading..." : "Load Labs Summary"}
                  </Button>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Summary Statistics Table */}
                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse border border-gray-200">
                      <thead>
                        <tr className="bg-gray-50">
                          <th className="border border-gray-200 px-4 py-2 text-left">Test</th>
                          <th className="border border-gray-200 px-4 py-2 text-center">Visit</th>
                          <th className="border border-gray-200 px-4 py-2 text-center">Arm</th>
                          <th className="border border-gray-200 px-4 py-2 text-center">N</th>
                          <th className="border border-gray-200 px-4 py-2 text-center">Mean</th>
                          <th className="border border-gray-200 px-4 py-2 text-center">SD</th>
                          <th className="border border-gray-200 px-4 py-2 text-center">Min</th>
                          <th className="border border-gray-200 px-4 py-2 text-center">Max</th>
                        </tr>
                      </thead>
                      <tbody>
                        {summaryData.test_summaries?.slice(0, 10).map((test: any, idx: number) => (
                          <tr key={idx}>
                            <td className="border border-gray-200 px-4 py-2 font-medium">{test.test_name}</td>
                            <td className="border border-gray-200 px-4 py-2 text-center">{test.visit_name}</td>
                            <td className="border border-gray-200 px-4 py-2 text-center">{test.treatment_arm}</td>
                            <td className="border border-gray-200 px-4 py-2 text-center">{test.n}</td>
                            <td className="border border-gray-200 px-4 py-2 text-center">{test.mean?.toFixed(2)}</td>
                            <td className="border border-gray-200 px-4 py-2 text-center">{test.std?.toFixed(2)}</td>
                            <td className="border border-gray-200 px-4 py-2 text-center">{test.min?.toFixed(2)}</td>
                            <td className="border border-gray-200 px-4 py-2 text-center">{test.max?.toFixed(2)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Lab Values Chart */}
                  {summaryData.test_summaries && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">Mean Lab Values by Test</h3>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={summaryData.test_summaries.slice(0, 8)}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="test_name" />
                          <YAxis />
                          <Tooltip />
                          <Legend />
                          <Bar dataKey="mean" fill="#8884d8" name="Mean Value" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Abnormal Labs Tab */}
        <TabsContent value="abnormal" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Abnormal Laboratory Values</CardTitle>
              <CardDescription>
                Detection and grading of abnormal lab values using CTCAE v5.0 criteria
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!abnormalData ? (
                <div className="text-center py-12">
                  <AlertTriangle className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <Button onClick={loadAbnormalLabs} disabled={loading}>
                    {loading ? "Loading..." : "Detect Abnormal Labs"}
                  </Button>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Abnormal Labs Summary */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Total Abnormal</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold">{abnormalData.total_abnormal || 0}</div>
                        <p className="text-sm text-muted-foreground mt-2">
                          {((abnormalData.abnormal_rate || 0) * 100).toFixed(1)}% of all tests
                        </p>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Grade 1 (Mild)</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-yellow-600">{abnormalData.grade1_count || 0}</div>
                        <Badge variant="outline" className="mt-2">Mild</Badge>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Grade 2 (Moderate)</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-orange-600">{abnormalData.grade2_count || 0}</div>
                        <Badge variant="secondary" className="mt-2">Moderate</Badge>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Grade 3+ (Severe)</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-red-600">{abnormalData.grade3_plus_count || 0}</div>
                        <Badge variant="destructive" className="mt-2">Severe</Badge>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Abnormal Labs by Test */}
                  {abnormalData.abnormal_by_test && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">Abnormal Labs by Test</h3>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={abnormalData.abnormal_by_test}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="test_name" />
                          <YAxis />
                          <Tooltip />
                          <Legend />
                          <Bar dataKey="abnormal_count" fill="#ff8042" name="Abnormal Count" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  )}

                  {/* Abnormal Labs Table */}
                  {abnormalData.abnormal_labs && abnormalData.abnormal_labs.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">Abnormal Lab Details</h3>
                      <div className="overflow-x-auto">
                        <table className="w-full border-collapse border border-gray-200">
                          <thead>
                            <tr className="bg-gray-50">
                              <th className="border border-gray-200 px-4 py-2 text-left">Subject</th>
                              <th className="border border-gray-200 px-4 py-2 text-center">Visit</th>
                              <th className="border border-gray-200 px-4 py-2 text-center">Test</th>
                              <th className="border border-gray-200 px-4 py-2 text-center">Value</th>
                              <th className="border border-gray-200 px-4 py-2 text-center">Grade</th>
                              <th className="border border-gray-200 px-4 py-2 text-center">Direction</th>
                            </tr>
                          </thead>
                          <tbody>
                            {abnormalData.abnormal_labs.slice(0, 10).map((lab: any, idx: number) => (
                              <tr key={idx}>
                                <td className="border border-gray-200 px-4 py-2">{lab.subject_id}</td>
                                <td className="border border-gray-200 px-4 py-2 text-center">{lab.visit_name}</td>
                                <td className="border border-gray-200 px-4 py-2 text-center">{lab.test_name}</td>
                                <td className="border border-gray-200 px-4 py-2 text-center">{lab.test_value?.toFixed(2)}</td>
                                <td className="border border-gray-200 px-4 py-2 text-center">
                                  <Badge variant={lab.grade >= 3 ? "destructive" : lab.grade === 2 ? "secondary" : "outline"}>
                                    Grade {lab.grade}
                                  </Badge>
                                </td>
                                <td className="border border-gray-200 px-4 py-2 text-center">{lab.direction}</td>
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

        {/* Shift Tables Tab */}
        <TabsContent value="shift" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Shift Tables</CardTitle>
              <CardDescription>
                Baseline to worst-case shift analysis (Normal → Abnormal transitions)
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!shiftData ? (
                <div className="text-center py-12">
                  <TableIcon className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <Button onClick={loadShiftTables} disabled={loading}>
                    {loading ? "Loading..." : "Generate Shift Tables"}
                  </Button>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Shift Summary */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Normal → Normal</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-green-600">{shiftData.normal_to_normal || 0}</div>
                        <p className="text-sm text-muted-foreground mt-2">Remained normal</p>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Normal → Abnormal</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-orange-600">{shiftData.normal_to_abnormal || 0}</div>
                        <p className="text-sm text-muted-foreground mt-2">Became abnormal</p>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Abnormal → Normal</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-blue-600">{shiftData.abnormal_to_normal || 0}</div>
                        <p className="text-sm text-muted-foreground mt-2">Resolved</p>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Shift Tables by Test */}
                  {shiftData.shift_tables && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">Shift Tables by Test</h3>
                      {shiftData.shift_tables.slice(0, 3).map((table: any, idx: number) => (
                        <div key={idx} className="mb-6">
                          <h4 className="font-semibold mb-2">{table.test_name} - {table.treatment_arm}</h4>
                          <div className="overflow-x-auto">
                            <table className="w-full border-collapse border border-gray-200">
                              <thead>
                                <tr className="bg-gray-50">
                                  <th className="border border-gray-200 px-4 py-2 text-left">Baseline</th>
                                  <th className="border border-gray-200 px-4 py-2 text-center">Normal (Post)</th>
                                  <th className="border border-gray-200 px-4 py-2 text-center">Abnormal (Post)</th>
                                  <th className="border border-gray-200 px-4 py-2 text-center">Total</th>
                                </tr>
                              </thead>
                              <tbody>
                                <tr>
                                  <td className="border border-gray-200 px-4 py-2 font-medium">Normal</td>
                                  <td className="border border-gray-200 px-4 py-2 text-center">{table.normal_to_normal}</td>
                                  <td className="border border-gray-200 px-4 py-2 text-center">{table.normal_to_abnormal}</td>
                                  <td className="border border-gray-200 px-4 py-2 text-center font-semibold">{table.baseline_normal}</td>
                                </tr>
                                <tr>
                                  <td className="border border-gray-200 px-4 py-2 font-medium">Abnormal</td>
                                  <td className="border border-gray-200 px-4 py-2 text-center">{table.abnormal_to_normal}</td>
                                  <td className="border border-gray-200 px-4 py-2 text-center">{table.abnormal_to_abnormal}</td>
                                  <td className="border border-gray-200 px-4 py-2 text-center font-semibold">{table.baseline_abnormal}</td>
                                </tr>
                              </tbody>
                            </table>
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

        {/* Safety Signals Tab */}
        <TabsContent value="safety" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Safety Signal Detection</CardTitle>
              <CardDescription>
                Automated detection of Hy's Law, kidney decline, and bone marrow suppression
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!safetySignals ? (
                <div className="text-center py-12">
                  <AlertTriangle className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <Button onClick={loadSafetySignals} disabled={loading}>
                    {loading ? "Loading..." : "Detect Safety Signals"}
                  </Button>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Safety Signals Summary */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Card className={safetySignals.hys_law_detected ? "border-red-500" : ""}>
                      <CardHeader>
                        <CardTitle className="text-lg">Hy's Law (DILI)</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center justify-between">
                          <div>
                            <Badge variant={safetySignals.hys_law_detected ? "destructive" : "default"}>
                              {safetySignals.hys_law_detected ? "DETECTED" : "Not Detected"}
                            </Badge>
                            <p className="text-sm text-muted-foreground mt-2">
                              Cases: {safetySignals.hys_law_cases || 0}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    <Card className={safetySignals.kidney_decline_detected ? "border-orange-500" : ""}>
                      <CardHeader>
                        <CardTitle className="text-lg">Kidney Decline</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center justify-between">
                          <div>
                            <Badge variant={safetySignals.kidney_decline_detected ? "destructive" : "default"}>
                              {safetySignals.kidney_decline_detected ? "DETECTED" : "Not Detected"}
                            </Badge>
                            <p className="text-sm text-muted-foreground mt-2">
                              Cases: {safetySignals.kidney_decline_cases || 0}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    <Card className={safetySignals.bone_marrow_suppression_detected ? "border-yellow-500" : ""}>
                      <CardHeader>
                        <CardTitle className="text-lg">Bone Marrow Suppression</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center justify-between">
                          <div>
                            <Badge variant={safetySignals.bone_marrow_suppression_detected ? "destructive" : "default"}>
                              {safetySignals.bone_marrow_suppression_detected ? "DETECTED" : "Not Detected"}
                            </Badge>
                            <p className="text-sm text-muted-foreground mt-2">
                              Cases: {safetySignals.bone_marrow_cases || 0}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Safety Signal Details */}
                  {(safetySignals.hys_law_subjects?.length > 0 ||
                    safetySignals.kidney_decline_subjects?.length > 0 ||
                    safetySignals.bone_marrow_subjects?.length > 0) && (
                    <Alert variant="destructive">
                      <AlertDescription>
                        <strong>Safety signals detected!</strong> Immediate review recommended for affected subjects.
                      </AlertDescription>
                    </Alert>
                  )}

                  {/* Affected Subjects */}
                  {safetySignals.hys_law_subjects?.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-2 text-red-600">Hy's Law Cases</h3>
                      <div className="bg-red-50 p-4 rounded">
                        <p className="text-sm font-medium mb-2">Subjects with drug-induced liver injury pattern:</p>
                        <p className="text-sm">{safetySignals.hys_law_subjects.join(", ")}</p>
                      </div>
                    </div>
                  )}

                  {safetySignals.interpretation && (
                    <Alert>
                      <AlertDescription>{safetySignals.interpretation}</AlertDescription>
                    </Alert>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Longitudinal Trends Tab */}
        <TabsContent value="longitudinal" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Longitudinal Trend Analysis</CardTitle>
              <CardDescription>
                Linear regression and trend analysis for lab values over time
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!longitudinalData ? (
                <div className="text-center py-12">
                  <TrendingUp className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <Button onClick={loadLongitudinalAnalysis} disabled={loading}>
                    {loading ? "Loading..." : "Analyze Longitudinal Trends"}
                  </Button>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Trend Summary */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {longitudinalData.trends?.slice(0, 4).map((trend: any, idx: number) => (
                      <Card key={idx}>
                        <CardHeader>
                          <CardTitle className="text-lg">{trend.test_name} - {trend.treatment_arm}</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-2">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Slope:</span>
                            <span className={`font-semibold ${trend.slope > 0 ? "text-red-600" : "text-green-600"}`}>
                              {trend.slope?.toFixed(3)} {trend.slope > 0 ? "↑" : "↓"}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">R²:</span>
                            <span className="font-semibold">{trend.r_squared?.toFixed(3)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">p-value:</span>
                            <span className="font-semibold">{trend.p_value?.toFixed(4)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Trend:</span>
                            <Badge variant={trend.significant ? "default" : "secondary"}>
                              {trend.trend_direction}
                            </Badge>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>

                  {/* Trend Charts */}
                  {longitudinalData.trend_data && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">Lab Value Trends Over Time</h3>
                      <ResponsiveContainer width="100%" height={400}>
                        <LineChart data={longitudinalData.trend_data}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="visit_num" label={{ value: "Visit Number", position: "insideBottom", offset: -5 }} />
                          <YAxis label={{ value: "Test Value", angle: -90, position: "insideLeft" }} />
                          <Tooltip />
                          <Legend />
                          <Line type="monotone" dataKey="mean_value" stroke="#8884d8" name="Mean Value" />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
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
