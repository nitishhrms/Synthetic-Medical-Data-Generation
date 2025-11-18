import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, BarChart3, Database, Users } from "lucide-react";
import type { Screen } from "@/components/layout/NavigationRail";
import { useData } from "@/contexts/DataContext";

interface DashboardProps {
  onNavigate?: (screen: Screen) => void;
}

interface ServiceStatus {
  name: string;
  port: number;
  status: "online" | "offline" | "checking";
}

export function Dashboard({ onNavigate }: DashboardProps) {
  const { generatedData, qualityMetrics } = useData();
  const [services, setServices] = useState<ServiceStatus[]>([
    { name: "Data Generation", port: 8002, status: "checking" },
    { name: "Analytics", port: 8003, status: "checking" },
    { name: "Security", port: 8005, status: "checking" },
    { name: "EDC Service", port: 8004, status: "checking" },
    { name: "Quality", port: 8006, status: "checking" },
  ]);

  useEffect(() => {
    // Check service health on mount
    const checkServices = async () => {
      const updatedServices = await Promise.all(
        services.map(async (service) => {
          try {
            const response = await fetch(`http://localhost:${service.port}/health`, {
              method: "GET",
              signal: AbortSignal.timeout(2000),
            });
            return {
              ...service,
              status: response.ok ? ("online" as const) : ("offline" as const),
            };
          } catch {
            return { ...service, status: "offline" as const };
          }
        })
      );
      setServices(updatedServices);
    };

    checkServices();
  }, []);

  // Calculate stats from actual data
  const generatedRecordsCount = generatedData?.length || 0;
  const qualityScore = qualityMetrics?.overall_quality_score
    ? (qualityMetrics.overall_quality_score * 100).toFixed(1)
    : "N/A";

  // Count unique subjects from generated data
  const uniqueSubjects = generatedData
    ? new Set(generatedData.map(r => r.SubjectID)).size
    : 0;

  const stats = [
    {
      title: "Active Studies",
      value: "Demo Mode",
      description: "EDC service offline",
      icon: Database,
      gradient: "from-blue-500 to-cyan-500",
      bg: "bg-blue-50",
    },
    {
      title: "Generated Records",
      value: generatedRecordsCount > 0 ? generatedRecordsCount.toString() : "0",
      description: "Synthetic vitals records",
      icon: Activity,
      gradient: "from-green-500 to-emerald-500",
      bg: "bg-green-50",
    },
    {
      title: "Unique Subjects",
      value: uniqueSubjects > 0 ? uniqueSubjects.toString() : "0",
      description: "From generated data",
      icon: Users,
      gradient: "from-purple-500 to-pink-500",
      bg: "bg-purple-50",
    },
    {
      title: "Quality Score",
      value: qualityScore,
      description: typeof qualityScore === "string" && qualityScore !== "N/A" ? "Excellent quality" : "Generate data first",
      icon: BarChart3,
      gradient: "from-orange-500 to-red-500",
      bg: "bg-orange-50",
    },
  ];

  const getStatusColor = (status: ServiceStatus["status"]) => {
    switch (status) {
      case "online":
        return "bg-green-500";
      case "offline":
        return "bg-red-500";
      case "checking":
        return "bg-yellow-500 animate-pulse";
    }
  };

  const getStatusText = (status: ServiceStatus["status"]) => {
    switch (status) {
      case "online":
        return "Online";
      case "offline":
        return "Offline";
      case "checking":
        return "Checking...";
    }
  };

  return (
    <div className="p-8 space-y-8">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-muted-foreground">
          Welcome to the Synthetic Medical Data Generation Platform
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.title} className="overflow-hidden border-2 hover:shadow-lg transition-shadow">
              <div className={`h-2 bg-gradient-to-r ${stat.gradient}`} />
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {stat.title}
                </CardTitle>
                <div className={`p-2 rounded-lg ${stat.bg}`}>
                  <Icon className={`h-5 w-5 bg-gradient-to-r ${stat.gradient} bg-clip-text text-transparent`} style={{ backgroundClip: 'text', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }} />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{stat.value}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  {stat.description}
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>
              Common tasks to get you started
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <div
              className="flex items-center gap-2 p-3 rounded-lg hover:bg-accent cursor-pointer transition-colors"
              onClick={() => onNavigate?.("generate")}
            >
              <Activity className="h-5 w-5 text-primary" />
              <div>
                <p className="text-sm font-medium">Generate Synthetic Data</p>
                <p className="text-xs text-muted-foreground">
                  Create vitals data using MVN, Bootstrap, or Rules
                </p>
              </div>
            </div>
            <div
              className="flex items-center gap-2 p-3 rounded-lg hover:bg-accent cursor-pointer transition-colors"
              onClick={() => onNavigate?.("analytics")}
            >
              <BarChart3 className="h-5 w-5 text-primary" />
              <div>
                <p className="text-sm font-medium">View Analytics</p>
                <p className="text-xs text-muted-foreground">
                  Analyze treatment effects and quality metrics
                </p>
              </div>
            </div>
            <div
              className="flex items-center gap-2 p-3 rounded-lg hover:bg-accent cursor-pointer transition-colors"
              onClick={() => onNavigate?.("quality")}
            >
              <Database className="h-5 w-5 text-primary" />
              <div>
                <p className="text-sm font-medium">Quality Assessment</p>
                <p className="text-xs text-muted-foreground">
                  Compare synthetic vs real data quality
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Getting Started</CardTitle>
            <CardDescription>
              Quick guide to use the platform
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-start gap-3">
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs text-primary-foreground">
                1
              </div>
              <div>
                <p className="text-sm font-medium">Generate Data</p>
                <p className="text-xs text-muted-foreground">
                  Choose MVN, Bootstrap, or Rules method
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs text-primary-foreground">
                2
              </div>
              <div>
                <p className="text-sm font-medium">Analyze Results</p>
                <p className="text-xs text-muted-foreground">
                  View Week-12 statistics and treatment effects
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs text-primary-foreground">
                3
              </div>
              <div>
                <p className="text-sm font-medium">Assess Quality</p>
                <p className="text-xs text-muted-foreground">
                  Compare with real pilot data
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Backend Services</CardTitle>
          <CardDescription>
            Microservices status and connectivity
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-3 lg:grid-cols-5">
            {services.map((service) => (
              <div key={service.name} className="p-3 border rounded-lg">
                <p className="text-sm font-medium">{service.name}</p>
                <p className="text-xs text-muted-foreground">Port {service.port}</p>
                <div className="mt-2 flex items-center gap-2">
                  <div className={`h-2 w-2 rounded-full ${getStatusColor(service.status)}`}></div>
                  <span className="text-xs">{getStatusText(service.status)}</span>
                </div>
              </div>
            ))}
          </div>
          {services.some(s => s.status === "offline") && (
            <p className="mt-4 text-xs text-muted-foreground">
              ℹ️ Some services are offline. EDC and Quality require database configuration.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
