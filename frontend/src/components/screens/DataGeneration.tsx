import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { dataGenerationApi } from "@/services/api";
import type { GenerationMethod, VitalsRecord } from "@/types";
import { Download, Loader2 } from "lucide-react";

export function DataGeneration() {
  const [selectedMethod, setSelectedMethod] = useState<GenerationMethod>("mvn");
  const [nPerArm, setNPerArm] = useState(50);
  const [targetEffect, setTargetEffect] = useState(-5.0);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedData, setGeneratedData] = useState<VitalsRecord[] | null>(null);
  const [metadata, setMetadata] = useState<any>(null);
  const [error, setError] = useState("");

  const methods = [
    {
      id: "mvn" as GenerationMethod,
      name: "MVN",
      description: "Multivariate Normal - Fast, statistically realistic",
      speed: "~29K records/sec",
    },
    {
      id: "bootstrap" as GenerationMethod,
      name: "Bootstrap",
      description: "Resampling from real data with jitter",
      speed: "~140K records/sec",
    },
    {
      id: "rules" as GenerationMethod,
      name: "Rules",
      description: "Deterministic business-rule driven",
      speed: "~80K records/sec",
    },
    {
      id: "llm" as GenerationMethod,
      name: "LLM",
      description: "OpenAI GPT-4o-mini powered generation",
      speed: "~70 records/sec",
    },
  ];

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError("");
    setGeneratedData(null);

    try {
      let response;
      const params = {
        n_per_arm: nPerArm,
        target_effect: targetEffect,
        seed: Math.floor(Math.random() * 10000),
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
        case "llm":
          response = await dataGenerationApi.generateLLM({
            ...params,
            indication: "Hypertension",
          });
          break;
      }

      setGeneratedData(response.data);
      setMetadata(response.metadata);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setIsGenerating(false);
    }
  };

  const downloadCSV = () => {
    if (!generatedData) return;

    const headers = ["SubjectID", "VisitName", "TreatmentArm", "SystolicBP", "DiastolicBP", "HeartRate", "Temperature"];
    const csvContent = [
      headers.join(","),
      ...generatedData.map((row) =>
        headers.map((h) => row[h as keyof VitalsRecord]).join(",")
      ),
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `synthetic_vitals_${selectedMethod}_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-8 space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Generate Synthetic Data</h2>
        <p className="text-muted-foreground">
          Create realistic clinical trial vitals data using multiple generation methods
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Generation Method</CardTitle>
            <CardDescription>
              Select a method to generate synthetic vitals data
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3">
              {methods.map((method) => (
                <button
                  key={method.id}
                  onClick={() => setSelectedMethod(method.id)}
                  className={`p-4 border rounded-lg text-left transition-all ${
                    selectedMethod === method.id
                      ? "border-primary bg-primary/5"
                      : "hover:border-muted-foreground/50"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold">{method.name}</span>
                    <Badge variant={selectedMethod === method.id ? "default" : "outline"}>
                      {method.speed}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">{method.description}</p>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Parameters</CardTitle>
            <CardDescription>
              Configure generation parameters
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="nPerArm">Subjects Per Arm</Label>
              <Input
                id="nPerArm"
                type="number"
                value={nPerArm}
                onChange={(e) => setNPerArm(parseInt(e.target.value))}
                min={1}
                max={1000}
              />
              <p className="text-xs text-muted-foreground">
                Number of subjects in each treatment arm (Active and Placebo)
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="targetEffect">Target Effect (mmHg)</Label>
              <Input
                id="targetEffect"
                type="number"
                value={targetEffect}
                onChange={(e) => setTargetEffect(parseFloat(e.target.value))}
                step={0.1}
              />
              <p className="text-xs text-muted-foreground">
                Target systolic BP reduction in Active arm (negative for reduction)
              </p>
            </div>

            {error && (
              <div className="text-sm text-destructive bg-destructive/10 p-3 rounded-md">
                {error}
              </div>
            )}

            <Button
              onClick={handleGenerate}
              className="w-full"
              disabled={isGenerating}
            >
              {isGenerating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generating...
                </>
              ) : (
                `Generate with ${methods.find(m => m.id === selectedMethod)?.name}`
              )}
            </Button>

            {metadata && (
              <div className="p-3 bg-muted rounded-lg space-y-1">
                <p className="text-sm font-medium">Generation Complete</p>
                <div className="text-xs text-muted-foreground space-y-0.5">
                  <p>Records: {metadata.records}</p>
                  <p>Subjects: {metadata.subjects}</p>
                  <p>Time: {metadata.generation_time_ms}ms</p>
                  <p>Method: {metadata.method}</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {generatedData && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Generated Data Preview</CardTitle>
                <CardDescription>
                  Showing first 10 records of {generatedData.length} total
                </CardDescription>
              </div>
              <Button onClick={downloadCSV} variant="outline">
                <Download className="mr-2 h-4 w-4" />
                Download CSV
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Subject ID</TableHead>
                    <TableHead>Visit</TableHead>
                    <TableHead>Arm</TableHead>
                    <TableHead>SBP</TableHead>
                    <TableHead>DBP</TableHead>
                    <TableHead>HR</TableHead>
                    <TableHead>Temp</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {generatedData.slice(0, 10).map((row, idx) => (
                    <TableRow key={idx}>
                      <TableCell className="font-mono text-sm">{row.SubjectID}</TableCell>
                      <TableCell>{row.VisitName}</TableCell>
                      <TableCell>
                        <Badge variant={row.TreatmentArm === "Active" ? "default" : "secondary"}>
                          {row.TreatmentArm}
                        </Badge>
                      </TableCell>
                      <TableCell>{row.SystolicBP}</TableCell>
                      <TableCell>{row.DiastolicBP}</TableCell>
                      <TableCell>{row.HeartRate}</TableCell>
                      <TableCell>{row.Temperature.toFixed(1)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
