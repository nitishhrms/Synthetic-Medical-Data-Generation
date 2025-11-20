import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { analyticsApi, dataGenerationApi } from "@/services/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Database, Download, CheckCircle2, FileJson, AlertCircle } from "lucide-react";

export default function AdamGeneration() {
  const [generatedDatasets, setGeneratedDatasets] = useState<any>(null);
  const [studyId, setStudyId] = useState("STUDY001");

  // Generate all ADaM datasets
  const generateAdamMutation = useMutation({
    mutationFn: async () => {
      // First generate sample data
      const pilotData = await dataGenerationApi.getPilotData();

      // Extract demographics
      const demographics = pilotData.map((record: any, index: number) => ({
        SubjectID: record.SubjectID || `SUB-${String(index + 1).padStart(3, "0")}`,
        TreatmentArm: index % 2 === 0 ? "Active" : "Placebo",
        Age: 55 + Math.floor(Math.random() * 20),
        Gender: Math.random() > 0.5 ? "Male" : "Female",
        Race: "White",
        Ethnicity: "Not Hispanic or Latino",
        Weight: 70 + Math.random() * 30,
        Height: 160 + Math.random() * 25,
      }));

      const uniqueSubjects = Array.from(
        new Map(demographics.map((d: any) => [d.SubjectID, d])).values()
      ).slice(0, 100);

      // Generate vitals data
      const vitalsData = pilotData.slice(0, 200);

      // Generate mock labs data
      const labsData = uniqueSubjects.flatMap((subject: any) =>
        ["Screening", "Week 4", "Week 12"].map((visit) => ({
          SubjectID: subject.SubjectID,
          VisitName: visit,
          TestName: "Hemoglobin",
          TestResult: 12 + Math.random() * 4,
          Unit: "g/dL",
          ReferenceRange: "12-16",
        }))
      );

      // Generate mock AE data
      const aeData = uniqueSubjects.slice(0, 30).map((subject: any, index: number) => ({
        SubjectID: subject.SubjectID,
        AETERM: ["Headache", "Nausea", "Fatigue", "Dizziness"][index % 4],
        AEDECOD: ["Headache", "Nausea", "Fatigue", "Dizziness"][index % 4],
        AEBODSYS: "General disorders and administration site conditions",
        AESEV: ["Mild", "Moderate", "Severe"][index % 3],
        AESER: index % 10 === 0 ? "Y" : "N",
        AEREL: ["Related", "Not Related"][index % 2],
        AESTDTC: "2025-01-15",
        AEENDTC: "2025-01-20",
      }));

      // Generate mock survival data
      const survivalAnalysis = await analyticsApi.comprehensiveSurvivalAnalysis({
        demographics_data: uniqueSubjects,
        indication: "oncology",
        median_survival_active: 18.0,
        median_survival_placebo: 12.0,
        seed: 42,
      });

      // Generate all ADaM datasets
      return analyticsApi.generateAllAdamDatasets({
        demographics_data: uniqueSubjects,
        vitals_data: vitalsData,
        labs_data: labsData,
        ae_data: aeData,
        survival_data: survivalAnalysis.survival_data,
        study_id: studyId,
      });
    },
    onSuccess: (data) => {
      setGeneratedDatasets(data);
    },
  });

  const handleDownloadDataset = (datasetName: string, data: any[]) => {
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${datasetName}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadCSV = (datasetName: string, data: any[]) => {
    if (!data || data.length === 0) return;

    const headers = Object.keys(data[0]).join(",");
    const rows = data.map((row) =>
      Object.values(row)
        .map((value) => `"${value}"`)
        .join(",")
    );
    const csv = [headers, ...rows].join("\n");

    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${datasetName}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const datasets = [
    {
      name: "ADSL",
      title: "Subject-Level Analysis Dataset",
      description: "One record per subject with demographics, treatment, and disposition",
      data: generatedDatasets?.datasets?.ADSL || [],
      icon: Database,
      color: "text-blue-500",
    },
    {
      name: "ADTTE",
      title: "Time-to-Event Analysis Dataset",
      description: "Survival and time-to-event data for efficacy analysis",
      data: generatedDatasets?.datasets?.ADTTE || [],
      icon: Database,
      color: "text-purple-500",
    },
    {
      name: "ADAE",
      title: "Adverse Event Analysis Dataset",
      description: "Analysis-ready adverse event data with treatment-emergent flags",
      data: generatedDatasets?.datasets?.ADAE || [],
      icon: Database,
      color: "text-red-500",
    },
    {
      name: "BDS_VITALS",
      title: "Basic Data Structure - Vitals",
      description: "Longitudinal vitals data with baseline and change from baseline",
      data: generatedDatasets?.datasets?.BDS_VITALS || [],
      icon: Database,
      color: "text-green-500",
    },
    {
      name: "BDS_LABS",
      title: "Basic Data Structure - Labs",
      description: "Longitudinal laboratory data with analysis flags",
      data: generatedDatasets?.datasets?.BDS_LABS || [],
      icon: Database,
      color: "text-yellow-500",
    },
  ];

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">ADaM Dataset Generation</h1>
          <p className="text-muted-foreground">
            Generate CDISC ADaM datasets for regulatory submissions (FDA/EMA)
          </p>
        </div>
        <Database className="h-8 w-8 text-primary" />
      </div>

      {/* Configuration Panel */}
      <Card>
        <CardHeader>
          <CardTitle>Dataset Configuration</CardTitle>
          <CardDescription>
            Configure ADaM dataset generation parameters
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Study ID</label>
              <input
                type="text"
                value={studyId}
                onChange={(e) => setStudyId(e.target.value)}
                className="w-full border rounded px-3 py-2"
                placeholder="e.g., STUDY001"
              />
            </div>
            <div className="flex items-end">
              <Button
                onClick={() => generateAdamMutation.mutate()}
                disabled={generateAdamMutation.isPending}
                className="w-full"
              >
                {generateAdamMutation.isPending ? "Generating..." : "Generate All ADaM Datasets"}
              </Button>
            </div>
          </div>

          {generatedDatasets && (
            <Alert>
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              <AlertDescription>
                Successfully generated {Object.keys(generatedDatasets.datasets).length} ADaM datasets
                with {generatedDatasets.summary?.total_records || 0} total records
              </AlertDescription>
            </Alert>
          )}

          {generateAdamMutation.isError && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {generateAdamMutation.error?.message || "Failed to generate ADaM datasets"}
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* CDISC ADaM Information */}
      <Card>
        <CardHeader>
          <CardTitle>About CDISC ADaM</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p className="text-muted-foreground">
            The Analysis Data Model (ADaM) is a CDISC standard for creating analysis-ready datasets
            for regulatory submissions. ADaM datasets are required by the FDA and EMA for all New Drug
            Applications (NDAs) and Biologics License Applications (BLAs).
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-1">
              <h4 className="font-semibold">ADSL</h4>
              <p className="text-muted-foreground text-xs">
                Subject-level data: one record per subject with all key analysis variables
              </p>
            </div>
            <div className="space-y-1">
              <h4 className="font-semibold">ADTTE</h4>
              <p className="text-muted-foreground text-xs">
                Time-to-event data for survival analysis (OS, PFS, etc.)
              </p>
            </div>
            <div className="space-y-1">
              <h4 className="font-semibold">ADAE</h4>
              <p className="text-muted-foreground text-xs">
                Adverse event analysis data with treatment-emergent flags
              </p>
            </div>
            <div className="space-y-1">
              <h4 className="font-semibold">BDS</h4>
              <p className="text-muted-foreground text-xs">
                Basic Data Structure for longitudinal endpoints (vitals, labs)
              </p>
            </div>
            <div className="space-y-1">
              <h4 className="font-semibold">Compliance</h4>
              <p className="text-muted-foreground text-xs">
                Full compliance with CDISC ADaM IG v1.3
              </p>
            </div>
            <div className="space-y-1">
              <h4 className="font-semibold">Validation</h4>
              <p className="text-muted-foreground text-xs">
                Includes all required variables and controlled terminology
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {generatedDatasets && (
        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList className="grid w-full grid-cols-6">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="adsl">ADSL</TabsTrigger>
            <TabsTrigger value="adtte">ADTTE</TabsTrigger>
            <TabsTrigger value="adae">ADAE</TabsTrigger>
            <TabsTrigger value="bds-vitals">BDS Vitals</TabsTrigger>
            <TabsTrigger value="bds-labs">BDS Labs</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {datasets.map((dataset) => (
                <Card key={dataset.name}>
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <dataset.icon className={`h-5 w-5 ${dataset.color}`} />
                      <Badge variant="secondary">{dataset.data.length} records</Badge>
                    </div>
                    <CardTitle className="text-lg">{dataset.name}</CardTitle>
                    <CardDescription className="text-xs">{dataset.title}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground mb-4">{dataset.description}</p>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDownloadDataset(dataset.name, dataset.data)}
                        className="flex-1"
                      >
                        <FileJson className="h-4 w-4 mr-1" />
                        JSON
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDownloadCSV(dataset.name, dataset.data)}
                        className="flex-1"
                      >
                        <Download className="h-4 w-4 mr-1" />
                        CSV
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Generation Summary */}
            <Card>
              <CardHeader>
                <CardTitle>Generation Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Study ID</p>
                    <p className="text-xl font-semibold">{generatedDatasets.summary?.study_id || studyId}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Total Datasets</p>
                    <p className="text-xl font-semibold">
                      {Object.keys(generatedDatasets.datasets).length}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Total Records</p>
                    <p className="text-xl font-semibold">{generatedDatasets.summary?.total_records || 0}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">CDISC Compliant</p>
                    <p className="text-xl font-semibold text-green-600">
                      <CheckCircle2 className="h-6 w-6 inline" />
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* ADSL Tab */}
          <TabsContent value="adsl" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>ADSL - Subject-Level Analysis Dataset</CardTitle>
                <CardDescription>
                  One record per subject with demographics, treatment, and disposition
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <p className="text-sm text-muted-foreground">
                      {datasets[0].data.length} subjects
                    </p>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDownloadDataset("ADSL", datasets[0].data)}
                      >
                        <FileJson className="h-4 w-4 mr-2" />
                        Download JSON
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDownloadCSV("ADSL", datasets[0].data)}
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Download CSV
                      </Button>
                    </div>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-muted">
                        <tr>
                          {datasets[0].data[0] &&
                            Object.keys(datasets[0].data[0])
                              .slice(0, 10)
                              .map((key) => (
                                <th key={key} className="px-3 py-2 text-left font-semibold">
                                  {key}
                                </th>
                              ))}
                        </tr>
                      </thead>
                      <tbody>
                        {datasets[0].data.slice(0, 10).map((row: any, index: number) => (
                          <tr key={index} className="border-b">
                            {Object.values(row)
                              .slice(0, 10)
                              .map((value: any, i: number) => (
                                <td key={i} className="px-3 py-2">
                                  {String(value)}
                                </td>
                              ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Showing first 10 records and 10 columns. Download full dataset for complete data.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* ADTTE Tab */}
          <TabsContent value="adtte" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>ADTTE - Time-to-Event Analysis Dataset</CardTitle>
                <CardDescription>
                  Survival and time-to-event data for efficacy analysis
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <p className="text-sm text-muted-foreground">
                      {datasets[1].data.length} records
                    </p>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDownloadDataset("ADTTE", datasets[1].data)}
                      >
                        <FileJson className="h-4 w-4 mr-2" />
                        Download JSON
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDownloadCSV("ADTTE", datasets[1].data)}
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Download CSV
                      </Button>
                    </div>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-muted">
                        <tr>
                          {datasets[1].data[0] &&
                            Object.keys(datasets[1].data[0])
                              .slice(0, 8)
                              .map((key) => (
                                <th key={key} className="px-3 py-2 text-left font-semibold">
                                  {key}
                                </th>
                              ))}
                        </tr>
                      </thead>
                      <tbody>
                        {datasets[1].data.slice(0, 10).map((row: any, index: number) => (
                          <tr key={index} className="border-b">
                            {Object.values(row)
                              .slice(0, 8)
                              .map((value: any, i: number) => (
                                <td key={i} className="px-3 py-2">
                                  {String(value)}
                                </td>
                              ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Showing first 10 records and 8 columns. Download full dataset for complete data.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* ADAE Tab */}
          <TabsContent value="adae" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>ADAE - Adverse Event Analysis Dataset</CardTitle>
                <CardDescription>
                  Analysis-ready adverse event data with treatment-emergent flags
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <p className="text-sm text-muted-foreground">
                      {datasets[2].data.length} adverse events
                    </p>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDownloadDataset("ADAE", datasets[2].data)}
                      >
                        <FileJson className="h-4 w-4 mr-2" />
                        Download JSON
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDownloadCSV("ADAE", datasets[2].data)}
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Download CSV
                      </Button>
                    </div>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-muted">
                        <tr>
                          {datasets[2].data[0] &&
                            Object.keys(datasets[2].data[0])
                              .slice(0, 8)
                              .map((key) => (
                                <th key={key} className="px-3 py-2 text-left font-semibold">
                                  {key}
                                </th>
                              ))}
                        </tr>
                      </thead>
                      <tbody>
                        {datasets[2].data.slice(0, 10).map((row: any, index: number) => (
                          <tr key={index} className="border-b">
                            {Object.values(row)
                              .slice(0, 8)
                              .map((value: any, i: number) => (
                                <td key={i} className="px-3 py-2">
                                  {String(value)}
                                </td>
                              ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Showing first 10 records and 8 columns. Download full dataset for complete data.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* BDS Vitals Tab */}
          <TabsContent value="bds-vitals" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>BDS - Vital Signs</CardTitle>
                <CardDescription>
                  Longitudinal vitals data with baseline and change from baseline
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <p className="text-sm text-muted-foreground">
                      {datasets[3].data.length} vitals observations
                    </p>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDownloadDataset("BDS_VITALS", datasets[3].data)}
                      >
                        <FileJson className="h-4 w-4 mr-2" />
                        Download JSON
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDownloadCSV("BDS_VITALS", datasets[3].data)}
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Download CSV
                      </Button>
                    </div>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-muted">
                        <tr>
                          {datasets[3].data[0] &&
                            Object.keys(datasets[3].data[0])
                              .slice(0, 8)
                              .map((key) => (
                                <th key={key} className="px-3 py-2 text-left font-semibold">
                                  {key}
                                </th>
                              ))}
                        </tr>
                      </thead>
                      <tbody>
                        {datasets[3].data.slice(0, 10).map((row: any, index: number) => (
                          <tr key={index} className="border-b">
                            {Object.values(row)
                              .slice(0, 8)
                              .map((value: any, i: number) => (
                                <td key={i} className="px-3 py-2">
                                  {String(value)}
                                </td>
                              ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Showing first 10 records and 8 columns. Download full dataset for complete data.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* BDS Labs Tab */}
          <TabsContent value="bds-labs" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>BDS - Laboratory Tests</CardTitle>
                <CardDescription>
                  Longitudinal laboratory data with analysis flags
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <p className="text-sm text-muted-foreground">
                      {datasets[4].data.length} lab observations
                    </p>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDownloadDataset("BDS_LABS", datasets[4].data)}
                      >
                        <FileJson className="h-4 w-4 mr-2" />
                        Download JSON
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDownloadCSV("BDS_LABS", datasets[4].data)}
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Download CSV
                      </Button>
                    </div>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-muted">
                        <tr>
                          {datasets[4].data[0] &&
                            Object.keys(datasets[4].data[0])
                              .slice(0, 8)
                              .map((key) => (
                                <th key={key} className="px-3 py-2 text-left font-semibold">
                                  {key}
                                </th>
                              ))}
                        </tr>
                      </thead>
                      <tbody>
                        {datasets[4].data.slice(0, 10).map((row: any, index: number) => (
                          <tr key={index} className="border-b">
                            {Object.values(row)
                              .slice(0, 8)
                              .map((value: any, i: number) => (
                                <td key={i} className="px-3 py-2">
                                  {String(value)}
                                </td>
                              ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Showing first 10 records and 8 columns. Download full dataset for complete data.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}
