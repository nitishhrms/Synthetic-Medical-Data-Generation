import { cn } from "@/lib/utils";
import { Home, Activity, BarChart3, Beaker, FileText, Settings, TrendingUp, MessageSquare, ClipboardEdit, Database, Shield } from "lucide-react";

export type Screen = "dashboard" | "generate" | "analytics" | "studies" | "quality" | "settings" | "system-check" | "rbqm" | "queries" | "data-entry" | "daft" | "linkup";

interface NavigationRailProps {
  activeScreen: Screen;
  onScreenChange: (screen: Screen) => void;
}

const navItems = [
  { id: "dashboard" as Screen, label: "Dashboard", icon: Home },
  { id: "generate" as Screen, label: "Generate", icon: Beaker },
  { id: "analytics" as Screen, label: "Analytics", icon: BarChart3 },
  { id: "daft" as Screen, label: "Daft", icon: Database },
  { id: "quality" as Screen, label: "Quality", icon: Activity },
  { id: "rbqm" as Screen, label: "RBQM", icon: TrendingUp },
  { id: "linkup" as Screen, label: "Linkup", icon: Shield },
  { id: "queries" as Screen, label: "Queries", icon: MessageSquare },
  { id: "data-entry" as Screen, label: "Data Entry", icon: ClipboardEdit },
  { id: "studies" as Screen, label: "Studies", icon: FileText },
  { id: "settings" as Screen, label: "Settings", icon: Settings },
];

export function NavigationRail({ activeScreen, onScreenChange }: NavigationRailProps) {
  return (
    <nav className="w-20 border-r border-primary/10 bg-gradient-to-b from-primary/5 via-primary/3 to-background flex flex-col items-center py-6 gap-3">
      {navItems.map((item) => {
        const Icon = item.icon;
        const isActive = activeScreen === item.id;

        return (
          <button
            key={item.id}
            onClick={() => onScreenChange(item.id)}
            className={cn(
              "flex flex-col items-center justify-center w-16 h-16 rounded-2xl transition-all duration-200",
              isActive
                ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20 scale-105"
                : "bg-background/60 hover:bg-primary/10 hover:text-primary text-muted-foreground hover:scale-105 shadow-sm"
            )}
            title={item.label}
          >
            <Icon className="h-6 w-6" />
            <span className="text-xs mt-1 font-medium">{item.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
