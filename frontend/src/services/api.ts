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
  ComprehensiveStudyRequest,
  ComprehensiveStudyResponse,
  BenchmarkResponse,
  StressTestResponse,
  PortfolioAnalytics,
} from "@/types";

// ============================================================================
// API Configuration
// ============================================================================

const DATA_GEN_SERVICE = import.meta.env.VITE_DATA_GEN_URL || "http://localhost:8001";
const ANALYTICS_SERVICE = import.meta.env.VITE_ANALYTICS_URL || "http://localhost:8003";
const EDC_SERVICE = import.meta.env.VITE_EDC_URL || "http://localhost:8001";
const SECURITY_SERVICE = import.meta.env.VITE_SECURITY_URL || "http://localhost:8005";
const QUALITY_SERVICE = import.meta.env.VITE_QUALITY_URL || "http://localhost:8004";
const DAFT_SERVICE = import.meta.env.VITE_DAFT_URL || "http://localhost:8007";
const AI_MONITOR_SERVICE = import.meta.env.VITE_AI_MONITOR_URL || "http://localhost:8008";

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
    let errorMessage = error.detail;
    if (Array.isArray(error.detail)) {
      errorMessage = error.detail.map((e: any) => `${e.loc.join(".")}: ${e.msg}`).join("\n");
    }
    throw new Error(errorMessage || `HTTP ${response.status}: ${response.statusText}`);
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

  async generateDiffusion(params: GenerationRequest & { n_steps?: number }): Promise<GenerationResponse> {
    const response = await fetch(`${DATA_GEN_SERVICE}/generate/diffusion`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        n_per_arm: params.n_per_arm ?? 50,
        target_effect: params.target_effect ?? -5.0,
        seed: params.seed ?? 42,
        n_steps: params.n_steps ?? 50,
      }),
    });
    const data = await handleResponse<VitalsRecord[]>(response);
    const uniqueSubjects = new Set(data.map(r => r.SubjectID)).size;
    return {
      data,
      metadata: {
        records: data.length,
        subjects: uniqueSubjects,
        method: "diffusion",
        generation_time_ms: 0,
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

  async generateLabs(params: { n_subjects: number; seed?: number; indication?: string; phase?: string }): Promise<any> {
    // Use AACT-enhanced endpoint by default for maximum realism
    const response = await fetch(`${DATA_GEN_SERVICE}/generate/labs-aact`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        n_subjects: params.n_subjects,
        seed: params.seed ?? 42,
        indication: params.indication || "hypertension",
        phase: params.phase || "Phase 3",
        use_duration: true,
      }),
    });
    const data = await handleResponse(response);
    // Backend returns array directly, wrap it in expected format
    return {
      data,
      metadata: {
        records: data.length,
        method: "labs-aact",
      },
    };
  },

  async generateAE(params: { n_subjects: number; seed?: number; indication?: string; phase?: string }): Promise<any> {
    // Use AACT-enhanced endpoint by default for maximum realism
    const response = await fetch(`${DATA_GEN_SERVICE}/generate/ae-aact`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        n_subjects: params.n_subjects,
        seed: params.seed ?? 7,
        indication: params.indication || "cancer",
        phase: params.phase || "Phase 2",
      }),
    });
    const data = await handleResponse(response);
    // Backend returns array directly, wrap it in expected format
    return {
      data,
      metadata: {
        records: data.length,
        method: "ae-aact",
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

  async generateComprehensiveStudy(params: ComprehensiveStudyRequest): Promise<ComprehensiveStudyResponse> {
    const response = await fetch(`${DATA_GEN_SERVICE}/generate/comprehensive-study`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        indication: params.indication || "hypertension",
        phase: params.phase || "Phase 3",
        n_per_arm: params.n_per_arm ?? 50,
        target_effect: params.target_effect ?? -5.0,
        seed: params.seed ?? 42,
        method: params.method ?? "mvn",
        use_duration: params.use_duration ?? true,
        dropout_rate: params.dropout_rate,
        missing_data_rate: params.missing_data_rate,
        site_heterogeneity: params.site_heterogeneity,
      }),
    });
    console.log("Generating Comprehensive Study with payload:", JSON.stringify({
      indication: params.indication || "hypertension",
      phase: params.phase || "Phase 3",
      n_per_arm: params.n_per_arm ?? 50,
      target_effect: params.target_effect ?? -5.0,
      seed: params.seed ?? 42,
      method: params.method ?? "mvn",
      use_duration: params.use_duration ?? true,
      dropout_rate: params.dropout_rate,
      missing_data_rate: params.missing_data_rate,
      site_heterogeneity: params.site_heterogeneity,
    }, null, 2));
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

  // ============================================================================
  // Scalability Features
  // ============================================================================

  async benchmarkPerformance(params: {
    n_per_arm?: number;
    methods?: string;
    indication?: string;
    phase?: string;
  }): Promise<BenchmarkResponse> {
    const queryParams = new URLSearchParams({
      n_per_arm: (params.n_per_arm ?? 50).toString(),
      methods: params.methods || "mvn,bootstrap,rules",
      indication: params.indication || "hypertension",
      phase: params.phase || "Phase 3",
    });

    const response = await fetch(`${DATA_GEN_SERVICE}/benchmark/performance?${queryParams}`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  async stressTestConcurrent(params: {
    n_concurrent_requests?: number;
    n_per_arm?: number;
    indication?: string;
    phase?: string;
  }): Promise<StressTestResponse> {
    const queryParams = new URLSearchParams({
      n_concurrent_requests: (params.n_concurrent_requests ?? 10).toString(),
      n_per_arm: (params.n_per_arm ?? 50).toString(),
      indication: params.indication || "hypertension",
      phase: params.phase || "Phase 3",
    });

    const response = await fetch(`${DATA_GEN_SERVICE}/stress-test/concurrent?${queryParams}`, {
      method: "POST",
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  async getPortfolioAnalytics(): Promise<PortfolioAnalytics> {
    const response = await fetch(`${DATA_GEN_SERVICE}/analytics/portfolio`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  // ============================================================================
  // Data Persistence
  // ============================================================================

  async saveGeneratedData(datasetName: string, datasetType: string, data: any[], metadata?: any): Promise<any> {
    const response = await fetch(`${DATA_GEN_SERVICE}/data/save`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        dataset_name: datasetName,
        dataset_type: datasetType,
        data: data,
        metadata: metadata
      }),
    });
    return handleResponse(response);
  },

  async loadLatestData(datasetType: string): Promise<any> {
    const response = await fetch(`${DATA_GEN_SERVICE}/data/load/${datasetType}`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  async loadDataById(datasetId: number): Promise<any> {
    const response = await fetch(`${DATA_GEN_SERVICE}/data/load/id/${datasetId}`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  async listDatasets(datasetType?: string, limit: number = 50, offset: number = 0): Promise<any> {
    const params = new URLSearchParams({ limit: limit.toString(), offset: offset.toString() });
    if (datasetType) {
      params.append('dataset_type', datasetType);
    }
    const response = await fetch(`${DATA_GEN_SERVICE}/data/list?${params}`, {
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

  // ============================================================================
  // Demographics Analytics (Phase 1 - 5 endpoints)
  // ============================================================================

  async getBaselineCharacteristics(demographicsData: any[]): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/stats/demographics/baseline`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ demographics_data: demographicsData }),
    });
    return handleResponse(response);
  },

  async getDemographicSummary(demographicsData: any[]): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/stats/demographics/summary`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ demographics_data: demographicsData }),
    });
    return handleResponse(response);
  },

  async assessDemographicBalance(demographicsData: any[]): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/stats/demographics/balance`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ demographics_data: demographicsData }),
    });
    return handleResponse(response);
  },

  async compareDemographicsQuality(realData: any[], syntheticData: any[]): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/quality/demographics/compare`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        real_demographics: realData,
        synthetic_demographics: syntheticData,
      }),
    });
    return handleResponse(response);
  },

  async exportDemographicsSDTM(demographicsData: any[]): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/sdtm/demographics/export`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ demographics_data: demographicsData }),
    });
    return handleResponse(response);
  },

  // ============================================================================
  // Labs Analytics (Phase 2 - 7 endpoints)
  // ============================================================================

  async getLabsSummary(labsData: any[]): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/stats/labs/summary`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ labs_data: labsData }),
    });
    return handleResponse(response);
  },

  async detectAbnormalLabs(labsData: any[]): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/stats/labs/abnormal`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ labs_data: labsData }),
    });
    return handleResponse(response);
  },

  async generateShiftTables(labsData: any[]): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/stats/labs/shift-tables`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ labs_data: labsData }),
    });
    return handleResponse(response);
  },

  async compareLabsQuality(realLabs: any[], syntheticLabs: any[]): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/quality/labs/compare`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        real_labs: realLabs,
        synthetic_labs: syntheticLabs,
      }),
    });
    return handleResponse(response);
  },

  async detectSafetySignals(labsData: any[]): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/stats/labs/safety-signals`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ labs_data: labsData }),
    });
    return handleResponse(response);
  },

  async analyzeLabsLongitudinal(labsData: any[]): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/stats/labs/longitudinal`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ labs_data: labsData }),
    });
    return handleResponse(response);
  },

  async exportLabsSDTM(labsData: any[]): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/sdtm/labs/export`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ labs_data: labsData }),
    });
    return handleResponse(response);
  },

  // ============================================================================
  // AE (Adverse Events) Analytics (Phase 3 - 5 endpoints)
  // ============================================================================

  async getAESummary(aeData: any[], treatmentStartDate?: string): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/stats/ae/summary`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        ae_data: aeData,
        treatment_start_date: treatmentStartDate,
      }),
    });
    return handleResponse(response);
  },

  async analyzeTreatmentEmergentAEs(aeData: any[], treatmentStartDate?: string): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/stats/ae/treatment-emergent`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        ae_data: aeData,
        treatment_start_date: treatmentStartDate,
      }),
    });
    return handleResponse(response);
  },

  async analyzeSOCDistribution(aeData: any[]): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/stats/ae/soc-analysis`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ ae_data: aeData }),
    });
    return handleResponse(response);
  },

  async compareAEQuality(realAE: any[], syntheticAE: any[]): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/quality/ae/compare`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        real_ae: realAE,
        synthetic_ae: syntheticAE,
      }),
    });
    return handleResponse(response);
  },

  async exportAESDTM(aeData: any[]): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/sdtm/ae/export`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ ae_data: aeData }),
    });
    return handleResponse(response);
  },

  // ============================================================================
  // AACT Integration (Phase 4 - 3 endpoints)
  // ============================================================================

  async compareStudyToAACT(params: {
    n_subjects: number;
    indication: string;
    phase: string;
    treatment_effect: number;
    vitals_data?: VitalsRecord[];
  }): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/aact/compare-study`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(params),
    });
    return handleResponse(response);
  },

  async benchmarkDemographics(demographicsData: any[], indication: string, phase: string): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/aact/benchmark-demographics`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        demographics_data: demographicsData,
        indication,
        phase,
      }),
    });
    return handleResponse(response);
  },

  async benchmarkAdverseEvents(aeData: any[], indication: string, phase: string): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/aact/benchmark-ae`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        ae_data: aeData,
        indication,
        phase,
      }),
    });
    return handleResponse(response);
  },

  // ============================================================================
  // Comprehensive Study Analytics (Phase 5 - 3 endpoints)
  // ============================================================================

  async getComprehensiveSummary(params: {
    demographics_data?: any[];
    vitals_data?: any[];
    labs_data?: any[];
    ae_data?: any[];
    indication?: string;
    phase?: string;
  }): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/study/comprehensive-summary`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(params),
    });
    return handleResponse(response);
  },

  async getCrossDomainCorrelations(params: {
    demographics_data?: any[];
    vitals_data?: any[];
    labs_data?: any[];
    ae_data?: any[];
  }): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/study/cross-domain-correlations`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(params),
    });
    return handleResponse(response);
  },

  async getTrialDashboard(params: {
    demographics_data?: any[];
    vitals_data?: any[];
    labs_data?: any[];
    ae_data?: any[];
    indication?: string;
    phase?: string;
  }): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/study/trial-dashboard`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(params),
    });
    return handleResponse(response);
  },

  // ============================================================================
  // Benchmarking & Extensions (Phase 6 - 3 endpoints)
  // ============================================================================

  async compareMethodPerformance(methodsData: Record<string, any>): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/benchmark/performance`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ methods_data: methodsData }),
    });
    return handleResponse(response);
  },

  async aggregateQualityScores(params: {
    demographics_quality?: number;
    vitals_quality?: number;
    labs_quality?: number;
    ae_quality?: number;
    aact_similarity?: number;
  }): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/benchmark/quality-scores`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(params),
    });
    return handleResponse(response);
  },

  async getRecommendations(params: {
    current_quality: number;
    aact_similarity?: number;
    generation_method?: string;
    n_subjects?: number;
    indication?: string;
    phase?: string;
  }): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/study/recommendations`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(params),
    });
    return handleResponse(response);
  },

  // ============================================================================
  // Survival Analysis (Tier 1 - 4 endpoints)
  // ============================================================================

  async comprehensiveSurvivalAnalysis(params: {
    demographics_data: any[];
    indication?: string;
    median_survival_active?: number;
    median_survival_placebo?: number;
    seed?: number;
  }): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/survival/comprehensive`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(params),
    });
    return handleResponse(response);
  },

  async calculateKaplanMeier(survivalData: any[], treatmentArm?: string): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/survival/kaplan-meier`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        survival_data: survivalData,
        treatment_arm: treatmentArm,
      }),
    });
    return handleResponse(response);
  },

  async performLogRankTest(survivalData: any[], arm1?: string, arm2?: string): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/survival/log-rank-test`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        survival_data: survivalData,
        arm1,
        arm2,
      }),
    });
    return handleResponse(response);
  },

  async calculateHazardRatio(survivalData: any[], referenceArm?: string, treatmentArm?: string): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/survival/hazard-ratio`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        survival_data: survivalData,
        reference_arm: referenceArm,
        treatment_arm: treatmentArm,
      }),
    });
    return handleResponse(response);
  },

  // ============================================================================
  // ADaM Dataset Generation (Tier 1 - 2 endpoints)
  // ============================================================================

  async generateAllAdamDatasets(params: {
    demographics_data: any[];
    vitals_data?: any[];
    labs_data?: any[];
    ae_data?: any[];
    survival_data?: any[];
    study_id?: string;
  }): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/adam/generate-all`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(params),
    });
    return handleResponse(response);
  },

  async generateADSL(params: {
    demographics_data: any[];
    vitals_data?: any[];
    ae_data?: any[];
    study_id?: string;
  }): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/adam/adsl`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(params),
    });
    return handleResponse(response);
  },

  // ============================================================================
  // TLF Automation (Tier 1 - 4 endpoints)
  // ============================================================================

  async generateAllTLFTables(params: {
    demographics_data: any[];
    ae_data?: any[];
    vitals_data?: any[];
    survival_data?: any[];
  }): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/tlf/generate-all`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(params),
    });
    return handleResponse(response);
  },

  async generateTable1Demographics(demographicsData: any[], includeStats?: boolean): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/tlf/table1-demographics`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        demographics_data: demographicsData,
        include_stats: includeStats,
      }),
    });
    return handleResponse(response);
  },

  async generateTable2AdverseEvents(aeData: any[], bySOC?: boolean, minIncidence?: number): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/tlf/table2-adverse-events`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        ae_data: aeData,
        by_soc: bySOC,
        min_incidence: minIncidence,
      }),
    });
    return handleResponse(response);
  },

  async generateTable3Efficacy(params: {
    vitals_data?: any[];
    survival_data?: any[];
    endpoint_type?: string;
  }): Promise<any> {
    const response = await fetch(`${ANALYTICS_SERVICE}/tlf/table3-efficacy`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(params),
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

  async getStudySubjects(studyId: string): Promise<{ subjects: any[] }> {
    const response = await fetch(`${EDC_SERVICE}/studies/${studyId}/subjects`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  async listQueries(params?: { status?: string; severity?: string; subject_id?: string }): Promise<any[]> {
    const queryParams = new URLSearchParams();
    if (params?.status && params.status !== 'all') queryParams.append('status_filter', params.status);
    if (params?.severity && params.severity !== 'all') queryParams.append('severity', params.severity);
    if (params?.subject_id) queryParams.append('subject_id', params.subject_id);

    const response = await fetch(`${EDC_SERVICE}/queries?${queryParams}`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  async respondToQuery(queryId: number, responseText: string): Promise<any> {
    // Note: Backend endpoint for respond might need to be created or verified
    // Assuming PUT /queries/{id}/respond based on frontend code
    const response = await fetch(`${EDC_SERVICE}/queries/${queryId}/respond`, {
      method: "PUT",
      headers: getAuthHeaders(),
      body: JSON.stringify({ response_text: responseText }),
    });
    return handleResponse(response);
  },

  async closeQuery(queryId: number, notes: string): Promise<any> {
    // Note: Backend endpoint for close might need to be created or verified
    // Assuming PUT /queries/{id}/close based on frontend code
    const response = await fetch(`${EDC_SERVICE}/queries/${queryId}/close`, {
      method: "PUT",
      headers: getAuthHeaders(),
      body: JSON.stringify({ resolution_notes: notes }),
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

  async assessSYNDATA(realData: any[], syntheticData: any[]): Promise<SYNDATAMetricsResponse> {
    const response = await fetch(`${QUALITY_SERVICE}/syndata/assess`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        real_data: realData,
        synthetic_data: syntheticData
      }),
    });
    return handleResponse(response);
  },

  async generateQualityReport(method: string, realData: any[], syntheticData: any[]): Promise<{ report: string }> {
    const response = await fetch(`${QUALITY_SERVICE}/report/generate`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        generation_method: method,
        real_data: realData,
        synthetic_data: syntheticData
      }),
    });
    return handleResponse(response);
  },

  async assessPrivacy(
    realData: any[],
    syntheticData: any[],
    quasiIdentifiers?: string[],
    sensitiveAttributes?: string[]
  ): Promise<PrivacyAssessmentResponse> {
    const response = await fetch(`${QUALITY_SERVICE}/privacy/assess`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        real_data: realData,
        synthetic_data: syntheticData,
        quasi_identifiers: quasiIdentifiers,
        sensitive_attributes: sensitiveAttributes
      }),
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

// ============================================================================
// AI Monitor API
// ============================================================================

export const aiMonitorApi = {
  async reviewSubject(studyId: string, subjectId: string): Promise<any> {
    const response = await fetch(`${AI_MONITOR_SERVICE}/review/subject`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ study_id: studyId, subject_id: subjectId }),
    });
    return handleResponse(response);
  },

  async reviewStudy(studyId: string, maxSubjects?: number): Promise<any> {
    const response = await fetch(`${AI_MONITOR_SERVICE}/review/study`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ study_id: studyId, max_subjects: maxSubjects || 10 }),
    });
    return handleResponse(response);
  },

  async reviewStudyAndPostQueries(studyId: string, maxSubjects?: number): Promise<any> {
    const response = await fetch(`${AI_MONITOR_SERVICE}/review/study/post-queries`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ study_id: studyId, max_subjects: maxSubjects || 10 }),
    });
    return handleResponse(response);
  },

  async healthCheck(): Promise<any> {
    const response = await fetch(`${AI_MONITOR_SERVICE}/health`, {
      method: "GET",
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },
};

