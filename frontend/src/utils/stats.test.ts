import {
  makeBins,
  histDensity,
  histCounts,
  calculateBoxPlotStats,
  calculateDiffPercent,
  mean,
  std,
  countUnique,
  extractField,
  groupBy,
  calculateVisitCompleteness,
  formatNumber,
} from './stats';

describe('makeBins', () => {
  it('should create bins with correct edges and centers', () => {
    const data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
    const result = makeBins(data, 5);

    expect(result.edges.length).toBe(6); // 5 bins = 6 edges
    expect(result.centers.length).toBe(5);
    expect(result.edges[0]).toBe(1);
    expect(result.edges[5]).toBe(10);
    expect(result.width).toBeCloseTo(1.8);
  });

  it('should handle combined datasets', () => {
    const data1 = [1, 2, 3];
    const data2 = [4, 5, 6];
    const result = makeBins([data1, data2], 3);

    expect(result.edges[0]).toBe(1);
    expect(result.edges[3]).toBe(6);
  });

  it('should handle empty data', () => {
    const result = makeBins([], 5);
    expect(result.edges).toEqual([]);
    expect(result.width).toBe(0);
  });
});

describe('histDensity', () => {
  it('should calculate density correctly', () => {
    const data = [1, 2, 3, 4, 5];
    const edges = [0, 2, 4, 6];
    const densities = histDensity(data, edges);

    expect(densities.length).toBe(3); // 4 edges = 3 bins
    expect(densities.reduce((sum, d) => sum + d * 2, 0)).toBeCloseTo(1, 1); // Integral ≈ 1
  });

  it('should handle empty data', () => {
    const result = histDensity([], [0, 1, 2]);
    expect(result).toEqual([]);
  });

  it('should place values in correct bins', () => {
    const data = [1, 1.5, 3, 3.5];
    const edges = [0, 2, 4];
    const densities = histDensity(data, edges);

    // First bin [0,2) should have 2 values
    // Second bin [2,4] should have 2 values
    expect(densities[0]).toBeCloseTo(0.25); // 2/(4*2) = 0.25
    expect(densities[1]).toBeCloseTo(0.25);
  });
});

describe('histCounts', () => {
  it('should count values in bins correctly', () => {
    const data = [1, 1.5, 3, 3.5];
    const edges = [0, 2, 4];
    const counts = histCounts(data, edges);

    expect(counts[0]).toBe(2);
    expect(counts[1]).toBe(2);
  });

  it('should handle edge cases', () => {
    const data = [0, 2, 4];
    const edges = [0, 2, 4];
    const counts = histCounts(data, edges);

    expect(counts[0]).toBe(1); // value 0 in [0,2)
    expect(counts[1]).toBe(2); // value 2 in [2,4], value 4 in [2,4]
  });
});

describe('calculateBoxPlotStats', () => {
  it('should calculate quartiles correctly', () => {
    const data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
    const stats = calculateBoxPlotStats(data);

    expect(stats.median).toBe(5.5); // Average of 5 and 6 for even-length array
    expect(stats.q1).toBe(3);
    expect(stats.q3).toBe(8);
    expect(stats.min).toBe(1);
    expect(stats.max).toBe(10);
  });

  it('should identify outliers correctly', () => {
    const data = [1, 2, 3, 4, 5, 100]; // 100 is an outlier
    const stats = calculateBoxPlotStats(data);

    expect(stats.outliers.length).toBeGreaterThan(0);
    expect(stats.outliers).toContain(100);
  });

  it('should calculate whiskers correctly', () => {
    const data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
    const stats = calculateBoxPlotStats(data);

    const iqr = stats.q3 - stats.q1;
    const expectedLowerBound = stats.q1 - 1.5 * iqr;
    const expectedUpperBound = stats.q3 + 1.5 * iqr;

    expect(stats.lowerWhisker).toBeGreaterThanOrEqual(expectedLowerBound);
    expect(stats.upperWhisker).toBeLessThanOrEqual(expectedUpperBound);
  });

  it('should handle empty array', () => {
    const stats = calculateBoxPlotStats([]);
    expect(stats.median).toBe(0);
    expect(stats.outliers).toEqual([]);
  });
});

describe('calculateDiffPercent', () => {
  it('should calculate percentage difference correctly', () => {
    expect(calculateDiffPercent(110, 100)).toBeCloseTo(10);
    expect(calculateDiffPercent(90, 100)).toBeCloseTo(-10);
    expect(calculateDiffPercent(100, 100)).toBeCloseTo(0);
  });

  it('should handle zero real mean', () => {
    expect(calculateDiffPercent(0, 0)).toBe(0);
    expect(calculateDiffPercent(10, 0)).toBe(Infinity);
  });

  it('should handle negative values', () => {
    expect(calculateDiffPercent(-110, -100)).toBeCloseTo(10);
  });
});

describe('mean', () => {
  it('should calculate mean correctly', () => {
    expect(mean([1, 2, 3, 4, 5])).toBeCloseTo(3);
    expect(mean([10, 20, 30])).toBeCloseTo(20);
  });

  it('should handle empty array', () => {
    expect(mean([])).toBe(0);
  });

  it('should handle single value', () => {
    expect(mean([42])).toBe(42);
  });
});

describe('std', () => {
  it('should calculate standard deviation correctly', () => {
    const data = [2, 4, 4, 4, 5, 5, 7, 9];
    const stdDev = std(data);
    expect(stdDev).toBeCloseTo(2, 0);
  });

  it('should return 0 for empty array', () => {
    expect(std([])).toBe(0);
  });

  it('should return 0 for constant array', () => {
    expect(std([5, 5, 5, 5])).toBeCloseTo(0);
  });
});

describe('countUnique', () => {
  it('should count unique values correctly', () => {
    expect(countUnique([1, 2, 3, 2, 1])).toBe(3);
    expect(countUnique(['a', 'b', 'a'])).toBe(2);
  });

  it('should handle empty array', () => {
    expect(countUnique([])).toBe(0);
  });

  it('should handle all unique values', () => {
    expect(countUnique([1, 2, 3, 4])).toBe(4);
  });
});

describe('extractField', () => {
  it('should extract numeric fields correctly', () => {
    const data = [
      { name: 'A', value: 10 },
      { name: 'B', value: 20 },
      { name: 'C', value: 30 },
    ];
    const values = extractField(data, 'value');
    expect(values).toEqual([10, 20, 30]);
  });

  it('should filter out non-numeric values', () => {
    const data = [
      { value: 10 },
      { value: 'not a number' as any },
      { value: 30 },
    ];
    const values = extractField(data, 'value');
    expect(values).toEqual([10, 30]);
  });
});

describe('groupBy', () => {
  it('should group objects by key field', () => {
    const data = [
      { category: 'A', value: 1 },
      { category: 'B', value: 2 },
      { category: 'A', value: 3 },
    ];
    const grouped = groupBy(data, 'category');

    expect(grouped.get('A')?.length).toBe(2);
    expect(grouped.get('B')?.length).toBe(1);
    expect(grouped.get('A')?.[0].value).toBe(1);
    expect(grouped.get('A')?.[1].value).toBe(3);
  });
});

describe('calculateVisitCompleteness', () => {
  it('should calculate visit completeness correctly', () => {
    const data = [
      { SubjectID: 'S1', VisitName: 'Screening' },
      { SubjectID: 'S1', VisitName: 'Day 1' },
      { SubjectID: 'S1', VisitName: 'Week 4' },
      { SubjectID: 'S1', VisitName: 'Week 12' },
      { SubjectID: 'S2', VisitName: 'Screening' },
      { SubjectID: 'S2', VisitName: 'Day 1' },
    ];
    const expectedVisits = ['Screening', 'Day 1', 'Week 4', 'Week 12'];
    const result = calculateVisitCompleteness(data, expectedVisits);

    expect(result.complete).toBe(1); // S1 has all visits
    expect(result.incomplete).toBe(1); // S2 is missing visits
  });

  it('should handle empty data', () => {
    const result = calculateVisitCompleteness([], ['Visit1', 'Visit2']);
    expect(result.complete).toBe(0);
    expect(result.incomplete).toBe(0);
  });
});

describe('formatNumber', () => {
  it('should format numbers with correct decimals', () => {
    expect(formatNumber(1234.5678, 2)).toBe('1,234.57');
    expect(formatNumber(1000000, 0)).toBe('1,000,000');
  });

  it('should handle small numbers', () => {
    expect(formatNumber(0.123, 3)).toBe('0.123');
  });
});

// Integration test: Binning + Density
describe('Integration: Binning and Density', () => {
  it('should produce densities that integrate to approximately 1', () => {
    const data = Array.from({ length: 1000 }, (_, i) => i / 10); // 0 to 99.9
    const { edges, width } = makeBins(data, 30);
    const densities = histDensity(data, edges);

    // Integral of density over bins should be close to 1
    const integral = densities.reduce((sum, density) => sum + density * width, 0);
    expect(integral).toBeCloseTo(1, 1);
  });

  it('should handle multiple overlapping datasets with shared bins', () => {
    const data1 = [1, 2, 3, 4, 5];
    const data2 = [3, 4, 5, 6, 7];
    const { edges, width } = makeBins([data1, data2], 10);

    const density1 = histDensity(data1, edges);
    const density2 = histDensity(data2, edges);

    // Both should integrate to ~1
    const integral1 = density1.reduce((sum, d) => sum + d * width, 0);
    const integral2 = density2.reduce((sum, d) => sum + d * width, 0);

    expect(integral1).toBeCloseTo(1, 1);
    expect(integral2).toBeCloseTo(1, 1);
  });
});
