import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import {
  FileText,
  CheckSquare,
  Shield,
  Search,
  AlertCircle,
  CheckCircle2,
  ExternalLink,
  Download,
  AlertTriangle,
} from "lucide-react";

interface Citation {
  url: string;
  snippet: string;
  relevance_score: number;
  domain: string;
}

interface EditCheckRule {
  rule_yaml: string;
  clinical_range: string;
  citations: Citation[];
  confidence: string;
}

interface ComplianceUpdate {
  source_name: string;
  update_title: string;
  impact_assessment: string;
  detected_date: string;
  url: string;
}

export function LinkupIntegration() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Evidence Pack State
  const [metricName, setMetricName] = useState("Wasserstein distance");
  const [metricValue, setMetricValue] = useState("2.34");
  const [citations, setCitations] = useState<Citation[]>([]);

  // Edit Check State
  const [variable, setVariable] = useState("systolic_bp");
  const [indication, setIndication] = useState("hypertension");
  const [severity, setSeverity] = useState("Major");
  const [editCheckRule, setEditCheckRule] = useState<EditCheckRule | null>(null);

  // Compliance State
  const [complianceUpdates, setComplianceUpdates] = useState<ComplianceUpdate[]>([]);
  const [dashboardSummary, setDashboardSummary] = useState<any>(null);

  const fetchCitations = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("http://localhost:8008/evidence/fetch-citations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          metric_name: metricName,
          metric_value: parseFloat(metricValue),
          context: "clinical trial data quality",
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
      }

      const result = await response.json();
      setCitations(result);
      setSuccess(`Found ${result.length} regulatory citations`);
    } catch (err: any) {
      setError(`Failed to fetch citations: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const generateEditCheckRule = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("http://localhost:8008/edit-checks/generate-rule", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          variable,
          indication,
          severity,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
      }

      const result = await response.json();
      setEditCheckRule(result);
      setSuccess("Edit check rule generated successfully");
    } catch (err: any) {
      setError(`Failed to generate rule: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const scanCompliance = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("http://localhost:8008/compliance/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
      }

      const result = await response.json();
      setComplianceUpdates(result.updates || []);
      setSuccess(`Scan completed: ${result.total_updates} updates found`);
    } catch (err: any) {
      setError(`Compliance scan failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const getDashboardSummary = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("http://localhost:8008/compliance/dashboard-summary");

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
      }

      const result = await response.json();
      setDashboardSummary(result);
      setSuccess("Dashboard summary loaded");
    } catch (err: any) {
      setError(`Failed to load dashboard: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Shield className="h-8 w-8 text-primary" />
            Linkup Regulatory Intelligence
          </h1>
          <p className="text-muted-foreground mt-2">
            AI-powered regulatory citations, edit check generation, and compliance monitoring
          </p>
        </div>
        <Badge variant="outline" className="text-sm">
          Port 8008
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

      <Tabs defaultValue="evidence" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="evidence">
            <FileText className="h-4 w-4 mr-2" />
            Evidence Pack
          </TabsTrigger>
          <TabsTrigger value="editchecks">
            <CheckSquare className="h-4 w-4 mr-2" />
            Edit Checks
          </TabsTrigger>
          <TabsTrigger value="compliance">
            <Shield className="h-4 w-4 mr-2" />
            Compliance Watcher
          </TabsTrigger>
        </TabsList>

        {/* Evidence Pack Tab */}
        <TabsContent value="evidence" className="space-y-6">
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Regulatory Citation Service</h2>
            <p className="text-sm text-muted-foreground mb-6">
              Fetch authoritative regulatory citations (FDA, ICH, CDISC) for quality metrics
            </p>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Metric Name</Label>
                  <select
                    value={metricName}
                    onChange={(e) => setMetricName(e.target.value)}
                    className="w-full mt-1 p-2 border rounded-md"
                  >
                    <option value="Wasserstein distance">Wasserstein Distance</option>
                    <option value="RMSE">RMSE (Root Mean Square Error)</option>
                    <option value="correlation preservation">Correlation Preservation</option>
                    <option value="KNN imputation">K-NN Imputation Score</option>
                  </select>
                </div>

                <div>
                  <Label>Metric Value</Label>
                  <input
                    type="number"
                    step="0.01"
                    value={metricValue}
                    onChange={(e) => setMetricValue(e.target.value)}
                    className="w-full mt-1 p-2 border rounded-md"
                  />
                </div>
              </div>

              <Button onClick={fetchCitations} disabled={loading} className="w-full">
                {loading ? (
                  <>
                    <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                    Fetching...
                  </>
                ) : (
                  <>
                    <Search className="h-4 w-4 mr-2" />
                    Fetch Regulatory Citations
                  </>
                )}
              </Button>

              {citations.length > 0 && (
                <div className="mt-6 space-y-4">
                  <h3 className="font-medium">Found {citations.length} Citations</h3>
                  <div className="space-y-3">
                    {citations.map((citation, idx) => (
                      <Card key={idx} className="p-4">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <Badge variant="outline">{citation.domain}</Badge>
                              <Badge variant="secondary">
                                Relevance: {(citation.relevance_score * 100).toFixed(0)}%
                              </Badge>
                            </div>
                            <p className="text-sm text-muted-foreground mb-2">{citation.snippet}</p>
                            <a
                              href={citation.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs text-primary hover:underline flex items-center gap-1"
                            >
                              {citation.url}
                              <ExternalLink className="h-3 w-3" />
                            </a>
                          </div>
                        </div>
                      </Card>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </Card>
        </TabsContent>

        {/* Edit Checks Tab */}
        <TabsContent value="editchecks" className="space-y-6">
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">AI-Assisted Edit Check Generator</h2>
            <p className="text-sm text-muted-foreground mb-6">
              Generate YAML validation rules with AI-discovered clinical ranges and citations
            </p>

            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label>Variable</Label>
                  <select
                    value={variable}
                    onChange={(e) => setVariable(e.target.value)}
                    className="w-full mt-1 p-2 border rounded-md"
                  >
                    <option value="systolic_bp">Systolic BP</option>
                    <option value="diastolic_bp">Diastolic BP</option>
                    <option value="heart_rate">Heart Rate</option>
                    <option value="temperature">Temperature</option>
                    <option value="respiratory_rate">Respiratory Rate</option>
                    <option value="oxygen_saturation">Oxygen Saturation</option>
                    <option value="weight">Weight</option>
                    <option value="height">Height</option>
                    <option value="bmi">BMI</option>
                  </select>
                </div>

                <div>
                  <Label>Indication</Label>
                  <input
                    type="text"
                    value={indication}
                    onChange={(e) => setIndication(e.target.value)}
                    placeholder="e.g., hypertension"
                    className="w-full mt-1 p-2 border rounded-md"
                  />
                </div>

                <div>
                  <Label>Severity</Label>
                  <select
                    value={severity}
                    onChange={(e) => setSeverity(e.target.value)}
                    className="w-full mt-1 p-2 border rounded-md"
                  >
                    <option value="Critical">Critical</option>
                    <option value="Major">Major</option>
                    <option value="Minor">Minor</option>
                    <option value="Warning">Warning</option>
                  </select>
                </div>
              </div>

              <Button onClick={generateEditCheckRule} disabled={loading} className="w-full">
                {loading ? (
                  <>
                    <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                    Generating...
                  </>
                ) : (
                  <>
                    <CheckSquare className="h-4 w-4 mr-2" />
                    Generate Edit Check Rule
                  </>
                )}
              </Button>

              {editCheckRule && (
                <div className="mt-6 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium">Generated Rule</h3>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={
                          editCheckRule.confidence === "high"
                            ? "default"
                            : editCheckRule.confidence === "medium"
                            ? "secondary"
                            : "outline"
                        }
                      >
                        Confidence: {editCheckRule.confidence}
                      </Badge>
                    </div>
                  </div>

                  <div className="bg-muted/50 p-4 rounded-lg">
                    <Label className="text-xs text-muted-foreground">Clinical Range</Label>
                    <p className="font-mono text-sm mt-1">{editCheckRule.clinical_range}</p>
                  </div>

                  <div>
                    <Label className="text-xs text-muted-foreground mb-2 block">YAML Rule</Label>
                    <pre className="bg-muted p-4 rounded-lg text-xs overflow-auto max-h-64">
                      {editCheckRule.rule_yaml}
                    </pre>
                    <Button variant="outline" size="sm" className="mt-2">
                      <Download className="h-4 w-4 mr-2" />
                      Download YAML
                    </Button>
                  </div>

                  {editCheckRule.citations && editCheckRule.citations.length > 0 && (
                    <div>
                      <Label className="text-xs text-muted-foreground mb-2 block">
                        Supporting Citations ({editCheckRule.citations.length})
                      </Label>
                      <div className="space-y-2">
                        {editCheckRule.citations.slice(0, 3).map((citation, idx) => (
                          <div key={idx} className="bg-muted/30 p-3 rounded text-xs">
                            <a
                              href={citation.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-primary hover:underline flex items-center gap-1"
                            >
                              {citation.domain}
                              <ExternalLink className="h-3 w-3" />
                            </a>
                            <p className="text-muted-foreground mt-1">{citation.snippet.substring(0, 150)}...</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </Card>
        </TabsContent>

        {/* Compliance Watcher Tab */}
        <TabsContent value="compliance" className="space-y-6">
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Compliance & RBQM Watcher</h2>
            <p className="text-sm text-muted-foreground mb-6">
              Automated monitoring of FDA, ICH, CDISC, and TransCelerate for regulatory updates
            </p>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <Button onClick={scanCompliance} disabled={loading}>
                  {loading ? (
                    <>
                      <div className="h-4 w-4 border-2 border-primary border-t-transparent rounded-full animate-spin mr-2" />
                      Scanning...
                    </>
                  ) : (
                    <>
                      <Search className="h-4 w-4 mr-2" />
                      Run Compliance Scan
                    </>
                  )}
                </Button>

                <Button variant="outline" onClick={getDashboardSummary} disabled={loading}>
                  <Shield className="h-4 w-4 mr-2" />
                  Load Dashboard Summary
                </Button>
              </div>

              {dashboardSummary && (
                <div className="grid grid-cols-3 gap-4">
                  <Card className="p-4">
                    <div className="text-sm text-muted-foreground">Total Updates (7 days)</div>
                    <div className="text-2xl font-bold">{dashboardSummary.summary.total_updates_last_7_days}</div>
                  </Card>
                  <Card className="p-4 border-destructive">
                    <div className="text-sm text-muted-foreground">High Impact</div>
                    <div className="text-2xl font-bold text-destructive">
                      {dashboardSummary.summary.high_impact_count}
                    </div>
                  </Card>
                  <Card className="p-4 border-amber-500">
                    <div className="text-sm text-muted-foreground">Medium Impact</div>
                    <div className="text-2xl font-bold text-amber-600">
                      {dashboardSummary.summary.medium_impact_count}
                    </div>
                  </Card>
                </div>
              )}

              {complianceUpdates.length > 0 && (
                <div className="mt-6 space-y-4">
                  <h3 className="font-medium">Recent Regulatory Updates</h3>
                  <div className="space-y-3">
                    {complianceUpdates.map((update, idx) => (
                      <Card key={idx} className="p-4">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <Badge variant="outline">{update.source_name}</Badge>
                              <Badge
                                variant={
                                  update.impact_assessment === "HIGH"
                                    ? "destructive"
                                    : update.impact_assessment === "MEDIUM"
                                    ? "default"
                                    : "secondary"
                                }
                              >
                                {update.impact_assessment} Impact
                              </Badge>
                            </div>
                            <h4 className="font-medium mb-2">{update.update_title}</h4>
                            <p className="text-xs text-muted-foreground mb-2">
                              Detected: {new Date(update.detected_date).toLocaleDateString()}
                            </p>
                            <a
                              href={update.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs text-primary hover:underline flex items-center gap-1"
                            >
                              View Update
                              <ExternalLink className="h-3 w-3" />
                            </a>
                          </div>
                          {update.impact_assessment === "HIGH" && (
                            <AlertTriangle className="h-5 w-5 text-destructive" />
                          )}
                        </div>
                      </Card>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
