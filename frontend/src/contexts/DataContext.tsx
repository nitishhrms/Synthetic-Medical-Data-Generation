import { createContext, useContext, useState, useEffect } from "react";
import type { ReactNode } from "react";
import type {
  VitalsRecord,
  Week12StatsResponse,
  QualityAssessmentResponse,
  PCAComparisonResponse,
  ValidationResponse,
} from "@/types";

// Planning Scenario Type
export interface PlanningScenario {
  id?: string;
  name?: string;
  timestamp?: string;
  // Feasibility Parameters
  nPerArm?: number;
  targetEffect?: number;
  power?: number;
  alpha?: number;
  stdDev?: number;
  dropoutRate?: number;
  allocationRatio?: number;
  testType?: "two-sided" | "one-sided";
  // Results
  requiredN?: number;
  cohensD?: number;
  feasibilityGrade?: string;
  // Source
  source?: "feasibility" | "what-if" | "virtual-control" | "template";
}
import { dataGenerationApi } from "@/services/api";

interface DataContextType {
  // Generated Data
  generatedData: VitalsRecord[] | null;
  setGeneratedData: (data: VitalsRecord[] | null) => void;
  generationMethod: string | null;
  setGenerationMethod: (method: string | null) => void;

  // Repaired Data
  repairedData: VitalsRecord[] | null;
  setRepairedData: (data: VitalsRecord[] | null) => void;

  // Pilot/Real Data
  pilotData: VitalsRecord[] | null;
  setPilotData: (data: VitalsRecord[] | null) => void;

  // Analytics
  week12Stats: Week12StatsResponse | null;
  setWeek12Stats: (stats: Week12StatsResponse | null) => void;
  qualityMetrics: QualityAssessmentResponse | null;
  setQualityMetrics: (metrics: QualityAssessmentResponse | null) => void;
  pcaComparison: PCAComparisonResponse | null;
  setPcaComparison: (pca: PCAComparisonResponse | null) => void;

  // Quality/Validation
  validationResults: ValidationResponse | null;
  setValidationResults: (results: ValidationResponse | null) => void;

  // Planning Scenario
  planningScenario: PlanningScenario | null;
  setPlanningScenario: (scenario: PlanningScenario | null) => void;

  // Helper function to clear all data
  clearAllData: () => void;
}

const DataContext = createContext<DataContextType | undefined>(undefined);

export function DataProvider({ children }: { children: ReactNode }) {
  const [generatedData, setGeneratedDataState] = useState<VitalsRecord[] | null>(null);
  const [generationMethod, setGenerationMethod] = useState<string | null>(null);
  const [repairedData, setRepairedData] = useState<VitalsRecord[] | null>(null);
  const [pilotData, setPilotData] = useState<VitalsRecord[] | null>(null);
  const [week12Stats, setWeek12Stats] = useState<Week12StatsResponse | null>(null);
  const [qualityMetrics, setQualityMetrics] = useState<QualityAssessmentResponse | null>(null);
  const [pcaComparison, setPcaComparison] = useState<PCAComparisonResponse | null>(null);
  const [validationResults, setValidationResults] = useState<ValidationResponse | null>(null);
  const [planningScenario, setPlanningScenario] = useState<PlanningScenario | null>(null);

  // Load persisted data on mount
  useEffect(() => {
    loadPersistedData();
  }, []);

  const loadPersistedData = async () => {
    try {
      const result = await dataGenerationApi.loadLatestData("vitals");
      if (result && result.data) {
        setGeneratedDataState(result.data);
        if (result.metadata?.method) {
          setGenerationMethod(result.metadata.method);
        }
        console.log("Loaded persisted data:", result.dataset_name);
      }
    } catch (err) {
      console.log("No persisted data found or failed to load");
    }
  };

  const setGeneratedData = (data: VitalsRecord[] | null) => {
    setGeneratedDataState(data);

    // Persist data when it's updated (and not null)
    if (data && data.length > 0) {
      const methodName = generationMethod || "unknown";
      dataGenerationApi.saveGeneratedData(
        `Generated ${methodName} ${new Date().toISOString()}`,
        "vitals",
        data,
        { method: methodName, count: data.length }
      ).catch((err: unknown) => console.error("Failed to persist data:", err));
    }
  };

  const clearAllData = () => {
    setGeneratedDataState(null);
    setGenerationMethod(null);
    setRepairedData(null);
    setPilotData(null);
    setWeek12Stats(null);
    setQualityMetrics(null);
    setPcaComparison(null);
    setValidationResults(null);
    setPlanningScenario(null);
  };

  return (
    <DataContext.Provider
      value={{
        generatedData,
        setGeneratedData,
        generationMethod,
        setGenerationMethod,
        repairedData,
        setRepairedData,
        pilotData,
        setPilotData,
        week12Stats,
        setWeek12Stats,
        qualityMetrics,
        setQualityMetrics,
        pcaComparison,
        setPcaComparison,
        validationResults,
        setValidationResults,
        planningScenario,
        setPlanningScenario,
        clearAllData,
      }}
    >
      {children}
    </DataContext.Provider>
  );
}

export function useData() {
  const context = useContext(DataContext);
  if (context === undefined) {
    throw new Error("useData must be used within a DataProvider");
  }
  return context;
}
