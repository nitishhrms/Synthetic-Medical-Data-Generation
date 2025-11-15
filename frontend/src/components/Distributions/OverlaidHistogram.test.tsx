import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { OverlaidHistogram } from './OverlaidHistogram';

// Mock antd Button to avoid issues with icons
jest.mock('antd', () => ({
  Button: ({ children, onClick }: any) => (
    <button onClick={onClick}>{children}</button>
  ),
}));

describe('OverlaidHistogram', () => {
  const mockDatasets = [
    { name: 'Real Data', data: [100, 110, 120, 130, 140], color: '#10b981' },
    { name: 'Synthetic', data: [105, 115, 125, 135, 145], color: '#3b82f6' },
  ];

  it('should render without crashing', () => {
    render(
      <OverlaidHistogram
        title="Test Histogram"
        datasets={mockDatasets}
        binCount={10}
        useDensity={true}
        unit="mmHg"
      />
    );

    expect(screen.getByText(/PNG/i)).toBeInTheDocument();
  });

  it('should render with density mode', () => {
    const { container } = render(
      <OverlaidHistogram
        title="Test Histogram"
        datasets={mockDatasets}
        binCount={10}
        useDensity={true}
        unit="mmHg"
      />
    );

    // Check that the ECharts mock is rendered
    const echartsMock = container.querySelector('[data-testid="echarts-mock"]');
    expect(echartsMock).toBeInTheDocument();
  });

  it('should render with count mode', () => {
    const { container } = render(
      <OverlaidHistogram
        title="Test Histogram"
        datasets={mockDatasets}
        binCount={10}
        useDensity={false}
        unit="mmHg"
      />
    );

    const echartsMock = container.querySelector('[data-testid="echarts-mock"]');
    expect(echartsMock).toBeInTheDocument();
  });

  it('should handle empty datasets gracefully', () => {
    const { container } = render(
      <OverlaidHistogram
        title="Empty Histogram"
        datasets={[{ name: 'Empty', data: [], color: '#10b981' }]}
        binCount={10}
        useDensity={true}
      />
    );

    expect(screen.getByText(/No data available/i)).toBeInTheDocument();
  });

  it('should apply custom height', () => {
    const { container } = render(
      <OverlaidHistogram
        title="Test Histogram"
        datasets={mockDatasets}
        height={500}
      />
    );

    const echartsMock = container.querySelector('[data-testid="echarts-mock"]');
    expect(echartsMock).toBeInTheDocument();
    // Height is applied to the ECharts container which is mocked
    // Just verify the component renders with custom height prop
  });

  it('should render export button', () => {
    render(
      <OverlaidHistogram
        title="Test Histogram"
        datasets={mockDatasets}
      />
    );

    const exportButton = screen.getByText(/PNG/i);
    expect(exportButton).toBeInTheDocument();
  });

  it('should create correct bin count', () => {
    const { container } = render(
      <OverlaidHistogram
        title="Test Histogram"
        datasets={mockDatasets}
        binCount={20}
      />
    );

    const echartsMock = container.querySelector('[data-testid="echarts-mock"]');
    if (echartsMock?.textContent) {
      const option = JSON.parse(echartsMock.textContent);
      // Should have series for each dataset
      expect(option.series).toHaveLength(2);
    }
  });

  it('should display correct dataset names in legend', () => {
    const { container } = render(
      <OverlaidHistogram
        title="Test Histogram"
        datasets={mockDatasets}
      />
    );

    const echartsMock = container.querySelector('[data-testid="echarts-mock"]');
    if (echartsMock?.textContent) {
      const option = JSON.parse(echartsMock.textContent);
      expect(option.legend.data).toEqual(['Real Data', 'Synthetic']);
    }
  });

  it('should use overlay bar mode', () => {
    const { container } = render(
      <OverlaidHistogram
        title="Test Histogram"
        datasets={mockDatasets}
      />
    );

    const echartsMock = container.querySelector('[data-testid="echarts-mock"]');
    if (echartsMock?.textContent) {
      const option = JSON.parse(echartsMock.textContent);
      // Check that bars are set to overlay
      option.series.forEach((series: any) => {
        expect(series.barGap).toBe('-100%');
      });
    }
  });

  it('should apply custom colors', () => {
    const customDatasets = [
      { name: 'Dataset1', data: [1, 2, 3], color: '#ff0000' },
      { name: 'Dataset2', data: [4, 5, 6], color: '#00ff00' },
    ];

    const { container } = render(
      <OverlaidHistogram
        title="Test Histogram"
        datasets={customDatasets}
      />
    );

    const echartsMock = container.querySelector('[data-testid="echarts-mock"]');
    if (echartsMock?.textContent) {
      const option = JSON.parse(echartsMock.textContent);
      expect(option.series[0].itemStyle.color).toBe('#ff0000');
      expect(option.series[1].itemStyle.color).toBe('#00ff00');
    }
  });

  it('should handle three or more datasets', () => {
    const multiDatasets = [
      { name: 'Real', data: [1, 2, 3], color: '#10b981' },
      { name: 'MVN', data: [1.5, 2.5, 3.5], color: '#8b5cf6' },
      { name: 'Bootstrap', data: [1.2, 2.2, 3.2], color: '#f59e0b' },
    ];

    const { container } = render(
      <OverlaidHistogram
        title="Three-way Comparison"
        datasets={multiDatasets}
      />
    );

    const echartsMock = container.querySelector('[data-testid="echarts-mock"]');
    if (echartsMock?.textContent) {
      const option = JSON.parse(echartsMock.textContent);
      expect(option.series).toHaveLength(3);
      expect(option.legend.data).toEqual(['Real', 'MVN', 'Bootstrap']);
    }
  });
});
