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
  SYNDATAMetricsResponse,
  QualityReportResponse,
  PrivacyAssessmentResponse,
  VirtualControlArmRequest,
  VirtualControlArmResponse,
  AugmentControlArmRequest,
  AugmentControlArmResponse,
  WhatIfEnrollmentRequest,
  WhatIfEnrollmentResponse,
  WhatIfPatientMixRequest,
  WhatIfPatientMixResponse,
  FeasibilityAssessmentRequest,
  FeasibilityAssessmentResponse,
} from "@/types";

// ============================================================================
// API Configuration
// ============================================================================

const DATA_GEN_SERVICE = import.meta.env.VITE_DATA_GEN_URL || "http://localhost:8002";
const ANALYTICS_SERVICE = import.meta.env.VITE_ANALYTICS_URL || "http://localhost:8003";
const EDC_SERVICE = import.meta.env.VITE_EDC_URL || "http://localhost:8004";
const SECURITY_SERVICE = import.meta.env.VITE_SECURITY_URL || "http://localhost:8005";
const QUALITY_SERVICE = import.meta.env.VITE_QUALITY_URL || "http://localhost:8006";

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

  async generateBayesian(params: GenerationRequest): Promise<GenerationResponse> {
    const response = await fetch(`${DATA_GEN_SERVICE}/generate/bayesian`, {
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
        method: "bayesian",
      },
    };
  },

  async generateMICE(params: GenerationRequest): Promise<GenerationResponse> {
    const response = await fetch(`${DATA_GEN_SERVICE}/generate/mice`, {
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
        method: "mice",
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

  async assessSYNDATA(realData: VitalsRecord[], syntheticData: VitalsRecord[]): Promise<SYNDATAMetricsResponse> {
    const response = await fetch(`${QUALITY_SERVICE}/syndata/assess`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        real_data: realData,
        synthetic_data: syntheticData,
      }),
    });
    return handleResponse(response);
  },

  async generateQualityReport(
    methodName: string,
    realData: VitalsRecord[],
    syntheticData: VitalsRecord[],
    syndataMetrics?: any,
    privacyMetrics?: any,
    generationTimeMs?: number
  ): Promise<QualityReportResponse> {
    const response = await fetch(`${QUALITY_SERVICE}/quality/report`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        method_name: methodName,
        real_data: realData,
        synthetic_data: syntheticData,
        syndata_metrics: syndataMetrics,
        privacy_metrics: privacyMetrics,
        generation_time_ms: generationTimeMs,
      }),
    });
    return handleResponse(response);
  },

  async assessPrivacy(
    realData: VitalsRecord[],
    syntheticData: VitalsRecord[],
    quasiIdentifiers?: string[],
    sensitiveAttributes?: string[]
  ): Promise<PrivacyAssessmentResponse> {
    const response = await fetch(`${QUALITY_SERVICE}/privacy/assess/comprehensive`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        real_data: realData,
        synthetic_data: syntheticData,
        quasi_identifiers: quasiIdentifiers,
        sensitive_attributes: sensitiveAttributes,
      }),
    });
    return handleResponse(response);
  },
};

// ============================================================================
// Trial Planning API
// ============================================================================

export const trialPlanningApi = {
  async createVirtualControlArm(request: VirtualControlArmRequest): Promise<VirtualControlArmResponse> {
    const response = await fetch(`${ANALYTICS_SERVICE}/trial-planning/virtual-control-arm`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
    });
    return handleResponse(response);
  },

  async augmentControlArm(request: AugmentControlArmRequest): Promise<AugmentControlArmResponse> {
    const response = await fetch(`${ANALYTICS_SERVICE}/trial-planning/augment-control-arm`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
    });
    return handleResponse(response);
  },

  async whatIfEnrollment(request: WhatIfEnrollmentRequest): Promise<WhatIfEnrollmentResponse> {
    const response = await fetch(`${ANALYTICS_SERVICE}/trial-planning/what-if/enrollment`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
    });
    return handleResponse(response);
  },

  async whatIfPatientMix(request: WhatIfPatientMixRequest): Promise<WhatIfPatientMixResponse> {
    const response = await fetch(`${ANALYTICS_SERVICE}/trial-planning/what-if/patient-mix`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
    });
    return handleResponse(response);
  },

  async assessFeasibility(request: FeasibilityAssessmentRequest): Promise<FeasibilityAssessmentResponse> {
    const response = await fetch(`${ANALYTICS_SERVICE}/trial-planning/feasibility`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
    });
    return handleResponse(response);
  },
};
