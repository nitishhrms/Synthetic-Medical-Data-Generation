import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle, XCircle, Loader2 } from "lucide-react";

interface ServiceStatus {
  name: string;
  url: string;
  status: "checking" | "online" | "offline";
  error?: string;
}

export function SystemCheck() {
  const [services, setServices] = useState<ServiceStatus[]>([
    { name: "Data Generation", url: "http://localhost:8002", status: "checking" },
    { name: "Analytics", url: "http://localhost:8003", status: "checking" },
    { name: "EDC", url: "http://localhost:8001", status: "checking" },
    { name: "Security", url: "http://localhost:8005", status: "checking" },
    { name: "Quality", url: "http://localhost:8004", status: "checking" },
  ]);

  const checkServices = async () => {
    setServices((prev) =>
      prev.map((s) => ({ ...s, status: "checking" as const, error: undefined }))
    );

    for (let i = 0; i < services.length; i++) {
      const service = services[i];
      try {
        console.log(`Checking ${service.name} at ${service.url}/health...`);
        const response = await fetch(`${service.url}/health`, {
          method: "GET",
          headers: { "Content-Type": "application/json" },
        });

        console.log(`${service.name} response:`, response.status, response.statusText);

        setServices((prev) =>
          prev.map((s, idx) =>
            idx === i
              ? {
                ...s,
                status: response.ok ? "online" : "offline",
                error: response.ok ? undefined : `HTTP ${response.status}`,
              }
              : s
          )
        );
      } catch (error) {
        console.error(`${service.name} error:`, error);
        setServices((prev) =>
          prev.map((s, idx) =>
            idx === i
              ? {
                ...s,
                status: "offline" as const,
                error: error instanceof Error ? error.message : "Connection failed",
              }
              : s
          )
        );
      }
    }
  };

  return (
    <div className="p-8 space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">System Health Check</h2>
        <p className="text-muted-foreground">
          Verify all backend services are running and accessible
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Backend Services</CardTitle>
          <CardDescription>
            Check connectivity to all microservices
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button onClick={checkServices}>
            Check All Services
          </Button>

          <div className="space-y-2">
            {services.map((service) => (
              <div
                key={service.name}
                className="flex items-center justify-between p-3 border rounded-lg"
              >
                <div>
                  <p className="font-medium">{service.name}</p>
                  <p className="text-sm text-muted-foreground">{service.url}</p>
                  {service.error && (
                    <p className="text-sm text-destructive">{service.error}</p>
                  )}
                </div>
                <div>
                  {service.status === "checking" && (
                    <Badge variant="secondary">
                      <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                      Checking...
                    </Badge>
                  )}
                  {service.status === "online" && (
                    <Badge className="bg-green-500">
                      <CheckCircle className="h-3 w-3 mr-1" />
                      Online
                    </Badge>
                  )}
                  {service.status === "offline" && (
                    <Badge variant="destructive">
                      <XCircle className="h-3 w-3 mr-1" />
                      Offline
                    </Badge>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="p-4 bg-muted rounded-lg">
            <p className="text-sm font-medium mb-2">Instructions:</p>
            <ol className="text-sm text-muted-foreground space-y-1 list-decimal list-inside">
              <li>Ensure all backend services are running</li>
              <li>Check that services are on the correct ports (8002-8006)</li>
              <li>Verify CORS is enabled on backend services</li>
              <li>Check browser console for detailed error messages</li>
            </ol>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
