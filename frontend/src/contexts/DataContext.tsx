import { createContext, useContext, useState, ReactNode } from "react";
import type {
  VitalsRecord,
  Week12StatsResponse,
  QualityAssessmentResponse,
  PCAComparisonResponse,
  ValidationResponse,
} from "@/types";

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

  // Helper function to clear all data
  clearAllData: () => void;
}

const DataContext = createContext<DataContextType | undefined>(undefined);

export function DataProvider({ children }: { children: ReactNode }) {
  const [generatedData, setGeneratedData] = useState<VitalsRecord[] | null>(null);
  const [generationMethod, setGenerationMethod] = useState<string | null>(null);
  const [repairedData, setRepairedData] = useState<VitalsRecord[] | null>(null);
  const [pilotData, setPilotData] = useState<VitalsRecord[] | null>(null);
  const [week12Stats, setWeek12Stats] = useState<Week12StatsResponse | null>(null);
  const [qualityMetrics, setQualityMetrics] = useState<QualityAssessmentResponse | null>(null);
  const [pcaComparison, setPcaComparison] = useState<PCAComparisonResponse | null>(null);
  const [validationResults, setValidationResults] = useState<ValidationResponse | null>(null);

  const clearAllData = () => {
    setGeneratedData(null);
    setGenerationMethod(null);
    setRepairedData(null);
    setPilotData(null);
    setWeek12Stats(null);
    setQualityMetrics(null);
    setPcaComparison(null);
    setValidationResults(null);
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
