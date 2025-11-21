/**
 * AACT API Service
 * 
 * Provides methods to fetch AACT (Aggregate Analysis of ClinicalTrials.gov) data
 * for use in the Analytics dashboard visualizations.
 */

const API_BASE_URL = 'http://localhost:8001';

export interface AgeDistribution {
    range: string;
    active: number;
    placebo: number;
}

export interface GenderDistribution {
    gender: string;
    value: number;
    percentage: number;
}

export interface RaceDistribution {
    race: string;
    value: number;
}

export interface DemographicsResponse {
    age_distribution: AgeDistribution[];
    gender_distribution: GenderDistribution[];
    race_distribution: RaceDistribution[];
    baseline_characteristics: {
        age: Record<string, any>;
        gender: Record<string, any>;
        race: Record<string, any>;
    };
    source: string;
    indication: string;
    phase: string;
}

export interface CommonAE {
    event: string;
    active: number;
    placebo: number;
    total: number;
}

export interface SOCDistribution {
    soc: string;
    value: number;
    percentage: number;
}

export interface SeverityDistribution {
    severity: string;
    active: number;
    placebo: number;
}

export interface AdverseEventsResponse {
    common_aes: CommonAE[];
    soc_distribution: SOCDistribution[];
    severity_distribution: SeverityDistribution[];
    top_events: any[];
    source: string;
    indication: string;
    phase: string;
}

export interface LabParameter {
    parameter: string;
    active: string;
    placebo: string;
    normalRange: string;
}

export interface UrinalysisResult {
    parameter: string;
    normal: number;
    abnormal: number;
}

export interface LabsResponse {
    hematology: LabParameter[];
    chemistry: LabParameter[];
    urinalysis: UrinalysisResult[];
    vitals_baselines: Record<string, any>;
    source: string;
    indication: string;
    phase: string;
}

/**
 * Fetch demographics analytics from AACT
 */
export async function fetchDemographicsAnalytics(
    indication: string = 'hypertension',
    phase: string = 'Phase 3'
): Promise<DemographicsResponse> {
    try {
        const response = await fetch(
            `${API_BASE_URL}/aact/analytics/demographics?indication=${encodeURIComponent(indication)}&phase=${encodeURIComponent(phase)}`
        );

        if (!response.ok) {
            throw new Error(`Failed to fetch demographics: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error fetching demographics analytics:', error);
        throw error;
    }
}

/**
 * Fetch adverse events analytics from AACT
 */
export async function fetchAdverseEventsAnalytics(
    indication: string = 'hypertension',
    phase: string = 'Phase 3'
): Promise<AdverseEventsResponse> {
    try {
        const response = await fetch(
            `${API_BASE_URL}/aact/analytics/adverse_events?indication=${encodeURIComponent(indication)}&phase=${encodeURIComponent(phase)}`
        );

        if (!response.ok) {
            throw new Error(`Failed to fetch adverse events: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error fetching adverse events analytics:', error);
        throw error;
    }
}

/**
 * Fetch labs analytics from AACT
 */
export async function fetchLabsAnalytics(
    indication: string = 'hypertension',
    phase: string = 'Phase 3'
): Promise<LabsResponse> {
    try {
        const response = await fetch(
            `${API_BASE_URL}/aact/analytics/labs?indication=${encodeURIComponent(indication)}&phase=${encodeURIComponent(phase)}`
        );

        if (!response.ok) {
            throw new Error(`Failed to fetch labs: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error fetching labs analytics:', error);
        throw error;
    }
}

/**
 * Fetch all AACT analytics data
 */
export async function fetchAllAACTAnalytics(
    indication: string = 'hypertension',
    phase: string = 'Phase 3'
) {
    try {
        const [demographics, adverseEvents, labs] = await Promise.all([
            fetchDemographicsAnalytics(indication, phase),
            fetchAdverseEventsAnalytics(indication, phase),
            fetchLabsAnalytics(indication, phase)
        ]);

        return {
            demographics,
            adverseEvents,
            labs
        };
    } catch (error) {
        console.error('Error fetching all AACT analytics:', error);
        throw error;
    }
}
