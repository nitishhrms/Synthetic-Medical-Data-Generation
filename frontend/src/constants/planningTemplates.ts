/**
 * Trial Planning Templates
 *
 * This file contains pre-configured trial planning templates for common study phases.
 * Each template includes typical parameters used in clinical trial design, based on
 * industry standards and regulatory guidelines.
 *
 * Templates help users quickly set up planning scenarios without manually entering
 * all parameters, reducing errors and ensuring consistency with best practices.
 *
 * Usage:
 * - User selects a template from dropdown in Planning screen
 * - Template parameters are loaded into the form
 * - User can review and adjust parameters before running assessments
 *
 * References:
 * - FDA Guidance: Statistical Considerations in Clinical Trials
 * - ICH E9: Statistical Principles for Clinical Trials
 * - ICH E6(R2): Good Clinical Practice
 */

export interface PlanningTemplate {
  id: string;
  name: string;
  description: string;
  phase: string;
  // Feasibility parameters
  target_effect: number;      // mmHg for hypertension trials
  expected_std: number;        // Standard deviation
  alpha: number;               // Type I error rate (significance level)
  power: number;               // Statistical power (1 - Type II error)
  allocation_ratio: number;    // Active:Control ratio (e.g., 1.0 = 1:1)
  dropout_rate: number;        // Expected dropout rate
  // Enrollment what-if scenarios
  enrollment_scenarios: number[];
  // Patient mix what-if scenarios
  baseline_sbp_scenarios: number[];
  // Metadata
  use_case: string;
  typical_duration: string;
  regulatory_considerations: string[];
}

/**
 * Phase 1 Safety Study Template
 *
 * Focus: Safety, tolerability, pharmacokinetics (PK), pharmacodynamics (PD)
 * Typical N: 20-80 subjects (often healthy volunteers)
 * Duration: 6-12 months
 * Primary Endpoint: Safety/tolerability
 * Secondary: PK/PD parameters
 *
 * Characteristics:
 * - Small sample size (safety focus, not efficacy)
 * - High dropout rate due to healthy volunteers
 * - Modest effect size expectations
 * - Higher alpha to be more conservative on safety
 */
export const PHASE_1_TEMPLATE: PlanningTemplate = {
  id: "phase-1-safety",
  name: "Phase 1: Safety Study",
  description: "Small safety and tolerability study in healthy volunteers or patients",
  phase: "Phase 1",
  // Feasibility parameters
  target_effect: -3.0,           // Modest effect expected
  expected_std: 12.0,             // Higher variability in small samples
  alpha: 0.10,                    // Less stringent for safety studies
  power: 0.70,                    // Lower power acceptable for Phase 1
  allocation_ratio: 1.0,          // 1:1 randomization typical
  dropout_rate: 0.25,             // 25% dropout (healthy volunteers can drop easily)
  // Enrollment scenarios for what-if analysis
  enrollment_scenarios: [10, 20, 30, 40, 50],
  // Patient mix scenarios (baseline SBP)
  baseline_sbp_scenarios: [120, 130, 140, 150],
  // Metadata
  use_case: "Evaluate safety, tolerability, and preliminary efficacy signal in a small population",
  typical_duration: "6-12 months",
  regulatory_considerations: [
    "FDA: Focus on dose-finding and safety endpoints",
    "EMA: Emphasis on first-in-human safety data",
    "ICH E1: Limited exposure adequate for Phase 1",
    "21 CFR 312.21: IND safety requirements"
  ]
};

/**
 * Phase 2 Efficacy Study Template
 *
 * Focus: Preliminary efficacy, dose-ranging, endpoint validation
 * Typical N: 100-300 patients
 * Duration: 1-2 years
 * Primary Endpoint: Efficacy (e.g., SBP reduction)
 * Secondary: Safety, biomarkers
 *
 * Characteristics:
 * - Moderate sample size (proof-of-concept)
 * - Standard alpha and power
 * - May use dose-ranging designs
 * - Provides basis for Phase 3 design
 */
export const PHASE_2_TEMPLATE: PlanningTemplate = {
  id: "phase-2-efficacy",
  name: "Phase 2: Dose-Ranging Efficacy",
  description: "Moderate-sized study to establish proof-of-concept and optimal dose",
  phase: "Phase 2",
  // Feasibility parameters
  target_effect: -5.0,            // Expected clinically meaningful effect
  expected_std: 10.0,             // Moderate variability
  alpha: 0.05,                    // Standard significance level
  power: 0.80,                    // Standard power (80%)
  allocation_ratio: 1.0,          // 1:1 randomization
  dropout_rate: 0.20,             // 20% dropout typical
  // Enrollment scenarios
  enrollment_scenarios: [50, 75, 100, 150, 200, 250],
  // Patient mix scenarios
  baseline_sbp_scenarios: [130, 140, 150, 160, 170],
  // Metadata
  use_case: "Establish proof-of-concept, determine optimal dose, and validate endpoints for Phase 3",
  typical_duration: "1-2 years",
  regulatory_considerations: [
    "FDA: Adequate and well-controlled studies for dose selection",
    "ICH E4: Dose-response information should inform Phase 3",
    "ICH E10: Clinical trial design considerations for dose-finding",
    "EMA: Adaptive designs increasingly accepted for Phase 2"
  ]
};

/**
 * Phase 3 Pivotal Trial Template
 *
 * Focus: Confirmatory efficacy, safety in large population
 * Typical N: 300-3000+ patients (depends on indication)
 * Duration: 2-4 years
 * Primary Endpoint: Pre-specified efficacy endpoint
 * Secondary: Additional efficacy, safety, quality of life
 *
 * Characteristics:
 * - Large sample size (definitive efficacy demonstration)
 * - Stringent alpha (often with multiplicity adjustments)
 * - High power required (typically 90%)
 * - Lower dropout expectations (better study conduct)
 * - Regulatory scrutiny - must meet FDA/EMA standards
 */
export const PHASE_3_TEMPLATE: PlanningTemplate = {
  id: "phase-3-pivotal",
  name: "Phase 3: Pivotal Confirmatory Trial",
  description: "Large confirmatory trial for regulatory approval",
  phase: "Phase 3",
  // Feasibility parameters
  target_effect: -6.0,            // Clinically and statistically significant effect
  expected_std: 10.0,             // Well-characterized variability from Phase 2
  alpha: 0.05,                    // Standard significance (may adjust for multiplicity)
  power: 0.90,                    // 90% power typical for pivotal trials
  allocation_ratio: 1.0,          // 1:1 standard (sometimes 2:1 for safety)
  dropout_rate: 0.15,             // 15% dropout (better retention in Phase 3)
  // Enrollment scenarios
  enrollment_scenarios: [100, 200, 300, 400, 500, 750, 1000],
  // Patient mix scenarios (broader population)
  baseline_sbp_scenarios: [130, 140, 150, 160, 170, 180],
  // Metadata
  use_case: "Provide definitive evidence of efficacy and safety for regulatory approval (NDA/BLA/MAA)",
  typical_duration: "2-4 years",
  regulatory_considerations: [
    "FDA: Must demonstrate substantial evidence of effectiveness (21 CFR 314.126)",
    "EMA: Two adequate and well-controlled studies typically required",
    "ICH E9: Pre-specified primary endpoint, analysis plan, and sample size",
    "FDA: Type I error control for multiple endpoints/interim analyses required",
    "21 CFR 312.85: Pre-NDA meeting strongly recommended",
    "ICH E6(R2): Risk-based monitoring and quality management essential"
  ]
};

/**
 * All Available Templates
 *
 * Export all templates as an array for easy iteration in UI components.
 * Templates are ordered by phase (1 → 2 → 3) to match typical development progression.
 */
export const PLANNING_TEMPLATES: PlanningTemplate[] = [
  PHASE_1_TEMPLATE,
  PHASE_2_TEMPLATE,
  PHASE_3_TEMPLATE
];

/**
 * Get Template by ID
 *
 * Helper function to retrieve a specific template by its unique identifier.
 * Returns undefined if template ID is not found.
 *
 * @param id - The template ID (e.g., "phase-1-safety")
 * @returns The matching template or undefined
 */
export function getTemplateById(id: string): PlanningTemplate | undefined {
  return PLANNING_TEMPLATES.find(t => t.id === id);
}
