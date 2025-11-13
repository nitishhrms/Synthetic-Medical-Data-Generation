// ============================================================================
// Backend API Types
// ============================================================================

// Vitals Record from Data Generation Service
export interface VitalsRecord {
  SubjectID: string;
  VisitName: "Screening" | "Day 1" | "Week 4" | "Week 12";
  TreatmentArm: "Active" | "Placebo";
  SystolicBP: number;
  DiastolicBP: number;
  HeartRate: number;
  Temperature: number;
}

// Generation Methods
export type GenerationMethod = "mvn" | "bootstrap" | "rules" | "llm";

// Generation Request
export interface GenerationRequest {
  n_per_arm?: number;
  target_effect?: number;
  seed?: number;
  jitter_frac?: number; // for bootstrap
  indication?: string; // for LLM
  api_key?: string; // for LLM
  model?: string; // for LLM
}

// Generation Response
export interface GenerationResponse {
  data: VitalsRecord[];
  metadata: {
    records: number;
    subjects: number;
    method: GenerationMethod;
    generation_time_ms: number;
    prompt_used?: string; // for LLM
  };
}

// Week-12 Statistics Request
export interface Week12StatsRequest {
  vitals_data: VitalsRecord[];
}

// Week-12 Statistics Response
export interface Week12StatsResponse {
  treatment_groups: {
    Active: {
      n: number;
      mean_systolic: number;
      std_systolic: number;
      se_systolic: number;
    };
    Placebo: {
      n: number;
      mean_systolic: number;
      std_systolic: number;
      se_systolic: number;
    };
  };
  treatment_effect: {
    difference: number;
    se_difference: number;
    t_statistic: number;
    p_value: number;
    ci_95_lower: number;
    ci_95_upper: number;
  };
  interpretation: {
    significant: boolean;
    effect_size: string;
    clinical_relevance: string;
  };
}

// Quality Assessment Response
export interface QualityAssessmentResponse {
  wasserstein_distances: {
    [key: string]: number;
  };
  correlation_preservation: number;
  rmse_by_column: {
    [key: string]: number;
  };
  knn_imputation_score: number;
  overall_quality_score: number;
  euclidean_distances: {
    mean_distance: number;
    median_distance: number;
    min_distance: number;
    max_distance: number;
    std_distance: number;
  };
  summary: string;
}

// Authentication Types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  password: string;
  email: string;
  role: "admin" | "researcher" | "viewer";
  tenant_id: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface User {
  id: string;
  username: string;
  email: string;
  role: "admin" | "researcher" | "viewer";
  tenant_id: string;
  created_at: string;
}

// Study Management Types
export interface Study {
  study_id: string;
  study_name: string;
  indication: string;
  phase: "Phase 1" | "Phase 2" | "Phase 3";
  sponsor: string;
  start_date: string;
  end_date?: string;
  status: "active" | "completed" | "suspended";
  tenant_id: string;
  created_at?: string;
}

export interface Subject {
  subject_id: string;
  study_id: string;
  site_id: string;
  treatment_arm: "Active" | "Placebo";
  enrollment_date: string;
  status: "enrolled" | "completed" | "withdrawn";
  created_at?: string;
}

// Validation Response
export interface ValidationResponse {
  valid: boolean;
  total_records: number;
  validation_results: {
    range_checks: {
      passed: number;
      failed: number;
      errors: string[];
    };
    bp_differential: {
      passed: number;
      failed: number;
      errors: string[];
    };
    completeness: {
      missing_values: number;
      completeness_rate: number;
    };
    duplicates: {
      duplicate_count: number;
    };
  };
}

// PCA Comparison Response
export interface PCAComparisonResponse {
  original_pca: Array<{ pca1: number; pca2: number }>;
  synthetic_pca: Array<{ pca1: number; pca2: number }>;
  explained_variance: number[];
  quality_score: number;
}
