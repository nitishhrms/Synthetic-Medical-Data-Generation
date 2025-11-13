import { useState } from "react";
import { AuthProvider, useAuth } from "@/hooks/useAuth";
import { Login } from "@/components/screens/Login";
import { Dashboard } from "@/components/screens/Dashboard";
import { DataGeneration } from "@/components/screens/DataGeneration";
import { Analytics } from "@/components/screens/Analytics";
import { Studies } from "@/components/screens/Studies";
import { Settings } from "@/components/screens/Settings";
import { TopAppBar } from "@/components/layout/TopAppBar";
import { NavigationRail, type Screen } from "@/components/layout/NavigationRail";

function AppContent() {
  const { isAuthenticated, isLoading } = useAuth();
  const [activeScreen, setActiveScreen] = useState<Screen>("dashboard");

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
    return <Login />;
  }

  const renderScreen = () => {
    switch (activeScreen) {
      case "dashboard":
        return <Dashboard />;
      case "generate":
        return <DataGeneration />;
      case "analytics":
      case "quality":
        return <Analytics />;
      case "studies":
        return <Studies />;
      case "settings":
        return <Settings />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
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
      <AppContent />
    </AuthProvider>
  );
}

export default App;
