import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { edcApi } from "@/services/api";
import { useData } from "@/contexts/DataContext";
import type { Study } from "@/types";
import { FileText, Plus, Upload, Loader2, Calendar, Users } from "lucide-react";

export function Studies() {
  const { generatedData } = useData();
  const [studies, setStudies] = useState<Study[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [selectedStudy, setSelectedStudy] = useState<Study | null>(null);
  const [error, setError] = useState("");
  const [isImporting, setIsImporting] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    study_name: "",
    indication: "",
    phase: "Phase 3" as "Phase 1" | "Phase 2" | "Phase 3",
    sponsor: "",
    start_date: new Date().toISOString().split("T")[0],
    status: "active" as const,
    tenant_id: "default-tenant", // TODO: Get from auth context
  });

  useEffect(() => {
    loadStudies();
  }, []);

  const loadStudies = async () => {
    setIsLoading(true);
    try {
      const response = await edcApi.listStudies();
      setStudies(response.studies);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load studies");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateStudy = async () => {
    setIsLoading(true);
    setError("");

    try {
      await edcApi.createStudy(formData);
      setShowCreateDialog(false);
      setFormData({
        study_name: "",
        indication: "",
        phase: "Phase 3" as "Phase 1" | "Phase 2" | "Phase 3",
        sponsor: "",
        start_date: new Date().toISOString().split("T")[0],
        status: "active" as const,
        tenant_id: "default-tenant", // TODO: Get from auth context
      });
      await loadStudies();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create study");
    } finally {
      setIsLoading(false);
    }
  };

  const handleImportData = async (study: Study) => {
    if (!generatedData) {
      setError("No generated data available. Please generate data first.");
      return;
    }

    setIsImporting(true);
    setError("");

    try {
      const response = await edcApi.importSyntheticData(
        study.study_id,
        generatedData,
        "frontend-generation"
      );
      alert(`Successfully imported ${response.subjects_imported} subjects with ${response.observations_imported} observations`);
      await loadStudies();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to import data");
    } finally {
      setIsImporting(false);
    }
  };

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Study Management</h2>
          <p className="text-muted-foreground">
            Manage clinical trials and import synthetic data
          </p>
        </div>
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Create Study
        </Button>
      </div>

      {error && (
        <div className="text-sm text-destructive bg-destructive/10 p-3 rounded-md">
          {error}
        </div>
      )}

      {isLoading && studies.length === 0 ? (
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </CardContent>
        </Card>
      ) : studies.length === 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Active Studies</CardTitle>
            <CardDescription>
              No studies found. Create your first study to get started.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <FileText className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No Studies Yet</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Create your first clinical trial study to start managing data
              </p>
              <Button onClick={() => setShowCreateDialog(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Create Your First Study
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {studies.map((study) => (
            <Card key={study.study_id} className="overflow-hidden hover:shadow-lg transition-shadow">
              <div className="h-2 bg-gradient-to-r from-blue-500 to-purple-500" />
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg">{study.study_name}</CardTitle>
                    <CardDescription className="mt-1">
                      {study.indication} • {study.phase}
                    </CardDescription>
                  </div>
                  <Badge variant={study.status === "active" ? "default" : "secondary"}>
                    {study.status || "active"}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-3 text-sm">
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Sponsor:</span>
                    <span className="font-medium">{study.sponsor}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Start Date:</span>
                    <span className="font-medium">
                      {new Date(study.start_date).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Study ID:</span>
                    <span className="font-mono text-xs">{study.study_id}</span>
                  </div>
                </div>

                <div className="pt-4 border-t flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    className="flex-1"
                    onClick={() => setSelectedStudy(study)}
                  >
                    View Details
                  </Button>
                  <Button
                    size="sm"
                    className="flex-1"
                    onClick={() => handleImportData(study)}
                    disabled={!generatedData || isImporting}
                  >
                    {isImporting ? (
                      <>
                        <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                        Importing...
                      </>
                    ) : (
                      <>
                        <Upload className="mr-2 h-3 w-3" />
                        Import Data
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create Study Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="sm:max-w-[525px]">
          <DialogHeader>
            <DialogTitle>Create New Study</DialogTitle>
            <DialogDescription>
              Set up a new clinical trial study to manage subjects and data
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="study_name">Study Name</Label>
              <Input
                id="study_name"
                placeholder="e.g., Hypertension Phase 3 Trial"
                value={formData.study_name}
                onChange={(e) => setFormData({ ...formData, study_name: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="indication">Indication</Label>
              <Input
                id="indication"
                placeholder="e.g., Hypertension"
                value={formData.indication}
                onChange={(e) => setFormData({ ...formData, indication: e.target.value })}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="phase">Phase</Label>
                <select
                  id="phase"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={formData.phase}
                  onChange={(e) => setFormData({ ...formData, phase: e.target.value as "Phase 1" | "Phase 2" | "Phase 3" })}
                >
                  <option value="Phase 1">Phase 1</option>
                  <option value="Phase 2">Phase 2</option>
                  <option value="Phase 3">Phase 3</option>
                  <option value="Phase 4">Phase 4</option>
                </select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="start_date">Start Date</Label>
                <Input
                  id="start_date"
                  type="date"
                  value={formData.start_date}
                  onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="sponsor">Sponsor</Label>
              <Input
                id="sponsor"
                placeholder="e.g., PharmaCo Inc"
                value={formData.sponsor}
                onChange={(e) => setFormData({ ...formData, sponsor: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateStudy} disabled={isLoading || !formData.study_name}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                "Create Study"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Study Details Dialog */}
      {selectedStudy && (
        <Dialog open={!!selectedStudy} onOpenChange={() => setSelectedStudy(null)}>
          <DialogContent className="sm:max-w-[600px]">
            <DialogHeader>
              <DialogTitle>{selectedStudy.study_name}</DialogTitle>
              <DialogDescription>Study Details and Information</DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Study ID</p>
                  <p className="text-sm font-mono mt-1">{selectedStudy.study_id}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Status</p>
                  <Badge className="mt-1">{selectedStudy.status || "active"}</Badge>
                </div>
              </div>

              <div>
                <p className="text-sm font-medium text-muted-foreground">Indication</p>
                <p className="text-sm mt-1">{selectedStudy.indication}</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Phase</p>
                  <p className="text-sm mt-1">{selectedStudy.phase}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Sponsor</p>
                  <p className="text-sm mt-1">{selectedStudy.sponsor}</p>
                </div>
              </div>

              <div>
                <p className="text-sm font-medium text-muted-foreground">Start Date</p>
                <p className="text-sm mt-1">
                  {new Date(selectedStudy.start_date).toLocaleDateString("en-US", {
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                  })}
                </p>
              </div>

              {selectedStudy.created_at && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Created</p>
                  <p className="text-sm mt-1">
                    {new Date(selectedStudy.created_at).toLocaleString()}
                  </p>
                </div>
              )}
            </div>
            <DialogFooter>
              <Button onClick={() => setSelectedStudy(null)}>Close</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
