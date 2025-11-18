import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { Button } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';
import { calculateBoxPlotStats } from '@/utils/stats';

export interface BoxPlotDataset {
  name: string;
  data: number[];
  color: string;
}

export interface BoxPlotProps {
  title: string;
  datasets: BoxPlotDataset[];
  categories?: string[];
  unit?: string;
  height?: number;
  orientation?: 'horizontal' | 'vertical';
}

/**
 * Box Plot Component using ECharts
 * Displays box plots with:
 * - Quartiles (Q1, Median, Q3)
 * - Whiskers at Q1 - 1.5*IQR and Q3 + 1.5*IQR
 * - Outliers marked as individual points
 * - PNG export functionality
 */
export const BoxPlot: React.FC<BoxPlotProps> = ({
  title,
  datasets,
  categories,
  unit = '',
  height = 400,
  orientation = 'vertical',
}) => {
  const chartRef = React.useRef<any>(null);

  const chartOption = useMemo(() => {
    // Calculate box plot statistics for each dataset
    const boxData: number[][] = [];
    const outlierData: Array<[number, number]> = [];

    datasets.forEach((dataset, datasetIdx) => {
      const stats = calculateBoxPlotStats(dataset.data);

      // ECharts boxplot format: [min, Q1, median, Q3, max]
      // But we use whiskers instead of absolute min/max
      boxData.push([
        stats.lowerWhisker,
        stats.q1,
        stats.median,
        stats.q3,
        stats.upperWhisker,
      ]);

      // Add outliers
      stats.outliers.forEach(outlier => {
        outlierData.push([datasetIdx, outlier]);
      });
    });

    const categoryNames = categories || datasets.map(d => d.name);

    if (orientation === 'horizontal') {
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
            if (params.componentSubType === 'boxplot') {
              const [lowerWhisker, q1, median, q3, upperWhisker] = params.value;
              return `
                <strong>${params.name}</strong><br/>
                Upper Whisker: ${upperWhisker.toFixed(1)}${unit}<br/>
                Q3: ${q3.toFixed(1)}${unit}<br/>
                Median: ${median.toFixed(1)}${unit}<br/>
                Q1: ${q1.toFixed(1)}${unit}<br/>
                Lower Whisker: ${lowerWhisker.toFixed(1)}${unit}
              `;
            } else {
              return `Outlier: ${params.value[1].toFixed(1)}${unit}`;
            }
          },
        },
        grid: {
          left: '15%',
          right: '10%',
          bottom: '15%',
          top: '60',
        },
        xAxis: {
          type: 'value',
          name: unit ? `Value (${unit})` : 'Value',
          nameLocation: 'middle',
          nameGap: 30,
          splitLine: {
            lineStyle: {
              type: 'dashed',
              opacity: 0.3,
            },
          },
        },
        yAxis: {
          type: 'category',
          data: categoryNames,
          boundaryGap: true,
          nameGap: 30,
          splitArea: {
            show: false,
          },
          splitLine: {
            show: false,
          },
        },
        series: [
          {
            name: 'boxplot',
            type: 'boxplot',
            data: boxData,
            itemStyle: {
              color: datasets[0]?.color || '#5470c6',
              borderColor: datasets[0]?.color || '#5470c6',
            },
            tooltip: {
              formatter: (params: any) => {
                const [lowerWhisker, q1, median, q3, upperWhisker] = params.value;
                return `
                  <strong>${params.name}</strong><br/>
                  Upper Whisker: ${upperWhisker.toFixed(1)}${unit}<br/>
                  Q3: ${q3.toFixed(1)}${unit}<br/>
                  Median: ${median.toFixed(1)}${unit}<br/>
                  Q1: ${q1.toFixed(1)}${unit}<br/>
                  Lower Whisker: ${lowerWhisker.toFixed(1)}${unit}
                `;
              },
            },
          },
          {
            name: 'outlier',
            type: 'scatter',
            data: outlierData,
            itemStyle: {
              color: 'rgba(220, 38, 38, 0.7)',
            },
            tooltip: {
              formatter: (params: any) => {
                return `Outlier: ${params.value[1].toFixed(1)}${unit}`;
              },
            },
          },
        ],
      };
    }

    // Vertical orientation
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
          if (params.componentSubType === 'boxplot') {
            const [lowerWhisker, q1, median, q3, upperWhisker] = params.value;
            return `
              <strong>${params.name}</strong><br/>
              Upper Whisker: ${upperWhisker.toFixed(1)}${unit}<br/>
              Q3: ${q3.toFixed(1)}${unit}<br/>
              Median: ${median.toFixed(1)}${unit}<br/>
              Q1: ${q1.toFixed(1)}${unit}<br/>
              Lower Whisker: ${lowerWhisker.toFixed(1)}${unit}
            `;
          } else {
            return `Outlier: ${params.value[1].toFixed(1)}${unit}`;
          }
        },
      },
      grid: {
        left: '10%',
        right: '10%',
        bottom: '20%',
        top: '60',
      },
      xAxis: {
        type: 'category',
        data: categoryNames,
        boundaryGap: true,
        nameGap: 30,
        axisLabel: {
          rotate: 45,
          fontSize: 11,
        },
        splitArea: {
          show: false,
        },
        splitLine: {
          show: false,
        },
      },
      yAxis: {
        type: 'value',
        name: unit ? `Value (${unit})` : 'Value',
        nameLocation: 'middle',
        nameGap: 50,
        splitLine: {
          lineStyle: {
            type: 'dashed',
            opacity: 0.3,
          },
        },
      },
      series: [
        {
          name: 'boxplot',
          type: 'boxplot',
          data: boxData,
          itemStyle: {
            color: datasets[0]?.color || '#5470c6',
            borderColor: datasets[0]?.color || '#5470c6',
          },
        },
        {
          name: 'outlier',
          type: 'scatter',
          data: outlierData,
          itemStyle: {
            color: 'rgba(220, 38, 38, 0.7)',
          },
        },
      ],
    };
  }, [datasets, categories, title, unit, height, orientation]);

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
