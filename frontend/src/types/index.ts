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
export type GenerationMethod = "mvn" | "bootstrap" | "rules" | "llm" | "bayesian" | "mice";

// Generation Request
export interface GenerationRequest {
  n_per_arm?: number;
  target_effect?: number;
  seed?: number;
  jitter_frac?: number; // for bootstrap
  indication?: string; // for LLM
  api_key?: string; // for LLM
  model?: string; // for LLM
  learn_structure?: boolean; // for bayesian
  missing_rate?: number; // for MICE
  estimator?: string; // for MICE - "bayesian_ridge" or "random_forest"
  n_imputations?: number; // for MICE
}

// Generation Response
export interface GenerationResponse {
  data: VitalsRecord[];
  metadata: {
    records: number;
    subjects?: number; // Optional - calculated if not provided
    method: GenerationMethod;
    generation_time_ms?: number; // Optional - not always available
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
  user_id: string;
  roles: string[];
}

export interface User {
  user_id: string;
  username: string;
  email?: string;  // Optional - may not be in login response
  role: "admin" | "researcher" | "viewer";
  tenant_id: string;
  created_at?: string;  // Optional - may not be in login response
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
  total_records: number;
  total_checks: number;
  violations: Array<{
    record: string;
    rule: string;
    severity: string;
    message: string;
  }>;
  quality_score: number;
  passed: boolean;
}

// PCA Comparison Response
export interface PCAComparisonResponse {
  original_pca: Array<{ pca1: number; pca2: number }>;
  synthetic_pca: Array<{ pca1: number; pca2: number }>;
  explained_variance: number[];
  quality_score: number;
}

// ============================================================================
// SYNDATA Quality Metrics Types
// ============================================================================

export interface SYNDATAMetricsResponse {
  syndata_metrics: {
    support_coverage: {
      overall_score: number;
      by_variable: { [key: string]: number };
    };
    cross_classification: {
      utility_score: number;
      joint_distribution_similarity: number;
    };
    ci_coverage: {
      overall_coverage: number;
      by_variable: { [key: string]: number };
      meets_cart_standard: boolean; // 88-98%
      interpretation: string;
    };
    membership_disclosure: {
      disclosure_risk: number;
      classifier_accuracy: number;
      safe: boolean;
    };
    attribute_disclosure: {
      disclosure_risk: number;
      prediction_accuracy: number;
      safe: boolean;
    };
    overall_syndata_score: number;
    grade: "A" | "B" | "C" | "D" | "F";
  };
  timestamp: string;
  service: string;
}

export interface QualityReportResponse {
  report: string; // Markdown formatted report
  method: GenerationMethod;
  timestamp: string;
  service: string;
}

// ============================================================================
// Trial Planning Types
// ============================================================================

export interface VirtualControlArmRequest {
  historical_data: VitalsRecord[];
  n_control: number;
  target_effect: number;
  baseline_mean_sbp: number;
  baseline_std_sbp: number;
  seed?: number;
}

export interface VirtualControlArmResponse {
  virtual_control_data: VitalsRecord[];
  summary: {
    virtual_control: {
      mean_sbp: number;
      std_sbp: number;
    };
  };
  quality_metrics: {
    similarity_score: number;
    wasserstein_distance: number;
    correlation_preservation: number;
  };
  use_case: string;
  timestamp?: string;
}

export interface AugmentControlArmRequest {
  real_control_data: VitalsRecord[];
  n_synthetic: number;
  target_effect: number;
  seed?: number;
}

export interface AugmentControlArmResponse {
  augmented_data: VitalsRecord[];
  summary: {
    n_real: number;
    n_synthetic: number;
    n_combined: number;
    real_only: {
      mean_sbp: number;
      std_sbp: number;
    };
    augmented: {
      mean_sbp: number;
      std_sbp: number;
    };
  };
  quality_metrics: {
    similarity_score: number;
    wasserstein_distance: number;
  };
  timestamp?: string;
}

export interface WhatIfEnrollmentRequest {
  baseline_data: VitalsRecord[];
  enrollment_sizes?: number[];
  target_effect?: number;
  n_simulations?: number;
  seed?: number;
}

export interface WhatIfEnrollmentResponse {
  scenarios: Array<{
    n_per_arm: number;
    power: number;
    significant: boolean;
    p_value: number;
    effect: number;
  }>;
  recommendation: string;
  timestamp?: string;
}

export interface WhatIfPatientMixRequest {
  baseline_data: VitalsRecord[];
  severity_shifts?: number[];
  n_per_arm?: number;
  target_effect?: number;
  seed?: number;
}

export interface WhatIfPatientMixResponse {
  scenarios: Array<{
    baseline_sbp: number;
    population_type: string;
    effect: number;
    significant: boolean;
    p_value: number;
  }>;
  recommendation: string;
  timestamp?: string;
}

export interface FeasibilityAssessmentRequest {
  baseline_data: VitalsRecord[];
  target_effect?: number;
  power?: number;
  dropout_rate?: number;
  alpha?: number;
}

export interface FeasibilityAssessmentResponse {
  required_n_per_arm: number;
  total_n: number;
  effect_size_cohens_d: number;
  feasibility: string;
  interpretation: string;
  assumptions: string[];
  recommendation: string;
  timestamp?: string;
}

// ============================================================================
// Privacy Assessment Types
// ============================================================================

export interface PrivacyAssessmentRequest {
  real_data: VitalsRecord[];
  synthetic_data: VitalsRecord[];
  quasi_identifiers?: string[];
  sensitive_attributes?: string[];
}

export interface PrivacyAssessmentResponse {
  dataset_info: {
    real_records: number;
    synthetic_records: number;
    real_columns: string[];
    synthetic_columns: string[];
  };
  k_anonymity: {
    k: number;
    mean_group_size: number;
    median_group_size: number;
    total_equivalence_classes: number;
    risky_records: number;
    risky_percentage: number;
    safe: boolean;
    recommendation: string;
    quasi_identifiers_used: string[];
  };
  l_diversity: {
    l: number;
    mean_diversity: number;
    safe: boolean;
    recommendation: string;
    quasi_identifiers_used: string[];
    sensitive_attributes_checked: string[];
  };
  reidentification: {
    singling_out?: {
      attack_rate: number;
      baseline_rate: number;
      risk: number;
      safe: boolean;
    };
    linkability?: {
      attack_rate: number;
      baseline_rate: number;
      risk: number;
      safe: boolean;
    };
    inference?: {
      attack_rate: number;
      baseline_rate: number;
      risk: number;
      safe: boolean;
      secret_column: string;
    };
    overall?: {
      max_risk: number;
      mean_risk: number;
      risk_level: string;
      safe_for_release: boolean;
    };
  };
  differential_privacy: {
    epsilon: number;
    delta: number;
    n_queries: number;
    total_epsilon: number;
    privacy_level: string;
    budget_remaining: number;
    recommendation: string;
  };
  overall_assessment: {
    k_anonymity_safe: boolean;
    l_diversity_safe: boolean;
    reidentification_safe: boolean;
    safe_for_release: boolean;
    recommendation: string;
  };
}

// ============================================================================
// Demographics Types
// ============================================================================

export interface DemographicRecord {
  SubjectID: string;
  Age: number;
  Gender: "Male" | "Female";
  Race: "White" | "Black" | "Asian" | "Other";
  Ethnicity: "Hispanic" | "Non-Hispanic";
  Height: number; // cm
  Weight: number; // kg
  BMI: number;
  SmokingStatus: "Never" | "Former" | "Current";
}

export interface GenerationParamsWithDemographics {
  n_per_arm?: number;
  target_effect?: number;
  seed?: number;
  include_demographics?: boolean;
  demographic_stratification?: {
    oversample_minority?: boolean;
    target_gender_ratio?: number; // 0.5 = 50/50
    target_age_range?: [number, number];
    target_race_distribution?: {
      White?: number;
      Black?: number;
      Asian?: number;
      Other?: number;
    };
  };
}

// ============================================================================
// Scalability Features Types
// ============================================================================

export interface ComprehensiveStudyRequest {
  indication?: string;
  phase?: string;
  n_per_arm?: number;
  target_effect?: number;
  seed?: number;
  method?: "mvn" | "bootstrap" | "rules";
  use_duration?: boolean;
}

export interface ComprehensiveStudyResponse {
  vitals: any[];
  demographics: any[];
  labs: any[];
  adverse_events: any[];
  metadata: {
    indication: string;
    phase: string;
    n_subjects: number;
    total_records: number;
    generation_time_ms: number;
    aact_enhanced: boolean;
  };
}

export interface BenchmarkResult {
  avg_time_ms: number;
  records_per_second: number;
  records_generated: number;
}

export interface BenchmarkResponse {
  benchmark_results: {
    [method: string]: BenchmarkResult;
  };
  fastest_method: string;
  ranking: Array<{
    method: string;
    avg_time_ms: number;
  }>;
}

export interface StressTestResponse {
  stress_test_results: {
    total_requests: number;
    successful_requests: number;
    failed_requests: number;
    total_time_seconds: number;
    aggregate_throughput_records_per_second: number;
  };
  pass_criteria: {
    target_time_seconds: number;
    achieved_time: number;
    passed: boolean;
  };
}

export interface PortfolioAnalytics {
  portfolio_summary: {
    total_studies: number;
    total_subjects: number;
    studies_by_indication: { [indication: string]: number };
    studies_by_phase: { [phase: string]: number };
    average_generation_time_ms: number;
  };
  quality_metrics: {
    average_quality_score: number;
    studies_meeting_quality_threshold: number;
  };
  resource_utilization: {
    cache_hit_rate: number;
    aact_lookup_rate: number;
  };
  note?: string;
}
