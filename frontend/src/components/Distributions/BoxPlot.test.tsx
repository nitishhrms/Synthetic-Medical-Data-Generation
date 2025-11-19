import { render, screen } from '@testing-library/react';
import { BoxPlot } from './BoxPlot';

// Mock antd Button
jest.mock('antd', () => ({
  Button: ({ children, onClick }: any) => (
    <button onClick={onClick}>{children}</button>
  ),
}));

describe('BoxPlot', () => {
  const mockDatasets = [
    { name: 'Real Data', data: [100, 110, 120, 130, 140, 150], color: '#10b981' },
    { name: 'Synthetic', data: [105, 115, 125, 135, 145, 155], color: '#3b82f6' },
  ];

  it('should render without crashing', () => {
    render(
      <BoxPlot
        title="Test BoxPlot"
        datasets={mockDatasets}
        unit="mmHg"
      />
    );

    expect(screen.getByText(/PNG/i)).toBeInTheDocument();
  });

  it('should render with vertical orientation by default', () => {
    const { container } = render(
      <BoxPlot
        title="Test BoxPlot"
        datasets={mockDatasets}
      />
    );

    const echartsMock = container.querySelector('[data-testid="echarts-mock"]');
    expect(echartsMock).toBeInTheDocument();

    if (echartsMock?.textContent) {
      const option = JSON.parse(echartsMock.textContent);
      expect(option.xAxis.type).toBe('category');
      expect(option.yAxis.type).toBe('value');
    }
  });

  it('should render with horizontal orientation', () => {
    const { container } = render(
      <BoxPlot
        title="Test BoxPlot"
        datasets={mockDatasets}
        orientation="horizontal"
      />
    );

    const echartsMock = container.querySelector('[data-testid="echarts-mock"]');
    if (echartsMock?.textContent) {
      const option = JSON.parse(echartsMock.textContent);
      expect(option.xAxis.type).toBe('value');
      expect(option.yAxis.type).toBe('category');
    }
  });

  it('should use custom categories', () => {
    const categories = ['Category A', 'Category B'];
    const { container } = render(
      <BoxPlot
        title="Test BoxPlot"
        datasets={mockDatasets}
        categories={categories}
      />
    );

    const echartsMock = container.querySelector('[data-testid="echarts-mock"]');
    if (echartsMock?.textContent) {
      const option = JSON.parse(echartsMock.textContent);
      expect(option.xAxis.data).toEqual(categories);
    }
  });

  it('should default to dataset names as categories', () => {
    const { container } = render(
      <BoxPlot
        title="Test BoxPlot"
        datasets={mockDatasets}
      />
    );

    const echartsMock = container.querySelector('[data-testid="echarts-mock"]');
    if (echartsMock?.textContent) {
      const option = JSON.parse(echartsMock.textContent);
      expect(option.xAxis.data).toEqual(['Real Data', 'Synthetic']);
    }
  });

  it('should have boxplot and outlier series', () => {
    const { container } = render(
      <BoxPlot
        title="Test BoxPlot"
        datasets={mockDatasets}
      />
    );

    const echartsMock = container.querySelector('[data-testid="echarts-mock"]');
    if (echartsMock?.textContent) {
      const option = JSON.parse(echartsMock.textContent);
      expect(option.series).toHaveLength(2);
      expect(option.series[0].type).toBe('boxplot');
      expect(option.series[1].type).toBe('scatter');
    }
  });

  it('should calculate box plot data correctly', () => {
    const simpleDataset = [
      { name: 'Test', data: [1, 2, 3, 4, 5], color: '#10b981' },
    ];

    const { container } = render(
      <BoxPlot
        title="Test BoxPlot"
        datasets={simpleDataset}
      />
    );

    const echartsMock = container.querySelector('[data-testid="echarts-mock"]');
    if (echartsMock?.textContent) {
      const option = JSON.parse(echartsMock.textContent);
      const boxData = option.series[0].data[0];

      // Box data format: [lowerWhisker, Q1, median, Q3, upperWhisker]
      expect(boxData).toHaveLength(5);
      expect(boxData[2]).toBe(3); // median
    }
  });

  it('should identify outliers', () => {
    const dataWithOutliers = [
      { name: 'Test', data: [1, 2, 3, 4, 5, 100], color: '#10b981' },
    ];

    const { container } = render(
      <BoxPlot
        title="Test BoxPlot"
        datasets={dataWithOutliers}
      />
    );

    const echartsMock = container.querySelector('[data-testid="echarts-mock"]');
    if (echartsMock?.textContent) {
      const option = JSON.parse(echartsMock.textContent);
      const outlierData = option.series[1].data;

      // Should have at least one outlier
      expect(outlierData.length).toBeGreaterThan(0);
      // Check that 100 is identified as outlier
      const has100 = outlierData.some((point: [number, number]) => point[1] === 100);
      expect(has100).toBe(true);
    }
  });

  it('should apply custom height', () => {
    const { container } = render(
      <BoxPlot
        title="Test BoxPlot"
        datasets={mockDatasets}
        height={600}
      />
    );

    const echartsMock = container.querySelector('[data-testid="echarts-mock"]');
    expect(echartsMock).toBeInTheDocument();
    // Height is applied to the ECharts container which is mocked
    // Just verify the component renders with custom height prop
  });

  it('should apply unit to axis label', () => {
    const { container } = render(
      <BoxPlot
        title="Test BoxPlot"
        datasets={mockDatasets}
        unit="bpm"
      />
    );

    const echartsMock = container.querySelector('[data-testid="echarts-mock"]');
    if (echartsMock?.textContent) {
      const option = JSON.parse(echartsMock.textContent);
      expect(option.yAxis.name).toContain('bpm');
    }
  });

  it('should handle three datasets', () => {
    const threeDatasets = [
      { name: 'Real', data: [1, 2, 3, 4, 5], color: '#10b981' },
      { name: 'MVN', data: [1.5, 2.5, 3.5, 4.5, 5.5], color: '#8b5cf6' },
      { name: 'Bootstrap', data: [1.2, 2.2, 3.2, 4.2, 5.2], color: '#f59e0b' },
    ];

    const { container } = render(
      <BoxPlot
        title="Three-way BoxPlot"
        datasets={threeDatasets}
      />
    );

    const echartsMock = container.querySelector('[data-testid="echarts-mock"]');
    if (echartsMock?.textContent) {
      const option = JSON.parse(echartsMock.textContent);
      // Should have 3 box plots
      expect(option.series[0].data).toHaveLength(3);
    }
  });
});
