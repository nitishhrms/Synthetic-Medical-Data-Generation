import { useState } from "react";
import { analyticsApi } from "../services/api";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Alert, AlertDescription } from "../components/ui/alert";
import { Badge } from "../components/ui/badge";
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from "recharts";
import { LayoutDashboard, Network, FileText } from "lucide-react";

export function StudyDashboard() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // State for each view
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [correlationsData, setCorrelationsData] = useState<any>(null);
  const [comprehensiveData, setComprehensiveData] = useState<any>(null);

  // Sample data for all domains
  const sampleDemographics = [
    { SubjectID: "S001", Age: 45, Gender: "Male", Race: "White", Weight: 75, Height: 175, BMI: 24.5, TreatmentArm: "Active" },
    { SubjectID: "S002", Age: 52, Gender: "Female", Race: "Asian", Weight: 68, Height: 165, BMI: 25.0, TreatmentArm: "Placebo" },
  ];

  const sampleVitals = [
    { SubjectID: "S001", VisitName: "Screening", TreatmentArm: "Active", SystolicBP: 142, DiastolicBP: 88, HeartRate: 72, Temperature: 36.7 },
    { SubjectID: "S001", VisitName: "Week 12", TreatmentArm: "Active", SystolicBP: 135, DiastolicBP: 82, HeartRate: 70, Temperature: 36.6 },
  ];

  const sampleLabs = [
    { SubjectID: "S001", VisitName: "Baseline", VisitNum: 1, TestName: "ALT", TestValue: 25, TreatmentArm: "Active" },
    { SubjectID: "S001", VisitName: "Week 4", VisitNum: 2, TestName: "ALT", TestValue: 28, TreatmentArm: "Active" },
  ];

  const sampleAE = [
    { SubjectID: "S001", SOC: "Gastrointestinal disorders", PT: "Nausea", Severity: "Mild", Relationship: "Possibly Related", Serious: "No", OnsetDate: "2025-01-15", TreatmentArm: "Active" },
  ];

  const loadTrialDashboard = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await analyticsApi.getTrialDashboard({
        demographics_data: sampleDemographics,
        vitals_data: sampleVitals,
        labs_data: sampleLabs,
        ae_data: sampleAE,
        indication: "hypertension",
        phase: "Phase 3"
      });
      setDashboardData(result);
    } catch (err: any) {
      setError(err.message || "Failed to load trial dashboard");
    } finally {
      setLoading(false);
    }
  };

  const loadCrossDomainCorrelations = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await analyticsApi.getCrossDomainCorrelations({
        demographics_data: sampleDemographics,
        vitals_data: sampleVitals,
        labs_data: sampleLabs,
        ae_data: sampleAE
      });
      setCorrelationsData(result);
    } catch (err: any) {
      setError(err.message || "Failed to load correlations");
    } finally {
      setLoading(false);
    }
  };

  const loadComprehensiveSummary = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await analyticsApi.getComprehensiveSummary({
        demographics_data: sampleDemographics,
        vitals_data: sampleVitals,
        labs_data: sampleLabs,
        ae_data: sampleAE,
        indication: "hypertension",
        phase: "Phase 3"
      });
      setComprehensiveData(result);
    } catch (err: any) {
      setError(err.message || "Failed to load comprehensive summary");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Study Dashboard</h1>
          <p className="text-muted-foreground mt-2">
            Executive overview, cross-domain analytics, and comprehensive study summary
          </p>
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
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="dashboard">
            <LayoutDashboard className="mr-2 h-4 w-4" />
            Executive Dashboard
          </TabsTrigger>
          <TabsTrigger value="correlations">
            <Network className="mr-2 h-4 w-4" />
            Correlations
          </TabsTrigger>
          <TabsTrigger value="comprehensive">
            <FileText className="mr-2 h-4 w-4" />
            Comprehensive
          </TabsTrigger>
        </TabsList>

        {/* Executive Dashboard Tab */}
        <TabsContent value="dashboard" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Trial Executive Dashboard</CardTitle>
              <CardDescription>
                Key performance indicators and regulatory readiness metrics
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!dashboardData ? (
                <div className="text-center py-12">
                  <LayoutDashboard className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <Button onClick={loadTrialDashboard} disabled={loading}>
                    {loading ? "Loading..." : "Load Executive Dashboard"}
                  </Button>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Executive KPIs */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Study Status</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <Badge className="text-lg" variant="default">{dashboardData.study_status || "Active"}</Badge>
                        <p className="text-sm text-muted-foreground mt-2">{dashboardData.indication} - {dashboardData.phase}</p>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Enrollment</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold">{dashboardData.total_subjects || 0}</div>
                        <p className="text-sm text-muted-foreground mt-2">
                          {dashboardData.enrollment_rate?.toFixed(1)}% of target
                        </p>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Data Completeness</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold">{(dashboardData.data_completeness * 100)?.toFixed(1)}%</div>
                        <Badge className="mt-2" variant={dashboardData.data_completeness > 0.95 ? "default" : "secondary"}>
                          {dashboardData.data_completeness > 0.95 ? "Excellent" : "Good"}
                        </Badge>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Quality Score</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold">{(dashboardData.overall_quality * 100)?.toFixed(1)}%</div>
                        <Badge className="mt-2" variant={dashboardData.overall_quality > 0.85 ? "default" : "secondary"}>
                          {dashboardData.quality_grade}
                        </Badge>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Domain-Specific Metrics */}
                  <div>
                    <h3 className="text-lg font-semibold mb-4">Domain Performance</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                      <Card>
                        <CardHeader>
                          <CardTitle className="text-md">Demographics</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-2">
                            <div className="flex justify-between">
                              <span className="text-sm text-muted-foreground">Records:</span>
                              <span className="font-semibold">{dashboardData.demographics_records || 0}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-sm text-muted-foreground">Complete:</span>
                              <span className="font-semibold">{(dashboardData.demographics_completeness * 100)?.toFixed(0)}%</span>
                            </div>
                            <Badge variant="outline">Balanced</Badge>
                          </div>
                        </CardContent>
                      </Card>

                      <Card>
                        <CardHeader>
                          <CardTitle className="text-md">Vitals</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-2">
                            <div className="flex justify-between">
                              <span className="text-sm text-muted-foreground">Records:</span>
                              <span className="font-semibold">{dashboardData.vitals_records || 0}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-sm text-muted-foreground">Complete:</span>
                              <span className="font-semibold">{(dashboardData.vitals_completeness * 100)?.toFixed(0)}%</span>
                            </div>
                            <Badge variant="outline">Normal Range</Badge>
                          </div>
                        </CardContent>
                      </Card>

                      <Card>
                        <CardHeader>
                          <CardTitle className="text-md">Labs</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-2">
                            <div className="flex justify-between">
                              <span className="text-sm text-muted-foreground">Records:</span>
                              <span className="font-semibold">{dashboardData.labs_records || 0}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-sm text-muted-foreground">Abnormal:</span>
                              <span className="font-semibold text-orange-600">{dashboardData.labs_abnormal_count || 0}</span>
                            </div>
                            <Badge variant={dashboardData.safety_signals_detected ? "destructive" : "outline"}>
                              {dashboardData.safety_signals_detected ? "Signals" : "No Signals"}
                            </Badge>
                          </div>
                        </CardContent>
                      </Card>

                      <Card>
                        <CardHeader>
                          <CardTitle className="text-md">Adverse Events</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-2">
                            <div className="flex justify-between">
                              <span className="text-sm text-muted-foreground">Total AEs:</span>
                              <span className="font-semibold">{dashboardData.total_aes || 0}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-sm text-muted-foreground">Serious:</span>
                              <span className="font-semibold text-red-600">{dashboardData.serious_aes || 0}</span>
                            </div>
                            <Badge variant="outline">Monitored</Badge>
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  </div>

                  {/* Regulatory Readiness */}
                  <div>
                    <h3 className="text-lg font-semibold mb-4">Regulatory Readiness</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <Card>
                        <CardHeader>
                          <CardTitle className="text-md">CDISC Compliance</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="text-2xl font-bold">{(dashboardData.cdisc_compliance * 100)?.toFixed(0)}%</div>
                          <Badge className="mt-2" variant={dashboardData.cdisc_compliance === 1.0 ? "default" : "secondary"}>
                            {dashboardData.cdisc_compliance === 1.0 ? "Compliant" : "In Progress"}
                          </Badge>
                        </CardContent>
                      </Card>

                      <Card>
                        <CardHeader>
                          <CardTitle className="text-md">CSR Ready</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <Badge className="text-lg" variant={dashboardData.csr_ready ? "default" : "secondary"}>
                            {dashboardData.csr_ready ? "Ready" : "Pending"}
                          </Badge>
                          <p className="text-sm text-muted-foreground mt-2">
                            {dashboardData.csr_pending_items || 0} items pending
                          </p>
                        </CardContent>
                      </Card>

                      <Card>
                        <CardHeader>
                          <CardTitle className="text-md">AACT Similarity</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="text-2xl font-bold">{(dashboardData.aact_similarity * 100)?.toFixed(1)}%</div>
                          <Badge className="mt-2" variant={dashboardData.aact_similarity > 0.9 ? "default" : "secondary"}>
                            Real-World Match
                          </Badge>
                        </CardContent>
                      </Card>
                    </div>
                  </div>

                  {/* Risk Flags */}
                  {dashboardData.risk_flags && dashboardData.risk_flags.length > 0 && (
                    <Alert variant="destructive">
                      <AlertDescription>
                        <strong>Risk Flags Detected:</strong>
                        <ul className="list-disc list-inside mt-2">
                          {dashboardData.risk_flags.map((flag: string, idx: number) => (
                            <li key={idx}>{flag}</li>
                          ))}
                        </ul>
                      </AlertDescription>
                    </Alert>
                  )}

                  {/* Radar Chart for Domain Quality */}
                  {dashboardData.domain_quality && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">Domain Quality Overview</h3>
                      <ResponsiveContainer width="100%" height={400}>
                        <RadarChart data={dashboardData.domain_quality}>
                          <PolarGrid />
                          <PolarAngleAxis dataKey="domain" />
                          <PolarRadiusAxis angle={90} domain={[0, 1]} />
                          <Radar name="Quality Score" dataKey="quality" stroke="#8884d8" fill="#8884d8" fillOpacity={0.6} />
                          <Tooltip />
                          <Legend />
                        </RadarChart>
                      </ResponsiveContainer>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Cross-Domain Correlations Tab */}
        <TabsContent value="correlations" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Cross-Domain Correlations</CardTitle>
              <CardDescription>
                Analyze relationships between demographics, vitals, labs, and adverse events
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!correlationsData ? (
                <div className="text-center py-12">
                  <Network className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <Button onClick={loadCrossDomainCorrelations} disabled={loading}>
                    {loading ? "Loading..." : "Load Correlations Analysis"}
                  </Button>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Correlation Summary */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Strong Correlations</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold">{correlationsData.strong_correlations || 0}</div>
                        <p className="text-sm text-muted-foreground mt-2">|r| ≥ 0.7</p>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Moderate Correlations</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold">{correlationsData.moderate_correlations || 0}</div>
                        <p className="text-sm text-muted-foreground mt-2">0.3 ≤ |r| < 0.7</p>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Weak Correlations</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold">{correlationsData.weak_correlations || 0}</div>
                        <p className="text-sm text-muted-foreground mt-2">|r| < 0.3</p>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Key Correlations Table */}
                  {correlationsData.key_correlations && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">Key Cross-Domain Correlations</h3>
                      <div className="overflow-x-auto">
                        <table className="w-full border-collapse border border-gray-200">
                          <thead>
                            <tr className="bg-gray-50">
                              <th className="border border-gray-200 px-4 py-2 text-left">Variable 1</th>
                              <th className="border border-gray-200 px-4 py-2 text-left">Variable 2</th>
                              <th className="border border-gray-200 px-4 py-2 text-center">Correlation</th>
                              <th className="border border-gray-200 px-4 py-2 text-center">p-value</th>
                              <th className="border border-gray-200 px-4 py-2 text-center">Strength</th>
                            </tr>
                          </thead>
                          <tbody>
                            {correlationsData.key_correlations.slice(0, 10).map((corr: any, idx: number) => (
                              <tr key={idx}>
                                <td className="border border-gray-200 px-4 py-2">{corr.var1}</td>
                                <td className="border border-gray-200 px-4 py-2">{corr.var2}</td>
                                <td className="border border-gray-200 px-4 py-2 text-center font-semibold">
                                  {corr.correlation?.toFixed(3)}
                                </td>
                                <td className="border border-gray-200 px-4 py-2 text-center">{corr.p_value?.toFixed(4)}</td>
                                <td className="border border-gray-200 px-4 py-2 text-center">
                                  <Badge variant={Math.abs(corr.correlation) >= 0.7 ? "default" : "secondary"}>
                                    {corr.strength}
                                  </Badge>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Scatter Plot Example */}
                  {correlationsData.scatter_data && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">Age vs. Systolic BP Correlation</h3>
                      <ResponsiveContainer width="100%" height={400}>
                        <ScatterChart>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="age" name="Age" label={{ value: "Age (years)", position: "insideBottom", offset: -5 }} />
                          <YAxis dataKey="sbp" name="Systolic BP" label={{ value: "Systolic BP (mmHg)", angle: -90, position: "insideLeft" }} />
                          <Tooltip cursor={{ strokeDasharray: "3 3" }} />
                          <Legend />
                          <Scatter name="Subjects" data={correlationsData.scatter_data} fill="#8884d8" />
                        </ScatterChart>
                      </ResponsiveContainer>
                    </div>
                  )}

                  {/* Interpretation */}
                  {correlationsData.interpretation && (
                    <Alert>
                      <AlertDescription>{correlationsData.interpretation}</AlertDescription>
                    </Alert>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Comprehensive Summary Tab */}
        <TabsContent value="comprehensive" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Comprehensive Study Summary</CardTitle>
              <CardDescription>
                Multi-domain integrated analysis with AACT benchmarking
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!comprehensiveData ? (
                <div className="text-center py-12">
                  <FileText className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <Button onClick={loadComprehensiveSummary} disabled={loading}>
                    {loading ? "Loading..." : "Load Comprehensive Summary"}
                  </Button>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Study Overview */}
                  <div className="bg-gray-50 p-6 rounded-lg">
                    <h3 className="text-xl font-bold mb-4">Study Overview</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-muted-foreground">Indication</p>
                        <p className="text-lg font-semibold">{comprehensiveData.indication}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Phase</p>
                        <p className="text-lg font-semibold">{comprehensiveData.phase}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Total Subjects</p>
                        <p className="text-lg font-semibold">{comprehensiveData.total_subjects}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Treatment Arms</p>
                        <p className="text-lg font-semibold">{comprehensiveData.treatment_arms?.join(", ")}</p>
                      </div>
                    </div>
                  </div>

                  {/* Efficacy Summary */}
                  {comprehensiveData.efficacy_summary && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">Efficacy Summary</h3>
                      <Card>
                        <CardContent className="pt-6 space-y-2">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Primary Endpoint:</span>
                            <span className="font-semibold">{comprehensiveData.efficacy_summary.primary_endpoint}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Treatment Effect:</span>
                            <span className="font-semibold">{comprehensiveData.efficacy_summary.treatment_effect?.toFixed(2)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">p-value:</span>
                            <span className="font-semibold">{comprehensiveData.efficacy_summary.p_value?.toFixed(4)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Significant:</span>
                            <Badge variant={comprehensiveData.efficacy_summary.significant ? "default" : "secondary"}>
                              {comprehensiveData.efficacy_summary.significant ? "Yes" : "No"}
                            </Badge>
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  )}

                  {/* Safety Summary */}
                  {comprehensiveData.safety_summary && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">Safety Summary</h3>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <Card>
                          <CardHeader>
                            <CardTitle className="text-md">Total AEs</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="text-2xl font-bold">{comprehensiveData.safety_summary.total_aes}</div>
                            <p className="text-sm text-muted-foreground mt-2">
                              {(comprehensiveData.safety_summary.ae_incidence_rate * 100).toFixed(1)}% incidence
                            </p>
                          </CardContent>
                        </Card>

                        <Card>
                          <CardHeader>
                            <CardTitle className="text-md">Serious AEs</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="text-2xl font-bold text-red-600">{comprehensiveData.safety_summary.serious_aes}</div>
                            <Badge variant="destructive" className="mt-2">SAE</Badge>
                          </CardContent>
                        </Card>

                        <Card>
                          <CardHeader>
                            <CardTitle className="text-md">Safety Signals</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <Badge className="text-lg" variant={comprehensiveData.safety_summary.safety_signals_detected ? "destructive" : "default"}>
                              {comprehensiveData.safety_summary.safety_signals_detected ? "Detected" : "None"}
                            </Badge>
                          </CardContent>
                        </Card>
                      </div>
                    </div>
                  )}

                  {/* AACT Benchmark Comparison */}
                  {comprehensiveData.aact_benchmark && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">AACT Benchmark Comparison</h3>
                      <Card>
                        <CardContent className="pt-6 space-y-2">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Overall Similarity:</span>
                            <span className="text-2xl font-bold">{(comprehensiveData.aact_benchmark.similarity * 100).toFixed(1)}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Enrollment Match:</span>
                            <Badge variant={comprehensiveData.aact_benchmark.enrollment_within_range ? "default" : "secondary"}>
                              {comprehensiveData.aact_benchmark.enrollment_within_range ? "Within Range" : "Outside Range"}
                            </Badge>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Effect Size Match:</span>
                            <Badge variant={comprehensiveData.aact_benchmark.effect_within_range ? "default" : "secondary"}>
                              {comprehensiveData.aact_benchmark.effect_within_range ? "Typical" : "Atypical"}
                            </Badge>
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  )}

                  {/* Executive Summary */}
                  {comprehensiveData.executive_summary && (
                    <Alert>
                      <AlertDescription>
                        <div dangerouslySetInnerHTML={{ __html: comprehensiveData.executive_summary }} />
                      </AlertDescription>
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
