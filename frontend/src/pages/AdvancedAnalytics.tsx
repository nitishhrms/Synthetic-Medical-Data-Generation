import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { analyticsApi } from "@/services/api";
import { Loader2, TrendingUp, Award, Activity, AlertCircle } from "lucide-react";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from "recharts";

export function AdvancedAnalytics() {
  const [activeTab, setActiveTab] = useState("quality");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // State for different analytics results
  const [qualityScores, setQualityScores] = useState<any>(null);
  const [aactBenchmark, setAactBenchmark] = useState<any>(null);
  const [recommendations, setRecommendations] = useState<any>(null);
  const [methodComparison, setMethodComparison] = useState<any>(null);

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

  // ============================================================================
  // Quality Scores Tab
  // ============================================================================

  const loadQualityScores = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await analyticsApi.aggregateQualityScores({
        demographics_quality: 0.89,
        vitals_quality: 0.92,
        labs_quality: 0.88,
        ae_quality: 0.85,
        aact_similarity: 0.91,
      });
      setQualityScores(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const renderQualityScores = () => {
    if (!qualityScores) {
      return (
        <div className="text-center py-12">
          <Button onClick={loadQualityScores} disabled={isLoading}>
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Loading...
              </>
            ) : (
              "Load Quality Assessment"
            )}
          </Button>
        </div>
      );
    }

    const domainData = Object.entries(qualityScores.domain_scores || {}).map(
      ([domain, data]: [string, any]) => ({
        domain: domain.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase()),
        score: data.score,
        grade: data.grade,
        status: data.status,
      })
    );

    return (
      <div className="space-y-6">
        {/* Overall Quality Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Award className="h-5 w-5" />
              Overall Quality Score
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-6">
              <div className="text-6xl font-bold text-blue-600">
                {(qualityScores.overall_quality * 100).toFixed(1)}%
              </div>
              <div>
                <Badge className="text-lg px-4 py-2 bg-green-100 text-green-800">
                  Grade {qualityScores.interpretation?.grade}
                </Badge>
                <p className="text-sm text-muted-foreground mt-2">
                  {qualityScores.interpretation?.status}
                </p>
                <p className="text-sm mt-2">{qualityScores.interpretation?.recommendation}</p>
              </div>
            </div>

            <div className="mt-6">
              <p className="text-sm font-semibold mb-2">
                Data Completeness: {(qualityScores.completeness * 100).toFixed(0)}%
              </p>
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-600 transition-all"
                  style={{ width: `${qualityScores.completeness * 100}%` }}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Domain Scores Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Quality by Domain</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={domainData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="domain" angle={-45} textAnchor="end" height={100} />
                <YAxis domain={[0, 1]} />
                <Tooltip />
                <Bar dataKey="score" fill="#3B82F6">
                  {domainData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Strengths & Weaknesses */}
        {qualityScores.interpretation && (
          <div className="grid md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-green-600">Strengths</CardTitle>
              </CardHeader>
              <CardContent>
                {qualityScores.interpretation.strengths?.length > 0 ? (
                  <ul className="space-y-2">
                    {qualityScores.interpretation.strengths.map((strength: string, i: number) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-green-600">✓</span>
                        <span className="text-sm">{strength}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-muted-foreground">No specific strengths identified</p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-orange-600">Areas for Improvement</CardTitle>
              </CardHeader>
              <CardContent>
                {qualityScores.interpretation.weaknesses?.length > 0 ? (
                  <ul className="space-y-2">
                    {qualityScores.interpretation.weaknesses.map((weakness: string, i: number) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-orange-600">!</span>
                        <span className="text-sm">{weakness}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-green-600">No significant weaknesses identified</p>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    );
  };

  // ============================================================================
  // AACT Benchmarking Tab
  // ============================================================================

  const loadAACTBenchmark = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await analyticsApi.compareStudyToAACT({
        n_subjects: 100,
        indication: "hypertension",
        phase: "Phase 3",
        treatment_effect: -5.2,
      });
      setAactBenchmark(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const renderAACTBenchmark = () => {
    if (!aactBenchmark) {
      return (
        <div className="text-center py-12">
          <Button onClick={loadAACTBenchmark} disabled={isLoading}>
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Loading...
              </>
            ) : (
              "Load AACT Benchmark"
            )}
          </Button>
        </div>
      );
    }

    const similarityPercent = (aactBenchmark.similarity_score * 100).toFixed(1);

    return (
      <div className="space-y-6">
        {/* Similarity Score */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              AACT Similarity Score
            </CardTitle>
            <CardDescription>
              Comparison with {aactBenchmark.aact_reference?.aact_database_size?.toLocaleString()} real-world trials
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-6">
              <div className="relative w-32 h-32">
                <svg className="w-full h-full transform -rotate-90">
                  <circle
                    cx="64"
                    cy="64"
                    r="56"
                    stroke="#e5e7eb"
                    strokeWidth="8"
                    fill="none"
                  />
                  <circle
                    cx="64"
                    cy="64"
                    r="56"
                    stroke="#10B981"
                    strokeWidth="8"
                    fill="none"
                    strokeDasharray={`${2 * Math.PI * 56}`}
                    strokeDashoffset={`${2 * Math.PI * 56 * (1 - aactBenchmark.similarity_score)}`}
                    strokeLinecap="round"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-2xl font-bold">{similarityPercent}%</span>
                </div>
              </div>
              <div className="flex-1">
                <p className="text-lg font-semibold text-green-600">
                  {aactBenchmark.interpretation?.overall_assessment}
                </p>
                <p className="text-sm text-muted-foreground mt-2">
                  {aactBenchmark.interpretation?.recommendation}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Enrollment Benchmark */}
        <Card>
          <CardHeader>
            <CardTitle>Enrollment Benchmark</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Your Study</p>
                <p className="text-2xl font-bold">{aactBenchmark.enrollment_benchmark?.synthetic_n}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">AACT Mean</p>
                <p className="text-2xl font-bold">
                  {aactBenchmark.enrollment_benchmark?.aact_mean?.toFixed(0)}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">AACT Median</p>
                <p className="text-2xl font-bold">
                  {aactBenchmark.enrollment_benchmark?.aact_median?.toFixed(0)}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Percentile</p>
                <p className="text-2xl font-bold text-blue-600">
                  {aactBenchmark.enrollment_benchmark?.percentile?.toFixed(1)}%
                </p>
              </div>
            </div>
            <p className="text-sm text-muted-foreground mt-4">
              {aactBenchmark.enrollment_benchmark?.interpretation}
            </p>
          </CardContent>
        </Card>

        {/* Treatment Effect Benchmark */}
        <Card>
          <CardHeader>
            <CardTitle>Treatment Effect Benchmark</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Your Effect</p>
                <p className="text-2xl font-bold">
                  {aactBenchmark.treatment_effect_benchmark?.synthetic_effect?.toFixed(1)}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">AACT Mean</p>
                <p className="text-2xl font-bold">
                  {aactBenchmark.treatment_effect_benchmark?.aact_mean?.toFixed(1)}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">AACT Median</p>
                <p className="text-2xl font-bold">
                  {aactBenchmark.treatment_effect_benchmark?.aact_median?.toFixed(1)}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Percentile</p>
                <p className="text-2xl font-bold text-blue-600">
                  {aactBenchmark.treatment_effect_benchmark?.percentile?.toFixed(1)}%
                </p>
              </div>
            </div>
            <p className="text-sm text-muted-foreground mt-4">
              {aactBenchmark.treatment_effect_benchmark?.interpretation}
            </p>
          </CardContent>
        </Card>

        {/* Reference Info */}
        {aactBenchmark.aact_reference && (
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Reference Data</CardTitle>
            </CardHeader>
            <CardContent className="text-sm">
              <div className="grid md:grid-cols-3 gap-4">
                <div>
                  <p className="text-muted-foreground">Total AACT Trials</p>
                  <p className="font-semibold">
                    {aactBenchmark.aact_reference.total_trials_in_aact?.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground">Phase-Specific Trials</p>
                  <p className="font-semibold">
                    {aactBenchmark.aact_reference.phase_trials_in_aact?.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground">Database Size</p>
                  <p className="font-semibold">
                    {aactBenchmark.aact_reference.aact_database_size?.toLocaleString()} trials
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    );
  };

  // ============================================================================
  // Recommendations Tab
  // ============================================================================

  const loadRecommendations = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await analyticsApi.getRecommendations({
        current_quality: 0.72,
        aact_similarity: 0.65,
        generation_method: "mvn",
        n_subjects: 50,
        indication: "hypertension",
        phase: "Phase 3",
      });
      setRecommendations(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const renderRecommendations = () => {
    if (!recommendations) {
      return (
        <div className="text-center py-12">
          <Button onClick={loadRecommendations} disabled={isLoading}>
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Loading...
              </>
            ) : (
              "Get Recommendations"
            )}
          </Button>
        </div>
      );
    }

    const priorityColors = {
      HIGH: "bg-red-100 text-red-800",
      MEDIUM: "bg-yellow-100 text-yellow-800",
      LOW: "bg-blue-100 text-blue-800",
    };

    return (
      <div className="space-y-6">
        {/* Current Status */}
        <Card>
          <CardHeader>
            <CardTitle>Current Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Quality Score</p>
                <p className="text-2xl font-bold">
                  {(recommendations.current_status?.quality_score * 100).toFixed(1)}%
                </p>
                <Badge className="mt-1">{recommendations.current_status?.quality_grade}</Badge>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">AACT Similarity</p>
                <p className="text-2xl font-bold">
                  {recommendations.current_status?.aact_similarity
                    ? (recommendations.current_status.aact_similarity * 100).toFixed(1) + "%"
                    : "N/A"}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Generation Method</p>
                <p className="text-xl font-bold uppercase">
                  {recommendations.current_status?.generation_method || "N/A"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Improvement Opportunities */}
        {recommendations.improvement_opportunities?.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertCircle className="h-5 w-5" />
                Improvement Opportunities
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recommendations.improvement_opportunities.map((opp: any, i: number) => (
                  <div key={i} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge className={priorityColors[opp.priority as keyof typeof priorityColors]}>
                            {opp.priority} PRIORITY
                          </Badge>
                          <span className="font-semibold">{opp.area}</span>
                        </div>
                        <p className="text-sm text-muted-foreground">{opp.issue}</p>
                        <p className="text-sm text-blue-600 mt-1">Impact: {opp.impact}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Expected Improvements */}
        {recommendations.expected_improvements && (
          <Card>
            <CardHeader>
              <CardTitle>Expected Improvements</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-semibold mb-2">Quality Score</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Current:</span>
                      <span className="font-semibold">
                        {(recommendations.expected_improvements.quality_score?.current * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Estimated:</span>
                      <span className="font-semibold text-green-600">
                        {(recommendations.expected_improvements.quality_score?.estimated * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Improvement:</span>
                      <span className="font-semibold text-blue-600">
                        +{(recommendations.expected_improvements.quality_score?.improvement * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>

                {recommendations.expected_improvements.aact_similarity?.current !== "N/A" && (
                  <div>
                    <h4 className="font-semibold mb-2">AACT Similarity</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Current:</span>
                        <span className="font-semibold">
                          {(recommendations.expected_improvements.aact_similarity?.current * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Estimated:</span>
                        <span className="font-semibold text-green-600">
                          {(recommendations.expected_improvements.aact_similarity?.estimated * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Improvement:</span>
                        <span className="font-semibold text-blue-600">
                          +{(recommendations.expected_improvements.aact_similarity?.improvement * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                <p className="text-sm">
                  <strong>Timeline:</strong> {recommendations.expected_improvements.timeline}
                </p>
                <p className="text-sm mt-1">
                  <strong>Effort:</strong>{" "}
                  <Badge variant="outline">{recommendations.expected_improvements.effort}</Badge>
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    );
  };

  // ============================================================================
  // Main Render
  // ============================================================================

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Advanced Analytics</h1>
        <p className="text-muted-foreground mt-2">
          Comprehensive quality assessment, AACT benchmarking, and optimization recommendations
        </p>
      </div>

      {error && (
        <Card className="mb-6 border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <p className="text-red-800">{error}</p>
          </CardContent>
        </Card>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="quality">Quality Scores</TabsTrigger>
          <TabsTrigger value="aact">AACT Benchmark</TabsTrigger>
          <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
        </TabsList>

        <TabsContent value="quality" className="mt-6">
          {renderQualityScores()}
        </TabsContent>

        <TabsContent value="aact" className="mt-6">
          {renderAACTBenchmark()}
        </TabsContent>

        <TabsContent value="recommendations" className="mt-6">
          {renderRecommendations()}
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default AdvancedAnalytics;
