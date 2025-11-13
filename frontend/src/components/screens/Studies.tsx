import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FileText, Plus } from "lucide-react";

export function Studies() {
  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Study Management</h2>
          <p className="text-muted-foreground">
            Manage clinical trials and import synthetic data
          </p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          Create Study
        </Button>
      </div>

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
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Create Your First Study
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
