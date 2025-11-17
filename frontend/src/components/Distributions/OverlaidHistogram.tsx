import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { Button } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';
import { makeBins, histDensity, histCounts } from '@/utils/stats';

export interface HistogramDataset {
  name: string;
  data: number[];
  color: string;
}

export interface OverlaidHistogramProps {
  title: string;
  datasets: HistogramDataset[];
  binCount?: number;
  useDensity?: boolean;
  unit?: string;
  height?: number;
}

/**
 * Overlaid Histogram Component using ECharts
 * Displays multiple datasets as overlaid density histograms with:
 * - Shared bin edges for perfect alignment
 * - Semi-transparent fills and solid borders
 * - Accessible color palette
 * - Tooltips showing bin range, value, and cohort name
 * - PNG export functionality
 */
export const OverlaidHistogram: React.FC<OverlaidHistogramProps> = ({
  title,
  datasets,
  binCount = 30,
  useDensity = true,
  unit = '',
  height = 350,
}) => {
  const chartRef = React.useRef<any>(null);

  const chartOption = useMemo(() => {
    // Combine all datasets to get shared bin edges
    const allData = datasets.flatMap(d => d.data);
    const { edges, centers, width } = makeBins(allData, binCount);

    if (edges.length === 0) {
      return null;
    }

    // Calculate histogram values for each dataset
    const series = datasets.map((dataset, idx) => {
      const values = useDensity
        ? histDensity(dataset.data, edges)
        : histCounts(dataset.data, edges);

      return {
        name: dataset.name,
        type: 'bar',
        data: values.map((val, i) => ({
          value: val,
          binStart: edges[i],
          binEnd: edges[i + 1],
          binCenter: centers[i],
        })),
        itemStyle: {
          color: dataset.color,
          opacity: 0.6,
          borderColor: dataset.color,
          borderWidth: 1,
        },
        emphasis: {
          itemStyle: {
            opacity: 0.8,
          },
        },
        barGap: '-100%', // Overlay bars
        barCategoryGap: '20%',
      };
    });

    return {
      title: {
        text: title,
        left: 'center',
        textStyle: {
          fontSize: 14,
          fontWeight: 'normal',
        },
      },
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => {
          const { seriesName, data, value } = params;
          const binStart = data.binStart?.toFixed(1) || '';
          const binEnd = data.binEnd?.toFixed(1) || '';
          const displayValue = useDensity
            ? value.toFixed(4)
            : Math.round(value);
          const label = useDensity ? 'Density' : 'Count';

          return `
            <strong>${seriesName}</strong><br/>
            Bin: [${binStart}, ${binEnd})${unit ? ' ' + unit : ''}<br/>
            ${label}: ${displayValue}
          `;
        },
      },
      legend: {
        top: '30',
        data: datasets.map(d => d.name),
      },
      grid: {
        left: '12%',
        right: '8%',
        bottom: '15%',
        top: '80',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: centers.map(c => c.toFixed(1)),
        name: unit ? `Value (${unit})` : 'Value',
        nameLocation: 'middle',
        nameGap: 30,
        axisLabel: {
          rotate: 45,
          fontSize: 10,
        },
      },
      yAxis: {
        type: 'value',
        name: useDensity ? 'Density' : 'Count',
        nameLocation: 'middle',
        nameGap: 50,
        splitLine: {
          lineStyle: {
            type: 'dashed',
            opacity: 0.3,
          },
        },
      },
      series,
    };
  }, [datasets, binCount, useDensity, title, unit]);

  const handleExport = () => {
    if (chartRef.current) {
      const echartInstance = chartRef.current.getEchartsInstance();
      const url = echartInstance.getDataURL({
        type: 'png',
        pixelRatio: 2,
        backgroundColor: '#fff',
      });

      const link = document.createElement('a');
      link.href = url;
      link.download = `${title.replace(/\s+/g, '_')}.png`;
      link.click();
    }
  };

  if (!chartOption) {
    return (
      <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <p>No data available</p>
      </div>
    );
  }

  return (
    <div style={{ position: 'relative' }}>
      <Button
        icon={<DownloadOutlined />}
        size="small"
        onClick={handleExport}
        style={{
          position: 'absolute',
          top: 8,
          right: 8,
          zIndex: 10,
        }}
      >
        PNG
      </Button>
      <ReactECharts
        ref={chartRef}
        option={chartOption}
        style={{ height }}
        opts={{ renderer: 'canvas' }}
      />
    </div>
  );
};
