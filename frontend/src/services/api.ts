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
