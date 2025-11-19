import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { trialPlanningApi } from "@/services/api";
import { useData } from "@/contexts/DataContext";
import type {
  VirtualControlArmResponse,
  AugmentControlArmResponse,
  WhatIfEnrollmentResponse,
  WhatIfPatientMixResponse,
  FeasibilityAssessmentResponse,
} from "@/types";
import {
  FlaskConical,
  Users,
  TrendingUp,
  Activity,
  Target,
  Loader2,
  CheckCircle,
  AlertCircle,
  BarChart3,
  Lightbulb,
} from "lucide-react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from "recharts";

export function TrialPlanning() {
  const { pilotData } = useData();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("virtual-control");

  // State for each feature
  const [virtualControlResult, setVirtualControlResult] = useState<VirtualControlArmResponse | null>(null);
  const [augmentResult, setAugmentResult] = useState<AugmentControlArmResponse | null>(null);
  const [enrollmentResult, setEnrollmentResult] = useState<WhatIfEnrollmentResponse | null>(null);
  const [patientMixResult, setPatientMixResult] = useState<WhatIfPatientMixResponse | null>(null);
  const [feasibilityResult, setFeasibilityResult] = useState<FeasibilityAssessmentResponse | null>(null);

  // Form states
  const [vcaParams, setVcaParams] = useState({
    n_control: 50,
    target_effect: -5.0,
    baseline_mean_sbp: 140,
    baseline_std_sbp: 10,
  });

  const [augmentParams, setAugmentParams] = useState({
    n_real: 20,
    n_synthetic: 30,
    target_effect: -5.0,
  });

  const [enrollmentParams, setEnrollmentParams] = useState({
    baseline_n: 50,
    scenarios: [25, 50, 75, 100, 150, 200],
    target_effect: -5.0,
  });

  const [patientMixParams, setPatientMixParams] = useState({
    n_per_scenario: 50,
    baseline_sbp_scenarios: [130, 140, 150, 160],
    target_effect: -5.0,
  });

  const [feasibilityParams, setFeasibilityParams] = useState({
    target_effect: -5.0,
    expected_std: 10,
    alpha: 0.05,
    power: 0.8,
    allocation_ratio: 1.0,
  });

  // Virtual Control Arm
  const generateVirtualControl = async () => {
    if (!pilotData) {
      setError("No pilot data available. Please wait for data to load.");
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      const result = await trialPlanningApi.createVirtualControlArm({
        historical_data: pilotData,
        n_control: vcaParams.n_control,
        target_effect: vcaParams.target_effect,
        baseline_mean_sbp: vcaParams.baseline_mean_sbp,
        baseline_std_sbp: vcaParams.baseline_std_sbp,
        seed: 42,
      });
      setVirtualControlResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate virtual control arm");
    } finally {
      setIsLoading(false);
    }
  };

  // Augment Control Arm
  const augmentControlArm = async () => {
    if (!pilotData) {
      setError("No pilot data available. Please wait for data to load.");
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      const result = await trialPlanningApi.augmentControlArm({
        real_control_data: pilotData.filter(r => r.TreatmentArm === "Placebo").slice(0, augmentParams.n_real),
        n_synthetic: augmentParams.n_synthetic,
        target_effect: augmentParams.target_effect,
        seed: 42,
      });
      setAugmentResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to augment control arm");
    } finally {
      setIsLoading(false);
    }
  };

  // What-If: Enrollment
  const runEnrollmentWhatIf = async () => {
    if (!pilotData) {
      setError("No pilot data available. Please wait for data to load.");
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      const result = await trialPlanningApi.whatIfEnrollment({
        historical_data: pilotData,
        baseline_n: enrollmentParams.baseline_n,
        scenarios: enrollmentParams.scenarios,
        target_effect: enrollmentParams.target_effect,
        seed: 42,
      });
      setEnrollmentResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run enrollment what-if");
    } finally {
      setIsLoading(false);
    }
  };

  // What-If: Patient Mix
  const runPatientMixWhatIf = async () => {
    if (!pilotData) {
      setError("No pilot data available. Please wait for data to load.");
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      const result = await trialPlanningApi.whatIfPatientMix({
        historical_data: pilotData,
        n_per_scenario: patientMixParams.n_per_scenario,
        baseline_sbp_scenarios: patientMixParams.baseline_sbp_scenarios,
        target_effect: patientMixParams.target_effect,
        seed: 42,
      });
      setPatientMixResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run patient mix what-if");
    } finally {
      setIsLoading(false);
    }
  };

  // Feasibility Assessment
  const assessFeasibility = async () => {
    setIsLoading(true);
    setError("");

    try {
      const result = await trialPlanningApi.assessFeasibility({
        target_effect: feasibilityParams.target_effect,
        expected_std: feasibilityParams.expected_std,
        alpha: feasibilityParams.alpha,
        power: feasibilityParams.power,
        allocation_ratio: feasibilityParams.allocation_ratio,
      });
      setFeasibilityResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to assess feasibility");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <FlaskConical className="h-8 w-8" />
          Trial Planning & Simulation
        </h1>
        <p className="text-muted-foreground mt-2">
          Use synthetic data to plan trials, generate virtual control arms, and run what-if scenarios
        </p>
      </div>

      {/* Info Banner */}
      <Card className="border-blue-200 bg-blue-50 dark:bg-blue-950">
        <CardContent className="pt-6">
          <div className="flex gap-3">
            <Lightbulb className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="font-medium text-blue-900 dark:text-blue-100">
                Industry-Inspired Trial Planning Features
              </p>
              <p className="text-sm text-blue-800 dark:text-blue-200">
                Similar to Medidata's Synthetic Control Arms product, these tools help you reduce placebo patients,
                estimate trial feasibility, and optimize study design using historical data and synthetic generation.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {error && (
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <p>{error}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="virtual-control">Virtual Control</TabsTrigger>
          <TabsTrigger value="augment">Augment Arm</TabsTrigger>
          <TabsTrigger value="enrollment">Enrollment</TabsTrigger>
          <TabsTrigger value="patient-mix">Patient Mix</TabsTrigger>
          <TabsTrigger value="feasibility">Feasibility</TabsTrigger>
        </TabsList>

        {/* ====== VIRTUAL CONTROL ARM ====== */}
        <TabsContent value="virtual-control" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Generate Virtual Control Arm
              </CardTitle>
              <CardDescription>
                Create a fully synthetic control arm from historical data to replace or supplement real placebo patients
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="vca-n">Control Arm Size (N)</Label>
                  <Input
                    id="vca-n"
                    type="number"
                    value={vcaParams.n_control}
                    onChange={(e) => setVcaParams({ ...vcaParams, n_control: parseInt(e.target.value) })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="vca-effect">Target Effect (mmHg)</Label>
                  <Input
                    id="vca-effect"
                    type="number"
                    step="0.1"
                    value={vcaParams.target_effect}
                    onChange={(e) => setVcaParams({ ...vcaParams, target_effect: parseFloat(e.target.value) })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="vca-mean">Baseline Mean SBP</Label>
                  <Input
                    id="vca-mean"
                    type="number"
                    value={vcaParams.baseline_mean_sbp}
                    onChange={(e) => setVcaParams({ ...vcaParams, baseline_mean_sbp: parseFloat(e.target.value) })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="vca-std">Baseline Std Dev</Label>
                  <Input
                    id="vca-std"
                    type="number"
                    value={vcaParams.baseline_std_sbp}
                    onChange={(e) => setVcaParams({ ...vcaParams, baseline_std_sbp: parseFloat(e.target.value) })}
                  />
                </div>
              </div>

              <Button onClick={generateVirtualControl} disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <FlaskConical className="mr-2 h-4 w-4" />
                    Generate Virtual Control
                  </>
                )}
              </Button>

              {virtualControlResult && (
                <div className="mt-6 space-y-4">
                  <div className="flex items-center gap-2 text-green-600">
                    <CheckCircle className="h-5 w-5" />
                    <span className="font-medium">Virtual control arm generated successfully!</span>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <Card>
                      <CardContent className="pt-6 text-center">
                        <p className="text-sm text-muted-foreground">Total Records</p>
                        <p className="text-3xl font-bold">{virtualControlResult.virtual_control_data.length}</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="pt-6 text-center">
                        <p className="text-sm text-muted-foreground">Mean SBP</p>
                        <p className="text-3xl font-bold">
                          {virtualControlResult.summary.virtual_control.mean_sbp.toFixed(1)}
                        </p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="pt-6 text-center">
                        <p className="text-sm text-muted-foreground">Quality Score</p>
                        <p className="text-3xl font-bold text-green-600">
                          {(virtualControlResult.quality_metrics.similarity_score * 100).toFixed(0)}%
                        </p>
                      </CardContent>
                    </Card>
                  </div>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Quality Metrics</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Wasserstein Distance:</span>
                          <span className="font-medium">
                            {virtualControlResult.quality_metrics.wasserstein_distance.toFixed(2)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Correlation Preservation:</span>
                          <span className="font-medium">
                            {(virtualControlResult.quality_metrics.correlation_preservation * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <div className="p-4 bg-blue-50 dark:bg-blue-950 rounded-lg border border-blue-200">
                    <p className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-1">Use Case</p>
                    <p className="text-sm text-blue-800 dark:text-blue-200">
                      {virtualControlResult.use_case}
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ====== AUGMENT CONTROL ARM ====== */}
        <TabsContent value="augment" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Augment Small Control Arm
              </CardTitle>
              <CardDescription>
                Combine a small real control group with synthetic patients to increase statistical power
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="aug-real">Real Control (N)</Label>
                  <Input
                    id="aug-real"
                    type="number"
                    value={augmentParams.n_real}
                    onChange={(e) => setAugmentParams({ ...augmentParams, n_real: parseInt(e.target.value) })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="aug-synth">Synthetic Add (N)</Label>
                  <Input
                    id="aug-synth"
                    type="number"
                    value={augmentParams.n_synthetic}
                    onChange={(e) => setAugmentParams({ ...augmentParams, n_synthetic: parseInt(e.target.value) })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="aug-effect">Target Effect</Label>
                  <Input
                    id="aug-effect"
                    type="number"
                    step="0.1"
                    value={augmentParams.target_effect}
                    onChange={(e) => setAugmentParams({ ...augmentParams, target_effect: parseFloat(e.target.value) })}
                  />
                </div>
              </div>

              <Button onClick={augmentControlArm} disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Augmenting...
                  </>
                ) : (
                  <>
                    <Activity className="mr-2 h-4 w-4" />
                    Augment Control Arm
                  </>
                )}
              </Button>

              {augmentResult && (
                <div className="mt-6 space-y-4">
                  <div className="flex items-center gap-2 text-green-600">
                    <CheckCircle className="h-5 w-5" />
                    <span className="font-medium">Control arm augmented successfully!</span>
                  </div>

                  <div className="grid grid-cols-4 gap-4">
                    <Card>
                      <CardContent className="pt-6 text-center">
                        <p className="text-sm text-muted-foreground">Real Patients</p>
                        <p className="text-3xl font-bold text-blue-600">{augmentResult.summary.n_real}</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="pt-6 text-center">
                        <p className="text-sm text-muted-foreground">Synthetic Added</p>
                        <p className="text-3xl font-bold text-purple-600">{augmentResult.summary.n_synthetic}</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="pt-6 text-center">
                        <p className="text-sm text-muted-foreground">Total Combined</p>
                        <p className="text-3xl font-bold text-green-600">{augmentResult.summary.n_combined}</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="pt-6 text-center">
                        <p className="text-sm text-muted-foreground">Similarity</p>
                        <p className="text-3xl font-bold">
                          {(augmentResult.quality_metrics.similarity_score * 100).toFixed(0)}%
                        </p>
                      </CardContent>
                    </Card>
                  </div>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Before vs After Augmentation</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="font-medium mb-2">Real Only (N={augmentResult.summary.n_real})</p>
                          <div className="space-y-1">
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Mean SBP:</span>
                              <span>{augmentResult.summary.real_only.mean_sbp.toFixed(1)} mmHg</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Std Dev:</span>
                              <span>{augmentResult.summary.real_only.std_sbp.toFixed(1)} mmHg</span>
                            </div>
                          </div>
                        </div>
                        <div>
                          <p className="font-medium mb-2">Combined (N={augmentResult.summary.n_combined})</p>
                          <div className="space-y-1">
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Mean SBP:</span>
                              <span>{augmentResult.summary.augmented.mean_sbp.toFixed(1)} mmHg</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Std Dev:</span>
                              <span>{augmentResult.summary.augmented.std_sbp.toFixed(1)} mmHg</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <div className="p-4 bg-green-50 dark:bg-green-950 rounded-lg border border-green-200">
                    <p className="text-sm font-medium text-green-900 dark:text-green-100 mb-1">Benefit</p>
                    <p className="text-sm text-green-800 dark:text-green-200">
                      Increased sample size from {augmentResult.summary.n_real} to {augmentResult.summary.n_combined}{" "}
                      ({((augmentResult.summary.n_combined / augmentResult.summary.n_real - 1) * 100).toFixed(0)}%
                      increase) while maintaining statistical properties. This improves power without recruiting more
                      placebo patients.
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ====== ENROLLMENT WHAT-IF ====== */}
        <TabsContent value="enrollment" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                What-If: Enrollment Scenarios
              </CardTitle>
              <CardDescription>
                See how different sample sizes affect statistical power and trial outcomes
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="enroll-base">Baseline N per Arm</Label>
                  <Input
                    id="enroll-base"
                    type="number"
                    value={enrollmentParams.baseline_n}
                    onChange={(e) => setEnrollmentParams({ ...enrollmentParams, baseline_n: parseInt(e.target.value) })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="enroll-effect">Target Effect</Label>
                  <Input
                    id="enroll-effect"
                    type="number"
                    step="0.1"
                    value={enrollmentParams.target_effect}
                    onChange={(e) =>
                      setEnrollmentParams({ ...enrollmentParams, target_effect: parseFloat(e.target.value) })
                    }
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Scenarios to Test (comma-separated N values)</Label>
                <Input
                  value={enrollmentParams.scenarios.join(", ")}
                  onChange={(e) =>
                    setEnrollmentParams({
                      ...enrollmentParams,
                      scenarios: e.target.value.split(",").map((s) => parseInt(s.trim())),
                    })
                  }
                  placeholder="25, 50, 75, 100, 150, 200"
                />
              </div>

              <Button onClick={runEnrollmentWhatIf} disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Running Scenarios...
                  </>
                ) : (
                  <>
                    <BarChart3 className="mr-2 h-4 w-4" />
                    Run Enrollment What-If
                  </>
                )}
              </Button>

              {enrollmentResult && (
                <div className="mt-6 space-y-4">
                  <div className="flex items-center gap-2 text-green-600">
                    <CheckCircle className="h-5 w-5" />
                    <span className="font-medium">
                      Analyzed {enrollmentResult.scenarios.length} enrollment scenarios
                    </span>
                  </div>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Power by Sample Size</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={enrollmentResult.scenarios}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="n_per_arm" label={{ value: "N per Arm", position: "insideBottom", offset: -5 }} />
                          <YAxis label={{ value: "Statistical Power", angle: -90, position: "insideLeft" }} domain={[0, 1]} />
                          <Tooltip />
                          <Legend />
                          <Line
                            type="monotone"
                            dataKey="power"
                            stroke="#10b981"
                            strokeWidth={2}
                            dot={{ r: 5 }}
                            name="Power"
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Scenario Details</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {enrollmentResult.scenarios.map((scenario, idx) => (
                          <div
                            key={idx}
                            className="flex items-center justify-between p-3 border rounded-lg"
                          >
                            <div className="flex items-center gap-4">
                              <div>
                                <p className="font-medium">N = {scenario.n_per_arm} per arm</p>
                                <p className="text-sm text-muted-foreground">
                                  Total: {scenario.n_per_arm * 2} patients
                                </p>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="flex items-center gap-2">
                                <Badge variant={scenario.power >= 0.8 ? "default" : "secondary"}>
                                  Power: {(scenario.power * 100).toFixed(1)}%
                                </Badge>
                                {scenario.significant && (
                                  <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                                    p &lt; 0.05
                                  </Badge>
                                )}
                              </div>
                              <p className="text-xs text-muted-foreground mt-1">
                                p = {scenario.p_value.toFixed(4)}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  <div className="p-4 bg-blue-50 dark:bg-blue-950 rounded-lg border border-blue-200">
                    <p className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-1">Recommendation</p>
                    <p className="text-sm text-blue-800 dark:text-blue-200">{enrollmentResult.recommendation}</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ====== PATIENT MIX WHAT-IF ====== */}
        <TabsContent value="patient-mix" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                What-If: Patient Mix Scenarios
              </CardTitle>
              <CardDescription>
                See how different baseline patient characteristics affect trial outcomes
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="mix-n">N per Scenario</Label>
                  <Input
                    id="mix-n"
                    type="number"
                    value={patientMixParams.n_per_scenario}
                    onChange={(e) =>
                      setPatientMixParams({ ...patientMixParams, n_per_scenario: parseInt(e.target.value) })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="mix-effect">Target Effect</Label>
                  <Input
                    id="mix-effect"
                    type="number"
                    step="0.1"
                    value={patientMixParams.target_effect}
                    onChange={(e) =>
                      setPatientMixParams({ ...patientMixParams, target_effect: parseFloat(e.target.value) })
                    }
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Baseline SBP Scenarios (comma-separated values)</Label>
                <Input
                  value={patientMixParams.baseline_sbp_scenarios.join(", ")}
                  onChange={(e) =>
                    setPatientMixParams({
                      ...patientMixParams,
                      baseline_sbp_scenarios: e.target.value.split(",").map((s) => parseFloat(s.trim())),
                    })
                  }
                  placeholder="130, 140, 150, 160"
                />
                <p className="text-xs text-muted-foreground">
                  Test different patient populations (e.g., 130 = mild hypertension, 160 = severe)
                </p>
              </div>

              <Button onClick={runPatientMixWhatIf} disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Running Scenarios...
                  </>
                ) : (
                  <>
                    <BarChart3 className="mr-2 h-4 w-4" />
                    Run Patient Mix What-If
                  </>
                )}
              </Button>

              {patientMixResult && (
                <div className="mt-6 space-y-4">
                  <div className="flex items-center gap-2 text-green-600">
                    <CheckCircle className="h-5 w-5" />
                    <span className="font-medium">
                      Analyzed {patientMixResult.scenarios.length} patient mix scenarios
                    </span>
                  </div>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Treatment Effect by Baseline Severity</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={patientMixResult.scenarios}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis
                            dataKey="baseline_sbp"
                            label={{ value: "Baseline SBP (mmHg)", position: "insideBottom", offset: -5 }}
                          />
                          <YAxis
                            label={{ value: "Treatment Effect (mmHg)", angle: -90, position: "insideLeft" }}
                          />
                          <Tooltip />
                          <Legend />
                          <Bar dataKey="effect" name="Effect Size">
                            {patientMixResult.scenarios.map((entry, index) => (
                              <Cell
                                key={`cell-${index}`}
                                fill={entry.significant ? "#10b981" : "#94a3b8"}
                              />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Scenario Comparison</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {patientMixResult.scenarios.map((scenario, idx) => (
                          <div
                            key={idx}
                            className="flex items-center justify-between p-3 border rounded-lg"
                          >
                            <div>
                              <p className="font-medium">Baseline SBP: {scenario.baseline_sbp} mmHg</p>
                              <p className="text-sm text-muted-foreground">{scenario.population_type}</p>
                            </div>
                            <div className="text-right">
                              <div className="flex items-center gap-2">
                                <Badge variant={scenario.significant ? "default" : "secondary"}>
                                  Effect: {scenario.effect.toFixed(1)} mmHg
                                </Badge>
                                {scenario.significant && (
                                  <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                                    Significant
                                  </Badge>
                                )}
                              </div>
                              <p className="text-xs text-muted-foreground mt-1">
                                p = {scenario.p_value.toFixed(4)}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  <div className="p-4 bg-blue-50 dark:bg-blue-950 rounded-lg border border-blue-200">
                    <p className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-1">Insight</p>
                    <p className="text-sm text-blue-800 dark:text-blue-200">{patientMixResult.recommendation}</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ====== FEASIBILITY ASSESSMENT ====== */}
        <TabsContent value="feasibility" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                Trial Feasibility Assessment
              </CardTitle>
              <CardDescription>
                Calculate required sample size and assess trial feasibility based on effect size and power requirements
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="feas-effect">Expected Effect Size (mmHg)</Label>
                  <Input
                    id="feas-effect"
                    type="number"
                    step="0.1"
                    value={feasibilityParams.target_effect}
                    onChange={(e) =>
                      setFeasibilityParams({ ...feasibilityParams, target_effect: parseFloat(e.target.value) })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="feas-std">Expected Std Dev (mmHg)</Label>
                  <Input
                    id="feas-std"
                    type="number"
                    step="0.1"
                    value={feasibilityParams.expected_std}
                    onChange={(e) =>
                      setFeasibilityParams({ ...feasibilityParams, expected_std: parseFloat(e.target.value) })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="feas-alpha">Significance Level (α)</Label>
                  <Input
                    id="feas-alpha"
                    type="number"
                    step="0.01"
                    value={feasibilityParams.alpha}
                    onChange={(e) =>
                      setFeasibilityParams({ ...feasibilityParams, alpha: parseFloat(e.target.value) })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="feas-power">Desired Power (1-β)</Label>
                  <Input
                    id="feas-power"
                    type="number"
                    step="0.05"
                    value={feasibilityParams.power}
                    onChange={(e) =>
                      setFeasibilityParams({ ...feasibilityParams, power: parseFloat(e.target.value) })
                    }
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="feas-ratio">Allocation Ratio (Active:Control)</Label>
                <Input
                  id="feas-ratio"
                  type="number"
                  step="0.1"
                  value={feasibilityParams.allocation_ratio}
                  onChange={(e) =>
                    setFeasibilityParams({ ...feasibilityParams, allocation_ratio: parseFloat(e.target.value) })
                  }
                />
                <p className="text-xs text-muted-foreground">
                  1.0 = equal allocation, 2.0 = 2:1 (Active:Control)
                </p>
              </div>

              <Button onClick={assessFeasibility} disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Calculating...
                  </>
                ) : (
                  <>
                    <Target className="mr-2 h-4 w-4" />
                    Assess Feasibility
                  </>
                )}
              </Button>

              {feasibilityResult && (
                <div className="mt-6 space-y-4">
                  <div className="flex items-center gap-2 text-green-600">
                    <CheckCircle className="h-5 w-5" />
                    <span className="font-medium">Feasibility assessment complete</span>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <Card className="border-2 border-primary">
                      <CardContent className="pt-6 text-center">
                        <p className="text-sm text-muted-foreground mb-2">Required Sample Size</p>
                        <p className="text-5xl font-bold text-primary">{feasibilityResult.required_n_per_arm}</p>
                        <p className="text-sm text-muted-foreground mt-2">per arm</p>
                        <p className="text-lg font-semibold mt-1">
                          Total: {feasibilityResult.total_n} patients
                        </p>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardContent className="pt-6">
                        <p className="text-sm text-muted-foreground mb-3">Study Parameters</p>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Effect Size:</span>
                            <span className="font-medium">{feasibilityParams.target_effect} mmHg</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Cohen's d:</span>
                            <span className="font-medium">{feasibilityResult.effect_size_cohens_d.toFixed(3)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Power:</span>
                            <span className="font-medium">{(feasibilityParams.power * 100).toFixed(0)}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Alpha:</span>
                            <span className="font-medium">{feasibilityParams.alpha}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Allocation:</span>
                            <span className="font-medium">{feasibilityParams.allocation_ratio}:1</span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Feasibility Assessment</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="flex items-center gap-2">
                          <Badge
                            variant={feasibilityResult.feasibility === "Highly Feasible" ? "default" : "secondary"}
                            className={
                              feasibilityResult.feasibility === "Highly Feasible"
                                ? "bg-green-500"
                                : feasibilityResult.feasibility === "Feasible"
                                ? "bg-yellow-500"
                                : "bg-red-500"
                            }
                          >
                            {feasibilityResult.feasibility}
                          </Badge>
                          <span className="text-sm">
                            Based on effect size of {Math.abs(feasibilityParams.target_effect)} mmHg
                          </span>
                        </div>

                        <div className="p-3 bg-muted rounded-lg">
                          <p className="text-sm">{feasibilityResult.interpretation}</p>
                        </div>

                        <div className="space-y-2">
                          <p className="text-sm font-medium">Assumptions:</p>
                          <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
                            {feasibilityResult.assumptions.map((assumption, idx) => (
                              <li key={idx}>{assumption}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <div className="p-4 bg-green-50 dark:bg-green-950 rounded-lg border border-green-200">
                    <p className="text-sm font-medium text-green-900 dark:text-green-100 mb-1">
                      Recommendation
                    </p>
                    <p className="text-sm text-green-800 dark:text-green-200">
                      {feasibilityResult.recommendation}
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
