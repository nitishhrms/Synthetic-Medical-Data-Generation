import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { BentoCard } from "@/components/ui/bento-card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";

import { cn } from "@/lib/utils";
import { dataGenerationApi, analyticsApi } from "@/services/api";
import { useData } from "@/contexts/DataContext";
import { Download, Loader2, AlertCircle, Activity, Users, FlaskConical, AlertTriangle, Database } from "lucide-react";

export function DataGeneration() {
  const { setGeneratedData, setPilotData, planningScenario, setPlanningScenario } = useData();

  // Common state
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("complete"); // Start with Complete Study (recommended)

  // Vitals state
  const [vitalsData, setVitalsData] = useState<any[]>([]);
  const [vitalsMetadata, setVitalsMetadata] = useState<any>(null);
  const [nPerArm, setNPerArm] = useState(50);
  const [targetEffect, setTargetEffect] = useState(-5.0);
  const [selectedMethod, setSelectedMethod] = useState<string>("mvn");

  // AACT parameters (NEW - for real-world data)
  const [indication, setIndication] = useState("hypertension");
  const [phase, setPhase] = useState("Phase 3");

  // Demographics state
  const [demographicsData, setDemographicsData] = useState<any[]>([]);
  const [demographicsMetadata, setDemographicsMetadata] = useState<any>(null);


  // Labs state
  const [labsData, setLabsData] = useState<any[]>([]);
  const [labsMetadata, setLabsMetadata] = useState<any>(null);


  // Advanced Simulation Parameters
  const [dropoutRate, setDropoutRate] = useState(0.15);
  const [missingDataRate, setMissingDataRate] = useState(0.08);
  const [siteHeterogeneity, setSiteHeterogeneity] = useState(0.3);

  // AE state
  const [aeData, setAeData] = useState<any[]>([]);
  const [aeMetadata, setAeMetadata] = useState<any>(null);


  // Dataset Name state
  const [datasetName, setDatasetName] = useState("");

  /**
   * Auto-Fill Form from Planning Parameters
   *
   * This effect runs when the component mounts or when planningScenario changes.
   * If a user clicked "Apply to Generation" from the Trial Planning screen,
   * the planning parameters will be stored in DataContext and automatically
   * pre-fill this form.
   *
   * Workflow:
   * 1. User completes feasibility assessment in Planning screen
   * 2. Clicks "Apply to Generation" → planningScenario saved to context
   * 3. Navigates to this screen → useEffect detects planningScenario
   * 4. Form fields auto-populate with recommended values
   * 5. User can review and adjust before generating data
   * 6. After use, we clear the planningScenario to prevent re-applying on next visit
   */
  useEffect(() => {
    if (planningScenario) {
      console.log("📋 Applying planning parameters to form:", planningScenario);

      // Pre-fill form fields with planning scenario values
      if (planningScenario.nPerArm) {
        setNPerArm(planningScenario.nPerArm);
      }
      if (planningScenario.targetEffect) {
        setTargetEffect(planningScenario.targetEffect);
      }
      if (planningScenario.dropoutRate) {
        setDropoutRate(planningScenario.dropoutRate);
      }

      // Show notification to user that planning parameters were applied
      const message = `✅ Planning parameters applied!\n` +
        `• Sample size: ${planningScenario.nPerArm || 'N/A'} per arm\n` +
        `• Target effect: ${planningScenario.targetEffect || 'N/A'} mmHg\n` +
        `• Expected power: ${planningScenario.power ? (planningScenario.power * 100).toFixed(0) + '%' : 'N/A'}\n\n` +
        `Review the parameters below and click "Generate Complete Study" when ready.`;

      alert(message);

      // Clear the planning scenario from context so it doesn't re-apply
      // on subsequent visits to this screen
      setPlanningScenario(null);
    }
  }, [planningScenario, setPlanningScenario]);



  const handleSaveDataset = async () => {
    if (vitalsData.length === 0) {
      setError("No data to save");
      return;
    }

    setIsGenerating(true);
    try {
      // Save vitals as the primary dataset for now
      // In a real app, we might save all domains linked together
      const nameToUse = datasetName.trim() || `Study-${indication}-${phase}-${new Date().toISOString().slice(0, 10)}`;
      await dataGenerationApi.saveGeneratedData(
        nameToUse,
        "vitals",
        vitalsData,
        {
          method: selectedMethod,
          indication,
          phase,
          n_per_arm: nPerArm,
          records: vitalsData.length,
          subjects: nPerArm * 2
        }
      );

      alert("Dataset saved successfully! You can now load it from the Dashboard or Analytics tab.");
    } catch (err: any) {
      setError(err?.message ?? "Failed to save dataset");
    } finally {
      setIsGenerating(false);
    }
  };

  const downloadCSV = (data: any[], filename: string) => {
    if (!data || (data ?? []).length === 0) {
      alert("No data to download");
      return;
    }

    const headers = Object.keys(data[0] ?? {});
    const csvContent = [
      headers.join(","),
      ...(data ?? []).map(row => headers.map(h => row[h] ?? "").join(","))
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Clinical Trial Data Generation</h1>
          <p className="text-muted-foreground">
            Generate complete, coordinated clinical trial datasets with guaranteed consistency across all domains
          </p>
        </div>
        <div />
      </div>



      {error && (
        <Card className="border-red-500 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-red-600">
              <AlertCircle className="h-5 w-5" />
              <span>{error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="complete">
            <Database className="h-4 w-4 mr-2" />
            Complete Study ⭐
          </TabsTrigger>
          <TabsTrigger value="vitals">
            <Activity className="h-4 w-4 mr-2" />
            Vitals
          </TabsTrigger>
          <TabsTrigger value="demographics">
            <Users className="h-4 w-4 mr-2" />
            Demographics
          </TabsTrigger>
          <TabsTrigger value="labs">
            <FlaskConical className="h-4 w-4 mr-2" />
            Labs
          </TabsTrigger>
          <TabsTrigger value="ae">
            <AlertTriangle className="h-4 w-4 mr-2" />
            Adverse Events
          </TabsTrigger>
        </TabsList>

        {/* COMPLETE STUDY TAB */}
        <TabsContent value="complete" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
            {/* Header Card */}
            <BentoCard
              title="Complete Study Generation"
              colSpan="md:col-span-12"
              className="bg-gradient-to-br from-zinc-900 to-zinc-950"
            >
              <div className="mt-4 flex items-start justify-between">
                <div className="space-y-1">
                  <h2 className="text-2xl font-bold text-white">Command Center</h2>
                  <p className="text-zinc-400 max-w-2xl">
                    Generate coordinated clinical trial datasets with guaranteed consistency across all domains.
                    All datasets will share the same subject IDs, visit schedules, and treatment arms.
                  </p>
                </div>
                <div className="flex gap-2">
                  <Badge variant="outline" className="bg-teal-950/30 text-teal-400 border-teal-900">
                    <Database className="h-3 w-3 mr-1" />
                    SDTM Compliant
                  </Badge>
                  <Badge variant="outline" className="bg-purple-950/30 text-purple-400 border-purple-900">
                    <Activity className="h-3 w-3 mr-1" />
                    AACT Real-World Data
                  </Badge>
                </div>
              </div>
            </BentoCard>

            {/* AACT Configuration */}
            <BentoCard
              title="Study Configuration"
              colSpan="md:col-span-4"
              icon={Database}
            >
              <div className="mt-4 space-y-4">
                <div className="space-y-2">
                  <Label className="text-zinc-400">Disease Indication</Label>
                  <Select value={indication} onValueChange={setIndication}>
                    <SelectTrigger className="bg-zinc-800/50 border-zinc-700 text-zinc-200">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-zinc-800 text-zinc-200">
                      <SelectItem value="hypertension">Hypertension (8,695 trials)</SelectItem>
                      <SelectItem value="diabetes">Diabetes (20,857 trials)</SelectItem>
                      <SelectItem value="cancer">Cancer (82,255 trials)</SelectItem>
                      <SelectItem value="heart failure">Heart Failure</SelectItem>
                      <SelectItem value="asthma">Asthma</SelectItem>
                      <SelectItem value="copd">COPD</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label className="text-zinc-400">Trial Phase</Label>
                  <Select value={phase} onValueChange={setPhase}>
                    <SelectTrigger className="bg-zinc-800/50 border-zinc-700 text-zinc-200">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-zinc-800 text-zinc-200">
                      <SelectItem value="Phase 1">Phase 1 - Safety</SelectItem>
                      <SelectItem value="Phase 2">Phase 2 - Efficacy</SelectItem>
                      <SelectItem value="Phase 3">Phase 3 - Confirmation</SelectItem>
                      <SelectItem value="Phase 4">Phase 4 - Post-Marketing</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label className="text-zinc-400">Generation Method</Label>
                  <Select value={selectedMethod} onValueChange={setSelectedMethod}>
                    <SelectTrigger className="bg-zinc-800/50 border-zinc-700 text-zinc-200">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-zinc-800 text-zinc-200">
                      <SelectItem value="mvn">MVN (Fastest)</SelectItem>
                      <SelectItem value="bootstrap">Bootstrap</SelectItem>
                      <SelectItem value="rules">Rules-based</SelectItem>
                      <SelectItem value="diffusion">Diffusion (Advanced)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </BentoCard>

            {/* Study Parameters */}
            <BentoCard
              title="Population Parameters"
              colSpan="md:col-span-4"
              icon={Users}
            >
              <div className="mt-4 space-y-6">
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <Label className="text-zinc-400">Subjects Per Arm</Label>
                    <span className="text-xs font-mono text-teal-400">{nPerArm}</span>
                  </div>
                  <Slider
                    value={[nPerArm]}
                    onValueChange={(vals) => setNPerArm(vals[0])}
                    min={10}
                    max={200}
                    step={10}
                    className="py-2"
                  />
                  <p className="text-xs text-zinc-500">Total: {nPerArm * 2} subjects</p>
                </div>

                <div className="space-y-3">
                  <div className="flex justify-between">
                    <Label className="text-zinc-400">Target Effect (mmHg)</Label>
                    <span className="text-xs font-mono text-teal-400">{targetEffect}</span>
                  </div>
                  <Slider
                    value={[Math.abs(targetEffect)]}
                    onValueChange={(vals) => setTargetEffect(-vals[0])}
                    min={0}
                    max={20}
                    step={0.5}
                    className="py-2"
                  />
                  <p className="text-xs text-zinc-500">Active vs Placebo difference</p>
                </div>

                <div className="space-y-2">
                  <Label className="text-zinc-400">Dataset Name</Label>
                  <Input
                    value={datasetName}
                    onChange={(e) => setDatasetName(e.target.value)}
                    placeholder="Optional custom name..."
                    className="bg-zinc-800/50 border-zinc-700 text-zinc-200 placeholder:text-zinc-600"
                  />
                </div>
              </div>
            </BentoCard>

            {/* Advanced Simulation */}
            <BentoCard
              title="Advanced Simulation"
              colSpan="md:col-span-4"
              icon={FlaskConical}
            >
              <div className="mt-4 space-y-6">
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <Label className="text-zinc-400">Dropout Rate</Label>
                    <span className="text-xs font-mono text-teal-400">{(dropoutRate * 100).toFixed(0)}%</span>
                  </div>
                  <Slider
                    value={[dropoutRate]}
                    onValueChange={(vals) => setDropoutRate(vals[0])}
                    min={0}
                    max={0.5}
                    step={0.01}
                    className="py-2"
                  />
                </div>

                <div className="space-y-3">
                  <div className="flex justify-between">
                    <Label className="text-zinc-400">Missing Data</Label>
                    <span className="text-xs font-mono text-teal-400">{(missingDataRate * 100).toFixed(0)}%</span>
                  </div>
                  <Slider
                    value={[missingDataRate]}
                    onValueChange={(vals) => setMissingDataRate(vals[0])}
                    min={0}
                    max={0.3}
                    step={0.01}
                    className="py-2"
                  />
                </div>

                <div className="space-y-3">
                  <div className="flex justify-between">
                    <Label className="text-zinc-400">Site Heterogeneity</Label>
                    <span className="text-xs font-mono text-teal-400">{(siteHeterogeneity * 100).toFixed(0)}%</span>
                  </div>
                  <Slider
                    value={[siteHeterogeneity]}
                    onValueChange={(vals) => setSiteHeterogeneity(vals[0])}
                    min={0}
                    max={1}
                    step={0.1}
                    className="py-2"
                  />
                </div>
              </div>
            </BentoCard>

            {/* Action Button */}
            <div className="md:col-span-12">
              <Button
                className="w-full h-14 text-lg font-semibold bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-500 hover:to-emerald-500 shadow-lg shadow-teal-900/20"
                onClick={async () => {
                  setIsGenerating(true);
                  setError("");
                  try {
                    const response = await dataGenerationApi.generateComprehensiveStudy({
                      n_per_arm: nPerArm,
                      target_effect: targetEffect,
                      method: selectedMethod as any,
                      indication,
                      phase,
                      include_vitals: true,
                      include_demographics: true,
                      dropout_rate: dropoutRate,
                      missing_data_rate: missingDataRate,
                      site_heterogeneity: siteHeterogeneity,
                      include_ae: true,
                      include_labs: true,
                      use_aact: true,
                      seed: 42
                    });

                    // Store all datasets
                    if (response?.vitals) {
                      setVitalsData(response.vitals);
                      setVitalsMetadata({ records: response.vitals.length, subjects: nPerArm * 2 });
                      setGeneratedData(response.vitals);
                    }
                    if (response?.demographics) {
                      setDemographicsData(response.demographics);
                      setDemographicsMetadata({ records: response.demographics.length, subjects: nPerArm * 2 });
                    }
                    if (response?.labs) {
                      setLabsData(response.labs);
                      setLabsMetadata({ records: response.labs.length, subjects: nPerArm * 2 });
                    }
                    if (response?.adverse_events) {
                      setAeData(response.adverse_events);
                      setAeMetadata({ records: response.adverse_events.length });
                    }

                    alert(`✅ Complete Study Generated Successfully!\n\n` +
                      `Vitals: ${response?.vitals?.length || 0} records\n` +
                      `Demographics: ${response?.demographics?.length || 0} subjects\n` +
                      `Labs: ${response?.labs?.length || 0} records\n` +
                      `Adverse Events: ${response?.adverse_events?.length || 0} events\n\n` +
                      `All datasets share the same ${nPerArm * 2} subjects with consistent IDs and visit schedules.`);
                  } catch (err: any) {
                    setError(err?.message ?? "Complete study generation failed");
                  } finally {
                    setIsGenerating(false);
                  }
                }}
                disabled={isGenerating}
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="h-6 w-6 mr-2 animate-spin" />
                    Generating Comprehensive Study...
                  </>
                ) : (
                  <>
                    <Database className="h-6 w-6 mr-2" />
                    Generate Complete Study
                  </>
                )}
              </Button>
            </div>

            {/* Summary Section */}
            {(vitalsData.length > 0 || demographicsData.length > 0 || labsData.length > 0 || aeData.length > 0) && (
              <BentoCard
                title="Generated Data Summary"
                colSpan="md:col-span-12"
                className="border-teal-900/50 bg-teal-950/10"
              >
                <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
                    <div className="flex items-center gap-2 mb-2">
                      <Activity className="h-4 w-4 text-teal-500" />
                      <span className="font-medium text-zinc-300">Vitals</span>
                    </div>
                    <p className="text-2xl font-bold text-white">{vitalsData.length}</p>
                    <p className="text-xs text-zinc-500">records</p>
                  </div>
                  <div className="p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
                    <div className="flex items-center gap-2 mb-2">
                      <Users className="h-4 w-4 text-purple-500" />
                      <span className="font-medium text-zinc-300">Demographics</span>
                    </div>
                    <p className="text-2xl font-bold text-white">{demographicsData.length}</p>
                    <p className="text-xs text-zinc-500">subjects</p>
                  </div>
                  <div className="p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
                    <div className="flex items-center gap-2 mb-2">
                      <FlaskConical className="h-4 w-4 text-blue-500" />
                      <span className="font-medium text-zinc-300">Labs</span>
                    </div>
                    <p className="text-2xl font-bold text-white">{labsData.length}</p>
                    <p className="text-xs text-zinc-500">records</p>
                  </div>
                  <div className="p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
                    <div className="flex items-center gap-2 mb-2">
                      <AlertTriangle className="h-4 w-4 text-orange-500" />
                      <span className="font-medium text-zinc-300">AEs</span>
                    </div>
                    <p className="text-2xl font-bold text-white">{aeData.length}</p>
                    <p className="text-xs text-zinc-500">events</p>
                  </div>
                </div>

                <div className="mt-6 flex flex-wrap gap-2">
                  <Button onClick={() => downloadCSV(vitalsData, "vitals.csv")} variant="outline" size="sm" className="border-zinc-700 text-zinc-300 hover:bg-zinc-800">
                    <Download className="h-3 w-3 mr-1" /> Vitals CSV
                  </Button>
                  <Button onClick={() => downloadCSV(demographicsData, "demographics.csv")} variant="outline" size="sm" className="border-zinc-700 text-zinc-300 hover:bg-zinc-800">
                    <Download className="h-3 w-3 mr-1" /> Demographics CSV
                  </Button>
                  <Button onClick={() => downloadCSV(labsData, "labs.csv")} variant="outline" size="sm" className="border-zinc-700 text-zinc-300 hover:bg-zinc-800">
                    <Download className="h-3 w-3 mr-1" /> Labs CSV
                  </Button>
                  <Button onClick={() => downloadCSV(aeData, "adverse_events.csv")} variant="outline" size="sm" className="border-zinc-700 text-zinc-300 hover:bg-zinc-800">
                    <Download className="h-3 w-3 mr-1" /> AE CSV
                  </Button>
                  <Button onClick={handleSaveDataset} variant="default" size="sm" className="ml-auto bg-teal-600 hover:bg-teal-700 text-white">
                    <Database className="h-3 w-3 mr-1" /> Save Dataset
                  </Button>
                </div>
              </BentoCard>
            )}
          </div>
        </TabsContent>

        {/* VITALS TAB */}
        <TabsContent value="vitals" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
            {/* Info Card */}
            <BentoCard
              title="Data Source"
              colSpan="md:col-span-4"
              icon={Database}
              className="bg-blue-950/10 border-blue-900/30"
            >
              <div className="mt-4 space-y-2">
                <p className="text-sm text-blue-200">
                  Data displayed from Complete Study generation.
                </p>
                <p className="text-xs text-blue-400">
                  Use the <strong>Complete Study</strong> tab to generate coordinated datasets with guaranteed consistency.
                </p>
              </div>
            </BentoCard>

            {/* Stats Card */}
            <BentoCard
              title="Generation Stats"
              colSpan="md:col-span-8"
              icon={Activity}
            >
              <div className="mt-4 grid grid-cols-3 gap-4">
                <div>
                  <p className="text-xs text-zinc-500 uppercase">Records</p>
                  <p className="text-2xl font-bold text-white">{vitalsMetadata?.records ?? 0}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500 uppercase">Subjects</p>
                  <p className="text-2xl font-bold text-white">{vitalsMetadata?.subjects ?? 0}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500 uppercase">Status</p>
                  <Badge variant="outline" className="mt-1 bg-emerald-950/30 text-emerald-400 border-emerald-900">
                    {vitalsMetadata ? "Generated" : "Pending"}
                  </Badge>
                </div>
              </div>
            </BentoCard>

            {/* Data Table Card */}
            <BentoCard
              title="Vital Signs Data"
              colSpan="md:col-span-12"
              className="min-h-[500px]"
            >
              <div className="mt-4 flex items-center justify-between mb-4">
                <p className="text-sm text-zinc-400">
                  Showing first 10 of {(vitalsData ?? []).length} records
                </p>
                <Button
                  onClick={() => downloadCSV(vitalsData, "vitals.csv")}
                  variant="outline"
                  size="sm"
                  className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
                  disabled={(vitalsData ?? []).length === 0}
                >
                  <Download className="h-3 w-3 mr-2" />
                  Download CSV
                </Button>
              </div>

              {(vitalsData ?? []).length > 0 ? (
                <div className="rounded-md border border-zinc-800 overflow-hidden">
                  <Table>
                    <TableHeader className="bg-zinc-900/50">
                      <TableRow className="hover:bg-zinc-900/50 border-zinc-800">
                        <TableHead className="text-zinc-400">Subject</TableHead>
                        <TableHead className="text-zinc-400">Visit</TableHead>
                        <TableHead className="text-zinc-400">Arm</TableHead>
                        <TableHead className="text-zinc-400">SBP</TableHead>
                        <TableHead className="text-zinc-400">DBP</TableHead>
                        <TableHead className="text-zinc-400">HR</TableHead>
                        <TableHead className="text-zinc-400">Temp</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(vitalsData ?? []).slice(0, 10).map((row, idx) => (
                        <TableRow key={idx} className="hover:bg-zinc-900/30 border-zinc-800">
                          <TableCell className="font-mono text-xs text-zinc-300">{row?.SubjectID ?? 'N/A'}</TableCell>
                          <TableCell className="text-zinc-300">{row?.VisitName ?? 'N/A'}</TableCell>
                          <TableCell>
                            <Badge variant="outline" className={cn(
                              "border-0",
                              (row?.TreatmentArm ?? "") === "Active"
                                ? "bg-teal-950/30 text-teal-400"
                                : "bg-zinc-800 text-zinc-400"
                            )}>
                              {row?.TreatmentArm ?? 'N/A'}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-zinc-300">{row?.SystolicBP ?? 'N/A'}</TableCell>
                          <TableCell className="text-zinc-300">{row?.DiastolicBP ?? 'N/A'}</TableCell>
                          <TableCell className="text-zinc-300">{row?.HeartRate ?? 'N/A'}</TableCell>
                          <TableCell className="text-zinc-300">{row?.Temperature?.toFixed?.(1) ?? 'N/A'}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-64 text-zinc-500 border border-dashed border-zinc-800 rounded-lg">
                  <Database className="h-8 w-8 mb-2 opacity-20" />
                  <p>No data generated yet</p>
                </div>
              )}
            </BentoCard>
          </div>
        </TabsContent>

        {/* DEMOGRAPHICS TAB */}
        <TabsContent value="demographics" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
            {/* Info Card */}
            <BentoCard
              title="Data Source"
              colSpan="md:col-span-4"
              icon={Database}
              className="bg-purple-950/10 border-purple-900/30"
            >
              <div className="mt-4 space-y-2">
                <p className="text-sm text-purple-200">
                  Data displayed from Complete Study generation.
                </p>
                <p className="text-xs text-purple-400">
                  Use the <strong>Complete Study</strong> tab to generate coordinated datasets with AACT real-world distributions.
                </p>
              </div>
            </BentoCard>

            {/* Stats Card */}
            <BentoCard
              title="Generation Stats"
              colSpan="md:col-span-8"
              icon={Users}
            >
              <div className="mt-4 grid grid-cols-3 gap-4">
                <div>
                  <p className="text-xs text-zinc-500 uppercase">Subjects</p>
                  <p className="text-2xl font-bold text-white">{demographicsMetadata?.subjects ?? 0}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500 uppercase">Records</p>
                  <p className="text-2xl font-bold text-white">{demographicsMetadata?.records ?? 0}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500 uppercase">Status</p>
                  <Badge variant="outline" className="mt-1 bg-emerald-950/30 text-emerald-400 border-emerald-900">
                    {demographicsMetadata ? "Generated" : "Pending"}
                  </Badge>
                </div>
              </div>
            </BentoCard>

            {/* Data Table Card */}
            <BentoCard
              title="Demographics Data"
              colSpan="md:col-span-12"
              className="min-h-[500px]"
            >
              <div className="mt-4 flex items-center justify-between mb-4">
                <p className="text-sm text-zinc-400">
                  Showing first 10 of {(demographicsData ?? []).length} subjects
                </p>
                <Button
                  onClick={() => downloadCSV(demographicsData, "demographics.csv")}
                  variant="outline"
                  size="sm"
                  className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
                  disabled={(demographicsData ?? []).length === 0}
                >
                  <Download className="h-3 w-3 mr-2" />
                  Download CSV
                </Button>
              </div>

              {(demographicsData ?? []).length > 0 ? (
                <div className="rounded-md border border-zinc-800 overflow-hidden">
                  <Table>
                    <TableHeader className="bg-zinc-900/50">
                      <TableRow className="hover:bg-zinc-900/50 border-zinc-800">
                        <TableHead className="text-zinc-400">Subject</TableHead>
                        <TableHead className="text-zinc-400">Age</TableHead>
                        <TableHead className="text-zinc-400">Gender</TableHead>
                        <TableHead className="text-zinc-400">Race</TableHead>
                        <TableHead className="text-zinc-400">Height (cm)</TableHead>
                        <TableHead className="text-zinc-400">Weight (kg)</TableHead>
                        <TableHead className="text-zinc-400">BMI</TableHead>
                        <TableHead className="text-zinc-400">Smoking</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(demographicsData ?? []).slice(0, 10).map((row, idx) => (
                        <TableRow key={idx} className="hover:bg-zinc-900/30 border-zinc-800">
                          <TableCell className="font-mono text-xs text-zinc-300">{row?.SubjectID ?? 'N/A'}</TableCell>
                          <TableCell className="text-zinc-300">{row?.Age ?? 'N/A'}</TableCell>
                          <TableCell className="text-zinc-300">{row?.Gender ?? 'N/A'}</TableCell>
                          <TableCell className="text-xs text-zinc-400">{row?.Race ?? 'N/A'}</TableCell>
                          <TableCell className="text-zinc-300">{row?.Height_cm?.toFixed?.(1) ?? 'N/A'}</TableCell>
                          <TableCell className="text-zinc-300">{row?.Weight_kg?.toFixed?.(1) ?? 'N/A'}</TableCell>
                          <TableCell className="text-zinc-300">{row?.BMI?.toFixed?.(1) ?? 'N/A'}</TableCell>
                          <TableCell className="text-xs text-zinc-400">{row?.SmokingStatus ?? 'N/A'}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-64 text-zinc-500 border border-dashed border-zinc-800 rounded-lg">
                  <Database className="h-8 w-8 mb-2 opacity-20" />
                  <p>No data generated yet</p>
                </div>
              )}
            </BentoCard>
          </div>
        </TabsContent>

        {/* LABS TAB */}
        <TabsContent value="labs" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
            {/* Info Card */}
            <BentoCard
              title="Data Source"
              colSpan="md:col-span-4"
              icon={Database}
              className="bg-green-950/10 border-green-900/30"
            >
              <div className="mt-4 space-y-2">
                <p className="text-sm text-green-200">
                  Data displayed from Complete Study generation.
                </p>
                <p className="text-xs text-green-400">
                  Use the <strong>Complete Study</strong> tab to generate coordinated datasets with consistent visit schedules.
                </p>
              </div>
            </BentoCard>

            {/* Stats Card */}
            <BentoCard
              title="Generation Stats"
              colSpan="md:col-span-8"
              icon={FlaskConical}
            >
              <div className="mt-4 grid grid-cols-3 gap-4">
                <div>
                  <p className="text-xs text-zinc-500 uppercase">Records</p>
                  <p className="text-2xl font-bold text-white">{labsMetadata?.records ?? 0}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500 uppercase">Subjects</p>
                  <p className="text-2xl font-bold text-white">{labsMetadata?.subjects ?? 0}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500 uppercase">Status</p>
                  <Badge variant="outline" className="mt-1 bg-emerald-950/30 text-emerald-400 border-emerald-900">
                    {labsMetadata ? "Generated" : "Pending"}
                  </Badge>
                </div>
              </div>
            </BentoCard>

            {/* Data Table Card */}
            <BentoCard
              title="Laboratory Data"
              colSpan="md:col-span-12"
              className="min-h-[500px]"
            >
              <div className="mt-4 flex items-center justify-between mb-4">
                <p className="text-sm text-zinc-400">
                  Showing first 10 of {(labsData ?? []).length} records
                </p>
                <Button
                  onClick={() => downloadCSV(labsData, "labs.csv")}
                  variant="outline"
                  size="sm"
                  className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
                  disabled={(labsData ?? []).length === 0}
                >
                  <Download className="h-3 w-3 mr-2" />
                  Download CSV
                </Button>
              </div>

              {(labsData ?? []).length > 0 ? (
                <div className="rounded-md border border-zinc-800 overflow-hidden">
                  <Table>
                    <TableHeader className="bg-zinc-900/50">
                      <TableRow className="hover:bg-zinc-900/50 border-zinc-800">
                        <TableHead className="text-zinc-400">Subject</TableHead>
                        <TableHead className="text-zinc-400">Visit</TableHead>
                        <TableHead className="text-zinc-400">Test Code</TableHead>
                        <TableHead className="text-zinc-400">Test Name</TableHead>
                        <TableHead className="text-zinc-400">Result</TableHead>
                        <TableHead className="text-zinc-400">Unit</TableHead>
                        <TableHead className="text-zinc-400">Ref Range</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(labsData ?? []).slice(0, 10).map((row, idx) => (
                        <TableRow key={idx} className="hover:bg-zinc-900/30 border-zinc-800">
                          <TableCell className="font-mono text-xs text-zinc-300">{row?.SubjectID ?? 'N/A'}</TableCell>
                          <TableCell className="text-zinc-300">{row?.VisitName ?? 'N/A'}</TableCell>
                          <TableCell className="font-mono text-xs text-zinc-400">{row?.LabTestCode ?? 'N/A'}</TableCell>
                          <TableCell className="text-zinc-300">{row?.LabTestName ?? 'N/A'}</TableCell>
                          <TableCell className="font-medium text-white">{row?.LabResult?.toFixed?.(2) ?? 'N/A'}</TableCell>
                          <TableCell className="text-xs text-zinc-400">{row?.LabUnit ?? 'N/A'}</TableCell>
                          <TableCell className="text-xs text-zinc-500">
                            {row?.ReferenceRangeLow} - {row?.ReferenceRangeHigh}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-64 text-zinc-500 border border-dashed border-zinc-800 rounded-lg">
                  <Database className="h-8 w-8 mb-2 opacity-20" />
                  <p>No data generated yet</p>
                </div>
              )}
            </BentoCard>
          </div>
        </TabsContent>

        {/* ADVERSE EVENTS TAB */}
        <TabsContent value="ae" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
            {/* Info Card */}
            <BentoCard
              title="Data Source"
              colSpan="md:col-span-4"
              icon={Database}
              className="bg-orange-950/10 border-orange-900/30"
            >
              <div className="mt-4 space-y-2">
                <p className="text-sm text-orange-200">
                  Data displayed from Complete Study generation.
                </p>
                <p className="text-xs text-orange-400">
                  Use the <strong>Complete Study</strong> tab to generate coordinated datasets with realistic AE distributions based on trial phase.
                </p>
              </div>
            </BentoCard>

            {/* Stats Card */}
            <BentoCard
              title="Generation Stats"
              colSpan="md:col-span-8"
              icon={AlertTriangle}
            >
              <div className="mt-4 grid grid-cols-3 gap-4">
                <div>
                  <p className="text-xs text-zinc-500 uppercase">Events</p>
                  <p className="text-2xl font-bold text-white">{aeMetadata?.records ?? 0}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500 uppercase">Serious AEs</p>
                  <p className="text-2xl font-bold text-white">
                    {(aeData ?? []).filter(r => r.Serious === "Yes").length}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500 uppercase">Status</p>
                  <Badge variant="outline" className="mt-1 bg-emerald-950/30 text-emerald-400 border-emerald-900">
                    {aeMetadata ? "Generated" : "Pending"}
                  </Badge>
                </div>
              </div>
            </BentoCard>

            {/* Data Table Card */}
            <BentoCard
              title="Adverse Events Data"
              colSpan="md:col-span-12"
              className="min-h-[500px]"
            >
              <div className="mt-4 flex items-center justify-between mb-4">
                <p className="text-sm text-zinc-400">
                  Showing first 10 of {(aeData ?? []).length} events
                </p>
                <Button
                  onClick={() => downloadCSV(aeData, "adverse_events.csv")}
                  variant="outline"
                  size="sm"
                  className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
                  disabled={(aeData ?? []).length === 0}
                >
                  <Download className="h-3 w-3 mr-2" />
                  Download CSV
                </Button>
              </div>

              {(aeData ?? []).length > 0 ? (
                <div className="rounded-md border border-zinc-800 overflow-hidden">
                  <Table>
                    <TableHeader className="bg-zinc-900/50">
                      <TableRow className="hover:bg-zinc-900/50 border-zinc-800">
                        <TableHead className="text-zinc-400">Subject</TableHead>
                        <TableHead className="text-zinc-400">Term</TableHead>
                        <TableHead className="text-zinc-400">Severity</TableHead>
                        <TableHead className="text-zinc-400">Serious</TableHead>
                        <TableHead className="text-zinc-400">Start Day</TableHead>
                        <TableHead className="text-zinc-400">End Day</TableHead>
                        <TableHead className="text-zinc-400">Outcome</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(aeData ?? []).slice(0, 10).map((row, idx) => (
                        <TableRow key={idx} className="hover:bg-zinc-900/30 border-zinc-800">
                          <TableCell className="font-mono text-xs text-zinc-300">{row?.SubjectID ?? 'N/A'}</TableCell>
                          <TableCell className="text-zinc-300">{row?.AdverseEventTerm ?? 'N/A'}</TableCell>
                          <TableCell>
                            <Badge variant="outline" className={cn(
                              "border-0",
                              row?.Severity === "Severe" ? "bg-red-950/30 text-red-400" :
                                row?.Severity === "Moderate" ? "bg-orange-950/30 text-orange-400" :
                                  "bg-yellow-950/30 text-yellow-400"
                            )}>
                              {row?.Severity ?? 'N/A'}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            {row?.Serious === "Yes" ? (
                              <Badge variant="destructive" className="bg-red-900/50 text-red-200 hover:bg-red-900/70">Yes</Badge>
                            ) : (
                              <span className="text-zinc-500">No</span>
                            )}
                          </TableCell>
                          <TableCell className="text-zinc-300">{row?.StartDay ?? 'N/A'}</TableCell>
                          <TableCell className="text-zinc-300">{row?.EndDay ?? 'N/A'}</TableCell>
                          <TableCell className="text-xs text-zinc-400">{row?.Outcome ?? 'N/A'}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-64 text-zinc-500 border border-dashed border-zinc-800 rounded-lg">
                  <Database className="h-8 w-8 mb-2 opacity-20" />
                  <p>No data generated yet</p>
                </div>
              )}
            </BentoCard>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
