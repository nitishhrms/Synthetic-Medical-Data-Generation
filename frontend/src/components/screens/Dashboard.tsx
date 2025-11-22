import { useState, useEffect } from "react";
import { Activity, Database, Users, FolderOpen, FileText, AlertCircle, TrendingUp } from "lucide-react";
import type { Screen } from "@/constants/navigation";
import { useData } from "@/contexts/DataContext";
import { dataGenerationApi } from "@/services/api";
import { motion } from "framer-motion";
import { AreaChart } from "@tremor/react";
import { cn } from "@/lib/utils";
import { BentoCard } from "@/components/ui/bento-card";

interface DashboardProps {
  onNavigate?: (screen: Screen) => void;
}

interface ServiceStatus {
  name: string;
  port: number;
  status: "online" | "offline" | "checking";
}

// Mock data for the chart
const enrollmentData = [
  { date: "Jan 23", "Active Subjects": 120, "Screened": 150 },
  { date: "Feb 23", "Active Subjects": 240, "Screened": 280 },
  { date: "Mar 23", "Active Subjects": 380, "Screened": 450 },
  { date: "Apr 23", "Active Subjects": 520, "Screened": 600 },
  { date: "May 23", "Active Subjects": 680, "Screened": 800 },
  { date: "Jun 23", "Active Subjects": 850, "Screened": 980 },
  { date: "Jul 23", "Active Subjects": 1020, "Screened": 1200 },
  { date: "Aug 23", "Active Subjects": 1284, "Screened": 1450 },
];

export function Dashboard({ onNavigate }: DashboardProps) {
  const { generatedData, qualityMetrics, setGeneratedData, setGenerationMethod } = useData();
  const [services, setServices] = useState<ServiceStatus[]>([
    { name: "Data Generation", port: 8002, status: "checking" },
    { name: "Analytics", port: 8003, status: "checking" },
    { name: "Security", port: 8005, status: "checking" },
    { name: "EDC Service", port: 8001, status: "checking" },
    { name: "Quality", port: 8004, status: "checking" },
  ]);
  const [savedDatasets, setSavedDatasets] = useState<any[]>([]);
  const [isLoadingDatasets, setIsLoadingDatasets] = useState(false);

  useEffect(() => {
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
    loadSavedDatasets();
  }, []);

  const loadSavedDatasets = async () => {
    setIsLoadingDatasets(true);
    try {
      const result = await dataGenerationApi.listDatasets();
      setSavedDatasets(result.datasets || []);
    } catch (err) {
      console.error("Failed to load saved datasets:", err);
    } finally {
      setIsLoadingDatasets(false);
    }
  };

  const loadDataset = async (datasetType: string) => {
    try {
      const result = await dataGenerationApi.loadLatestData(datasetType);
      if (result && result.data) {
        setGeneratedData(result.data);
        if (result.metadata?.method) {
          setGenerationMethod(result.metadata.method);
        }
      }
    } catch (err) {
      console.error("Failed to load dataset:", err);
    }
  };

  const uniqueSubjects = generatedData
    ? new Set(generatedData.map(r => r.SubjectID)).size
    : 0;

  const qualityScore = qualityMetrics?.overall_quality_score
    ? (qualityMetrics.overall_quality_score * 100).toFixed(1) + "%"
    : "N/A";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="space-y-6"
    >
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Clinical Overview</h2>
          <p className="text-zinc-400">Real-time monitoring of synthetic clinical trials</p>
        </div>
        <div className="flex gap-2">
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900 border border-zinc-800 text-xs text-zinc-400">
            <div className="h-2 w-2 rounded-full bg-teal-500 animate-pulse" />
            System Online
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 auto-rows-[minmax(180px,auto)]">
        {/* Key Metrics (1x1) */}
        <BentoCard
          title="Total Patients"
          value={uniqueSubjects > 0 ? uniqueSubjects.toLocaleString() : "1,284"}
          subtitle="+12% from last month"
          icon={Users}
        >
          <div className="mt-4 h-1 w-full bg-zinc-800 rounded-full overflow-hidden">
            <div className="h-full bg-teal-500 w-[75%]" />
          </div>
        </BentoCard>

        <BentoCard
          title="Active Sites"
          value="142"
          subtitle="Across 12 regions"
          icon={Database}
        >
          <div className="mt-4 flex -space-x-2 overflow-hidden">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="inline-block h-6 w-6 rounded-full ring-2 ring-zinc-900 bg-zinc-800" />
            ))}
            <div className="flex h-6 w-6 items-center justify-center rounded-full ring-2 ring-zinc-900 bg-zinc-800 text-[10px] text-zinc-400">+8</div>
          </div>
        </BentoCard>

        <BentoCard
          title="Critical AEs"
          value="23"
          subtitle="Requires immediate attention"
          icon={AlertCircle}
          className="border-red-900/20 bg-red-950/10 hover:border-red-900/40"
        >
          <div className="mt-4 h-1 w-full bg-zinc-800 rounded-full overflow-hidden">
            <div className="h-full bg-red-500 w-[15%]" />
          </div>
        </BentoCard>

        <BentoCard
          title="Data Quality"
          value={qualityScore}
          subtitle="Synthetic fidelity score"
          icon={Activity}
        >
          <div className="mt-4 h-1 w-full bg-zinc-800 rounded-full overflow-hidden">
            <div className="h-full bg-emerald-500 w-[98%]" />
          </div>
        </BentoCard>

        {/* Main Chart (2x2) */}
        <BentoCard
          title="Enrollment over Time"
          colSpan="lg:col-span-2"
          rowSpan="lg:row-span-2"
          className="min-h-[400px]"
        >
          <div className="mt-4 h-full w-full">
            <AreaChart
              className="h-72 mt-4"
              data={enrollmentData}
              index="date"
              categories={["Active Subjects", "Screened"]}
              colors={["teal", "zinc"]}
              valueFormatter={(number) => Intl.NumberFormat("us").format(number).toString()}
              showLegend={true}
              showGridLines={false}
              showYAxis={true}
              showXAxis={true}
              startEndOnly={false}
            />
          </div>
        </BentoCard>

        {/* Recent Queries Sidebar (1x2) */}
        <BentoCard
          title="Recent Queries"
          colSpan="lg:col-span-1"
          rowSpan="lg:row-span-2"
        >
          <div className="mt-4 space-y-3 overflow-y-auto max-h-[320px] pr-2 scrollbar-thin scrollbar-thumb-zinc-800">
            {[
              { id: "Q-1023", subject: "SUB-001", status: "Open", time: "2m ago" },
              { id: "Q-1022", subject: "SUB-042", status: "Resolved", time: "15m ago" },
              { id: "Q-1021", subject: "SUB-089", status: "Open", time: "1h ago" },
              { id: "Q-1020", subject: "SUB-112", status: "Pending", time: "2h ago" },
              { id: "Q-1019", subject: "SUB-005", status: "Resolved", time: "3h ago" },
              { id: "Q-1018", subject: "SUB-033", status: "Open", time: "5h ago" },
            ].map((query) => (
              <div key={query.id} className="flex items-center justify-between p-3 rounded-lg bg-zinc-800/30 border border-zinc-800/50 hover:bg-zinc-800/50 transition-colors cursor-pointer">
                <div className="flex items-center gap-3">
                  <div className={cn(
                    "h-2 w-2 rounded-full",
                    query.status === "Open" ? "bg-red-500" :
                      query.status === "Resolved" ? "bg-emerald-500" : "bg-yellow-500"
                  )} />
                  <div>
                    <p className="text-sm font-medium text-zinc-200">{query.id}</p>
                    <p className="text-xs text-zinc-500">{query.subject}</p>
                  </div>
                </div>
                <span className="text-xs text-zinc-600 font-mono">{query.time}</span>
              </div>
            ))}
          </div>
          <button
            onClick={() => onNavigate?.("queries")}
            className="mt-4 w-full py-2 text-xs font-medium text-teal-500 hover:text-teal-400 hover:bg-teal-500/10 rounded-lg transition-colors"
          >
            View All Queries
          </button>
        </BentoCard>

        {/* Saved Datasets (1x1) */}
        <BentoCard
          title="Saved Datasets"
          colSpan="lg:col-span-1"
          icon={FolderOpen}
        >
          <div className="mt-4 space-y-2">
            {isLoadingDatasets ? (
              <div className="text-xs text-zinc-500">Loading...</div>
            ) : savedDatasets.slice(0, 3).map((ds) => (
              <div key={ds.id} className="flex items-center justify-between text-xs group/item cursor-pointer" onClick={() => loadDataset(ds.dataset_type)}>
                <div className="flex items-center gap-2 text-zinc-300">
                  <FileText className="h-3 w-3 text-zinc-500" />
                  <span className="truncate max-w-[120px]">{ds.dataset_name}</span>
                </div>
                <TrendingUp className="h-3 w-3 text-zinc-600 group-hover/item:text-teal-500" />
              </div>
            ))}
            {savedDatasets.length === 0 && (
              <div className="text-xs text-zinc-500">No datasets found</div>
            )}
          </div>
        </BentoCard>

        {/* System Status (1x1) */}
        <BentoCard
          title="System Status"
          colSpan="lg:col-span-1"
          icon={Activity}
        >
          <div className="mt-4 space-y-2">
            {services.slice(0, 4).map((s) => (
              <div key={s.name} className="flex items-center justify-between text-xs">
                <span className="text-zinc-400">{s.name}</span>
                <div className="flex items-center gap-1.5">
                  <div className={cn(
                    "h-1.5 w-1.5 rounded-full",
                    s.status === "online" ? "bg-emerald-500" :
                      s.status === "checking" ? "bg-yellow-500" : "bg-red-500"
                  )} />
                  <span className={cn(
                    "capitalize",
                    s.status === "online" ? "text-emerald-500" :
                      s.status === "checking" ? "text-yellow-500" : "text-red-500"
                  )}>{s.status}</span>
                </div>
              </div>
            ))}
          </div>
        </BentoCard>
      </div>
    </motion.div >
  );
}
