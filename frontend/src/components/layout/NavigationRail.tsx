import { cn } from "@/lib/utils";
import { Home, Activity, BarChart3, Beaker, FileText, Settings } from "lucide-react";

export type Screen = "dashboard" | "generate" | "analytics" | "studies" | "quality" | "settings";

interface NavigationRailProps {
  activeScreen: Screen;
  onScreenChange: (screen: Screen) => void;
}

const navItems = [
  { id: "dashboard" as Screen, label: "Dashboard", icon: Home },
  { id: "generate" as Screen, label: "Generate Data", icon: Beaker },
  { id: "analytics" as Screen, label: "Analytics", icon: BarChart3 },
  { id: "quality" as Screen, label: "Quality", icon: Activity },
  { id: "studies" as Screen, label: "Studies", icon: FileText },
  { id: "settings" as Screen, label: "Settings", icon: Settings },
];

export function NavigationRail({ activeScreen, onScreenChange }: NavigationRailProps) {
  return (
    <nav className="w-20 border-r bg-muted/10 flex flex-col items-center py-4 gap-2">
      {navItems.map((item) => {
        const Icon = item.icon;
        const isActive = activeScreen === item.id;

        return (
          <button
            key={item.id}
            onClick={() => onScreenChange(item.id)}
            className={cn(
              "flex flex-col items-center justify-center w-16 h-16 rounded-lg transition-colors",
              isActive
                ? "bg-primary text-primary-foreground"
                : "hover:bg-accent hover:text-accent-foreground text-muted-foreground"
            )}
            title={item.label}
          >
            <Icon className="h-6 w-6" />
            <span className="text-xs mt-1">{item.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
