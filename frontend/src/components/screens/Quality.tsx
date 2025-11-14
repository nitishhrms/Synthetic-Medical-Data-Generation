import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { qualityApi } from "@/services/api";
import { useData } from "@/contexts/DataContext";
import type { ValidationResponse } from "@/types";
import { CheckCircle2, XCircle, AlertTriangle, Loader2, Shield } from "lucide-react";

export function Quality() {
  const { generatedData, validationResults, setValidationResults } = useData();
  const [isValidating, setIsValidating] = useState(false);
  const [error, setError] = useState("");

  const runValidation = async () => {
    if (!generatedData) {
      setError("No generated data available. Please generate data first from the Generate screen.");
      return;
    }

    setIsValidating(true);
    setError("");

    try {
      const results = await qualityApi.validateVitals(generatedData);
      setValidationResults(results);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Validation failed");
    } finally {
      setIsValidating(false);
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity.toLowerCase()) {
      case "error":
        return <XCircle className="h-4 w-4 text-destructive" />;
      case "warning":
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity.toLowerCase()) {
      case "error":
        return <Badge variant="destructive">Error</Badge>;
      case "warning":
        return <Badge className="bg-yellow-500">Warning</Badge>;
      default:
        return <Badge variant="secondary">Info</Badge>;
    }
  };

  return (
    <div className="p-8 space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Quality Validation</h2>
        <p className="text-muted-foreground">
          Run edit checks and data validation on generated synthetic data
        </p>
      </div>

      {!generatedData ? (
        <Card>
          <CardHeader>
            <CardTitle>No Data Available</CardTitle>
            <CardDescription>
              Please generate synthetic data first from the Generate screen
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-sm text-muted-foreground">
              Go to the Generate screen and create some synthetic data to validate.
            </div>
          </CardContent>
        </Card>
      ) : (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Run Validation</CardTitle>
              <CardDescription>
                Validate {generatedData.length} generated records against quality rules
              </CardDescription>
            </CardHeader>
            <CardContent>
              {error && (
                <div className="text-sm text-destructive bg-destructive/10 p-3 rounded-md mb-4">
                  {error}
                </div>
              )}

              <Button onClick={runValidation} disabled={isValidating}>
                {isValidating ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Validating...
                  </>
                ) : (
                  <>
                    <Shield className="mr-2 h-4 w-4" />
                    Run Quality Checks
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </>
      )}

      {validationResults && (
        <>
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Total Records</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{validationResults.total_records}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Checks Run</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{validationResults.total_checks}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Quality Score</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {(validationResults.quality_score * 100).toFixed(0)}%
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Validation Status</CardTitle>
              </CardHeader>
              <CardContent>
                {validationResults.passed ? (
                  <Badge className="bg-green-500">
                    <CheckCircle2 className="mr-1 h-3 w-3" />
                    Passed
                  </Badge>
                ) : (
                  <Badge variant="destructive">
                    <XCircle className="mr-1 h-3 w-3" />
                    Failed
                  </Badge>
                )}
              </CardContent>
            </Card>
          </div>

          {validationResults.violations.length > 0 ? (
            <Card>
              <CardHeader>
                <CardTitle>Validation Violations</CardTitle>
                <CardDescription>
                  {validationResults.violations.length} violations found
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {validationResults.violations.slice(0, 20).map((violation, idx) => (
                    <div
                      key={idx}
                      className="flex items-start gap-3 p-3 border rounded-lg hover:bg-accent/50 transition-colors"
                    >
                      {getSeverityIcon(violation.severity)}
                      <div className="flex-1 space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-sm font-medium">
                            {violation.record}
                          </span>
                          {getSeverityBadge(violation.severity)}
                          <Badge variant="outline" className="text-xs">
                            {violation.rule}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">{violation.message}</p>
                      </div>
                    </div>
                  ))}
                  {validationResults.violations.length > 20 && (
                    <div className="text-sm text-muted-foreground text-center pt-2">
                      Showing first 20 of {validationResults.violations.length} violations
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-green-600">
                  <CheckCircle2 className="h-5 w-5" />
                  All Checks Passed
                </CardTitle>
                <CardDescription>
                  No validation violations found in the generated data
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                  <p className="text-sm text-green-800">
                    The generated data passed all {validationResults.total_checks} quality checks successfully.
                    The data meets all validation rules and is ready for use.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
