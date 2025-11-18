import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import {
  Database,
  Filter,
  BarChart3,
  Activity,
  Download,
  Play,
  AlertCircle,
  CheckCircle2,
  TrendingUp,
  Users,
  Calendar,
} from "lucide-react";
import { api } from "@/services/api";

interface VitalsRecord {
  SubjectID: string;
  VisitName: string;
  TreatmentArm: string;
  SystolicBP: number;
  DiastolicBP: number;
  HeartRate: number;
  Temperature: number;
}

interface TreatmentEffectResult {
  endpoint: string;
  visit: string;
  active: {
    n: number;
    mean: number;
    std: number;
    se: number;
  };
  placebo: {
    n: number;
    mean: number;
    std: number;
    se: number;
  };
  treatment_effect: {
    difference: number;
    se_difference: number;
    t_statistic: number;
    p_value: number;
    ci_95_lower: number;
    ci_95_upper: number;
    significant: boolean;
  };
}

export function DaftAnalytics() {
  const [data, setData] = useState<VitalsRecord[]>([]);
  const [filteredData, setFilteredData] = useState<VitalsRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Analysis results
  const [treatmentEffect, setTreatmentEffect] = useState<TreatmentEffectResult | null>(null);
  const [aggregationResults, setAggregationResults] = useState<any>(null);
  const [qcResults, setQcResults] = useState<any>(null);

  // Filters
  const [treatmentArm, setTreatmentArm] = useState<string>("");
  const [visitName, setVisitName] = useState<string>("");
  const [condition, setCondition] = useState<string>("");

  const loadSampleData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Load sample data from the data generation service
      const response = await fetch("http://localhost:8002/generate/mvn", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ n_per_arm: 50, target_effect: -5.0 }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      // Handle both response formats: direct array or wrapped in data property
      let dataArray: VitalsRecord[];

      if (Array.isArray(result)) {
        // Direct array response
        dataArray = result;
      } else if (result.data && Array.isArray(result.data)) {
        // Wrapped response with data property
        dataArray = result.data;
      } else {
        console.error("Invalid result structure:", result);
        throw new Error("Invalid response format: expected array or object with data property");
      }

      setData(dataArray);
      setFilteredData(dataArray);
      const recordCount = result.metadata?.records ?? dataArray.length;
      setSuccess(`Loaded ${recordCount} records`);
    } catch (err: any) {
      setError(`Failed to load data: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("http://localhost:8007/daft/filter", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          data,
          treatment_arm: treatmentArm || undefined,
          visit_name: visitName || undefined,
          condition: condition || undefined,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      if (!result.filtered_data || !Array.isArray(result.filtered_data)) {
        throw new Error("Invalid response format: missing or invalid filtered_data array");
      }

      setFilteredData(result.filtered_data);
      const rowCount = result.row_count ?? result.filtered_data.length;
      setSuccess(`Filtered to ${rowCount} records`);
    } catch (err: any) {
      setError(`Filter failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const aggregateByTreatmentArm = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("http://localhost:8007/daft/aggregate/by-treatment-arm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ data: filteredData }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      if (!result.aggregations) {
        throw new Error("Invalid response format: missing aggregations");
      }

      setAggregationResults(result.aggregations);
      setSuccess("Aggregation completed successfully");
    } catch (err: any) {
      setError(`Aggregation failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const computeTreatmentEffect = async () => {
    setLoading(true);
    setError(null);
    try {
      console.log("Sending treatment effect request with data:", {
        dataLength: filteredData?.length,
        sampleRecord: filteredData?.[0]
      });

      const response = await fetch("http://localhost:8007/daft/treatment-effect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          data: filteredData,
          endpoint: "SystolicBP",
          visit: "Week 12",
        }),
      });

      console.log("Response status:", response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error("Error response:", errorText);
        throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
      }

      const result = await response.json();
      console.log("Treatment effect result:", result);

      if (!result.treatment_effect) {
        throw new Error("Invalid response format: missing treatment_effect");
      }

      setTreatmentEffect(result.treatment_effect);
      setSuccess("Treatment effect analysis completed");
    } catch (err: any) {
      console.error("Treatment effect error:", err);
      setError(`Analysis failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const applyQualityFlags = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("http://localhost:8007/daft/apply-quality-flags", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ data: filteredData }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      if (!result.qc_summary || !result.data) {
        throw new Error("Invalid response format: missing qc_summary or data");
      }

      setQcResults(result.qc_summary);
      setFilteredData(result.data);
      setSuccess("Quality control flags applied");
    } catch (err: any) {
      setError(`QC failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const exportToParquet = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("http://localhost:8007/daft/export/parquet", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          data: filteredData,
          filename: `daft_export_${Date.now()}.parquet`,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      if (!result.filepath) {
        throw new Error("Invalid response format: missing filepath");
      }

      setSuccess(`Exported to ${result.filepath}`);
    } catch (err: any) {
      setError(`Export failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Database className="h-8 w-8 text-primary" />
            Daft Distributed Analytics
          </h1>
          <p className="text-muted-foreground mt-2">
            High-performance distributed data analysis for clinical trials
          </p>
        </div>
        <Badge variant="outline" className="text-sm">
          Port 8007
        </Badge>
      </div>

      {/* Status Messages */}
      {error && (
        <Card className="p-4 border-destructive bg-destructive/10">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-destructive mt-0.5" />
            <div className="flex-1">
              <p className="font-medium text-destructive">Error</p>
              <p className="text-sm text-destructive/90">{error}</p>
            </div>
            <Button variant="ghost" size="sm" onClick={() => setError(null)}>
              Dismiss
            </Button>
          </div>
        </Card>
      )}

      {success && (
        <Card className="p-4 border-green-500 bg-green-50">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
            <div className="flex-1">
              <p className="font-medium text-green-900">Success</p>
              <p className="text-sm text-green-800">{success}</p>
            </div>
            <Button variant="ghost" size="sm" onClick={() => setSuccess(null)}>
              Dismiss
            </Button>
          </div>
        </Card>
      )}

      <Tabs defaultValue="load" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="load">
            <Database className="h-4 w-4 mr-2" />
            Load Data
          </TabsTrigger>
          <TabsTrigger value="filter">
            <Filter className="h-4 w-4 mr-2" />
            Filter & Transform
          </TabsTrigger>
          <TabsTrigger value="aggregate">
            <BarChart3 className="h-4 w-4 mr-2" />
            Aggregations
          </TabsTrigger>
          <TabsTrigger value="analysis">
            <TrendingUp className="h-4 w-4 mr-2" />
            Analysis
          </TabsTrigger>
          <TabsTrigger value="qc">
            <Activity className="h-4 w-4 mr-2" />
            Quality Control
          </TabsTrigger>
        </TabsList>

        {/* Load Data Tab */}
        <TabsContent value="load" className="space-y-6">
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Load Clinical Data</h2>
            <div className="space-y-4">
              <div className="bg-muted/50 p-4 rounded-lg">
                <p className="text-sm text-muted-foreground mb-2">
                  Load sample data or upload your own clinical trial data
                </p>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium">Current Records:</span> {data?.length ?? 0}
                  </div>
                  <div>
                    <span className="font-medium">Filtered Records:</span> {filteredData?.length ?? 0}
                  </div>
                </div>
              </div>

              <Button onClick={loadSampleData} disabled={loading} className="w-full">
                {loading ? (
                  <>
                    <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                    Loading...
                  </>
                ) : (
                  <>
                    <Database className="h-4 w-4 mr-2" />
                    Load Sample Data (MVN Generator)
                  </>
                )}
              </Button>

              {(data?.length ?? 0) > 0 && (
                <div className="mt-6">
                  <h3 className="font-medium mb-3">Data Preview (First 5 Records)</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm border rounded-lg">
                      <thead className="bg-muted">
                        <tr>
                          <th className="p-2 text-left">Subject ID</th>
                          <th className="p-2 text-left">Visit</th>
                          <th className="p-2 text-left">Arm</th>
                          <th className="p-2 text-right">SBP</th>
                          <th className="p-2 text-right">DBP</th>
                          <th className="p-2 text-right">HR</th>
                          <th className="p-2 text-right">Temp</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.slice(0, 5).map((record, idx) => (
                          <tr key={idx} className="border-t">
                            <td className="p-2">{record.SubjectID}</td>
                            <td className="p-2">{record.VisitName}</td>
                            <td className="p-2">
                              <Badge variant={record.TreatmentArm === "Active" ? "default" : "secondary"}>
                                {record.TreatmentArm}
                              </Badge>
                            </td>
                            <td className="p-2 text-right">{record.SystolicBP}</td>
                            <td className="p-2 text-right">{record.DiastolicBP}</td>
                            <td className="p-2 text-right">{record.HeartRate}</td>
                            <td className="p-2 text-right">{record.Temperature.toFixed(1)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          </Card>
        </TabsContent>

        {/* Filter & Transform Tab */}
        <TabsContent value="filter" className="space-y-6">
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Filter & Transform Data</h2>
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label>Treatment Arm</Label>
                  <select
                    value={treatmentArm}
                    onChange={(e) => setTreatmentArm(e.target.value)}
                    className="w-full mt-1 p-2 border rounded-md"
                  >
                    <option value="">All</option>
                    <option value="Active">Active</option>
                    <option value="Placebo">Placebo</option>
                  </select>
                </div>

                <div>
                  <Label>Visit Name</Label>
                  <select
                    value={visitName}
                    onChange={(e) => setVisitName(e.target.value)}
                    className="w-full mt-1 p-2 border rounded-md"
                  >
                    <option value="">All</option>
                    <option value="Screening">Screening</option>
                    <option value="Day 1">Day 1</option>
                    <option value="Week 4">Week 4</option>
                    <option value="Week 12">Week 12</option>
                  </select>
                </div>

                <div>
                  <Label>Condition</Label>
                  <input
                    type="text"
                    value={condition}
                    onChange={(e) => setCondition(e.target.value)}
                    placeholder="e.g., SystolicBP > 140"
                    className="w-full mt-1 p-2 border rounded-md"
                  />
                </div>
              </div>

              <Button onClick={applyFilters} disabled={loading || (data?.length ?? 0) === 0} className="w-full">
                <Filter className="h-4 w-4 mr-2" />
                Apply Filters
              </Button>
            </div>
          </Card>
        </TabsContent>

        {/* Aggregations Tab */}
        <TabsContent value="aggregate" className="space-y-6">
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Data Aggregations</h2>
            <div className="space-y-4">
              <Button
                onClick={aggregateByTreatmentArm}
                disabled={loading || (filteredData?.length ?? 0) === 0}
                className="w-full"
              >
                <Users className="h-4 w-4 mr-2" />
                Aggregate by Treatment Arm
              </Button>

              {aggregationResults && (
                <div className="mt-6 space-y-4">
                  <h3 className="font-medium">Aggregation Results</h3>
                  <pre className="bg-muted p-4 rounded-lg text-xs overflow-auto max-h-96">
                    {JSON.stringify(aggregationResults, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </Card>
        </TabsContent>

        {/* Analysis Tab */}
        <TabsContent value="analysis" className="space-y-6">
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Treatment Effect Analysis</h2>
            <div className="space-y-4">
              <Button
                onClick={computeTreatmentEffect}
                disabled={loading || (filteredData?.length ?? 0) === 0}
                className="w-full"
              >
                <TrendingUp className="h-4 w-4 mr-2" />
                Compute Treatment Effect (Week 12)
              </Button>

              {treatmentEffect && (
                <div className="mt-6 space-y-4">
                  <h3 className="font-medium">Treatment Effect Results</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <Card className="p-4">
                      <div className="text-sm text-muted-foreground">Active Arm Mean (n={treatmentEffect.active.n})</div>
                      <div className="text-2xl font-bold">{treatmentEffect.active.mean.toFixed(1)} mmHg</div>
                      <div className="text-xs text-muted-foreground mt-1">SD: {treatmentEffect.active.std.toFixed(1)}</div>
                    </Card>
                    <Card className="p-4">
                      <div className="text-sm text-muted-foreground">Placebo Arm Mean (n={treatmentEffect.placebo.n})</div>
                      <div className="text-2xl font-bold">{treatmentEffect.placebo.mean.toFixed(1)} mmHg</div>
                      <div className="text-xs text-muted-foreground mt-1">SD: {treatmentEffect.placebo.std.toFixed(1)}</div>
                    </Card>
                    <Card className="p-4">
                      <div className="text-sm text-muted-foreground">Difference</div>
                      <div className="text-2xl font-bold text-primary">
                        {treatmentEffect.treatment_effect.difference.toFixed(1)} mmHg
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        95% CI: [{treatmentEffect.treatment_effect.ci_95_lower.toFixed(1)}, {treatmentEffect.treatment_effect.ci_95_upper.toFixed(1)}]
                      </div>
                    </Card>
                    <Card className="p-4">
                      <div className="text-sm text-muted-foreground">P-value</div>
                      <div className="text-2xl font-bold">
                        {treatmentEffect.treatment_effect.p_value.toFixed(4)}
                        {treatmentEffect.treatment_effect.significant && (
                          <Badge variant="default" className="ml-2">Significant</Badge>
                        )}
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">t = {treatmentEffect.treatment_effect.t_statistic.toFixed(2)}</div>
                    </Card>
                  </div>
                </div>
              )}
            </div>
          </Card>
        </TabsContent>

        {/* Quality Control Tab */}
        <TabsContent value="qc" className="space-y-6">
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Quality Control</h2>
            <div className="space-y-4">
              <Button
                onClick={applyQualityFlags}
                disabled={loading || (filteredData?.length ?? 0) === 0}
                className="w-full"
              >
                <Activity className="h-4 w-4 mr-2" />
                Apply Quality Control Flags
              </Button>

              {qcResults && (
                <div className="mt-6 space-y-4">
                  <h3 className="font-medium">QC Summary</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <Card className="p-4">
                      <div className="text-sm text-muted-foreground">BP Errors</div>
                      <div className="text-2xl font-bold text-destructive">{qcResults.bp_errors}</div>
                    </Card>
                    <Card className="p-4">
                      <div className="text-sm text-muted-foreground">Abnormal Vitals</div>
                      <div className="text-2xl font-bold text-amber-600">{qcResults.abnormal_vitals}</div>
                    </Card>
                    <Card className="p-4">
                      <div className="text-sm text-muted-foreground">Intervention Needed</div>
                      <div className="text-2xl font-bold text-red-600">{qcResults.intervention_needed}</div>
                    </Card>
                    <Card className="p-4">
                      <div className="text-sm text-muted-foreground">Total Records</div>
                      <div className="text-2xl font-bold">{qcResults.total_records}</div>
                    </Card>
                  </div>
                </div>
              )}

              <div className="pt-4 border-t">
                <h3 className="font-medium mb-3">Export Data</h3>
                <Button onClick={exportToParquet} disabled={loading || (filteredData?.length ?? 0) === 0} className="w-full">
                  <Download className="h-4 w-4 mr-2" />
                  Export to Parquet
                </Button>
              </div>
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
