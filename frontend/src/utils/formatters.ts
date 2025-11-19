/**
 * Utility functions for formatting and safely displaying metrics
 * Handles NaN, Infinity, and undefined values gracefully
 */

/**
 * Safely format a number as a percentage, handling NaN and Infinity
 * @param value - Numeric value to format (0-1 scale)
 * @param decimals - Number of decimal places (default: 1)
 * @param defaultValue - Value to return if NaN/Infinity (default: "--")
 * @returns Formatted percentage string
 */
export function safePercent(
  value: number | undefined | null,
  decimals: number = 1,
  defaultValue: string = "--"
): string {
  if (value == null || !isFinite(value) || isNaN(value)) {
    return defaultValue;
  }
  return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * Safely format a number, handling NaN and Infinity
 * @param value - Numeric value to format
 * @param decimals - Number of decimal places (default: 2)
 * @param defaultValue - Value to return if NaN/Infinity (default: "--")
 * @returns Formatted number string
 */
export function safeNumber(
  value: number | undefined | null,
  decimals: number = 2,
  defaultValue: string = "--"
): string {
  if (value == null || !isFinite(value) || isNaN(value)) {
    return defaultValue;
  }
  return value.toFixed(decimals);
}

/**
 * Safely divide two numbers, handling division by zero and invalid values
 * @param numerator - Top number
 * @param denominator - Bottom number
 * @param defaultValue - Value to return if invalid (default: 0)
 * @returns Result of division or default value
 */
export function safeDivide(
  numerator: number | undefined | null,
  denominator: number | undefined | null,
  defaultValue: number = 0
): number {
  if (
    numerator == null ||
    denominator == null ||
    !isFinite(numerator) ||
    !isFinite(denominator) ||
    isNaN(numerator) ||
    isNaN(denominator) ||
    denominator === 0
  ) {
    return defaultValue;
  }
  const result = numerator / denominator;
  return isFinite(result) && !isNaN(result) ? result : defaultValue;
}

/**
 * Check if a value is valid (not NaN, not Infinity, not null/undefined)
 * @param value - Value to check
 * @returns true if valid number
 */
export function isValidNumber(value: any): value is number {
  return typeof value === 'number' && isFinite(value) && !isNaN(value);
}

/**
 * Get a safe numeric value with fallback
 * @param value - Value to check
 * @param fallback - Fallback value if invalid (default: 0)
 * @returns Valid number or fallback
 */
export function getSafeNumber(
  value: number | undefined | null,
  fallback: number = 0
): number {
  return isValidNumber(value) ? value : fallback;
}

/**
 * Calculate safe average from an array of numbers
 * @param values - Array of numbers
 * @param defaultValue - Value to return if invalid (default: 0)
 * @returns Average or default value
 */
export function safeAverage(
  values: (number | undefined | null)[],
  defaultValue: number = 0
): number {
  const validValues = values.filter(isValidNumber);
  if (validValues.length === 0) {
    return defaultValue;
  }
  const sum = validValues.reduce((acc, val) => acc + val, 0);
  return sum / validValues.length;
}

/**
 * Format a metric with proper NaN handling for display
 * @param value - Metric value
 * @param options - Formatting options
 * @returns Formatted metric object
 */
export interface MetricFormatOptions {
  decimals?: number;
  unit?: string;
  isPercentage?: boolean;
  showZero?: boolean;
  defaultDisplay?: string;
}

export interface FormattedMetric {
  value: number | null;
  display: string;
  isValid: boolean;
  hasWarning: boolean;
}

export function formatMetric(
  value: number | undefined | null,
  options: MetricFormatOptions = {}
): FormattedMetric {
  const {
    decimals = 2,
    unit = '',
    isPercentage = false,
    showZero = true,
    defaultDisplay = '--',
  } = options;

  // Check if value is invalid
  if (value == null || !isFinite(value) || isNaN(value)) {
    return {
      value: null,
      display: defaultDisplay,
      isValid: false,
      hasWarning: true,
    };
  }

  // Handle zero case
  if (value === 0 && !showZero) {
    return {
      value: 0,
      display: defaultDisplay,
      isValid: true,
      hasWarning: false,
    };
  }

  // Format the value
  let display: string;
  if (isPercentage) {
    display = `${(value * 100).toFixed(decimals)}%`;
  } else {
    display = value.toFixed(decimals);
    if (unit) {
      display += ` ${unit}`;
    }
  }

  return {
    value,
    display,
    isValid: true,
    hasWarning: false,
  };
}

/**
 * Format CI/coverage metrics safely
 * @param coverage - Coverage value (0-1)
 * @param target - Target value (0-1)
 * @returns Formatted coverage display
 */
export function formatCoverage(
  coverage: number | undefined | null,
  target: { min?: number; max?: number } = {}
): { display: string; status: 'excellent' | 'good' | 'poor' | 'unknown' } {
  if (!isValidNumber(coverage)) {
    return { display: '--', status: 'unknown' };
  }

  const display = `${(coverage * 100).toFixed(1)}%`;

  let status: 'excellent' | 'good' | 'poor' | 'unknown' = 'unknown';
  if (target.min != null && target.max != null) {
    if (coverage >= target.min && coverage <= target.max) {
      status = 'excellent';
    } else if (coverage >= (target.min - 0.05)) {
      status = 'good';
    } else {
      status = 'poor';
    }
  }

  return { display, status };
}

/**
 * Calculate utility score with safe handling
 * @param matchingPairs - Number of matching pairs
 * @param totalPairs - Total number of pairs
 * @returns Utility score (0-1) or null if invalid
 */
export function calculateUtilityScore(
  matchingPairs: number | undefined | null,
  totalPairs: number | undefined | null
): number | null {
  if (!isValidNumber(matchingPairs) || !isValidNumber(totalPairs) || totalPairs === 0) {
    return null;
  }
  const score = matchingPairs / totalPairs;
  return isValidNumber(score) ? Math.max(0, Math.min(1, score)) : null;
}
