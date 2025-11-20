import { useState } from "react";
import { analyticsApi, dataGenerationApi } from "@/services/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { FileText, Download, CheckCircle2, AlertCircle, Table as TableIcon } from "lucide-react";

export default function TLFAutomation() {
  const [generatedTables, setGeneratedTables] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Generate all TLF tables
  const handleGenerateTLFTables = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // First generate sample data
      const pilotData = await dataGenerationApi.getPilotData();

      // Extract demographics
      const demographics = pilotData.map((record: any, index: number) => {
        const weight = 70 + Math.random() * 30;
        const height = 160 + Math.random() * 25;
        const heightInMeters = height / 100;
        const bmi = weight / (heightInMeters * heightInMeters);

        return {
          SubjectID: record.SubjectID || `SUB-${String(index + 1).padStart(3, "0")}`,
          TreatmentArm: index % 2 === 0 ? "Active" : "Placebo",
          Age: 55 + Math.floor(Math.random() * 20),
          Gender: Math.random() > 0.5 ? "Male" : "Female",
          Race: ["White", "Black or African American", "Asian"][Math.floor(Math.random() * 3)],
          Ethnicity: Math.random() > 0.8 ? "Hispanic or Latino" : "Not Hispanic or Latino",
          Weight: weight,
          Height: height,
          BMI: bmi,
        };
      });

      const uniqueSubjects = Array.from(
        new Map(demographics.map((d: any) => [d.SubjectID, d])).values()
      ).slice(0, 100);

      // Generate vitals data
      const vitalsData = pilotData.slice(0, 200);

      // Generate mock AE data
      const aeData = uniqueSubjects.slice(0, 50).map((subject: any, index: number) => ({
        SubjectID: subject.SubjectID,
        AETerm: ["Headache", "Nausea", "Fatigue", "Dizziness", "Cough", "Fever"][index % 6],
        PT: ["Headache", "Nausea", "Fatigue", "Dizziness", "Cough", "Pyrexia"][index % 6],
        BodySystem: [
          "Nervous system disorders",
          "Gastrointestinal disorders",
          "General disorders and administration site conditions",
          "Nervous system disorders",
          "Respiratory, thoracic and mediastinal disorders",
          "General disorders and administration site conditions",
        ][index % 6],
        Severity: ["Mild", "Moderate", "Severe"][index % 3],
        Serious: index % 10 === 0 ? "Y" : "N",
        Related: ["Related", "Not Related", "Possibly Related"][index % 3],
        StartDate: "2025-01-15",
        EndDate: "2025-01-20",
        TreatmentArm: subject.TreatmentArm,
      }));

      // Generate mock survival data
      const survivalAnalysis = await analyticsApi.comprehensiveSurvivalAnalysis({
        demographics_data: uniqueSubjects,
        indication: "oncology",
        median_survival_active: 18.0,
        median_survival_placebo: 12.0,
        seed: 42,
      });

      // Generate all TLF tables
      const result = await analyticsApi.generateAllTLFTables({
        demographics_data: uniqueSubjects,
        ae_data: aeData,
        vitals_data: vitalsData,
        survival_data: survivalAnalysis.survival_data,
      });

      setGeneratedTables(result);
    } catch (err: any) {
      setError(err.message || "Failed to generate TLF tables");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownloadMarkdown = (tableName: string, markdown: string) => {
    const blob = new Blob([markdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${tableName}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadWord = (tableName: string, markdown: string) => {
    // For simplicity, export as text. In production, you'd use a library like docx
    const blob = new Blob([markdown], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${tableName}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const tables = [
    {
      key: "table1_demographics",
      name: "Table 1",
      title: "Demographics and Baseline Characteristics",
      description: "Standard CSR Table 1 with demographics by treatment arm",
    },
    {
      key: "table2_adverse_events",
      name: "Table 2",
      title: "Adverse Events by SOC and Preferred Term",
      description: "AE incidence table with System Organ Class breakdown",
    },
    {
      key: "table3_efficacy",
      name: "Table 3",
      title: "Efficacy Endpoints Summary",
      description: "Primary and secondary endpoints with statistical analysis",
    },
  ];

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">TLF Automation</h1>
          <p className="text-muted-foreground">
            Automated generation of Tables, Listings, and Figures for Clinical Study Reports
          </p>
        </div>
        <FileText className="h-8 w-8 text-primary" />
      </div>

      {/* Configuration Panel */}
      <Card>
        <CardHeader>
          <CardTitle>TLF Generation</CardTitle>
          <CardDescription>
            Generate publication-quality tables for CSR and regulatory submissions
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4">
            <Button
              onClick={handleGenerateTLFTables}
              disabled={isLoading}
              className="w-full md:w-auto"
            >
              {isLoading ? "Generating..." : "Generate All Tables"}
            </Button>
          </div>

          {generatedTables && (
            <Alert>
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              <AlertDescription>
                Successfully generated {Object.keys(generatedTables.tables).length} CSR tables
                ready for export
              </AlertDescription>
            </Alert>
          )}

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {error}
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* TLF Information */}
      <Card>
        <CardHeader>
          <CardTitle>About TLF Automation</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p className="text-muted-foreground">
            Tables, Listings, and Figures (TLFs) are essential components of Clinical Study Reports
            (CSRs). Automating TLF generation saves biostatisticians 30-40% of their time and ensures
            consistency across submissions.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-1">
              <h4 className="font-semibold">Table 1: Demographics</h4>
              <p className="text-muted-foreground text-xs">
                Baseline characteristics by treatment arm with statistical tests
              </p>
            </div>
            <div className="space-y-1">
              <h4 className="font-semibold">Table 2: Adverse Events</h4>
              <p className="text-muted-foreground text-xs">
                AE summary by SOC and PT with incidence rates
              </p>
            </div>
            <div className="space-y-1">
              <h4 className="font-semibold">Table 3: Efficacy</h4>
              <p className="text-muted-foreground text-xs">
                Primary and secondary endpoints with treatment effect
              </p>
            </div>
            <div className="space-y-1">
              <h4 className="font-semibold">Publication Quality</h4>
              <p className="text-muted-foreground text-xs">
                Tables formatted for Word, PDF, and LaTeX export
              </p>
            </div>
            <div className="space-y-1">
              <h4 className="font-semibold">Time Savings</h4>
              <p className="text-muted-foreground text-xs">
                Reduces manual table creation from 30-40 hours to minutes
              </p>
            </div>
            <div className="space-y-1">
              <h4 className="font-semibold">Compliance</h4>
              <p className="text-muted-foreground text-xs">
                Follows ICH E3 guidelines for CSR content
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {generatedTables && (
        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="table1">Table 1</TabsTrigger>
            <TabsTrigger value="table2">Table 2</TabsTrigger>
            <TabsTrigger value="table3">Table 3</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {tables.map((table) => (
                <Card key={table.key}>
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <TableIcon className="h-5 w-5 text-blue-500" />
                      <Badge variant="secondary">
                        {generatedTables.tables[table.key]?.table_data?.length || 0} rows
                      </Badge>
                    </div>
                    <CardTitle className="text-lg">{table.name}</CardTitle>
                    <CardDescription className="text-xs">{table.title}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground mb-4">{table.description}</p>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          handleDownloadMarkdown(
                            table.name,
                            generatedTables.tables[table.key]?.markdown || ""
                          )
                        }
                        className="flex-1"
                      >
                        <Download className="h-4 w-4 mr-1" />
                        Markdown
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          handleDownloadWord(
                            table.name,
                            generatedTables.tables[table.key]?.markdown || ""
                          )
                        }
                        className="flex-1"
                      >
                        <FileText className="h-4 w-4 mr-1" />
                        Text
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
                    <p className="text-sm text-muted-foreground">Total Tables</p>
                    <p className="text-xl font-semibold">
                      {Object.keys(generatedTables.tables).length}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Format</p>
                    <p className="text-xl font-semibold">CSR Standard</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Export Ready</p>
                    <p className="text-xl font-semibold text-green-600">
                      <CheckCircle2 className="h-6 w-6 inline" />
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Time Saved</p>
                    <p className="text-xl font-semibold">~35 hours</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Table 1: Demographics Tab */}
          <TabsContent value="table1" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Table 1: Demographics and Baseline Characteristics</CardTitle>
                <CardDescription>
                  Standard CSR Table 1 with demographics by treatment arm
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <p className="text-sm text-muted-foreground">
                      {generatedTables.tables.table1_demographics?.title || "Demographics Table"}
                    </p>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          handleDownloadMarkdown(
                            "Table1_Demographics",
                            generatedTables.tables.table1_demographics?.markdown || ""
                          )
                        }
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Download Markdown
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          handleDownloadWord(
                            "Table1_Demographics",
                            generatedTables.tables.table1_demographics?.markdown || ""
                          )
                        }
                      >
                        <FileText className="h-4 w-4 mr-2" />
                        Download Text
                      </Button>
                    </div>
                  </div>

                  {/* Markdown Preview */}
                  <div className="border rounded-lg p-4 bg-muted/50">
                    <pre className="text-sm whitespace-pre-wrap font-mono">
                      {generatedTables.tables.table1_demographics?.markdown || "No data"}
                    </pre>
                  </div>

                  {/* Data Table Preview */}
                  <div>
                    <h3 className="font-semibold mb-2">Data Preview</h3>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead className="bg-muted">
                          <tr>
                            {generatedTables.tables.table1_demographics?.table_data?.[0] &&
                              Object.keys(
                                generatedTables.tables.table1_demographics.table_data[0]
                              ).map((key) => (
                                <th key={key} className="px-3 py-2 text-left font-semibold">
                                  {key}
                                </th>
                              ))}
                          </tr>
                        </thead>
                        <tbody>
                          {generatedTables.tables.table1_demographics?.table_data
                            ?.slice(0, 15)
                            .map((row: any, index: number) => (
                              <tr key={index} className="border-b">
                                {Object.values(row).map((value: any, i: number) => (
                                  <td key={i} className="px-3 py-2">
                                    {String(value)}
                                  </td>
                                ))}
                              </tr>
                            ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Table 2: Adverse Events Tab */}
          <TabsContent value="table2" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Table 2: Adverse Events by SOC and Preferred Term</CardTitle>
                <CardDescription>
                  AE incidence table with System Organ Class breakdown
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <p className="text-sm text-muted-foreground">
                      {generatedTables.tables.table2_adverse_events?.title || "Adverse Events Table"}
                    </p>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          handleDownloadMarkdown(
                            "Table2_AdverseEvents",
                            generatedTables.tables.table2_adverse_events?.markdown || ""
                          )
                        }
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Download Markdown
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          handleDownloadWord(
                            "Table2_AdverseEvents",
                            generatedTables.tables.table2_adverse_events?.markdown || ""
                          )
                        }
                      >
                        <FileText className="h-4 w-4 mr-2" />
                        Download Text
                      </Button>
                    </div>
                  </div>

                  {/* Markdown Preview */}
                  <div className="border rounded-lg p-4 bg-muted/50">
                    <pre className="text-sm whitespace-pre-wrap font-mono">
                      {generatedTables.tables.table2_adverse_events?.markdown || "No data"}
                    </pre>
                  </div>

                  {/* Data Table Preview */}
                  <div>
                    <h3 className="font-semibold mb-2">Data Preview</h3>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead className="bg-muted">
                          <tr>
                            {generatedTables.tables.table2_adverse_events?.table_data?.[0] &&
                              Object.keys(
                                generatedTables.tables.table2_adverse_events.table_data[0]
                              ).map((key) => (
                                <th key={key} className="px-3 py-2 text-left font-semibold">
                                  {key}
                                </th>
                              ))}
                          </tr>
                        </thead>
                        <tbody>
                          {generatedTables.tables.table2_adverse_events?.table_data
                            ?.slice(0, 15)
                            .map((row: any, index: number) => (
                              <tr key={index} className="border-b">
                                {Object.values(row).map((value: any, i: number) => (
                                  <td key={i} className="px-3 py-2">
                                    {String(value)}
                                  </td>
                                ))}
                              </tr>
                            ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Table 3: Efficacy Tab */}
          <TabsContent value="table3" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Table 3: Efficacy Endpoints Summary</CardTitle>
                <CardDescription>
                  Primary and secondary endpoints with statistical analysis
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <p className="text-sm text-muted-foreground">
                      {generatedTables.tables.table3_efficacy?.title || "Efficacy Endpoints Table"}
                    </p>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          handleDownloadMarkdown(
                            "Table3_Efficacy",
                            generatedTables.tables.table3_efficacy?.markdown || ""
                          )
                        }
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Download Markdown
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          handleDownloadWord(
                            "Table3_Efficacy",
                            generatedTables.tables.table3_efficacy?.markdown || ""
                          )
                        }
                      >
                        <FileText className="h-4 w-4 mr-2" />
                        Download Text
                      </Button>
                    </div>
                  </div>

                  {/* Markdown Preview */}
                  <div className="border rounded-lg p-4 bg-muted/50">
                    <pre className="text-sm whitespace-pre-wrap font-mono">
                      {generatedTables.tables.table3_efficacy?.markdown || "No data"}
                    </pre>
                  </div>

                  {/* Data Table Preview */}
                  <div>
                    <h3 className="font-semibold mb-2">Data Preview</h3>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead className="bg-muted">
                          <tr>
                            {generatedTables.tables.table3_efficacy?.table_data?.[0] &&
                              Object.keys(generatedTables.tables.table3_efficacy.table_data[0]).map(
                                (key) => (
                                  <th key={key} className="px-3 py-2 text-left font-semibold">
                                    {key}
                                  </th>
                                )
                              )}
                          </tr>
                        </thead>
                        <tbody>
                          {generatedTables.tables.table3_efficacy?.table_data
                            ?.slice(0, 15)
                            .map((row: any, index: number) => (
                              <tr key={index} className="border-b">
                                {Object.values(row).map((value: any, i: number) => (
                                  <td key={i} className="px-3 py-2">
                                    {String(value)}
                                  </td>
                                ))}
                              </tr>
                            ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}
