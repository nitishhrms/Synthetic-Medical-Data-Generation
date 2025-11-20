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
const EDC_SERVICE = import.meta.env.VITE_EDC_URL || "http://localhost:8001";
const SECURITY_SERVICE = import.meta.env.VITE_SECURITY_URL || "http://localhost:8005";
const QUALITY_SERVICE = import.meta.env.VITE_QUALITY_URL || "http://localhost:8004";
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
  async generateMVN(params: GenerationRequest & { indication?: string; phase?: string }): Promise<GenerationResponse> {
    // Use AACT-enhanced endpoint by default for maximum realism
    const response = await fetch(`${DATA_GEN_SERVICE}/generate/mvn-aact`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        ...params,
        indication: params.indication || "hypertension",
        phase: params.phase || "Phase 3",
        use_duration: true,
      }),
    });
    const data = await handleResponse<VitalsRecord[]>(response);
    // Backend returns array directly, wrap it in expected format
    const uniqueSubjects = new Set(data.map(r => r.SubjectID)).size;
    return {
      data,
      metadata: {
        records: data.length,
        subjects: uniqueSubjects,
        method: "mvn-aact",
      },
    };
  },

  async generateBootstrap(params: GenerationRequest & { indication?: string; phase?: string }): Promise<GenerationResponse> {
    // Use AACT-enhanced endpoint by default for maximum realism
    const response = await fetch(`${DATA_GEN_SERVICE}/generate/bootstrap-aact`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        ...params,
        indication: params.indication || "hypertension",
        phase: params.phase || "Phase 3",
        use_duration: true,
        jitter_frac: 0.05,
      }),
    });
    const data = await handleResponse<VitalsRecord[]>(response);
    const uniqueSubjects = new Set(data.map(r => r.SubjectID)).size;
    return {
      data,
      metadata: {
        records: data.length,
        subjects: uniqueSubjects,
        method: "bootstrap-aact",
      },
    };
  },

  async generateRules(params: GenerationRequest & { indication?: string; phase?: string }): Promise<GenerationResponse> {
    // Use AACT-enhanced endpoint by default for maximum realism
    const response = await fetch(`${DATA_GEN_SERVICE}/generate/rules-aact`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        ...params,
        indication: params.indication || "hypertension",
        phase: params.phase || "Phase 3",
        use_duration: true,
      }),
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

  async generateBayesian(params: GenerationRequest & { indication?: string; phase?: string }): Promise<GenerationResponse> {
    // Use AACT-enhanced endpoint by default for maximum realism
    const response = await fetch(`${DATA_GEN_SERVICE}/generate/bayesian-aact`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        ...params,
        indication: params.indication || "hypertension",
        phase: params.phase || "Phase 3",
        use_duration: true,
      }),
    });
    const data = await handleResponse<VitalsRecord[]>(response);
    const uniqueSubjects = new Set(data.map(r => r.SubjectID)).size;
    return {
      data,
      metadata: {
        records: data.length,
        subjects: uniqueSubjects,
        method: "bayesian-aact",
      },
    };
  },

  async generateMICE(params: GenerationRequest & { indication?: string; phase?: string; missing_rate?: number; estimator?: string }): Promise<GenerationResponse> {
    // Use AACT-enhanced endpoint by default for maximum realism
    const response = await fetch(`${DATA_GEN_SERVICE}/generate/mice-aact`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        ...params,
        indication: params.indication || "hypertension",
        phase: params.phase || "Phase 3",
        use_duration: true,
        missing_rate: params.missing_rate || 0.10,
        estimator: params.estimator || "bayesian_ridge",
      }),
    });
    const data = await handleResponse<VitalsRecord[]>(response);
    const uniqueSubjects = new Set(data.map(r => r.SubjectID)).size;
    return {
      data,
      metadata: {
        records: data.length,
        subjects: uniqueSubjects,
        method: "mice-aact",
      },
    };
  },

  async generateMillionScale(params: {
    total_subjects: number;
    chunk_size?: number;
    target_effect?: number;
    output_path?: string;
    format?: string;
  }): Promise<any> {
    const response = await fetch(`${DATA_GEN_SERVICE}/generate/million-scale`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(params),
    });
    return handleResponse(response);
  },

  async estimateMemory(params: { total_subjects: number; chunk_size: number }): Promise<any> {
    const response = await fetch(`${DATA_GEN_SERVICE}/generate/estimate-memory`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(params),
    });
    return handleResponse(response);
  },

  async getDaftStatus(): Promise<any> {
    const response = await fetch(`${DATA_GEN_SERVICE}/daft/status`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  async generateDemographics(params: { n_subjects: number; seed?: number; indication?: string; phase?: string }): Promise<any> {
    // Use AACT-enhanced endpoint by default for maximum realism
    const response = await fetch(`${DATA_GEN_SERVICE}/generate/demographics-aact`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        n_subjects: params.n_subjects,
        seed: params.seed ?? 42,
        indication: params.indication || "hypertension",
        phase: params.phase || "Phase 3",
      }),
    });
    const data = await handleResponse(response);
    // Return in expected format with metadata
    return {
      data,
      metadata: {
        records: data.length,
        method: "demographics-aact",
      },
    };
  },

  async generateLabs(params: { n_subjects: number; seed?: number }): Promise<any> {
    const response = await fetch(`${DATA_GEN_SERVICE}/generate/labs`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        n_subjects: params.n_subjects,
        seed: params.seed ?? 42
      }),
    });
    const data = await handleResponse(response);
    // Backend returns array directly, wrap it in expected format
    return {
      data,
      metadata: {
        records: data.length,
        method: "labs",
      },
    };
  },

  async generateAE(params: { n_subjects: number; seed?: number }): Promise<any> {
    const response = await fetch(`${DATA_GEN_SERVICE}/generate/ae`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        n_subjects: params.n_subjects,
        seed: params.seed ?? 7
      }),
    });
    const data = await handleResponse(response);
    // Backend returns array directly, wrap it in expected format
    return {
      data,
      metadata: {
        records: data.length,
        method: "adverse-events",
      },
    };
  },

  async getRealVitalSigns(): Promise<any[]> {
    const response = await fetch(`${DATA_GEN_SERVICE}/data/real-vitals`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  async getRealDemographics(): Promise<any[]> {
    const response = await fetch(`${DATA_GEN_SERVICE}/data/real-demographics`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  async getRealAdverseEvents(): Promise<any[]> {
    const response = await fetch(`${DATA_GEN_SERVICE}/data/real-ae`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  async generateComprehensiveStudy(params: {
    n_per_arm?: number;
    target_effect?: number;
    method?: string;
    include_vitals?: boolean;
    include_demographics?: boolean;
    include_ae?: boolean;
    include_labs?: boolean;
    seed?: number;
  }): Promise<any> {
    const response = await fetch(`${DATA_GEN_SERVICE}/generate/comprehensive-study`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        n_per_arm: params.n_per_arm ?? 50,
        target_effect: params.target_effect ?? -5.0,
        method: params.method ?? "mvn",
        include_vitals: params.include_vitals ?? true,
        include_demographics: params.include_demographics ?? true,
        include_ae: params.include_ae ?? true,
        include_labs: params.include_labs ?? true,
        seed: params.seed ?? 42,
      }),
    });
    return handleResponse(response);
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

  async repairVitals(data: VitalsRecord[]): Promise<{
    repaired_records: VitalsRecord[];
    validation_after: ValidationResponse;
  }> {
    const response = await fetch(`${EDC_SERVICE}/repair`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ records: data }),
    });
    return handleResponse(response);
  },
};

// ============================================================================
// Trial Planning API
// ============================================================================

export const trialPlanningApi = {
  async createVirtualControlArm(
    request: VirtualControlArmRequest
  ): Promise<VirtualControlArmResponse> {
    const response = await fetch(`${ANALYTICS_SERVICE}/trial-planning/virtual-control-arm`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
    });
    return handleResponse(response);
  },

  async augmentControlArm(
    request: AugmentControlArmRequest
  ): Promise<AugmentControlArmResponse> {
    const response = await fetch(`${ANALYTICS_SERVICE}/trial-planning/augment-control-arm`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
    });
    return handleResponse(response);
  },

  async whatIfEnrollment(
    request: WhatIfEnrollmentRequest
  ): Promise<WhatIfEnrollmentResponse> {
    const response = await fetch(`${ANALYTICS_SERVICE}/trial-planning/what-if/enrollment`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
    });
    return handleResponse(response);
  },

  async whatIfPatientMix(
    request: WhatIfPatientMixRequest
  ): Promise<WhatIfPatientMixResponse> {
    const response = await fetch(`${ANALYTICS_SERVICE}/trial-planning/what-if/patient-mix`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
    });
    return handleResponse(response);
  },

  async assessFeasibility(
    request: FeasibilityAssessmentRequest
  ): Promise<FeasibilityAssessmentResponse> {
    const response = await fetch(`${ANALYTICS_SERVICE}/trial-planning/feasibility`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
    });
    return handleResponse(response);
  },
};

// ============================================================================
// Medical Imaging API
// ============================================================================

export const medicalImagingApi = {
  async uploadImage(
    file: File,
    subjectId: string,
    visitName?: string,
    imageType?: string
  ): Promise<any> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("subject_id", subjectId);
    if (visitName) formData.append("visit_name", visitName);
    if (imageType) formData.append("image_type", imageType);

    const token = localStorage.getItem("token");
    const headers: HeadersInit = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${EDC_SERVICE}/imaging/upload`, {
      method: "POST",
      headers,
      body: formData,
    });
    return handleResponse(response);
  },

  async getSubjectImages(subjectId: string): Promise<any[]> {
    const response = await fetch(`${EDC_SERVICE}/imaging/subject/${subjectId}`, {
      method: "GET",
      headers: getAuthHeaders(),
    });
    const result = await handleResponse(response);
    return result.images || [];
  },

  async getImageFile(imageId: number, thumbnail: boolean = false): Promise<Blob> {
    const endpoint = thumbnail ? "thumbnail" : "file";
    const response = await fetch(`${EDC_SERVICE}/imaging/${imageId}/${endpoint}`, {
      method: "GET",
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      throw new Error(`Failed to fetch image: ${response.statusText}`);
    }
    return response.blob();
  },

  async deleteImage(imageId: number): Promise<void> {
    const response = await fetch(`${EDC_SERVICE}/imaging/${imageId}`, {
      method: "DELETE",
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  async getStatus(): Promise<{ imaging_available: boolean; message?: string }> {
    const response = await fetch(`${EDC_SERVICE}/imaging/status`, {
      method: "GET",
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },
};
