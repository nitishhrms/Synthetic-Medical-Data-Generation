import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
  const [demographicsN, setDemographicsN] = useState(100);

  // Labs state
  const [labsData, setLabsData] = useState<any[]>([]);
  const [labsMetadata, setLabsMetadata] = useState<any>(null);
  const [labsN, setLabsN] = useState(100);

  // Advanced Simulation Parameters
  const [dropoutRate, setDropoutRate] = useState(0.15);
  const [missingDataRate, setMissingDataRate] = useState(0.08);
  const [siteHeterogeneity, setSiteHeterogeneity] = useState(0.3);

  // AE state
  const [aeData, setAeData] = useState<any[]>([]);
  const [aeMetadata, setAeMetadata] = useState<any>(null);
  const [aeN, setAeN] = useState(30);
  // Real data state
  const [realDataLoaded, setRealDataLoaded] = useState(false);
  const [realVitalsCount, setRealVitalsCount] = useState(0);
  const [realDemoCount, setRealDemoCount] = useState(0);
  const [realAeCount, setRealAeCount] = useState(0);

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

  const methods = [
    { id: "mvn", name: "MVN", speed: "~29K records/sec" },
    { id: "bootstrap", name: "Bootstrap", speed: "~140K records/sec" },
    { id: "rules", name: "Rules", speed: "~80K records/sec" },
    { id: "bayesian", name: "Bayesian", speed: "~5K records/sec" },
    { id: "mice", name: "MICE", speed: "~3K records/sec" },
    { id: "diffusion", name: "Diffusion", speed: "~10K records/sec" },
  ];

  const handleGenerateVitals = async () => {
    setIsGenerating(true);
    setError("");

    try {
      let response;
      // Include AACT parameters for real-world data
      const params = {
        n_per_arm: nPerArm,
        target_effect: targetEffect,
        seed: 42,
        indication,
        phase,
      };

      switch (selectedMethod) {
        case "mvn":
          response = await dataGenerationApi.generateMVN(params);
          break;
        case "bootstrap":
          response = await dataGenerationApi.generateBootstrap(params);
          break;
        case "rules":
          response = await dataGenerationApi.generateRules(params);
          break;
        case "bayesian":
          response = await dataGenerationApi.generateBayesian(params);
          break;
        case "mice":
          response = await dataGenerationApi.generateMICE(params);
          break;
        case "diffusion":
          response = await dataGenerationApi.generateDiffusion({
            ...params,
            n_steps: 50, // Default diffusion steps
          });
          break;
        default:
          throw new Error("Unknown method");
      }

      setVitalsData(response?.data ?? []);
      setVitalsMetadata(response?.metadata ?? {});
      setGeneratedData(response?.data ?? []);
    } catch (err: any) {
      setError(err?.message ?? "Generation failed");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleGenerateDemographics = async () => {
    setIsGenerating(true);
    setError("");

    try {
      const response = await dataGenerationApi.generateDemographics({
        n_subjects: demographicsN,
        seed: 42,
        indication,
        phase,
      });

      setDemographicsData(response?.data ?? []);
      setDemographicsMetadata(response?.metadata ?? {});
    } catch (err: any) {
      setError(err?.message ?? "Demographics generation failed");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleGenerateLabs = async () => {
    setIsGenerating(true);
    setError("");

    try {
      const response = await dataGenerationApi.generateLabs({
        n_subjects: labsN,
        seed: 42
      });

      setLabsData(response?.data ?? []);
      setLabsMetadata(response?.metadata ?? {});
    } catch (err: any) {
      setError(err?.message ?? "Labs generation failed");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleGenerateAE = async () => {
    setIsGenerating(true);
    setError("");

    try {
      const response = await dataGenerationApi.generateAE({
        n_subjects: aeN,
        seed: 7
      });

      setAeData(response?.data ?? []);
      setAeMetadata(response?.metadata ?? {});
    } catch (err: any) {
      setError(err?.message ?? "AE generation failed");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleLoadRealData = async () => {
    setIsGenerating(true);
    setError("");

    try {
      const [vitals, demographics, ae] = await Promise.all([
        dataGenerationApi.getRealVitalSigns(),
        dataGenerationApi.getRealDemographics(),
        dataGenerationApi.getRealAdverseEvents()
      ]);

      setRealVitalsCount((vitals ?? []).length);
      setRealDemoCount((demographics ?? []).length);
      setRealAeCount((ae ?? []).length);
      setRealDataLoaded(true);
      setPilotData(vitals ?? []);

      alert(`Real CDISC data loaded:\n\nVitals: ${(vitals ?? []).length} records\nDemographics: ${(demographics ?? []).length} subjects\nAdverse Events: ${(ae ?? []).length} events`);
    } catch (err: any) {
      setError(err?.message ?? "Failed to load real data");
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
    URL.revokeObjectURL(url);
  };

  const handleExportSDTM = async (domain: "vitals" | "demographics" | "labs" | "ae") => {
    try {
      let response;
      switch (domain) {
        case "vitals":
          response = await analyticsApi.exportSDTM(vitalsData);
          break;
        case "demographics":
          response = await analyticsApi.exportDemographicsSDTM(demographicsData);
          break;
        case "labs":
          response = await analyticsApi.exportLabsSDTM(labsData);
          break;
        case "ae":
          response = await analyticsApi.exportAESDTM(aeData);
          break;
      }

      // Download the response as JSON (or CSV if backend supports it)
      const blob = new Blob([JSON.stringify(response, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${domain}_sdtm.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

    } catch (err: any) {
      setError(`Failed to export ${domain} to SDTM: ${err.message}`);
    }
  };

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

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Clinical Trial Data Generation</h1>
          <p className="text-muted-foreground">
            Generate complete, coordinated clinical trial datasets with guaranteed consistency across all domains
          </p>
        </div>
        <Button onClick={handleLoadRealData} variant="outline" disabled={isGenerating}>
          {isGenerating ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <>
              <Database className="h-4 w-4 mr-2" />
              Load Real CDISC Data
            </>
          )}
        </Button>
      </div>

      {realDataLoaded && (
        <Card className="border-green-500 bg-green-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-green-700">
              <Activity className="h-5 w-5" />
              <span className="font-medium">
                Real data loaded: {realVitalsCount.toLocaleString()} vitals, {realDemoCount} demographics, {realAeCount} AEs
              </span>
            </div>
          </CardContent>
        </Card>
      )}

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

        {/* VITALS TAB */}
        <TabsContent value="vitals" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Vital Signs Data</CardTitle>
              <CardDescription>View vitals generated from Complete Study tab (SBP, DBP, Heart Rate, Temperature)</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg">
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-blue-600" />
                  <div className="text-sm text-blue-900">
                    <p className="font-semibold">ℹ️ Data displayed from Complete Study generation</p>
                    <p className="text-xs text-blue-700 mt-1">
                      Use the <strong>Complete Study ⭐</strong> tab to generate coordinated datasets with guaranteed consistency
                    </p>
                  </div>
                </div>
              </div>

              {vitalsMetadata && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-sm">
                  <p className="font-medium text-green-900">✅ Generated</p>
                  <p className="text-green-700">Records: {vitalsMetadata?.records ?? 0}</p>
                  <p className="text-green-700">Subjects: {vitalsMetadata?.subjects ?? 0}</p>
                </div>
              )}

              {!vitalsMetadata && (
                <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg text-center">
                  <p className="text-sm text-gray-600">No data generated yet. Please use the <strong>Complete Study ⭐</strong> tab to generate data.</p>
                </div>
              )}
            </CardContent>
          </Card>

          {(vitalsData ?? []).length > 0 && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Data Preview</CardTitle>
                    <CardDescription>Showing first 10 of {(vitalsData ?? []).length} records</CardDescription>
                  </div>
                  <Button onClick={() => downloadCSV(vitalsData, "vitals.csv")} variant="outline">
                    <Download className="h-4 w-4 mr-2" />
                    Download CSV
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Subject</TableHead>
                      <TableHead>Visit</TableHead>
                      <TableHead>Arm</TableHead>
                      <TableHead>SBP</TableHead>
                      <TableHead>DBP</TableHead>
                      <TableHead>HR</TableHead>
                      <TableHead>Temp</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {(vitalsData ?? []).slice(0, 10).map((row, idx) => (
                      <TableRow key={idx}>
                        <TableCell className="font-mono text-sm">{row?.SubjectID ?? 'N/A'}</TableCell>
                        <TableCell>{row?.VisitName ?? 'N/A'}</TableCell>
                        <TableCell>
                          <Badge variant={(row?.TreatmentArm ?? "") === "Active" ? "default" : "secondary"}>
                            {row?.TreatmentArm ?? 'N/A'}
                          </Badge>
                        </TableCell>
                        <TableCell>{row?.SystolicBP ?? 'N/A'}</TableCell>
                        <TableCell>{row?.DiastolicBP ?? 'N/A'}</TableCell>
                        <TableCell>{row?.HeartRate ?? 'N/A'}</TableCell>
                        <TableCell>{row?.Temperature?.toFixed?.(1) ?? 'N/A'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* DEMOGRAPHICS TAB */}
        <TabsContent value="demographics" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Demographics Data</CardTitle>
              <CardDescription>View demographics generated from Complete Study tab (Age, Gender, Race, Ethnicity, Height, Weight, BMI, Smoking Status)</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg">
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-blue-600" />
                  <div className="text-sm text-blue-900">
                    <p className="font-semibold">ℹ️ Data displayed from Complete Study generation</p>
                    <p className="text-xs text-blue-700 mt-1">
                      Use the <strong>Complete Study ⭐</strong> tab to generate coordinated datasets with AACT real-world distributions
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-muted rounded-lg">
                <h3 className="font-medium mb-2">Generated Fields:</h3>
                <ul className="text-sm space-y-1 text-muted-foreground">
                  <li>• Age (from AACT real distribution)</li>
                  <li>• Gender (from AACT real ratio)</li>
                  <li>• Race (from AACT baseline characteristics)</li>
                  <li>• Ethnicity (Hispanic/Not Hispanic)</li>
                  <li>• Height (gender-specific, cm)</li>
                  <li>• Weight (age-correlated, kg)</li>
                  <li>• BMI (auto-calculated)</li>
                  <li>• Smoking Status</li>
                </ul>
              </div>

              {demographicsMetadata && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-sm">
                  <p className="font-medium text-green-900">✅ Generated</p>
                  <p className="text-green-700">Subjects: {demographicsMetadata?.subjects ?? 0}</p>
                  <p className="text-green-700">Records: {demographicsMetadata?.records ?? 0}</p>
                </div>
              )}

              {!demographicsMetadata && (
                <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg text-center">
                  <p className="text-sm text-gray-600">No data generated yet. Please use the <strong>Complete Study ⭐</strong> tab to generate data.</p>
                </div>
              )}
            </CardContent>
          </Card>

          {(demographicsData ?? []).length > 0 && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Demographics Preview</CardTitle>
                    <CardDescription>Showing first 10 of {(demographicsData ?? []).length} subjects</CardDescription>
                  </div>
                  <Button onClick={() => downloadCSV(demographicsData, "demographics.csv")} variant="outline">
                    <Download className="h-4 w-4 mr-2" />
                    Download CSV
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Subject</TableHead>
                      <TableHead>Age</TableHead>
                      <TableHead>Gender</TableHead>
                      <TableHead>Race</TableHead>
                      <TableHead>Height (cm)</TableHead>
                      <TableHead>Weight (kg)</TableHead>
                      <TableHead>BMI</TableHead>
                      <TableHead>Smoking</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {(demographicsData ?? []).slice(0, 10).map((row, idx) => (
                      <TableRow key={idx}>
                        <TableCell className="font-mono text-sm">{row?.SubjectID ?? 'N/A'}</TableCell>
                        <TableCell>{row?.Age ?? 'N/A'}</TableCell>
                        <TableCell>{row?.Gender ?? 'N/A'}</TableCell>
                        <TableCell className="text-xs">{row?.Race ?? 'N/A'}</TableCell>
                        <TableCell>{row?.Height_cm?.toFixed?.(1) ?? 'N/A'}</TableCell>
                        <TableCell>{row?.Weight_kg?.toFixed?.(1) ?? 'N/A'}</TableCell>
                        <TableCell>{row?.BMI?.toFixed?.(1) ?? 'N/A'}</TableCell>
                        <TableCell className="text-xs">{row?.SmokingStatus ?? 'N/A'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* LABS TAB */}
        <TabsContent value="labs" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Lab Results Data</CardTitle>
              <CardDescription>View lab results generated from Complete Study tab (Hematology, Chemistry, and Lipid panels)</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg">
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-blue-600" />
                  <div className="text-sm text-blue-900">
                    <p className="font-semibold">ℹ️ Data displayed from Complete Study generation</p>
                    <p className="text-xs text-blue-700 mt-1">
                      Use the <strong>Complete Study ⭐</strong> tab to generate coordinated datasets with shared visit schedules
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-muted rounded-lg">
                <h3 className="font-medium mb-2">Generated Lab Tests:</h3>
                <div className="text-sm space-y-2 text-muted-foreground">
                  <div>
                    <strong>Hematology:</strong> Hemoglobin, Hematocrit, WBC, Platelets
                  </div>
                  <div>
                    <strong>Chemistry:</strong> Glucose, Creatinine, BUN, ALT, AST, Bilirubin
                  </div>
                  <div>
                    <strong>Lipids:</strong> Total Chol, LDL, HDL, Triglycerides
                  </div>
                </div>
              </div>

              {labsMetadata && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-sm">
                  <p className="font-medium text-green-900">✅ Generated</p>
                  <p className="text-green-700">Subjects: {labsMetadata?.subjects ?? 0}</p>
                  <p className="text-green-700">Records: {labsMetadata?.records ?? 0}</p>
                  <p className="text-green-700">Visits: {labsMetadata?.visits_per_subject ?? 0} per subject</p>
                </div>
              )}

              {!labsMetadata && (
                <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg text-center">
                  <p className="text-sm text-gray-600">No data generated yet. Please use the <strong>Complete Study ⭐</strong> tab to generate data.</p>
                </div>
              )}
            </CardContent>
          </Card>

          {(labsData ?? []).length > 0 && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Labs Preview</CardTitle>
                    <CardDescription>Showing first 10 of {(labsData ?? []).length} lab records</CardDescription>
                  </div>
                  <Button onClick={() => downloadCSV(labsData, "labs.csv")} variant="outline">
                    <Download className="h-4 w-4 mr-2" />
                    Download CSV
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Subject</TableHead>
                        <TableHead>Visit</TableHead>
                        <TableHead>Hgb</TableHead>
                        <TableHead>WBC</TableHead>
                        <TableHead>Glucose</TableHead>
                        <TableHead>Creatinine</TableHead>
                        <TableHead>ALT</TableHead>
                        <TableHead>Chol</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(labsData ?? []).slice(0, 10).map((row, idx) => (
                        <TableRow key={idx}>
                          <TableCell className="font-mono text-sm">{row?.SubjectID ?? 'N/A'}</TableCell>
                          <TableCell className="text-xs">{row?.VisitName ?? 'N/A'}</TableCell>
                          <TableCell>{row?.Hemoglobin?.toFixed?.(1) ?? 'N/A'}</TableCell>
                          <TableCell>{row?.WBC?.toFixed?.(1) ?? 'N/A'}</TableCell>
                          <TableCell>{row?.Glucose?.toFixed?.(0) ?? 'N/A'}</TableCell>
                          <TableCell>{row?.Creatinine?.toFixed?.(2) ?? 'N/A'}</TableCell>
                          <TableCell>{row?.ALT?.toFixed?.(0) ?? 'N/A'}</TableCell>
                          <TableCell>{row?.TotalCholesterol?.toFixed?.(0) ?? 'N/A'}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* ADVERSE EVENTS TAB */}
        <TabsContent value="ae" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Adverse Events Data</CardTitle>
              <CardDescription>View adverse events generated from Complete Study tab (MedDRA coding, severity, and causality)</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg">
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-blue-600" />
                  <div className="text-sm text-blue-900">
                    <p className="font-semibold">ℹ️ Data displayed from Complete Study generation</p>
                    <p className="text-xs text-blue-700 mt-1">
                      Use the <strong>Complete Study ⭐</strong> tab to generate coordinated datasets with phase-appropriate AE rates
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-muted rounded-lg">
                <h3 className="font-medium mb-2">Generated AE Data:</h3>
                <ul className="text-sm space-y-1 text-muted-foreground">
                  <li>• AE Terms (Neutropenia, Nausea, etc.)</li>
                  <li>• Body System (SOC - MedDRA)</li>
                  <li>• Seriousness (Y/N)</li>
                  <li>• Causality/Relationship (Y/N)</li>
                  <li>• Outcome (RESOLVED/ONGOING/FATAL)</li>
                  <li>• Includes mandatory serious/related events</li>
                </ul>
              </div>

              {aeMetadata && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-sm">
                  <p className="font-medium text-green-900">✅ Generated</p>
                  <p className="text-green-700">AE Records: {aeMetadata?.records ?? (aeData ?? []).length}</p>
                </div>
              )}

              {!aeMetadata && (
                <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg text-center">
                  <p className="text-sm text-gray-600">No data generated yet. Please use the <strong>Complete Study ⭐</strong> tab to generate data.</p>
                </div>
              )}
            </CardContent>
          </Card>

          {(aeData ?? []).length > 0 && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>AE Preview</CardTitle>
                    <CardDescription>Showing first 10 of {(aeData ?? []).length} adverse events</CardDescription>
                  </div>
                  <Button onClick={() => downloadCSV(aeData, "adverse_events.csv")} variant="outline">
                    <Download className="h-4 w-4 mr-2" />
                    Download CSV
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Subject</TableHead>
                      <TableHead>AE Term</TableHead>
                      <TableHead>Body System</TableHead>
                      <TableHead>Serious</TableHead>
                      <TableHead>Related</TableHead>
                      <TableHead>Outcome</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {(aeData ?? []).slice(0, 10).map((row, idx) => (
                      <TableRow key={idx}>
                        <TableCell className="font-mono text-sm">{row?.SubjectID ?? 'N/A'}</TableCell>
                        <TableCell>{row?.AETerm ?? 'N/A'}</TableCell>
                        <TableCell className="text-xs">{row?.BodySystem ?? 'N/A'}</TableCell>
                        <TableCell>
                          <Badge variant={(row?.Serious ?? "") === "Y" ? "destructive" : "secondary"}>
                            {row?.Serious ?? 'N/A'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={(row?.Related ?? "") === "Y" ? "default" : "secondary"}>
                            {row?.Related ?? 'N/A'}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-xs">{row?.Outcome ?? 'N/A'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* COMPLETE STUDY TAB */}
        <TabsContent value="complete" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>🎯 Complete Study Generation (Recommended)</CardTitle>
              <CardDescription>
                Generate all domains simultaneously with guaranteed data consistency
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Key Benefit Callout */}
              <div className="p-4 bg-gradient-to-r from-green-50 to-blue-50 border border-green-300 rounded-lg">
                <div className="flex items-start gap-2">
                  <Database className="h-5 w-5 text-green-600 mt-0.5" />
                  <div className="text-sm text-green-900">
                    <p className="font-semibold mb-2">✅ Why Use Complete Study Generation?</p>
                    <ul className="list-disc list-inside space-y-1 ml-2">
                      <li><strong>Guaranteed Consistency:</strong> All datasets share the same subject IDs</li>
                      <li><strong>Same Visit Schedule:</strong> Vitals and labs use identical visit names</li>
                      <li><strong>Matched Treatment Arms:</strong> Subject RA001-001 is "Active" in all datasets</li>
                      <li><strong>SDTM-Compliant:</strong> Datasets can be joined on SubjectID with 100% match rate</li>
                      <li><strong>Parameter Coordination:</strong> Indication/phase affect ALL datasets appropriately</li>
                    </ul>
                    <p className="mt-2 text-xs text-green-700">
                      ℹ️ This is the recommended approach for realistic clinical trial data generation
                    </p>
                  </div>
                </div>
              </div>

              {/* AACT Configuration */}
              <div className="p-4 bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-lg">
                <div className="flex items-center gap-2 mb-3">
                  <Database className="h-4 w-4 text-purple-600" />
                  <h3 className="font-semibold text-purple-900">AACT Real-World Data (557K+ Trials)</h3>
                  <Badge variant="outline" className="bg-white">Enhanced v4.0</Badge>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-purple-900">Disease Indication</Label>
                    <select
                      value={indication}
                      onChange={(e) => setIndication(e.target.value)}
                      className="w-full mt-1 p-2 border rounded-md bg-white"
                    >
                      <option value="hypertension">Hypertension (8,695 trials)</option>
                      <option value="diabetes">Diabetes (20,857 trials)</option>
                      <option value="cancer">Cancer (82,255 trials)</option>
                      <option value="heart failure">Heart Failure</option>
                      <option value="asthma">Asthma</option>
                      <option value="copd">COPD</option>
                    </select>
                  </div>
                  <div>
                    <Label className="text-purple-900">Trial Phase</Label>
                    <select
                      value={phase}
                      onChange={(e) => setPhase(e.target.value)}
                      className="w-full mt-1 p-2 border rounded-md bg-white"
                    >
                      <option value="Phase 1">Phase 1 - Safety (30% serious AEs)</option>
                      <option value="Phase 2">Phase 2 - Efficacy</option>
                      <option value="Phase 3">Phase 3 - Confirmation (15% serious AEs)</option>
                      <option value="Phase 4">Phase 4 - Post-Marketing</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Study Parameters */}
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <Label>Dataset Name (Optional)</Label>
                  <Input
                    type="text"
                    placeholder="e.g., My Hypertension Study"
                    value={datasetName}
                    onChange={(e) => setDatasetName(e.target.value)}
                    className="mt-1"
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Custom name for the generated dataset
                  </p>
                </div>
                <div>
                  <Label>Subjects Per Arm</Label>
                  <Input
                    type="number"
                    value={nPerArm}
                    onChange={(e) => setNPerArm(parseInt(e.target.value) || 0)}
                    min={10}
                    max={200}
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Total: {nPerArm * 2} subjects
                  </p>
                </div>
                <div>
                  <Label>Target Effect (mmHg)</Label>
                  <Input
                    type="number"
                    value={targetEffect}
                    onChange={(e) => setTargetEffect(parseFloat(e.target.value) || 0)}
                    step={0.1}
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Active vs Placebo SBP difference
                  </p>
                </div>
                <div>
                  <Label>Generation Method</Label>
                  <select
                    value={selectedMethod}
                    onChange={(e) => setSelectedMethod(e.target.value)}
                    className="w-full mt-1 p-2 border rounded-md"
                  >
                    <option value="mvn">MVN (Fastest)</option>
                    <option value="bootstrap">Bootstrap</option>
                    <option value="rules">Rules-based</option>
                    <option value="diffusion">Diffusion (Advanced)</option>
                  </select>
                </div>
              </div>

              {/* Advanced Simulation Parameters */}
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg">
                <div className="flex items-center gap-2 mb-3">
                  <Activity className="h-4 w-4 text-slate-600" />
                  <h3 className="font-semibold text-slate-900">Advanced Simulation Scenarios</h3>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label>Dropout Rate ({(dropoutRate * 100).toFixed(0)}%)</Label>
                    <div className="flex items-center gap-2">
                      <Input
                        type="range"
                        min="0"
                        max="0.5"
                        step="0.01"
                        value={dropoutRate}
                        onChange={(e) => setDropoutRate(parseFloat(e.target.value))}
                        className="mt-1"
                      />
                      <span className="text-sm w-12">{(dropoutRate * 100).toFixed(0)}%</span>
                    </div>
                    <p className="text-xs text-muted-foreground">Subject attrition over time</p>
                  </div>
                  <div>
                    <Label>Missing Data ({(missingDataRate * 100).toFixed(0)}%)</Label>
                    <div className="flex items-center gap-2">
                      <Input
                        type="range"
                        min="0"
                        max="0.3"
                        step="0.01"
                        value={missingDataRate}
                        onChange={(e) => setMissingDataRate(parseFloat(e.target.value))}
                        className="mt-1"
                      />
                      <span className="text-sm w-12">{(missingDataRate * 100).toFixed(0)}%</span>
                    </div>
                    <p className="text-xs text-muted-foreground">Random missing values</p>
                  </div>
                  <div>
                    <Label>Site Heterogeneity ({(siteHeterogeneity * 100).toFixed(0)}%)</Label>
                    <div className="flex items-center gap-2">
                      <Input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={siteHeterogeneity}
                        onChange={(e) => setSiteHeterogeneity(parseFloat(e.target.value))}
                        className="mt-1"
                      />
                      <span className="text-sm w-12">{(siteHeterogeneity * 100).toFixed(0)}%</span>
                    </div>
                    <p className="text-xs text-muted-foreground">Variability between sites</p>
                  </div>
                </div>
              </div>

              {/* Generate Button */}
              <Button
                className="w-full"
                size="lg"
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
                    <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                    Generating Complete Study...
                  </>
                ) : (
                  <>
                    <Database className="h-5 w-5 mr-2" />
                    Generate Complete Study
                  </>
                )}
              </Button>

              <p className="text-sm text-muted-foreground text-center">
                After generation, view individual datasets in the Vitals, Demographics, Labs, and AE tabs above
              </p>
            </CardContent>
          </Card>

          {/* Summary Card (shown after generation) */}
          {(vitalsData.length > 0 || demographicsData.length > 0 || labsData.length > 0 || aeData.length > 0) && (
            <Card className="border-green-500">
              <CardHeader>
                <CardTitle>📊 Generated Data Summary</CardTitle>
                <CardDescription>All datasets are coordinated and ready for analysis</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Activity className="h-4 w-4 text-blue-600" />
                      <span className="font-medium text-blue-900">Vitals</span>
                    </div>
                    <p className="text-2xl font-bold text-blue-600">{vitalsData.length}</p>
                    <p className="text-xs text-blue-700">records</p>
                  </div>
                  <div className="p-4 bg-purple-50 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Users className="h-4 w-4 text-purple-600" />
                      <span className="font-medium text-purple-900">Demographics</span>
                    </div>
                    <p className="text-2xl font-bold text-purple-600">{demographicsData.length}</p>
                    <p className="text-xs text-purple-700">subjects</p>
                  </div>
                  <div className="p-4 bg-green-50 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <FlaskConical className="h-4 w-4 text-green-600" />
                      <span className="font-medium text-green-900">Labs</span>
                    </div>
                    <p className="text-2xl font-bold text-green-600">{labsData.length}</p>
                    <p className="text-xs text-green-700">records</p>
                  </div>
                  <div className="p-4 bg-orange-50 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <AlertTriangle className="h-4 w-4 text-orange-600" />
                      <span className="font-medium text-orange-900">AEs</span>
                    </div>
                    <p className="text-2xl font-bold text-orange-600">{aeData.length}</p>
                    <p className="text-xs text-orange-700">events</p>
                  </div>
                </div>
                <div className="mt-4 flex gap-2">
                  <Button onClick={() => downloadCSV(vitalsData, "vitals.csv")} variant="outline" size="sm">
                    <Download className="h-3 w-3 mr-1" /> Vitals CSV
                  </Button>
                  <Button onClick={() => downloadCSV(demographicsData, "demographics.csv")} variant="outline" size="sm">
                    <Download className="h-3 w-3 mr-1" /> Demographics CSV
                  </Button>
                  <Button onClick={() => downloadCSV(labsData, "labs.csv")} variant="outline" size="sm">
                    <Download className="h-3 w-3 mr-1" /> Labs CSV
                  </Button>
                  <Button onClick={() => downloadCSV(aeData, "adverse_events.csv")} variant="outline" size="sm">
                    <Download className="h-3 w-3 mr-1" /> AE CSV
                  </Button>
                  <Button onClick={handleSaveDataset} variant="default" size="sm" className="ml-auto bg-blue-600 hover:bg-blue-700">
                    <Database className="h-3 w-3 mr-1" /> Save Dataset
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
