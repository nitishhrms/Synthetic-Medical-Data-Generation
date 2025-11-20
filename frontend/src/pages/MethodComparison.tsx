import { useState } from "react";
import { analyticsApi } from "../services/api";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Alert, AlertDescription } from "../components/ui/alert";
import { Badge } from "../components/ui/badge";
import { ScatterChart, Scatter, BarChart, Bar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { Zap, Award, Lightbulb } from "lucide-react";

export function MethodComparison() {
  const [activeTab, setActiveTab] = useState("performance");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // State for each analysis type
  const [performanceData, setPerformanceData] = useState<any>(null);
  const [qualityData, setQualityData] = useState<any>(null);
  const [recommendationsData, setRecommendationsData] = useState<any>(null);

  // Sample method performance data
  const sampleMethodsData = {
    mvn: {
      generation_time_ms: 14,
      records_generated: 400,
      quality_score: 0.87,
      aact_similarity: 0.91
    },
    bootstrap: {
      generation_time_ms: 3,
      records_generated: 400,
      quality_score: 0.92,
      aact_similarity: 0.88
    },
    rules: {
      generation_time_ms: 5,
      records_generated: 400,
      quality_score: 0.83,
      aact_similarity: 0.85
    },
    llm: {
      generation_time_ms: 2500,
      records_generated: 200,
      quality_score: 0.89,
      aact_similarity: 0.93
    }
  };

  const loadPerformanceComparison = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await analyticsApi.compareMethodPerformance(sampleMethodsData);
      setPerformanceData(result);
    } catch (err: any) {
      setError(err.message || "Failed to load performance comparison");
    } finally {
      setLoading(false);
    }
  };

  const loadQualityAggregation = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await analyticsApi.aggregateQualityScores({
        demographics_quality: 0.89,
        vitals_quality: 0.92,
        labs_quality: 0.88,
        ae_quality: 0.85,
        aact_similarity: 0.91
      });
      setQualityData(result);
    } catch (err: any) {
      setError(err.message || "Failed to aggregate quality scores");
    } finally {
      setLoading(false);
    }
  };

  const loadRecommendations = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await analyticsApi.getRecommendations({
        current_quality: 0.72,
        aact_similarity: 0.65,
        generation_method: "mvn",
        n_subjects: 50,
        indication: "hypertension",
        phase: "Phase 3"
      });
      setRecommendationsData(result);
    } catch (err: any) {
      setError(err.message || "Failed to load recommendations");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Method Comparison & Optimization</h1>
          <p className="text-muted-foreground mt-2">
            Compare generation methods, analyze quality scores, and get optimization recommendations
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
          <TabsTrigger value="performance">
            <Zap className="mr-2 h-4 w-4" />
            Performance
          </TabsTrigger>
          <TabsTrigger value="quality">
            <Award className="mr-2 h-4 w-4" />
            Quality
          </TabsTrigger>
          <TabsTrigger value="recommendations">
            <Lightbulb className="mr-2 h-4 w-4" />
            Recommendations
          </TabsTrigger>
        </TabsList>

        {/* Performance Comparison Tab */}
        <TabsContent value="performance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Generation Method Performance Comparison</CardTitle>
              <CardDescription>
                Compare MVN, Bootstrap, Rules, and LLM methods across quality, speed, and AACT similarity
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!performanceData ? (
                <div className="text-center py-12">
                  <Zap className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <Button onClick={loadPerformanceComparison} disabled={loading}>
                    {loading ? "Loading..." : "Load Performance Comparison"}
                  </Button>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Winner and Ranking */}
                  <div className="bg-gradient-to-r from-yellow-50 to-orange-50 p-6 rounded-lg border-2 border-yellow-200">
                    <h3 className="text-xl font-bold mb-2">🏆 Recommended Method</h3>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-2xl font-bold uppercase">{performanceData.recommended_method}</p>
                        <p className="text-sm text-muted-foreground mt-1">
                          Overall weighted score: {(performanceData.recommended_score * 100).toFixed(1)}%
                        </p>
                      </div>
                      <Badge className="text-lg px-4 py-2">Best Overall</Badge>
                    </div>
                  </div>

                  {/* Method Rankings */}
                  <div>
                    <h3 className="text-lg font-semibold mb-4">Method Rankings</h3>
                    <div className="space-y-2">
                      {performanceData.ranking?.map((method: any, idx: number) => (
                        <Card key={idx} className={idx === 0 ? "border-2 border-yellow-400" : ""}>
                          <CardContent className="pt-6">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-4">
                                <span className="text-3xl font-bold text-muted-foreground">#{idx + 1}</span>
                                <div>
                                  <p className="text-lg font-bold uppercase">{method.method}</p>
                                  <p className="text-sm text-muted-foreground">
                                    Weighted Score: {(method.weighted_score * 100).toFixed(1)}%
                                  </p>
                                </div>
                              </div>
                              <div className="text-right">
                                <div className="flex gap-2 mb-2">
                                  <Badge variant="outline">Q: {(method.quality_score * 100).toFixed(0)}%</Badge>
                                  <Badge variant="outline">S: {method.speed_rank}</Badge>
                                  <Badge variant="outline">A: {(method.aact_similarity * 100).toFixed(0)}%</Badge>
                                </div>
                                <p className="text-xs text-muted-foreground">{method.records_per_second?.toFixed(0)} rec/sec</p>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </div>

                  {/* Performance Metrics Comparison */}
                  <div>
                    <h3 className="text-lg font-semibold mb-4">Performance Metrics Comparison</h3>
                    <div className="overflow-x-auto">
                      <table className="w-full border-collapse border border-gray-200">
                        <thead>
                          <tr className="bg-gray-50">
                            <th className="border border-gray-200 px-4 py-2 text-left">Method</th>
                            <th className="border border-gray-200 px-4 py-2 text-center">Generation Time</th>
                            <th className="border border-gray-200 px-4 py-2 text-center">Records/sec</th>
                            <th className="border border-gray-200 px-4 py-2 text-center">Quality Score</th>
                            <th className="border border-gray-200 px-4 py-2 text-center">AACT Similarity</th>
                            <th className="border border-gray-200 px-4 py-2 text-center">Weighted Score</th>
                          </tr>
                        </thead>
                        <tbody>
                          {performanceData.method_comparison?.map((method: any, idx: number) => (
                            <tr key={idx} className={method.method === performanceData.recommended_method ? "bg-yellow-50" : ""}>
                              <td className="border border-gray-200 px-4 py-2 font-semibold uppercase">{method.method}</td>
                              <td className="border border-gray-200 px-4 py-2 text-center">{method.generation_time_ms}ms</td>
                              <td className="border border-gray-200 px-4 py-2 text-center">{method.records_per_second?.toFixed(0)}</td>
                              <td className="border border-gray-200 px-4 py-2 text-center">
                                <Badge variant={method.quality_score >= 0.85 ? "default" : "secondary"}>
                                  {(method.quality_score * 100).toFixed(1)}%
                                </Badge>
                              </td>
                              <td className="border border-gray-200 px-4 py-2 text-center">
                                {(method.aact_similarity * 100).toFixed(1)}%
                              </td>
                              <td className="border border-gray-200 px-4 py-2 text-center font-bold">
                                {(method.weighted_score * 100).toFixed(1)}%
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Quality vs Speed Scatter Plot */}
                  {performanceData.method_comparison && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">Quality vs. Speed Tradeoff</h3>
                      <ResponsiveContainer width="100%" height={400}>
                        <ScatterChart>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis
                            dataKey="records_per_second"
                            name="Speed"
                            label={{ value: "Records/Second", position: "insideBottom", offset: -5 }}
                            scale="log"
                            domain={['auto', 'auto']}
                          />
                          <YAxis
                            dataKey="quality_score"
                            name="Quality"
                            label={{ value: "Quality Score", angle: -90, position: "insideLeft" }}
                            domain={[0.8, 1.0]}
                          />
                          <Tooltip cursor={{ strokeDasharray: "3 3" }} />
                          <Legend />
                          <Scatter name="Methods" data={performanceData.method_comparison} fill="#8884d8" />
                        </ScatterChart>
                      </ResponsiveContainer>
                      <p className="text-sm text-muted-foreground text-center mt-2">
                        Top-right corner represents ideal balance of high quality and high speed
                      </p>
                    </div>
                  )}

                  {/* Radar Chart for Multi-Dimensional Comparison */}
                  {performanceData.radar_data && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">Multi-Dimensional Comparison</h3>
                      <ResponsiveContainer width="100%" height={400}>
                        <RadarChart data={performanceData.radar_data}>
                          <PolarGrid />
                          <PolarAngleAxis dataKey="metric" />
                          <PolarRadiusAxis angle={90} domain={[0, 1]} />
                          <Radar name="MVN" dataKey="mvn" stroke="#8884d8" fill="#8884d8" fillOpacity={0.3} />
                          <Radar name="Bootstrap" dataKey="bootstrap" stroke="#82ca9d" fill="#82ca9d" fillOpacity={0.3} />
                          <Radar name="Rules" dataKey="rules" stroke="#ffc658" fill="#ffc658" fillOpacity={0.3} />
                          <Radar name="LLM" dataKey="llm" stroke="#ff8042" fill="#ff8042" fillOpacity={0.3} />
                          <Tooltip />
                          <Legend />
                        </RadarChart>
                      </ResponsiveContainer>
                    </div>
                  )}

                  {/* Tradeoffs Summary */}
                  {performanceData.tradeoffs && (
                    <Alert>
                      <AlertDescription>
                        <h4 className="font-semibold mb-2">Key Tradeoffs</h4>
                        <ul className="list-disc list-inside space-y-1">
                          {performanceData.tradeoffs.map((tradeoff: string, idx: number) => (
                            <li key={idx}>{tradeoff}</li>
                          ))}
                        </ul>
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Quality Aggregation Tab */}
        <TabsContent value="quality" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Quality Score Aggregation</CardTitle>
              <CardDescription>
                Aggregate quality scores across demographics, vitals, labs, AEs, and AACT similarity
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!qualityData ? (
                <div className="text-center py-12">
                  <Award className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <Button onClick={loadQualityAggregation} disabled={loading}>
                    {loading ? "Loading..." : "Load Quality Scores"}
                  </Button>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Overall Quality Score */}
                  <div className="bg-gradient-to-r from-blue-50 to-cyan-50 p-8 rounded-lg border-2 border-blue-200 text-center">
                    <p className="text-sm text-muted-foreground mb-2">Overall Quality Score</p>
                    <p className="text-6xl font-bold">{(qualityData.overall_quality * 100).toFixed(1)}%</p>
                    <Badge className="mt-4 text-lg px-4 py-2" variant={qualityData.overall_quality >= 0.85 ? "default" : "secondary"}>
                      Grade {qualityData.quality_grade}
                    </Badge>
                    <p className="text-sm text-muted-foreground mt-2">{qualityData.interpretation}</p>
                  </div>

                  {/* Domain Scores Breakdown */}
                  <div>
                    <h3 className="text-lg font-semibold mb-4">Domain Quality Scores</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
                      {qualityData.domain_scores?.map((domain: any, idx: number) => (
                        <Card key={idx}>
                          <CardHeader>
                            <CardTitle className="text-md">{domain.domain}</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="text-3xl font-bold">{(domain.score * 100).toFixed(1)}%</div>
                            <p className="text-xs text-muted-foreground mt-2">Weight: {(domain.weight * 100).toFixed(0)}%</p>
                            <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
                              <div
                                className={`h-full ${domain.score >= 0.85 ? "bg-green-500" : domain.score >= 0.7 ? "bg-yellow-500" : "bg-red-500"}`}
                                style={{ width: `${domain.score * 100}%` }}
                              />
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </div>

                  {/* Quality Scores Bar Chart */}
                  {qualityData.domain_scores && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">Domain Quality Comparison</h3>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={qualityData.domain_scores}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="domain" />
                          <YAxis domain={[0, 1]} />
                          <Tooltip />
                          <Legend />
                          <Bar dataKey="score" fill="#82ca9d" name="Quality Score" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  )}

                  {/* Strengths and Weaknesses */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {qualityData.strengths && qualityData.strengths.length > 0 && (
                      <Card>
                        <CardHeader>
                          <CardTitle className="text-lg text-green-600">✓ Strengths</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <ul className="space-y-2">
                            {qualityData.strengths.map((strength: string, idx: number) => (
                              <li key={idx} className="flex items-start">
                                <span className="text-green-600 mr-2">•</span>
                                <span className="text-sm">{strength}</span>
                              </li>
                            ))}
                          </ul>
                        </CardContent>
                      </Card>
                    )}

                    {qualityData.weaknesses && qualityData.weaknesses.length > 0 && (
                      <Card>
                        <CardHeader>
                          <CardTitle className="text-lg text-orange-600">⚠ Areas for Improvement</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <ul className="space-y-2">
                            {qualityData.weaknesses.map((weakness: string, idx: number) => (
                              <li key={idx} className="flex items-start">
                                <span className="text-orange-600 mr-2">•</span>
                                <span className="text-sm">{weakness}</span>
                              </li>
                            ))}
                          </ul>
                        </CardContent>
                      </Card>
                    )}
                  </div>

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

        {/* Recommendations Tab */}
        <TabsContent value="recommendations" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Parameter Optimization Recommendations</CardTitle>
              <CardDescription>
                Get actionable recommendations to improve data quality and AACT similarity
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!recommendationsData ? (
                <div className="text-center py-12">
                  <Lightbulb className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <Button onClick={loadRecommendations} disabled={loading}>
                    {loading ? "Loading..." : "Load Recommendations"}
                  </Button>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Current Status */}
                  <div>
                    <h3 className="text-lg font-semibold mb-4">Current Status</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <Card>
                        <CardHeader>
                          <CardTitle className="text-md">Current Quality</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="text-3xl font-bold">{(recommendationsData.current_quality * 100).toFixed(1)}%</div>
                          <Badge className="mt-2" variant={recommendationsData.current_quality >= 0.85 ? "default" : "secondary"}>
                            {recommendationsData.current_quality >= 0.85 ? "Good" : "Needs Improvement"}
                          </Badge>
                        </CardContent>
                      </Card>

                      <Card>
                        <CardHeader>
                          <CardTitle className="text-md">AACT Similarity</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="text-3xl font-bold">{(recommendationsData.aact_similarity * 100).toFixed(1)}%</div>
                          <Badge className="mt-2" variant={recommendationsData.aact_similarity >= 0.90 ? "default" : "secondary"}>
                            {recommendationsData.aact_similarity >= 0.90 ? "Excellent" : "Can Improve"}
                          </Badge>
                        </CardContent>
                      </Card>

                      <Card>
                        <CardHeader>
                          <CardTitle className="text-md">Current Method</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <p className="text-2xl font-bold uppercase">{recommendationsData.current_method}</p>
                          <p className="text-sm text-muted-foreground mt-2">Generation method</p>
                        </CardContent>
                      </Card>
                    </div>
                  </div>

                  {/* Improvement Opportunities */}
                  {recommendationsData.improvement_opportunities && recommendationsData.improvement_opportunities.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">💡 Improvement Opportunities</h3>
                      <div className="space-y-3">
                        {recommendationsData.improvement_opportunities.map((opp: any, idx: number) => (
                          <Card key={idx} className="border-l-4 border-l-blue-500">
                            <CardContent className="pt-6">
                              <div className="flex items-start justify-between">
                                <div className="flex-1">
                                  <h4 className="font-semibold mb-2">{opp.area}</h4>
                                  <p className="text-sm text-muted-foreground mb-3">{opp.recommendation}</p>
                                  {opp.expected_improvement && (
                                    <Badge variant="outline">
                                      Expected improvement: +{(opp.expected_improvement * 100).toFixed(0)}%
                                    </Badge>
                                  )}
                                </div>
                                <Badge className="ml-4" variant={opp.priority === "high" ? "destructive" : opp.priority === "medium" ? "secondary" : "outline"}>
                                  {opp.priority} priority
                                </Badge>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Parameter Recommendations */}
                  {recommendationsData.parameter_recommendations && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">🔧 Recommended Parameter Changes</h3>
                      <div className="overflow-x-auto">
                        <table className="w-full border-collapse border border-gray-200">
                          <thead>
                            <tr className="bg-gray-50">
                              <th className="border border-gray-200 px-4 py-2 text-left">Parameter</th>
                              <th className="border border-gray-200 px-4 py-2 text-center">Current Value</th>
                              <th className="border border-gray-200 px-4 py-2 text-center">Recommended Value</th>
                              <th className="border border-gray-200 px-4 py-2 text-left">Rationale</th>
                            </tr>
                          </thead>
                          <tbody>
                            {recommendationsData.parameter_recommendations.map((param: any, idx: number) => (
                              <tr key={idx}>
                                <td className="border border-gray-200 px-4 py-2 font-medium">{param.parameter}</td>
                                <td className="border border-gray-200 px-4 py-2 text-center">{param.current_value}</td>
                                <td className="border border-gray-200 px-4 py-2 text-center">
                                  <Badge variant="default">{param.recommended_value}</Badge>
                                </td>
                                <td className="border border-gray-200 px-4 py-2 text-sm">{param.rationale}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Expected Outcomes */}
                  {recommendationsData.expected_outcomes && (
                    <Card className="bg-green-50 border-green-200">
                      <CardHeader>
                        <CardTitle className="text-lg">📈 Expected Outcomes</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-3">
                          <div className="flex justify-between items-center">
                            <span className="font-medium">Projected Quality Score:</span>
                            <div className="flex items-center gap-2">
                              <span className="text-muted-foreground">{(recommendationsData.current_quality * 100).toFixed(1)}%</span>
                              <span className="text-xl">→</span>
                              <span className="text-xl font-bold text-green-600">
                                {(recommendationsData.expected_outcomes.projected_quality * 100).toFixed(1)}%
                              </span>
                            </div>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="font-medium">Projected AACT Similarity:</span>
                            <div className="flex items-center gap-2">
                              <span className="text-muted-foreground">{(recommendationsData.aact_similarity * 100).toFixed(1)}%</span>
                              <span className="text-xl">→</span>
                              <span className="text-xl font-bold text-green-600">
                                {(recommendationsData.expected_outcomes.projected_aact_similarity * 100).toFixed(1)}%
                              </span>
                            </div>
                          </div>
                          {recommendationsData.expected_outcomes.estimated_improvement_time && (
                            <div className="flex justify-between items-center">
                              <span className="font-medium">Estimated Implementation Time:</span>
                              <Badge variant="outline">{recommendationsData.expected_outcomes.estimated_improvement_time}</Badge>
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* Next Steps */}
                  {recommendationsData.next_steps && (
                    <Alert>
                      <AlertDescription>
                        <h4 className="font-semibold mb-2">🚀 Next Steps</h4>
                        <ol className="list-decimal list-inside space-y-1">
                          {recommendationsData.next_steps.map((step: string, idx: number) => (
                            <li key={idx}>{step}</li>
                          ))}
                        </ol>
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
