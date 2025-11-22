import { useState } from "react";
import { AuthProvider, useAuth } from "@/hooks/useAuth";
import { DataProvider } from "@/contexts/DataContext";
import { Login } from "@/components/screens/Login";
import { Dashboard } from "@/components/screens/Dashboard";
import { DataGeneration } from "@/components/screens/DataGeneration";
import { Analytics } from "@/components/screens/Analytics";
import { QualityDashboard } from "@/components/screens/QualityDashboard";
import { TrialPlanning } from "@/components/screens/TrialPlanning";
import { LinkupIntegration } from "@/components/screens/LinkupIntegration";
import { MedicalImaging } from "@/components/screens/MedicalImaging";
import { Studies } from "@/components/screens/Studies";
import { Settings } from "@/components/screens/Settings";
import { SystemCheck } from "@/components/screens/SystemCheck";
import { RBQMDashboard } from "@/components/screens/RBQMDashboard";
import { Queries } from "@/components/screens/Queries";
import { DataEntry } from "@/components/screens/DataEntry";
import { AIMedicalMonitor } from "@/components/screens/AIMedicalMonitor";
import SurvivalAnalysis from "@/pages/SurvivalAnalysis";
import AdamGeneration from "@/pages/AdamGeneration";
import TLFAutomation from "@/pages/TLFAutomation";
import { TopAppBar } from "@/components/layout/TopAppBar";
import { GlassSidebar } from "@/components/layout/GlassSidebar";
import { CommandMenu } from "@/components/layout/CommandMenu";
import type { Screen } from "@/constants/navigation";

function AppContent() {
  const { isAuthenticated, isLoading } = useAuth();
  const [activeScreen, setActiveScreen] = useState<Screen>("dashboard");
  const [showSystemCheck, setShowSystemCheck] = useState(false);
  const [commandMenuOpen, setCommandMenuOpen] = useState(false);

  // State for passing data between screens
  const [selectedSubjectId, setSelectedSubjectId] = useState<string | null>(null);
  const [selectedQueryId, setSelectedQueryId] = useState<number | null>(null);

  // Navigation handler with data
  const navigateToDataEntry = (subjectId: string, queryId?: number) => {
    setSelectedSubjectId(subjectId);
    setSelectedQueryId(queryId || null);
    setActiveScreen("data-entry");
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-zinc-950 text-zinc-100">
        <div className="text-center">
          <div className="h-12 w-12 border-4 border-teal-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-zinc-400 font-mono text-sm">INITIALIZING SYSTEM...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    if (showSystemCheck) {
      return (
        <div className="min-h-screen flex flex-col bg-zinc-950 text-zinc-100">
          <header className="sticky top-0 z-50 w-full border-b border-zinc-800 bg-zinc-950/80 backdrop-blur-md">
            <div className="container flex h-16 items-center justify-between">
              <h1 className="text-xl font-semibold tracking-tight">System Health Check</h1>
              <button
                onClick={() => setShowSystemCheck(false)}
                className="text-sm text-teal-500 hover:text-teal-400 hover:underline"
              >
                Back to Login
              </button>
            </div>
          </header>
          <SystemCheck />
        </div>
      );
    }

    return <Login onShowSystemCheck={() => setShowSystemCheck(true)} />;
  }

  const renderScreen = () => {
    switch (activeScreen) {
      case "dashboard":
        return <Dashboard onNavigate={setActiveScreen} />;
      case "generate":
        return <DataGeneration />;
      case "analytics":
        return <Analytics />;
      case "survival":
        return <SurvivalAnalysis />;
      case "adam":
        return <AdamGeneration />;
      case "tlf":
        return <TLFAutomation />;

      case "quality":
        return <QualityDashboard />;
      case "trial-planning":
        return <TrialPlanning />;
      case "rbqm":
        return <RBQMDashboard />;
      case "linkup":
        return <LinkupIntegration />;
      case "medical-imaging":
        return <MedicalImaging />;
      case "queries":
        return <Queries onNavigateToDataEntry={navigateToDataEntry} />;
      case "data-entry":
        return <DataEntry selectedSubjectId={selectedSubjectId} selectedQueryId={selectedQueryId} />;
      case "ai-monitor":
        return <AIMedicalMonitor />;
      case "studies":
        return <Studies />;
      case "settings":
        return <Settings />;
      case "system-check":
        return <SystemCheck />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="min-h-screen flex bg-zinc-950 text-zinc-100 font-sans selection:bg-teal-500/30">
      <GlassSidebar activeScreen={activeScreen} onScreenChange={setActiveScreen} />

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <TopAppBar />
        <main className="flex-1 overflow-auto p-6 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
          <div className="mx-auto max-w-7xl animate-in fade-in slide-in-from-bottom-4 duration-500">
            {renderScreen()}
          </div>
        </main>
      </div>

      <CommandMenu
        open={commandMenuOpen}
        onOpenChange={setCommandMenuOpen}
        onNavigate={setActiveScreen}
      />

      {/* Keyboard shortcut hint */}
      <div className="fixed bottom-4 right-4 z-50 hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-zinc-900/80 border border-zinc-800 text-xs text-zinc-500 backdrop-blur-sm">
        <span>Command Menu</span>
        <kbd className="pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border border-zinc-700 bg-zinc-800 px-1.5 font-mono text-[10px] font-medium text-zinc-400 opacity-100">
          <span className="text-xs">⌘</span>K
        </kbd>
      </div>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <DataProvider>
        <AppContent />
      </DataProvider>
    </AuthProvider>
  );
}

export default App;
