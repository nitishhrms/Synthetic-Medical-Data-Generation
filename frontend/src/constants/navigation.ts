import { Home, Activity, BarChart3, Beaker, FileText, Settings, TrendingUp, MessageSquare, ClipboardEdit, ActivitySquare, Database, Table, FlaskConical, Shield, ImageIcon, Brain } from "lucide-react";

export type Screen = "dashboard" | "generate" | "analytics" | "studies" | "quality" | "settings" | "system-check" | "rbqm" | "queries" | "data-entry" | "survival" | "adam" | "tlf" | "trial-planning" | "linkup" | "medical-imaging" | "ai-monitor";

export const NAV_ITEMS = [
    { id: "dashboard" as Screen, label: "Dashboard", icon: Home },
    { id: "generate" as Screen, label: "Generate", icon: Beaker },
    { id: "analytics" as Screen, label: "Analytics", icon: BarChart3 },
    { id: "survival" as Screen, label: "Survival", icon: ActivitySquare },
    { id: "adam" as Screen, label: "ADaM", icon: Database },
    { id: "tlf" as Screen, label: "TLF", icon: Table },
    { id: "quality" as Screen, label: "Quality", icon: Activity },
    { id: "trial-planning" as Screen, label: "Planning", icon: FlaskConical },
    { id: "rbqm" as Screen, label: "RBQM", icon: TrendingUp },
    { id: "linkup" as Screen, label: "Linkup", icon: Shield },
    { id: "medical-imaging" as Screen, label: "Imaging", icon: ImageIcon },
    { id: "ai-monitor" as Screen, label: "AI Monitor", icon: Brain },
    { id: "queries" as Screen, label: "Queries", icon: MessageSquare },
    { id: "data-entry" as Screen, label: "Data Entry", icon: ClipboardEdit },
    { id: "studies" as Screen, label: "Studies", icon: FileText },
    { id: "settings" as Screen, label: "Settings", icon: Settings },
];
