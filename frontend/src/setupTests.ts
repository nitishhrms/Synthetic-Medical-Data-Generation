import '@testing-library/jest-dom';
import React from 'react';

// Mock ECharts to avoid canvas-related errors in tests
jest.mock('echarts-for-react', () => {
  return {
    __esModule: true,
    default: function MockECharts({ option }: any) {
      return React.createElement('div', {
        'data-testid': 'echarts-mock',
        children: JSON.stringify(option),
      });
    },
  };
});
