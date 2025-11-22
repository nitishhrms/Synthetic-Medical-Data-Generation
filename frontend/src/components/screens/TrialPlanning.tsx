import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { trialPlanningApi, dataGenerationApi } from "@/services/api";
import { PLANNING_TEMPLATES, type PlanningTemplate } from "@/constants/planningTemplates";
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
  ArrowRight,
  Save,
  FolderOpen,
  History,
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
  // Get data context
  const { pilotData, setPilotData, setPlanningScenario } = useData();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("virtual-control");

  // State for each feature
  const [virtualControlResult, setVirtualControlResult] = useState<VirtualControlArmResponse | null>(null);
  const [augmentResult, setAugmentResult] = useState<AugmentControlArmResponse | null>(null);
  const [enrollmentResult, setEnrollmentResult] = useState<WhatIfEnrollmentResponse | null>(null);
  const [patientMixResult, setPatientMixResult] = useState<WhatIfPatientMixResponse | null>(null);
  const [feasibilityResult, setFeasibilityResult] = useState<FeasibilityAssessmentResponse | null>(null);

  // Planning Scenario Save/Load State
  const [savedScenarios, setSavedScenarios] = useState<any[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string | null>(null);
  const [scenarioName, setScenarioName] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [isLoadingScenarios, setIsLoadingScenarios] = useState(false);

  // Load pilot data on mount
  useEffect(() => {
    if (!pilotData) {
      loadPilotData();
    }
  }, []);

  const loadPilotData = async () => {
    try {
      const data = await dataGenerationApi.getPilotData();
      setPilotData(data);
    } catch (err) {
      console.error("Failed to load pilot data:", err);
      setError("Failed to load pilot data. Please try refreshing the page.");
    }
  };

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

  // Cost/Budget Planning Parameters
  const [costParams, setCostParams] = useState({
    n_per_arm: 100, // Will be auto-filled from feasibility result
    duration_months: 24, // Trial duration
    cost_per_patient: 10000, // Cost per patient enrolled
    cost_per_visit: 500, // Cost per patient visit
    visits_per_patient: 10, // Number of visits per patient
    num_sites: 10, // Number of clinical sites
    cost_per_site: 50000, // Setup cost per site
    overhead_monthly: 25000, // Monthly overhead (staff, admin, etc.)
    monitoring_cost: 100000, // Data monitoring and safety costs
    regulatory_cost: 150000, // Regulatory filing and compliance costs
  });

  const [costEstimate, setCostEstimate] = useState<any>(null);

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
      const message = err instanceof Error && err.message.includes("404")
        ? "⚠️ Augment Control Arm feature is coming soon."
        : (err instanceof Error ? err.message : "Failed to augment control arm");
      setError(message);
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
        baseline_data: pilotData,
        enrollment_sizes: enrollmentParams.scenarios,
        target_effect: enrollmentParams.target_effect,
        n_simulations: 1000,
        seed: 42,
      });
      setEnrollmentResult(result);
    } catch (err) {
      const message = err instanceof Error && err.message.includes("404")
        ? "⚠️ Enrollment What-If feature is coming soon."
        : (err instanceof Error ? err.message : "Failed to run enrollment what-if");
      setError(message);
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
        baseline_data: pilotData,
        severity_shifts: patientMixParams.baseline_sbp_scenarios,
        n_per_arm: patientMixParams.n_per_scenario,
        target_effect: patientMixParams.target_effect,
        seed: 42,
      });
      setPatientMixResult(result);
    } catch (err) {
      const message = err instanceof Error && err.message.includes("404")
        ? "⚠️ Patient Mix What-If feature is coming soon."
        : (err instanceof Error ? err.message : "Failed to run patient mix what-if");
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  // Feasibility Assessment
  const assessFeasibility = async () => {
    if (!pilotData) {
      setError("No pilot data available. Please wait for data to load.");
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      const result = await trialPlanningApi.assessFeasibility({
        baseline_data: pilotData,
        target_effect: feasibilityParams.target_effect,
        power: feasibilityParams.power,
        dropout_rate: 0.10,
        alpha: feasibilityParams.alpha,
      });
      setFeasibilityResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to assess feasibility");
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Load Planning Template
   *
   * This function applies a pre-configured template to the feasibility assessment form.
   * Templates contain typical parameters for Phase 1, 2, or 3 trials based on industry
   * standards and regulatory guidelines (FDA, EMA, ICH).
   *
   * Benefits:
   * - Quick setup: No need to manually enter all parameters
   * - Best practices: Parameters based on regulatory guidance
   * - Consistency: Standardized approach across trials
   * - Education: Learn typical values for different study phases
   *
   * Workflow:
   * 1. User selects template from dropdown (Phase 1/2/3)
   * 2. Template parameters auto-fill the form
   * 3. User can review and adjust before running assessment
   * 4. Template metadata (use case, regulatory considerations) shown for reference
   *
   * @param template - The template to load (Phase 1, 2, or 3)
   */
  const loadTemplate = (template: PlanningTemplate) => {
    console.log("📋 Loading planning template:", template.name);

    // Apply template parameters to feasibility form
    setFeasibilityParams({
      target_effect: template.target_effect,
      expected_std: template.expected_std,
      alpha: template.alpha,
      power: template.power,
      allocation_ratio: template.allocation_ratio,
    });

    // Update enrollment what-if scenarios
    setEnrollmentParams({
      ...enrollmentParams,
      scenarios: template.enrollment_scenarios,
      target_effect: template.target_effect,
    });

    // Update patient mix what-if scenarios
    setPatientMixParams({
      ...patientMixParams,
      baseline_sbp_scenarios: template.baseline_sbp_scenarios,
      target_effect: template.target_effect,
    });

    // Show confirmation to user
    alert(
      `✅ Template loaded: ${template.name}\n\n` +
      `Phase: ${template.phase}\n` +
      `Use Case: ${template.use_case}\n\n` +
      `Parameters:\n` +
      `• Target effect: ${template.target_effect} mmHg\n` +
      `• Power: ${(template.power * 100).toFixed(0)}%\n` +
      `• Alpha: ${template.alpha}\n` +
      `• Dropout rate: ${(template.dropout_rate * 100).toFixed(0)}%\n\n` +
      `Review the parameters below and click "Assess Feasibility" to run the analysis.`
    );
  };

  // ============================================================================
  // Planning Scenario Save/Load Functions
  // ============================================================================

  /**
   * Load Saved Planning Scenarios on Component Mount
   *
   * This effect runs once when the component mounts and fetches all previously
   * saved planning scenarios from the database. This allows users to quickly
   * access and reload their planning work.
   */
  useEffect(() => {
    loadSavedScenarios();
  }, []);

  /**
   * Load All Saved Planning Scenarios
   *
   * Fetches the list of all saved planning scenarios from the backend database.
   * These scenarios can then be selected and loaded to restore previous planning work.
   *
   * Use Cases:
   * - Review historical trial planning decisions
   * - Compare different planning approaches
   * - Resume work on a previous feasibility assessment
   */
  const loadSavedScenarios = async () => {
    setIsLoadingScenarios(true);
    try {
      const result = await dataGenerationApi.listPlanningScenarios();
      console.log("📂 Loaded planning scenarios:", result);
      setSavedScenarios(result.datasets || []);
    } catch (err) {
      console.error("Failed to load planning scenarios:", err);
      // Don't show error to user - just log it (scenarios are optional)
    } finally {
      setIsLoadingScenarios(false);
    }
  };

  /**
   * Save Current Planning Scenario
   *
   * Saves the current feasibility assessment results and parameters to the database
   * for future reference and comparison. This creates a permanent record of trial
   * planning decisions that can be:
   * - Loaded later to resume work
   * - Compared with other scenarios
   * - Included in regulatory submissions
   * - Shared with team members
   *
   * The scenario includes:
   * - All input parameters (effect size, power, alpha, etc.)
   * - Calculated results (required N, Cohen's d, feasibility grade)
   * - Timestamp and user-provided name
   */
  const saveCurrentScenario = async () => {
    if (!feasibilityResult) {
      setError("Please run feasibility assessment first before saving");
      return;
    }

    if (!scenarioName.trim()) {
      setError("Please enter a name for this scenario");
      return;
    }

    setIsSaving(true);
    setError("");

    try {
      // Create planning scenario object with all current parameters
      const scenarioData = {
        id: `planning-${Date.now()}`,
        name: scenarioName,
        timestamp: new Date().toISOString(),
        // Input parameters
        nPerArm: feasibilityResult.required_n_per_arm || 0,
        targetEffect: feasibilityParams.target_effect,
        power: feasibilityParams.power,
        alpha: feasibilityParams.alpha,
        stdDev: feasibilityParams.expected_std,
        dropoutRate: 0.10,
        allocationRatio: feasibilityParams.allocation_ratio,
        testType: "two-sided" as const,
        // Results
        requiredN: feasibilityResult.required_n_per_arm || 0,
        cohensD: feasibilityResult.effect_size_cohens_d || 0,
        feasibilityGrade: feasibilityResult.feasibility || "Unknown",
        source: "feasibility" as const,
        // Additional context
        enrollmentScenarios: enrollmentParams.scenarios,
        patientMixScenarios: patientMixParams.baseline_sbp_scenarios,
      };

      // Save to database
      await dataGenerationApi.savePlanningScenario(
        scenarioName,
        scenarioData,
        {
          user_notes: `Saved from Trial Planning screen at ${new Date().toLocaleString()}`,
          feasibility_grade: feasibilityResult.feasibility,
        }
      );

      // Success feedback
      alert(`✅ Planning scenario saved successfully!\n\nName: ${scenarioName}\n\nYou can now load this scenario later from the "Load Saved Scenario" dropdown.`);

      // Clear scenario name input and reload scenarios list
      setScenarioName("");
      loadSavedScenarios();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save planning scenario");
    } finally {
      setIsSaving(false);
    }
  };

  /**
   * Load Planning Scenario by ID
   *
   * Retrieves a specific saved planning scenario and restores all parameters
   * to the form, allowing users to continue work on a previous feasibility assessment.
   *
   * Workflow:
   * 1. User selects a scenario from the dropdown
   * 2. Scenario data is fetched from database
   * 3. All form parameters are updated with saved values
   * 4. User can review, modify, and re-run the assessment
   */
  const loadScenarioById = async (scenarioId: number) => {
    setIsLoading(true);
    setError("");

    try {
      const result = await dataGenerationApi.loadPlanningScenarioById(scenarioId);
      console.log("📥 Loaded planning scenario:", result);

      // Extract scenario data (it's wrapped in an array from the API)
      const scenarioData = result.data && result.data[0] ? result.data[0] : result.data;

      if (scenarioData) {
        // Restore feasibility parameters
        setFeasibilityParams({
          target_effect: scenarioData.targetEffect || -5.0,
          expected_std: scenarioData.stdDev || 10,
          alpha: scenarioData.alpha || 0.05,
          power: scenarioData.power || 0.8,
          allocation_ratio: scenarioData.allocationRatio || 1.0,
        });

        // Restore enrollment scenarios if available
        if (scenarioData.enrollmentScenarios) {
          setEnrollmentParams({
            ...enrollmentParams,
            scenarios: scenarioData.enrollmentScenarios,
            target_effect: scenarioData.targetEffect || -5.0,
          });
        }

        // Restore patient mix scenarios if available
        if (scenarioData.patientMixScenarios) {
          setPatientMixParams({
            ...patientMixParams,
            baseline_sbp_scenarios: scenarioData.patientMixScenarios,
            target_effect: scenarioData.targetEffect || -5.0,
          });
        }

        // Restore results if available (so user can see previous assessment)
        if (scenarioData.requiredN) {
          setFeasibilityResult({
            required_n_per_arm: scenarioData.requiredN,
            total_n: scenarioData.requiredN * 2,
            effect_size_cohens_d: scenarioData.cohensD || 0,
            feasibility: scenarioData.feasibilityGrade || "Unknown",
            interpretation: `Restored from saved scenario: ${result.dataset_name}`,
            assumptions: [],
            recommendation: `Review the restored parameters and re-run assessment if needed.`,
          });
        }

        // Show success message
        alert(`✅ Planning scenario loaded successfully!\n\n` +
          `Scenario: ${result.dataset_name}\n` +
          `Saved: ${new Date(result.created_at).toLocaleString()}\n\n` +
          `All parameters have been restored. You can now review and modify them as needed.`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load planning scenario");
    } finally {
      setIsLoading(false);
    }
  };

  // ============================================================================
  // Cost/Budget Planning Functions
  // ============================================================================

  /**
   * Calculate Trial Cost Estimate
   *
   * Calculates comprehensive cost estimates for running a clinical trial based on:
   * - Patient enrollment costs (recruitment, screening, retention)
   * - Per-visit costs (assessments, labs, procedures)
   * - Site costs (setup, training, monitoring)
   * - Overhead costs (staff salaries, administration, facilities)
   * - Monitoring costs (data management, safety monitoring, DSMB)
   * - Regulatory costs (IND filing, regulatory submissions, compliance)
   *
   * Cost categories follow industry standards and regulatory guidelines:
   * - FDA: Guidance on Clinical Trial Costs and Budgeting
   * - CTTI: Clinical Trials Transformation Initiative cost benchmarks
   * - Industry averages from Tufts CSDD and similar research
   *
   * Output provides:
   * - Total trial cost
   * - Cost per patient
   * - Cost breakdown by category
   * - Cost per arm
   * - Monthly cost burn rate
   * - Sensitivity analysis (±20% variance)
   */
  const calculateCostEstimate = () => {
    try {
      console.log("💰 Calculating cost estimate...");
      // Use feasibility result N if available, otherwise use manual input
      const nPerArm = feasibilityResult?.required_n_per_arm || costParams.n_per_arm;
      const totalPatients = nPerArm * 2; // Active + Control arms

      // Patient-related costs
      const patientEnrollmentCost = totalPatients * costParams.cost_per_patient;
      const visitCosts = totalPatients * costParams.visits_per_patient * costParams.cost_per_visit;
      const totalPatientCosts = patientEnrollmentCost + visitCosts;

      // Site-related costs
      const siteCosts = costParams.num_sites * costParams.cost_per_site;

      // Duration-dependent costs
      const overheadCosts = costParams.duration_months * costParams.overhead_monthly;

      // Fixed costs
      const monitoringCosts = costParams.monitoring_cost;
      const regulatoryCosts = costParams.regulatory_cost;

      // Calculate totals
      const totalCost = totalPatientCosts + siteCosts + overheadCosts + monitoringCosts + regulatoryCosts;
      const costPerPatient = totalCost / totalPatients;
      const costPerArm = totalCost / 2;
      const monthlyCostBurnRate = totalCost / costParams.duration_months;

      // Sensitivity analysis (±20%)
      const lowEstimate = totalCost * 0.8;
      const highEstimate = totalCost * 1.2;

      // Set the cost estimate result
      setCostEstimate({
        totalCost,
        costPerPatient,
        costPerArm,
        monthlyCostBurnRate,
        totalPatients,
        nPerArm,
        durationMonths: costParams.duration_months,
        breakdown: {
          patientEnrollment: patientEnrollmentCost,
          visitCosts: visitCosts,
          siteCosts: siteCosts,
          overheadCosts: overheadCosts,
          monitoringCosts: monitoringCosts,
          regulatoryCosts: regulatoryCosts,
        },
        sensitivity: {
          low: lowEstimate,
          base: totalCost,
          high: highEstimate,
        },
      });

      console.log("✅ Cost estimate calculated:", {
        totalCost: totalCost,
        nPerArm: nPerArm,
        totalPatients: totalPatients
      });
    } catch (error) {
      console.error("❌ Error calculating cost estimate:", error);
    }
  };

  /**
   * Auto-fill Cost Params from Feasibility Result
   *
   * When feasibility assessment is run, automatically update the cost estimate
   * to use the recommended sample size.
   */
  const autoFillCostFromFeasibility = () => {
    if (feasibilityResult?.required_n_per_arm) {
      setCostParams({
        ...costParams,
        n_per_arm: feasibilityResult.required_n_per_arm,
      });
      // Auto-calculate after filling
      setTimeout(calculateCostEstimate, 100);
    }
  };

  /**
   * Apply Planning Parameters to Data Generation
   *
   * This function takes the current feasibility assessment results and saves them
   * to the global DataContext. This allows the Data Generation screen to automatically
   * pre-fill form fields with the recommended trial parameters.
   *
   * Workflow:
   * 1. User runs feasibility assessment → Gets required sample size
   * 2. User clicks "Apply to Generation" → Parameters saved to context
   * 3. User navigates to Data Generation → Form auto-fills with planning data
   * 4. User generates synthetic data with recommended parameters
   *
   * This eliminates manual parameter copying and ensures consistency between
   * planning and execution phases.
   */
  const applyToGeneration = () => {
    if (!feasibilityResult) {
      setError("Please run feasibility assessment first");
      return;
    }

    // Save planning parameters to global context for Data Generation screen to use
    setPlanningScenario({
      id: `planning-${Date.now()}`,
      name: `Feasibility Assessment - ${new Date().toLocaleString()}`,
      timestamp: new Date().toISOString(),
      // Input parameters from user's feasibility assessment
      nPerArm: feasibilityResult.required_n_per_arm || 0,
      targetEffect: feasibilityParams.target_effect,
      power: feasibilityParams.power,
      alpha: feasibilityParams.alpha,
      stdDev: feasibilityParams.expected_std,
      dropoutRate: 0.10, // Default dropout rate used in assessment
      allocationRatio: feasibilityParams.allocation_ratio,
      testType: "two-sided" as const,
      // Results from feasibility calculation
      requiredN: feasibilityResult.required_n_per_arm || 0,
      cohensD: feasibilityResult.effect_size_cohens_d || 0,
      feasibilityGrade: feasibilityResult.feasibility || "Unknown",
      source: "feasibility" as const,
    });

    // Parameters are now saved to context and will be auto-filled when user navigates to Data Generation
    console.log("✅ Planning parameters saved to context. Navigate to Data Generation to use them.");
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
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="virtual-control">Virtual Control</TabsTrigger>
          <TabsTrigger value="augment">Augment Arm</TabsTrigger>
          <TabsTrigger value="enrollment">Enrollment</TabsTrigger>
          <TabsTrigger value="patient-mix">Patient Mix</TabsTrigger>
          <TabsTrigger value="feasibility">Feasibility</TabsTrigger>
          <TabsTrigger value="cost-budget">Cost/Budget</TabsTrigger>
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
                        <p className="text-3xl font-bold">{virtualControlResult.virtual_control_data?.length ?? 0}</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="pt-6 text-center">
                        <p className="text-sm text-muted-foreground">Mean SBP</p>
                        <p className="text-3xl font-bold">
                          {virtualControlResult.summary?.virtual_control?.mean_sbp?.toFixed(1) ?? 'N/A'}
                        </p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="pt-6 text-center">
                        <p className="text-sm text-muted-foreground">Quality Score</p>
                        <p className="text-3xl font-bold text-green-600">
                          {((virtualControlResult.quality_metrics?.similarity_score ?? 0) * 100).toFixed(0)}%
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
                            {virtualControlResult.quality_metrics?.wasserstein_distance?.toFixed(2) ?? 'N/A'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Correlation Preservation:</span>
                          <span className="font-medium">
                            {((virtualControlResult.quality_metrics?.correlation_preservation ?? 0) * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <div className="p-4 bg-blue-50 dark:bg-blue-950 rounded-lg border border-blue-200">
                    <p className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-1">Use Case</p>
                    <p className="text-sm text-blue-800 dark:text-blue-200">
                      {virtualControlResult.use_case ?? 'N/A'}
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
                        <p className="text-3xl font-bold text-blue-600">{augmentResult.summary?.n_real ?? 0}</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="pt-6 text-center">
                        <p className="text-sm text-muted-foreground">Synthetic Added</p>
                        <p className="text-3xl font-bold text-purple-600">{augmentResult.summary?.n_synthetic ?? 0}</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="pt-6 text-center">
                        <p className="text-sm text-muted-foreground">Total Combined</p>
                        <p className="text-3xl font-bold text-green-600">{augmentResult.summary?.n_combined ?? 0}</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="pt-6 text-center">
                        <p className="text-sm text-muted-foreground">Similarity</p>
                        <p className="text-3xl font-bold">
                          {((augmentResult.quality_metrics?.similarity_score ?? 0) * 100).toFixed(0)}%
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
                          <p className="font-medium mb-2">Real Only (N={augmentResult.summary?.n_real ?? 0})</p>
                          <div className="space-y-1">
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Mean SBP:</span>
                              <span>{augmentResult.summary?.real_only?.mean_sbp?.toFixed(1) ?? 'N/A'} mmHg</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Std Dev:</span>
                              <span>{augmentResult.summary?.real_only?.std_sbp?.toFixed(1) ?? 'N/A'} mmHg</span>
                            </div>
                          </div>
                        </div>
                        <div>
                          <p className="font-medium mb-2">Combined (N={augmentResult.summary?.n_combined ?? 0})</p>
                          <div className="space-y-1">
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Mean SBP:</span>
                              <span>{augmentResult.summary?.augmented?.mean_sbp?.toFixed(1) ?? 'N/A'} mmHg</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Std Dev:</span>
                              <span>{augmentResult.summary?.augmented?.std_sbp?.toFixed(1) ?? 'N/A'} mmHg</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <div className="p-4 bg-green-50 dark:bg-green-950 rounded-lg border border-green-200">
                    <p className="text-sm font-medium text-green-900 dark:text-green-100 mb-1">Benefit</p>
                    <p className="text-sm text-green-800 dark:text-green-200">
                      Increased sample size from {augmentResult.summary?.n_real ?? 0} to {augmentResult.summary?.n_combined ?? 0}{" "}
                      ({(((augmentResult.summary?.n_combined ?? 0) / (augmentResult.summary?.n_real || 1) - 1) * 100).toFixed(0)}%
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
                      Analyzed {enrollmentResult.scenarios?.length ?? 0} enrollment scenarios
                    </span>
                  </div>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Power by Sample Size</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={enrollmentResult.scenarios ?? []}>
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
                        {(enrollmentResult.scenarios ?? []).map((scenario, idx) => (
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
                    <p className="text-sm text-blue-800 dark:text-blue-200">{enrollmentResult.recommendation ?? 'N/A'}</p>
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
                      Analyzed {patientMixResult.scenarios?.length ?? 0} patient mix scenarios
                    </span>
                  </div>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Treatment Effect by Baseline Severity</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={patientMixResult.scenarios ?? []}>
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
                            {(patientMixResult.scenarios ?? []).map((entry, index) => (
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
                        {(patientMixResult.scenarios ?? []).map((scenario, idx) => (
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
                    <p className="text-sm text-blue-800 dark:text-blue-200">{patientMixResult.recommendation ?? 'N/A'}</p>
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
              {/* ====== PLANNING TEMPLATE SELECTOR - QUICK SETUP ====== */}
              {/**
               * Planning Template Quick Setup
               *
               * Allows users to quickly populate all planning parameters with industry-standard
               * templates for Phase 1, 2, or 3 clinical trials. This provides:
               * - Immediate parameter setup based on regulatory best practices
               * - Educational value by showing typical trial design parameters
               * - Consistency with FDA, EMA, and ICH guidelines
               *
               * When a template is selected:
               * 1. Feasibility parameters are updated (effect size, power, alpha, etc.)
               * 2. Enrollment what-if scenarios are updated with phase-appropriate ranges
               * 3. Patient mix what-if scenarios are updated
               * 4. User is notified and can review/adjust parameters before running assessment
               *
               * Templates include regulatory considerations from:
               * - FDA: 21 CFR, guidance documents
               * - EMA: European Medicines Agency guidelines
               * - ICH: International Council for Harmonisation (E4, E6, E9, E10)
               */}
              <Card className="border-blue-200 bg-blue-50">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-blue-900">
                        Quick Setup: Load Template
                      </h3>
                      <p className="text-sm text-blue-700 mt-1">
                        Pre-fill parameters with industry-standard templates for Phase 1, 2, or 3 trials
                      </p>
                    </div>
                    <Select
                      onValueChange={(value) => {
                        const template = PLANNING_TEMPLATES.find((t) => t.id === value);
                        if (template) loadTemplate(template);
                      }}
                    >
                      <SelectTrigger className="w-[280px] bg-white border-gray-300">
                        <SelectValue placeholder="Select trial phase template..." />
                      </SelectTrigger>
                      <SelectContent>
                        {PLANNING_TEMPLATES.map((template) => (
                          <SelectItem key={template.id} value={template.id}>
                            <div className="flex flex-col">
                              <span className="font-medium text-gray-900">{template.name}</span>
                              <span className="text-xs text-gray-600">{template.description}</span>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="mt-3 p-3 bg-white rounded border border-blue-200">
                    <p className="text-xs text-blue-800">
                      💡 <strong>Tip:</strong> Templates automatically configure parameters based on regulatory
                      guidelines (FDA, EMA, ICH). You can adjust values after loading.
                    </p>
                  </div>
                </CardContent>
              </Card>

              {/* ====== PLANNING SCENARIO SAVE/LOAD ====== */}
              {/**
               * Planning Scenario Save/Load Interface
               *
               * Provides persistence functionality for trial planning scenarios, enabling users to:
               * - Save current feasibility assessments for future reference
               * - Load previously saved scenarios to resume work
               * - Compare different planning approaches over time
               * - Maintain a historical record of trial design decisions
               *
               * Use Cases:
               * 1. Save scenarios before trying different parameter combinations
               * 2. Create a library of planning scenarios for different indications
               * 3. Document planning decisions for regulatory submissions
               * 4. Share planning work with team members
               *
               * Data Persistence:
               * - Scenarios are saved to the backend database via data persistence API
               * - Each scenario includes all parameters, results, and metadata
               * - Scenarios can be retrieved by ID or listed chronologically
               */}
              <Card className="border-green-200 bg-green-50">
                <CardContent className="pt-6">
                  <div className="space-y-4">
                    {/* Load Saved Scenario Section */}
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <FolderOpen className="h-4 w-4 text-green-600" />
                        <h3 className="text-sm font-semibold text-green-900">
                          Load Saved Scenario
                        </h3>
                      </div>
                      <Select
                        value={selectedScenarioId || undefined}
                        onValueChange={(value) => {
                          setSelectedScenarioId(value);
                          loadScenarioById(parseInt(value));
                        }}
                        disabled={isLoadingScenarios || savedScenarios.length === 0}
                      >
                        <SelectTrigger className="w-full bg-white border-gray-300">
                          <SelectValue placeholder={
                            isLoadingScenarios
                              ? "Loading scenarios..."
                              : savedScenarios.length === 0
                                ? "No saved scenarios yet"
                                : "Select a saved scenario to load..."
                          } />
                        </SelectTrigger>
                        <SelectContent>
                          {savedScenarios.map((scenario) => (
                            <SelectItem key={scenario.id} value={scenario.id.toString()}>
                              <div className="flex flex-col">
                                <span className="font-medium text-gray-900">{scenario.dataset_name}</span>
                                <span className="text-xs text-gray-600">
                                  {new Date(scenario.created_at).toLocaleString()} • {scenario.record_count} parameter{scenario.record_count !== 1 ? 's' : ''}
                                </span>
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Divider */}
                    <div className="relative">
                      <div className="absolute inset-0 flex items-center">
                        <div className="w-full border-t border-green-300"></div>
                      </div>
                      <div className="relative flex justify-center text-xs">
                        <span className="bg-green-50 px-2 text-green-600">
                          OR
                        </span>
                      </div>
                    </div>

                    {/* Save Current Scenario Section */}
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Save className="h-4 w-4 text-green-600" />
                        <h3 className="text-sm font-semibold text-green-900">
                          Save Current Scenario
                        </h3>
                      </div>
                      <div className="flex gap-2">
                        <Input
                          placeholder="Enter scenario name (e.g., 'Phase 2 - 80% Power')"
                          value={scenarioName}
                          onChange={(e) => setScenarioName(e.target.value)}
                          className="flex-1 bg-white border-gray-300"
                          disabled={!feasibilityResult}
                        />
                        <Button
                          onClick={saveCurrentScenario}
                          disabled={!feasibilityResult || !scenarioName.trim() || isSaving}
                          variant="outline"
                          className="border-green-300 hover:bg-green-100"
                        >
                          {isSaving ? (
                            <>
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              Saving...
                            </>
                          ) : (
                            <>
                              <Save className="mr-2 h-4 w-4" />
                              Save
                            </>
                          )}
                        </Button>
                      </div>
                      <p className="text-xs text-green-700 mt-2">
                        💾 Run feasibility assessment first, then save your scenario for future reference
                      </p>
                    </div>

                    {/* Saved Scenarios Count */}
                    {savedScenarios.length > 0 && (
                      <div className="flex items-center gap-2 text-xs text-green-700 p-2 bg-white rounded border border-green-200">
                        <History className="h-3 w-3" />
                        <span>{savedScenarios.length} saved scenario{savedScenarios.length !== 1 ? 's' : ''} available</span>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* ====== MANUAL PARAMETER INPUTS ====== */}
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
                    <Card className="border-2 border-blue-200 bg-blue-50">
                      <CardContent className="pt-6 text-center">
                        <p className="text-sm text-gray-600 mb-2">Required Sample Size</p>
                        <p className="text-5xl font-bold text-blue-700">{feasibilityResult.required_n_per_arm ?? 0}</p>
                        <p className="text-sm text-gray-600 mt-2">per arm</p>
                        <p className="text-lg font-semibold text-gray-800 mt-1">
                          Total: {feasibilityResult.total_n ?? 0} patients
                        </p>
                      </CardContent>
                    </Card>

                    <Card className="bg-gray-50">
                      <CardContent className="pt-6">
                        <p className="text-sm text-gray-600 mb-3">Study Parameters</p>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Effect Size:</span>
                            <span className="font-medium text-gray-900">{feasibilityParams.target_effect} mmHg</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Cohen's d:</span>
                            <span className="font-medium text-gray-900">{feasibilityResult.effect_size_cohens_d?.toFixed(3) ?? 'N/A'}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Power:</span>
                            <span className="font-medium text-gray-900">{(feasibilityParams.power * 100).toFixed(0)}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Alpha:</span>
                            <span className="font-medium text-gray-900">{feasibilityParams.alpha}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Allocation:</span>
                            <span className="font-medium text-gray-900">{feasibilityParams.allocation_ratio}:1</span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  <Card className="bg-white">
                    <CardHeader>
                      <CardTitle className="text-base">Feasibility Assessment</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="flex items-center gap-2">
                          <Badge
                            variant="outline"
                            className={
                              (feasibilityResult.feasibility ?? "") === "Highly Feasible"
                                ? "bg-green-100 text-green-800 border-green-300"
                                : (feasibilityResult.feasibility ?? "") === "Feasible"
                                  ? "bg-blue-100 text-blue-800 border-blue-300"
                                  : (feasibilityResult.feasibility ?? "") === "Challenging"
                                    ? "bg-yellow-100 text-yellow-800 border-yellow-300"
                                    : "bg-red-100 text-red-800 border-red-300"
                            }
                          >
                            {feasibilityResult.feasibility ?? 'Unknown'}
                          </Badge>
                          <span className="text-sm text-gray-700">
                            Based on effect size of {Math.abs(feasibilityParams.target_effect)} mmHg
                          </span>
                        </div>

                        <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                          <p className="text-sm text-gray-800">{feasibilityResult.interpretation ?? 'N/A'}</p>
                        </div>

                        <div className="space-y-2">
                          <p className="text-sm font-medium text-gray-900">Assumptions:</p>
                          <ul className="text-sm text-gray-700 space-y-1 list-disc list-inside">
                            {(feasibilityResult.assumptions ?? []).map((assumption, idx) => (
                              <li key={idx}>{assumption}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <div className="p-4 bg-green-50 rounded-lg border border-green-300">
                    <p className="text-sm font-medium text-green-900 mb-1">
                      Recommendation
                    </p>
                    <p className="text-sm text-green-800">
                      {feasibilityResult.recommendation ?? 'N/A'}
                    </p>
                  </div>

                  {/* Apply to Generation Button
                      This button saves the planning parameters to DataContext and navigates
                      to the Data Generation screen, where the form will be auto-filled with
                      the recommended sample size and target effect size.
                  */}
                  <Card className="border-2 border-blue-300 bg-blue-50">
                    <CardContent className="pt-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="text-lg font-semibold mb-1 text-gray-900">Ready to Generate Data?</h3>
                          <p className="text-sm text-gray-600">
                            Use these planning parameters to generate synthetic trial data
                          </p>
                        </div>
                        <Button
                          size="lg"
                          onClick={applyToGeneration}
                          className="ml-4"
                        >
                          <ArrowRight className="mr-2 h-4 w-4" />
                          Apply to Generation
                        </Button>
                      </div>
                      <div className="mt-4 p-3 bg-white rounded-lg border border-gray-200">
                        <p className="text-xs text-gray-600 mb-2">
                          This will pre-fill the Data Generation form with:
                        </p>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Subjects per arm:</span>
                            <span className="font-medium text-gray-900">{feasibilityResult.required_n_per_arm ?? 0}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Target effect:</span>
                            <span className="font-medium text-gray-900">{feasibilityParams.target_effect} mmHg</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Expected power:</span>
                            <span className="font-medium text-gray-900">{(feasibilityParams.power * 100).toFixed(0)}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Dropout rate:</span>
                            <span className="font-medium text-gray-900">10%</span>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ====== COST/BUDGET PLANNING ====== */}
        {/**
         * Cost/Budget Planning Tab
         *
         * Provides comprehensive cost estimation for clinical trials based on:
         * - Sample size requirements (from feasibility assessment or manual input)
         * - Patient enrollment and retention costs
         * - Per-visit costs (procedures, assessments, labs)
         * - Site setup and management costs
         * - Overhead costs (staff, facilities, administration)
         * - Monitoring and safety costs (DSMB, data management)
         * - Regulatory costs (IND filing, submissions)
         *
         * Features:
         * - Auto-fill from feasibility assessment
         * - Detailed cost breakdown by category
         * - Cost per patient and cost per arm analysis
         * - Monthly burn rate calculation
         * - Sensitivity analysis (±20% variance)
         * - Industry benchmarks and guidelines
         *
         * Cost estimates follow industry standards:
         * - Tufts CSDD (Center for the Study of Drug Development)
         * - CTTI (Clinical Trials Transformation Initiative)
         * - FDA guidance on trial budgeting
         */}
        <TabsContent value="cost-budget" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Trial Cost & Budget Estimation
              </CardTitle>
              <CardDescription>
                Estimate comprehensive costs for your clinical trial based on sample size, duration, and operational parameters
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Auto-fill from Feasibility */}
              {feasibilityResult && (
                <Card className="border-blue-200 bg-blue-50 dark:bg-blue-950">
                  <CardContent className="pt-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
                          Use Feasibility Assessment Results
                        </p>
                        <p className="text-xs text-blue-700 dark:text-blue-300 mt-1">
                          Sample size: {feasibilityResult.required_n_per_arm} per arm ({feasibilityResult.required_n_per_arm * 2} total)
                        </p>
                      </div>
                      <Button
                        onClick={autoFillCostFromFeasibility}
                        size="sm"
                        variant="outline"
                        className="border-blue-300"
                      >
                        <ArrowRight className="mr-2 h-4 w-4" />
                        Auto-Fill
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Cost Parameters Input */}
              <div className="grid grid-cols-2 gap-6">
                {/* Patient-Related Costs */}
                <div className="space-y-4">
                  <h3 className="text-sm font-semibold border-b pb-2">Patient-Related Costs</h3>

                  <div className="space-y-2">
                    <Label htmlFor="cost-n-per-arm">Sample Size (per arm)</Label>
                    <Input
                      id="cost-n-per-arm"
                      type="number"
                      value={costParams.n_per_arm}
                      onChange={(e) => setCostParams({ ...costParams, n_per_arm: parseInt(e.target.value) })}
                    />
                    <p className="text-xs text-muted-foreground">Total patients: {costParams.n_per_arm * 2}</p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="cost-per-patient">Cost per Patient Enrolled ($)</Label>
                    <Input
                      id="cost-per-patient"
                      type="number"
                      value={costParams.cost_per_patient}
                      onChange={(e) => setCostParams({ ...costParams, cost_per_patient: parseInt(e.target.value) })}
                    />
                    <p className="text-xs text-muted-foreground">Includes recruitment, screening, consent</p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="visits-per-patient">Visits per Patient</Label>
                    <Input
                      id="visits-per-patient"
                      type="number"
                      value={costParams.visits_per_patient}
                      onChange={(e) => setCostParams({ ...costParams, visits_per_patient: parseInt(e.target.value) })}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="cost-per-visit">Cost per Visit ($)</Label>
                    <Input
                      id="cost-per-visit"
                      type="number"
                      value={costParams.cost_per_visit}
                      onChange={(e) => setCostParams({ ...costParams, cost_per_visit: parseInt(e.target.value) })}
                    />
                    <p className="text-xs text-muted-foreground">Assessments, labs, procedures per visit</p>
                  </div>
                </div>

                {/* Operational Costs */}
                <div className="space-y-4">
                  <h3 className="text-sm font-semibold border-b pb-2">Operational Costs</h3>

                  <div className="space-y-2">
                    <Label htmlFor="duration-months">Trial Duration (months)</Label>
                    <Input
                      id="duration-months"
                      type="number"
                      value={costParams.duration_months}
                      onChange={(e) => setCostParams({ ...costParams, duration_months: parseInt(e.target.value) })}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="num-sites">Number of Sites</Label>
                    <Input
                      id="num-sites"
                      type="number"
                      value={costParams.num_sites}
                      onChange={(e) => setCostParams({ ...costParams, num_sites: parseInt(e.target.value) })}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="cost-per-site">Cost per Site Setup ($)</Label>
                    <Input
                      id="cost-per-site"
                      type="number"
                      value={costParams.cost_per_site}
                      onChange={(e) => setCostParams({ ...costParams, cost_per_site: parseInt(e.target.value) })}
                    />
                    <p className="text-xs text-muted-foreground">Site activation, training, equipment</p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="overhead-monthly">Monthly Overhead ($)</Label>
                    <Input
                      id="overhead-monthly"
                      type="number"
                      value={costParams.overhead_monthly}
                      onChange={(e) => setCostParams({ ...costParams, overhead_monthly: parseInt(e.target.value) })}
                    />
                    <p className="text-xs text-muted-foreground">Staff salaries, admin, facilities</p>
                  </div>
                </div>

                {/* Fixed Costs */}
                <div className="space-y-4 col-span-2">
                  <h3 className="text-sm font-semibold border-b pb-2">Fixed Costs</h3>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="monitoring-cost">Monitoring & Safety ($)</Label>
                      <Input
                        id="monitoring-cost"
                        type="number"
                        value={costParams.monitoring_cost}
                        onChange={(e) => setCostParams({ ...costParams, monitoring_cost: parseInt(e.target.value) })}
                      />
                      <p className="text-xs text-muted-foreground">DSMB, data monitoring, EDC system</p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="regulatory-cost">Regulatory & Compliance ($)</Label>
                      <Input
                        id="regulatory-cost"
                        type="number"
                        value={costParams.regulatory_cost}
                        onChange={(e) => setCostParams({ ...costParams, regulatory_cost: parseInt(e.target.value) })}
                      />
                      <p className="text-xs text-muted-foreground">IND filing, submissions, audits</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Calculate Button */}
              <Button onClick={calculateCostEstimate} className="w-full" size="lg">
                <Activity className="mr-2 h-4 w-4" />
                Calculate Cost Estimate
              </Button>

              {/* Cost Estimate Results */}
              {costEstimate && (
                <>
                  {/* Summary Cards */}
                  <div className="grid grid-cols-4 gap-4">
                    <Card className="border-2 border-blue-300 bg-blue-50">
                      <CardContent className="pt-6">
                        <div className="text-center">
                          <p className="text-xs text-gray-600 mb-1">Total Trial Cost</p>
                          <p className="text-2xl font-bold text-blue-700">
                            ${(costEstimate.totalCost / 1000000).toFixed(2)}M
                          </p>
                        </div>
                      </CardContent>
                    </Card>

                    <Card className="bg-gray-50">
                      <CardContent className="pt-6">
                        <div className="text-center">
                          <p className="text-xs text-gray-600 mb-1">Cost per Patient</p>
                          <p className="text-2xl font-bold text-gray-900">
                            ${(costEstimate.costPerPatient / 1000).toFixed(1)}K
                          </p>
                        </div>
                      </CardContent>
                    </Card>

                    <Card className="bg-gray-50">
                      <CardContent className="pt-6">
                        <div className="text-center">
                          <p className="text-xs text-gray-600 mb-1">Cost per Arm</p>
                          <p className="text-2xl font-bold text-gray-900">
                            ${(costEstimate.costPerArm / 1000000).toFixed(2)}M
                          </p>
                        </div>
                      </CardContent>
                    </Card>

                    <Card className="bg-gray-50">
                      <CardContent className="pt-6">
                        <div className="text-center">
                          <p className="text-xs text-gray-600 mb-1">Monthly Burn Rate</p>
                          <p className="text-2xl font-bold text-gray-900">
                            ${(costEstimate.monthlyCostBurnRate / 1000).toFixed(0)}K
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Cost Breakdown */}
                  <Card className="bg-white">
                    <CardHeader>
                      <CardTitle className="text-gray-900">Cost Breakdown</CardTitle>
                      <CardDescription className="text-gray-600">Detailed breakdown by cost category</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {Object.entries(costEstimate.breakdown).map(([category, amount]: [string, any]) => {
                          const percentage = ((amount / costEstimate.totalCost) * 100).toFixed(1);
                          const categoryLabels: Record<string, string> = {
                            patientEnrollment: "Patient Enrollment",
                            visitCosts: "Patient Visit Costs",
                            siteCosts: "Site Setup & Management",
                            overheadCosts: "Overhead (Staff, Admin, Facilities)",
                            monitoringCosts: "Monitoring & Data Management",
                            regulatoryCosts: "Regulatory & Compliance",
                          };

                          return (
                            <div key={category} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                              <div className="flex-1">
                                <div className="flex items-center justify-between mb-1">
                                  <span className="text-sm font-medium text-gray-900">{categoryLabels[category]}</span>
                                  <span className="text-sm font-bold text-gray-900">${(amount / 1000).toFixed(0)}K</span>
                                </div>
                                <div className="w-full bg-gray-200 rounded-full h-2">
                                  <div
                                    className="bg-blue-600 rounded-full h-2"
                                    style={{ width: `${percentage}%` }}
                                  />
                                </div>
                                <p className="text-xs text-gray-600 mt-1">{percentage}% of total</p>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </CardContent>
                  </Card>

                  {/* Sensitivity Analysis */}
                  <Card className="border-orange-300 bg-orange-50">
                    <CardHeader>
                      <CardTitle className="text-orange-900">Sensitivity Analysis</CardTitle>
                      <CardDescription className="text-orange-700">
                        Cost variance scenarios (±20% from base estimate)
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-3 gap-4">
                        <div className="text-center p-4 bg-white rounded border border-gray-200">
                          <p className="text-xs text-gray-600 mb-1">Low Estimate (-20%)</p>
                          <p className="text-xl font-bold text-green-600">
                            ${(costEstimate.sensitivity.low / 1000000).toFixed(2)}M
                          </p>
                        </div>
                        <div className="text-center p-4 bg-white dark:bg-gray-950 rounded border border-2 border-orange-300">
                          <p className="text-xs text-muted-foreground mb-1">Base Estimate</p>
                          <p className="text-xl font-bold text-orange-600">
                            ${(costEstimate.sensitivity.base / 1000000).toFixed(2)}M
                          </p>
                        </div>
                        <div className="text-center p-4 bg-white dark:bg-gray-950 rounded border">
                          <p className="text-xs text-muted-foreground mb-1">High Estimate (+20%)</p>
                          <p className="text-xl font-bold text-red-600">
                            ${(costEstimate.sensitivity.high / 1000000).toFixed(2)}M
                          </p>
                        </div>
                      </div>
                      <p className="text-xs text-orange-700 dark:text-orange-300 mt-4 text-center">
                        💡 Industry standard: Plan for high estimate to account for unforeseen costs
                      </p>
                    </CardContent>
                  </Card>

                  {/* Industry Benchmarks */}
                  <Card className="border-purple-200 bg-purple-50 dark:bg-purple-950">
                    <CardHeader>
                      <CardTitle className="text-purple-900 dark:text-purple-100">Industry Benchmarks</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-sm text-purple-800 dark:text-purple-200 space-y-2">
                        <p className="font-medium">Typical Phase 2 Trial Costs (Tufts CSDD 2024):</p>
                        <ul className="list-disc list-inside space-y-1 ml-4">
                          <li>Average: $7-19M (varies by indication)</li>
                          <li>Per patient: $10,000-$30,000 (depending on complexity)</li>
                          <li>Duration: 18-36 months</li>
                          <li>Sites: 5-20 sites</li>
                        </ul>
                        <p className="font-medium mt-3">Typical Phase 3 Trial Costs:</p>
                        <ul className="list-disc list-inside space-y-1 ml-4">
                          <li>Average: $11-53M (varies by indication)</li>
                          <li>Per patient: $15,000-$50,000</li>
                          <li>Duration: 24-48 months</li>
                          <li>Sites: 20-100 sites</li>
                        </ul>
                      </div>
                    </CardContent>
                  </Card>
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
