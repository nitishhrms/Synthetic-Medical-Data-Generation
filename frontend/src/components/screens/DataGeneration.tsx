import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { dataGenerationApi } from "@/services/api";
import { useData } from "@/contexts/DataContext";
import { Download, Loader2, AlertCircle, Activity, Users, FlaskConical, AlertTriangle, Database } from "lucide-react";

export function DataGeneration() {
  const { setGeneratedData, setPilotData } = useData();

  // Common state
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("vitals");

  // Vitals state
  const [vitalsData, setVitalsData] = useState<any[]>([]);
  const [vitalsMetadata, setVitalsMetadata] = useState<any>(null);
  const [nPerArm, setNPerArm] = useState(50);
  const [targetEffect, setTargetEffect] = useState(-5.0);
  const [selectedMethod, setSelectedMethod] = useState<string>("mvn");

  // Demographics state
  const [demographicsData, setDemographicsData] = useState<any[]>([]);
  const [demographicsMetadata, setDemographicsMetadata] = useState<any>(null);
  const [demographicsN, setDemographicsN] = useState(100);

  // Labs state
  const [labsData, setLabsData] = useState<any[]>([]);
  const [labsMetadata, setLabsMetadata] = useState<any>(null);
  const [labsN, setLabsN] = useState(100);

  // AE state
  const [aeData, setAeData] = useState<any[]>([]);
  const [aeMetadata, setAeMetadata] = useState<any>(null);
  const [aeN, setAeN] = useState(30);

  // Real data state
  const [realDataLoaded, setRealDataLoaded] = useState(false);
  const [realVitalsCount, setRealVitalsCount] = useState(0);
  const [realDemoCount, setRealDemoCount] = useState(0);
  const [realAeCount, setRealAeCount] = useState(0);

  const methods = [
    { id: "mvn", name: "MVN", speed: "~29K records/sec" },
    { id: "bootstrap", name: "Bootstrap", speed: "~140K records/sec" },
    { id: "rules", name: "Rules", speed: "~80K records/sec" },
    { id: "bayesian", name: "Bayesian", speed: "~5K records/sec" },
    { id: "mice", name: "MICE", speed: "~3K records/sec" },
  ];

  const handleGenerateVitals = async () => {
    setIsGenerating(true);
    setError("");

    try {
      let response;
      const params = { n_per_arm: nPerArm, target_effect: targetEffect, seed: 42 };

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
        seed: 42
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
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Multi-Domain Data Generation</h1>
          <p className="text-muted-foreground">
            Generate comprehensive clinical trial data: Vitals, Demographics, Labs, and Adverse Events
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
          <TabsTrigger value="complete">
            <Database className="h-4 w-4 mr-2" />
            Complete Study
          </TabsTrigger>
        </TabsList>

        {/* VITALS TAB */}
        <TabsContent value="vitals" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Vital Signs Generation</CardTitle>
              <CardDescription>Generate SBP, DBP, Heart Rate, Temperature</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Generation Method</Label>
                  <div className="grid gap-2 mt-2">
                    {methods.map((method) => (
                      <button
                        key={method.id}
                        onClick={() => setSelectedMethod(method.id)}
                        className={`p-3 border rounded-lg text-left ${
                          selectedMethod === method.id ? "border-primary bg-primary/5" : ""
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-medium">{method.name}</span>
                          <Badge variant="outline">{method.speed}</Badge>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
                <div className="space-y-4">
                  <div>
                    <Label>Subjects Per Arm</Label>
                    <Input
                      type="number"
                      value={nPerArm}
                      onChange={(e) => setNPerArm(parseInt(e.target.value) || 0)}
                      min={1}
                      max={1000}
                    />
                  </div>
                  <div>
                    <Label>Target Effect (mmHg)</Label>
                    <Input
                      type="number"
                      value={targetEffect}
                      onChange={(e) => setTargetEffect(parseFloat(e.target.value) || 0)}
                      step={0.1}
                    />
                  </div>
                  <Button onClick={handleGenerateVitals} disabled={isGenerating} className="w-full">
                    {isGenerating ? (
                      <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Generating...</>
                    ) : (
                      `Generate with ${methods.find(m => m.id === selectedMethod)?.name ?? 'MVN'}`
                    )}
                  </Button>
                  {vitalsMetadata && (
                    <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-sm">
                      <p className="font-medium text-green-900">✅ Generated</p>
                      <p className="text-green-700">Records: {vitalsMetadata?.records ?? 0}</p>
                      <p className="text-green-700">Subjects: {vitalsMetadata?.subjects ?? 0}</p>
                    </div>
                  )}
                </div>
              </div>
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
              <CardTitle>Demographics Generation</CardTitle>
              <CardDescription>Generate Age, Gender, Race, Ethnicity, Height, Weight, BMI, Smoking Status</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-muted rounded-lg">
                  <h3 className="font-medium mb-2">Generated Fields:</h3>
                  <ul className="text-sm space-y-1 text-muted-foreground">
                    <li>• Age (18-85, normally distributed)</li>
                    <li>• Gender (Male/Female, 50/50)</li>
                    <li>• Race (US demographics)</li>
                    <li>• Ethnicity (Hispanic/Not Hispanic)</li>
                    <li>• Height (gender-specific, cm)</li>
                    <li>• Weight (age-correlated, kg)</li>
                    <li>• BMI (auto-calculated)</li>
                    <li>• Smoking Status</li>
                  </ul>
                </div>
                <div className="space-y-4">
                  <div>
                    <Label>Number of Subjects</Label>
                    <Input
                      type="number"
                      value={demographicsN}
                      onChange={(e) => setDemographicsN(parseInt(e.target.value) || 0)}
                      min={1}
                      max={1000}
                    />
                  </div>
                  <Button onClick={handleGenerateDemographics} disabled={isGenerating} className="w-full">
                    {isGenerating ? (
                      <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Generating...</>
                    ) : (
                      'Generate Demographics'
                    )}
                  </Button>
                  {demographicsMetadata && (
                    <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-sm">
                      <p className="font-medium text-green-900">✅ Generated</p>
                      <p className="text-green-700">Subjects: {demographicsMetadata?.subjects ?? 0}</p>
                      <p className="text-green-700">Records: {demographicsMetadata?.records ?? 0}</p>
                    </div>
                  )}
                </div>
              </div>
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
              <CardTitle>Lab Results Generation</CardTitle>
              <CardDescription>Generate Hematology, Chemistry, and Lipid panels for multiple visits</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
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
                    <div className="text-xs mt-2">
                      For visits: Screening, Week 4, Week 12
                    </div>
                  </div>
                </div>
                <div className="space-y-4">
                  <div>
                    <Label>Number of Subjects</Label>
                    <Input
                      type="number"
                      value={labsN}
                      onChange={(e) => setLabsN(parseInt(e.target.value) || 0)}
                      min={1}
                      max={1000}
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                      Each subject will have 3 visits = {(labsN * 3).toLocaleString()} lab records
                    </p>
                  </div>
                  <Button onClick={handleGenerateLabs} disabled={isGenerating} className="w-full">
                    {isGenerating ? (
                      <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Generating...</>
                    ) : (
                      'Generate Lab Results'
                    )}
                  </Button>
                  {labsMetadata && (
                    <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-sm">
                      <p className="font-medium text-green-900">✅ Generated</p>
                      <p className="text-green-700">Subjects: {labsMetadata?.subjects ?? 0}</p>
                      <p className="text-green-700">Records: {labsMetadata?.records ?? 0}</p>
                      <p className="text-green-700">Visits: {labsMetadata?.visits_per_subject ?? 0} per subject</p>
                    </div>
                  )}
                </div>
              </div>
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
              <CardTitle>Adverse Events Generation</CardTitle>
              <CardDescription>Generate realistic AEs with MedDRA coding, severity, and causality</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
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
                <div className="space-y-4">
                  <div>
                    <Label>Number of Subjects</Label>
                    <Input
                      type="number"
                      value={aeN}
                      onChange={(e) => setAeN(parseInt(e.target.value) || 0)}
                      min={10}
                      max={100}
                    />
                  </div>
                  <Button onClick={handleGenerateAE} disabled={isGenerating} className="w-full">
                    {isGenerating ? (
                      <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Generating...</>
                    ) : (
                      'Generate Adverse Events'
                    )}
                  </Button>
                  {aeMetadata && (
                    <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-sm">
                      <p className="font-medium text-green-900">✅ Generated</p>
                      <p className="text-green-700">AE Records: {aeMetadata?.records ?? (aeData ?? []).length}</p>
                      <p className="text-green-700">Subjects: {aeN}</p>
                    </div>
                  )}
                </div>
              </div>
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
              <CardTitle>Complete Study Generation</CardTitle>
              <CardDescription>Generate all domains simultaneously for a complete clinical trial dataset</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-start gap-2">
                  <Database className="h-5 w-5 text-blue-600 mt-0.5" />
                  <div className="text-sm text-blue-800">
                    <p className="font-medium mb-1">Complete Study will generate:</p>
                    <ul className="list-disc list-inside space-y-1 ml-2">
                      <li>Demographics for all subjects</li>
                      <li>Vitals for all visits (Screening, Day 1, Week 4, Week 12)</li>
                      <li>Lab results for key visits (Screening, Week 4, Week 12)</li>
                      <li>Adverse events throughout the study</li>
                      <li>Multi-sheet Excel export or separate SDTM CSVs</li>
                    </ul>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Total Subjects (both arms)</Label>
                  <Input type="number" defaultValue={100} min={20} max={500} />
                </div>
                <div>
                  <Label>Target Effect (mmHg)</Label>
                  <Input type="number" defaultValue={-5.0} step={0.1} />
                </div>
              </div>

              <Button
                className="w-full"
                size="lg"
                onClick={async () => {
                  alert("Complete Study generation coming soon!\n\nThis will:\n- Generate all domains\n- Link data via SubjectID\n- Export as multi-sheet Excel or SDTM datasets");
                }}
              >
                <Database className="h-5 w-5 mr-2" />
                Generate Complete Study
              </Button>

              <p className="text-sm text-muted-foreground text-center">
                Complete study generation will create a fully integrated dataset with all domains
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
