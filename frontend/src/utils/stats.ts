/**
 * Statistical utility functions for analytics dashboard
 * Includes binning, density calculation, quantiles, and comparative statistics
 */

export interface BinResult {
  edges: number[];
  width: number;
  centers: number[];
}

export interface DensityResult {
  densities: number[];
  binCenters: number[];
}

export interface BoxPlotStats {
  min: number;
  q1: number;
  median: number;
  q3: number;
  max: number;
  outliers: number[];
  lowerWhisker: number;
  upperWhisker: number;
}

/**
 * Create bins for histogram with shared edges across multiple datasets
 * @param data - Array of numbers or array of arrays for combined binning
 * @param binCount - Number of bins to create
 * @returns BinResult containing edges, width, and centers
 */
export function makeBins(
  data: number[] | number[][],
  binCount: number = 30
): BinResult {
  // Flatten if array of arrays
  const flatData = Array.isArray(data[0])
    ? (data as number[][]).flat()
    : (data as number[]);

  if (flatData.length === 0) {
    return { edges: [], width: 0, centers: [] };
  }

  const min = Math.min(...flatData);
  const max = Math.max(...flatData);
  const width = (max - min) / binCount;

  // Create bin edges
  const edges: number[] = [];
  for (let i = 0; i <= binCount; i++) {
    edges.push(min + i * width);
  }

  // Create bin centers
  const centers: number[] = [];
  for (let i = 0; i < binCount; i++) {
    centers.push(edges[i] + width / 2);
  }

  return { edges, width, centers };
}

/**
 * Calculate histogram densities (normalized)
 * Density = count / (n * binWidth)
 * @param series - Data series to compute density for
 * @param edges - Bin edges from makeBins
 * @returns Array of density values
 */
export function histDensity(series: number[], edges: number[]): number[] {
  if (series.length === 0 || edges.length < 2) {
    return [];
  }

  const binCount = edges.length - 1;
  const counts = new Array(binCount).fill(0);
  const binWidth = edges[1] - edges[0];

  // Count occurrences in each bin
  series.forEach(value => {
    // Find which bin this value belongs to
    for (let i = 0; i < binCount; i++) {
      if (value >= edges[i] && value < edges[i + 1]) {
        counts[i]++;
        break;
      } else if (i === binCount - 1 && value === edges[i + 1]) {
        // Include max value in last bin
        counts[i]++;
        break;
      }
    }
  });

  // Calculate densities: count / (n * binWidth)
  const n = series.length;
  const densities = counts.map(count => count / (n * binWidth));

  return densities;
}

/**
 * Calculate histogram counts (non-normalized)
 * @param series - Data series to compute counts for
 * @param edges - Bin edges from makeBins
 * @returns Array of count values
 */
export function histCounts(series: number[], edges: number[]): number[] {
  if (series.length === 0 || edges.length < 2) {
    return [];
  }

  const binCount = edges.length - 1;
  const counts = new Array(binCount).fill(0);

  // Count occurrences in each bin
  series.forEach(value => {
    for (let i = 0; i < binCount; i++) {
      if (value >= edges[i] && value < edges[i + 1]) {
        counts[i]++;
        break;
      } else if (i === binCount - 1 && value === edges[i + 1]) {
        counts[i]++;
        break;
      }
    }
  });

  return counts;
}

/**
 * Calculate box plot statistics with outliers
 * @param data - Array of numbers
 * @returns BoxPlotStats object
 */
export function calculateBoxPlotStats(data: number[]): BoxPlotStats {
  if (data.length === 0) {
    return {
      min: 0,
      q1: 0,
      median: 0,
      q3: 0,
      max: 0,
      outliers: [],
      lowerWhisker: 0,
      upperWhisker: 0,
    };
  }

  const sorted = [...data].sort((a, b) => a - b);
  const n = sorted.length;

  // Calculate quartiles
  const q1Index = Math.floor(n * 0.25);
  const q3Index = Math.floor(n * 0.75);

  const q1 = sorted[q1Index];
  const q3 = sorted[q3Index];

  // Calculate median (average of middle two if even length)
  let median: number;
  if (n % 2 === 0) {
    const mid1 = Math.floor(n / 2) - 1;
    const mid2 = Math.floor(n / 2);
    median = (sorted[mid1] + sorted[mid2]) / 2;
  } else {
    median = sorted[Math.floor(n / 2)];
  }

  const iqr = q3 - q1;

  // Calculate whiskers (Q1 - 1.5*IQR, Q3 + 1.5*IQR)
  const lowerBound = q1 - 1.5 * iqr;
  const upperBound = q3 + 1.5 * iqr;

  // Find actual whisker values (closest values within bounds)
  let lowerWhisker = sorted[0];
  let upperWhisker = sorted[n - 1];

  for (let i = 0; i < n; i++) {
    if (sorted[i] >= lowerBound) {
      lowerWhisker = sorted[i];
      break;
    }
  }

  for (let i = n - 1; i >= 0; i--) {
    if (sorted[i] <= upperBound) {
      upperWhisker = sorted[i];
      break;
    }
  }

  // Identify outliers
  const outliers = sorted.filter(
    value => value < lowerBound || value > upperBound
  );

  return {
    min: sorted[0],
    q1,
    median,
    q3,
    max: sorted[n - 1],
    outliers,
    lowerWhisker,
    upperWhisker,
  };
}

/**
 * Calculate percentage difference between two means
 * diff% = 100 * (mean_syn - mean_real) / mean_real
 * @param syntheticMean - Mean of synthetic data
 * @param realMean - Mean of real data
 * @returns Percentage difference
 */
export function calculateDiffPercent(
  syntheticMean: number,
  realMean: number
): number {
  if (realMean === 0) {
    return syntheticMean === 0 ? 0 : Infinity;
  }
  return (100 * (syntheticMean - realMean)) / realMean;
}

/**
 * Calculate mean of an array
 * @param data - Array of numbers
 * @returns Mean value
 */
export function mean(data: number[]): number {
  if (data.length === 0) return 0;
  return data.reduce((sum, val) => sum + val, 0) / data.length;
}

/**
 * Calculate standard deviation
 * @param data - Array of numbers
 * @returns Standard deviation
 */
export function std(data: number[]): number {
  if (data.length === 0) return 0;
  const avg = mean(data);
  const squareDiffs = data.map(value => Math.pow(value - avg, 2));
  return Math.sqrt(mean(squareDiffs));
}

/**
 * Count unique values in an array
 * @param data - Array of any type
 * @returns Count of unique values
 */
export function countUnique<T>(data: T[]): number {
  return new Set(data).size;
}

/**
 * Format number with thousands separators
 * @param num - Number to format
 * @param decimals - Number of decimal places
 * @returns Formatted string
 */
export function formatNumber(num: number, decimals: number = 2): string {
  return num.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

/**
 * Calculate visit sequence completeness
 * @param data - Array with SubjectID and VisitName fields
 * @param expectedVisits - Array of expected visit names in order
 * @returns Object with complete and incomplete counts
 */
export function calculateVisitCompleteness<
  T extends { SubjectID: string; VisitName: string }
>(data: T[], expectedVisits: string[]): { complete: number; incomplete: number } {
  // Group by subject
  const subjectVisits = new Map<string, Set<string>>();

  data.forEach(record => {
    if (!subjectVisits.has(record.SubjectID)) {
      subjectVisits.set(record.SubjectID, new Set());
    }
    subjectVisits.get(record.SubjectID)!.add(record.VisitName);
  });

  let complete = 0;
  let incomplete = 0;

  subjectVisits.forEach(visits => {
    const hasAllVisits = expectedVisits.every(visit => visits.has(visit));
    if (hasAllVisits) {
      complete++;
    } else {
      incomplete++;
    }
  });

  return { complete, incomplete };
}

/**
 * Group data by a key field
 * @param data - Array of objects
 * @param keyField - Field name to group by
 * @returns Map of key to array of records
 */
export function groupBy<T, K extends keyof T>(
  data: T[],
  keyField: K
): Map<T[K], T[]> {
  const groups = new Map<T[K], T[]>();

  data.forEach(item => {
    const key = item[keyField];
    if (!groups.has(key)) {
      groups.set(key, []);
    }
    groups.get(key)!.push(item);
  });

  return groups;
}

/**
 * Extract numeric field from array of objects
 * @param data - Array of objects
 * @param field - Field name to extract
 * @returns Array of numbers
 */
export function extractField<T>(data: T[], field: keyof T): number[] {
  return data
    .map(item => item[field])
    .filter(val => typeof val === 'number') as number[];
}
