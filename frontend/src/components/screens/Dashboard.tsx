import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, BarChart3, Database, Users } from "lucide-react";

export function Dashboard() {
  const stats = [
    {
      title: "Total Studies",
      value: "0",
      description: "Active clinical trials",
      icon: Database,
      color: "text-blue-600",
    },
    {
      title: "Generated Records",
      value: "0",
      description: "Synthetic vitals records",
      icon: Activity,
      color: "text-green-600",
    },
    {
      title: "Enrolled Subjects",
      value: "0",
      description: "Across all studies",
      icon: Users,
      color: "text-purple-600",
    },
    {
      title: "Quality Score",
      value: "N/A",
      description: "Latest generation",
      icon: BarChart3,
      color: "text-orange-600",
    },
  ];

  return (
    <div className="p-8 space-y-8">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-muted-foreground">
          Welcome to the Clinical Trial Analytics Platform
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.title}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {stat.title}
                </CardTitle>
                <Icon className={`h-4 w-4 ${stat.color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <p className="text-xs text-muted-foreground">
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
            <div className="flex items-center gap-2 p-3 rounded-lg hover:bg-accent cursor-pointer">
              <Activity className="h-5 w-5 text-primary" />
              <div>
                <p className="text-sm font-medium">Generate Synthetic Data</p>
                <p className="text-xs text-muted-foreground">
                  Create vitals data using MVN, Bootstrap, or LLM
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 p-3 rounded-lg hover:bg-accent cursor-pointer">
              <BarChart3 className="h-5 w-5 text-primary" />
              <div>
                <p className="text-sm font-medium">Analyze Quality</p>
                <p className="text-xs text-muted-foreground">
                  Run comprehensive quality assessment
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 p-3 rounded-lg hover:bg-accent cursor-pointer">
              <Database className="h-5 w-5 text-primary" />
              <div>
                <p className="text-sm font-medium">Create Study</p>
                <p className="text-xs text-muted-foreground">
                  Set up a new clinical trial
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>
              Your latest actions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              No recent activity to display
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>System Information</CardTitle>
          <CardDescription>
            Backend services status
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 md:grid-cols-3">
            <div className="p-3 border rounded-lg">
              <p className="text-sm font-medium">Data Generation</p>
              <p className="text-xs text-muted-foreground">Port 8002</p>
              <div className="mt-2 flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-green-500"></div>
                <span className="text-xs">Ready</span>
              </div>
            </div>
            <div className="p-3 border rounded-lg">
              <p className="text-sm font-medium">Analytics</p>
              <p className="text-xs text-muted-foreground">Port 8003</p>
              <div className="mt-2 flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-green-500"></div>
                <span className="text-xs">Ready</span>
              </div>
            </div>
            <div className="p-3 border rounded-lg">
              <p className="text-sm font-medium">EDC Service</p>
              <p className="text-xs text-muted-foreground">Port 8004</p>
              <div className="mt-2 flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-green-500"></div>
                <span className="text-xs">Ready</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
