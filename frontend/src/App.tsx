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
import { QueryManagement } from "@/components/screens/QueryManagement";
import { DataEntry } from "@/components/screens/DataEntry";
import SurvivalAnalysis from "@/pages/SurvivalAnalysis";
import AdamGeneration from "@/pages/AdamGeneration";
import TLFAutomation from "@/pages/TLFAutomation";
import { TopAppBar } from "@/components/layout/TopAppBar";
import { NavigationRail, type Screen } from "@/components/layout/NavigationRail";

function AppContent() {
  const { isAuthenticated, isLoading } = useAuth();
  const [activeScreen, setActiveScreen] = useState<Screen>("dashboard");
  const [showSystemCheck, setShowSystemCheck] = useState(false);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="h-12 w-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    if (showSystemCheck) {
      return (
        <div className="min-h-screen flex flex-col">
          <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur">
            <div className="container flex h-16 items-center justify-between">
              <h1 className="text-xl font-semibold">System Health Check</h1>
              <button
                onClick={() => setShowSystemCheck(false)}
                className="text-sm text-primary hover:underline"
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
        return <QueryManagement />;
      case "data-entry":
        return <DataEntry />;
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
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-background via-primary/5 to-background">
      <TopAppBar />
      <div className="flex flex-1">
        <NavigationRail activeScreen={activeScreen} onScreenChange={setActiveScreen} />
        <main className="flex-1 overflow-auto">
          {renderScreen()}
        </main>
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
