import type {
  AuthResponse,
  GenerationRequest,
  GenerationResponse,
  LoginRequest,
  QualityAssessmentResponse,
  RegisterRequest,
  Study,
  User,
  ValidationResponse,
  VitalsRecord,
  Week12StatsRequest,
  Week12StatsResponse,
  PCAComparisonResponse,
} from "@/types";

// ============================================================================
// API Configuration
// ============================================================================

const DATA_GEN_SERVICE = import.meta.env.VITE_DATA_GEN_URL || "http://localhost:8002";
const ANALYTICS_SERVICE = import.meta.env.VITE_ANALYTICS_URL || "http://localhost:8003";
const EDC_SERVICE = import.meta.env.VITE_EDC_URL || "http://localhost:8001";
const SECURITY_SERVICE = import.meta.env.VITE_SECURITY_URL || "http://localhost:8005";
const QUALITY_SERVICE = import.meta.env.VITE_QUALITY_URL || "http://localhost:8006";
const DAFT_SERVICE = import.meta.env.VITE_DAFT_URL || "http://localhost:8007";

// ============================================================================
// Helper Functions
// ============================================================================

function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem("token");
  return {
    "Content-Type": "application/json",
    ...(token && { Authorization: `Bearer ${token}` }),
  };
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "An error occurred" }));
    throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
  }
  return response.json();
}

// ============================================================================
// Authentication API
// ============================================================================

export const authApi = {
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await fetch(`${SECURITY_SERVICE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(credentials),
    });
    const data = await handleResponse<AuthResponse>(response);
    localStorage.setItem("token", data.access_token);
    return data;
  },

  async register(userData: RegisterRequest): Promise<{ user_id: string; message: string }> {
    const response = await fetch(`${SECURITY_SERVICE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(userData),
    });
    return handleResponse(response);
  },

  async getCurrentUser(): Promise<User> {
    const response = await fetch(`${SECURITY_SERVICE}/auth/me`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  logout() {
    localStorage.removeItem("token");
  },
};

// ============================================================================
// Data Generation API
// ============================================================================

export const dataGenerationApi = {
  async generateMVN(params: GenerationRequest): Promise<GenerationResponse> {
    const response = await fetch(`${DATA_GEN_SERVICE}/generate/mvn`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(params),
    });
    const data = await handleResponse<VitalsRecord[]>(response);
    // Backend returns array directly, wrap it in expected format
    const uniqueSubjects = new Set(data.map(r => r.SubjectID)).size;
    return {
      data,
      metadata: {
        records: data.length,
        subjects: uniqueSubjects,
        method: "mvn",
      },
    };
  },

  async generateBootstrap(params: GenerationRequest): Promise<GenerationResponse> {
    // First, fetch pilot data to use as training data
    const pilotData = await this.getPilotData();

    const response = await fetch(`${DATA_GEN_SERVICE}/generate/bootstrap`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        ...params,
        training_data: pilotData,
      }),
    });
    const data = await handleResponse<VitalsRecord[]>(response);
    const uniqueSubjects = new Set(data.map(r => r.SubjectID)).size;
    return {
      data,
      metadata: {
        records: data.length,
        subjects: uniqueSubjects,
        method: "bootstrap",
      },
    };
  },

  async generateRules(params: GenerationRequest): Promise<GenerationResponse> {
    const response = await fetch(`${DATA_GEN_SERVICE}/generate/rules`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(params),
    });
    const data = await handleResponse<VitalsRecord[]>(response);
    const uniqueSubjects = new Set(data.map(r => r.SubjectID)).size;
    return {
      data,
      metadata: {
        records: data.length,
        subjects: uniqueSubjects,
        method: "rules",
      },
    };
  },

  async generateLLM(params: GenerationRequest): Promise<GenerationResponse> {
    const response = await fetch(`${DATA_GEN_SERVICE}/generate/llm`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(params),
    });
    return handleResponse(response);
  },

  async generateDiffusion(params: GenerationRequest): Promise<GenerationResponse> {
    const response = await fetch(`${DATA_GEN_SERVICE}/generate/diffusion`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(params),
    });
    const data = await handleResponse<VitalsRecord[]>(response);
    return {
      data,
      metadata: {
        records: data.length,
        method: "diffusion",
      },
    };
  },

  async compareMethods(params: GenerationRequest): Promise<any> {
    const response = await fetch(`${DATA_GEN_SERVICE}/compare?${new URLSearchParams(params as any)}`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  async getPilotData(): Promise<VitalsRecord[]> {
    const response = await fetch(`${DATA_GEN_SERVICE}/data/pilot`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },
};

// ============================================================================
// Analytics API
// ============================================================================

export const analyticsApi = {
  async getWeek12Stats(request: Week12StatsRequest): Promise<Week12StatsResponse> {
    const response = await fetch(`${ANALYTICS_SERVICE}/stats/week12`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
    });
    return handleResponse(response);
  },

  async comprehensiveQuality(
    original: VitalsRecord[],
    synthetic: VitalsRecord[],
    k: number = 5
  ): Promise<QualityAssessmentResponse> {
    const response = await fetch(`${ANALYTICS_SERVICE}/quality/comprehensive`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        original_data: original,
        synthetic_data: synthetic,
        k,
      }),
    });
    return handleResponse(response);
  },

  async pcaComparison(
    original: VitalsRecord[],
    synthetic: VitalsRecord[]
  ): Promise<PCAComparisonResponse> {
    const response = await fetch(`${ANALYTICS_SERVICE}/quality/pca-comparison`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        original_data: original,
        synthetic_data: synthetic,
      }),
    });
    return handleResponse(response);
  },

  async generateCSR(statistics: Week12StatsResponse, aeData: any[], nRows: number): Promise<{ csr_markdown: string }> {
    const response = await fetch(`${ANALYTICS_SERVICE}/csr/draft`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        statistics,
        ae_data: aeData,
        n_rows: nRows,
      }),
    });
    return handleResponse(response);
  },

  async exportSDTM(vitalsData: VitalsRecord[]): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/sdtm/export`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ vitals_data: vitalsData }),
    });
    return handleResponse(response);
  },
};

// ============================================================================
// EDC (Study Management) API
// ============================================================================

export const edcApi = {
  async createStudy(study: Omit<Study, "study_id" | "created_at">): Promise<{ study_id: string; message: string }> {
    const response = await fetch(`${EDC_SERVICE}/studies`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(study),
    });
    return handleResponse(response);
  },

  async listStudies(): Promise<{ studies: Study[] }> {
    const response = await fetch(`${EDC_SERVICE}/studies`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  async getStudy(studyId: string): Promise<Study> {
    const response = await fetch(`${EDC_SERVICE}/studies/${studyId}`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  async importSyntheticData(
    studyId: string,
    data: VitalsRecord[],
    source: string
  ): Promise<{ subjects_imported: number; observations_imported: number; message: string }> {
    const response = await fetch(`${EDC_SERVICE}/import/synthetic`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        study_id: studyId,
        data,
        source,
      }),
    });
    return handleResponse(response);
  },
};

// ============================================================================
// Quality API
// ============================================================================

export const qualityApi = {
  async validateVitals(data: VitalsRecord[]): Promise<ValidationResponse> {
    const response = await fetch(`${QUALITY_SERVICE}/checks/validate`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ data }),
    });
    return handleResponse(response);
  },
};

// ============================================================================
// Daft Analytics API
// ============================================================================

export const daftApi = {
  // Health check
  async healthCheck(): Promise<any> {
    const response = await fetch(`${DAFT_SERVICE}/health`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  // Core Data Processing
  async loadData(data: VitalsRecord[]): Promise<any> {
    const response = await fetch(`${DAFT_SERVICE}/daft/load`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ data }),
    });
    return handleResponse(response);
  },

  async filterData(
    data: VitalsRecord[],
    condition?: string,
    treatmentArm?: string,
    visitName?: string
  ): Promise<any> {
    const response = await fetch(`${DAFT_SERVICE}/daft/filter`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        data,
        condition,
        treatment_arm: treatmentArm,
        visit_name: visitName,
      }),
    });
    return handleResponse(response);
  },

  async selectColumns(data: VitalsRecord[], columns: string[]): Promise<any> {
    const response = await fetch(`${DAFT_SERVICE}/daft/select?${new URLSearchParams({ columns: columns.join(",") })}`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ data }),
    });
    return handleResponse(response);
  },

  async addDerivedColumn(data: VitalsRecord[], columnName: string, expression: string): Promise<any> {
    const response = await fetch(`${DAFT_SERVICE}/daft/add-derived-column`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        data,
        column_name: columnName,
        expression,
      }),
    });
    return handleResponse(response);
  },

  async addMedicalFeatures(data: VitalsRecord[]): Promise<any> {
    const response = await fetch(`${DAFT_SERVICE}/daft/add-medical-features`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ data }),
    });
    return handleResponse(response);
  },

  // Aggregation endpoints
  async aggregateByTreatmentArm(data: VitalsRecord[]): Promise<any> {
    const response = await fetch(`${DAFT_SERVICE}/daft/aggregate/by-treatment-arm`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ data }),
    });
    return handleResponse(response);
  },

  async aggregateByVisit(data: VitalsRecord[]): Promise<any> {
    const response = await fetch(`${DAFT_SERVICE}/daft/aggregate/by-visit`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ data }),
    });
    return handleResponse(response);
  },

  async aggregateBySubject(data: VitalsRecord[]): Promise<any> {
    const response = await fetch(`${DAFT_SERVICE}/daft/aggregate/by-subject`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ data }),
    });
    return handleResponse(response);
  },

  async computeTreatmentEffect(
    data: VitalsRecord[],
    endpoint: string = "SystolicBP",
    visit: string = "Week 12"
  ): Promise<any> {
    const response = await fetch(`${DAFT_SERVICE}/daft/treatment-effect`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ data, endpoint, visit }),
    });
    return handleResponse(response);
  },

  async computeLongitudinalSummary(data: VitalsRecord[]): Promise<any> {
    const response = await fetch(`${DAFT_SERVICE}/daft/longitudinal-summary`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ data }),
    });
    return handleResponse(response);
  },

  async computeCorrelationMatrix(data: VitalsRecord[]): Promise<any> {
    const response = await fetch(`${DAFT_SERVICE}/daft/correlation-matrix`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ data }),
    });
    return handleResponse(response);
  },

  // Advanced Analytics
  async computeChangeFromBaseline(data: VitalsRecord[]): Promise<any> {
    const response = await fetch(`${DAFT_SERVICE}/daft/change-from-baseline`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ data }),
    });
    return handleResponse(response);
  },

  async responderAnalysis(
    data: VitalsRecord[],
    threshold: number = -10.0,
    endpoint: string = "SystolicBP"
  ): Promise<any> {
    const response = await fetch(`${DAFT_SERVICE}/daft/responder-analysis`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ data, threshold, endpoint }),
    });
    return handleResponse(response);
  },

  async timeToEffect(
    data: VitalsRecord[],
    threshold: number = -5.0,
    endpoint: string = "SystolicBP"
  ): Promise<any> {
    const response = await fetch(`${DAFT_SERVICE}/daft/time-to-effect?${new URLSearchParams({
      threshold: threshold.toString(),
      endpoint,
    })}`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ data }),
    });
    return handleResponse(response);
  },

  async detectOutliers(
    data: VitalsRecord[],
    column: string = "SystolicBP",
    method: string = "iqr"
  ): Promise<any> {
    const response = await fetch(`${DAFT_SERVICE}/daft/outlier-detection`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ data, column, method }),
    });
    return handleResponse(response);
  },

  // UDF endpoints
  async applyQualityFlags(data: VitalsRecord[]): Promise<any> {
    const response = await fetch(`${DAFT_SERVICE}/daft/apply-quality-flags`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ data }),
    });
    return handleResponse(response);
  },

  async identifyResponders(
    data: VitalsRecord[],
    threshold: number = -10.0,
    endpoint: string = "SystolicBP"
  ): Promise<any> {
    const response = await fetch(`${DAFT_SERVICE}/daft/identify-responders?${new URLSearchParams({
      threshold: threshold.toString(),
      endpoint,
    })}`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ data }),
    });
    return handleResponse(response);
  },

  // SQL Query
  async executeSqlQuery(data: VitalsRecord[], query: string): Promise<any> {
    const response = await fetch(`${DAFT_SERVICE}/daft/sql`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ data, query }),
    });
    return handleResponse(response);
  },

  // Export endpoints
  async exportToCsv(data: VitalsRecord[], filename: string = "daft_export.csv"): Promise<any> {
    const response = await fetch(`${DAFT_SERVICE}/daft/export/csv?${new URLSearchParams({ filename })}`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ data }),
    });
    return handleResponse(response);
  },

  async exportToParquet(data: VitalsRecord[], filename: string = "daft_export.parquet"): Promise<any> {
    const response = await fetch(`${DAFT_SERVICE}/daft/export/parquet?${new URLSearchParams({ filename })}`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ data }),
    });
    return handleResponse(response);
  },

  // Explain & Benchmark
  async explainExecutionPlan(data: VitalsRecord[], operations: string[] = []): Promise<any> {
    const response = await fetch(`${DAFT_SERVICE}/daft/explain?${new URLSearchParams({ operations: operations.join(",") })}`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ data }),
    });
    return handleResponse(response);
  },

  async benchmark(data: VitalsRecord[]): Promise<any> {
    const response = await fetch(`${DAFT_SERVICE}/daft/benchmark`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ data }),
    });
    return handleResponse(response);
  },
};

// ============================================================================
// Default export (for backward compatibility)
// ============================================================================

export const api = {
  auth: authApi,
  dataGeneration: dataGenerationApi,
  analytics: analyticsApi,
  edc: edcApi,
  quality: qualityApi,
  daft: daftApi,
};
