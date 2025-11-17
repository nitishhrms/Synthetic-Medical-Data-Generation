import React from 'react';
import { Table, Button } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { formatNumber } from '@/utils/stats';

export interface SummaryTableProps {
  title?: string;
  data: Record<string, any>[];
  columns?: ColumnsType<any>;
  showExport?: boolean;
  fileName?: string;
}

/**
 * Summary Table Component using Ant Design
 * Features:
 * - Numeric alignment
 * - Thousands separators
 * - CSV export functionality
 * - Responsive design
 */
export const SummaryTable: React.FC<SummaryTableProps> = ({
  title,
  data,
  columns,
  showExport = true,
  fileName = 'summary_table',
}) => {
  const handleExportCSV = () => {
    if (!data || data.length === 0) return;

    // Get headers from columns or data keys
    const headers = columns
      ? columns.map(col => col.title as string)
      : Object.keys(data[0]);

    const dataKeys = columns
      ? columns.map(col => col.dataIndex as string)
      : Object.keys(data[0]);

    // Create CSV content
    const csvRows = [headers.join(',')];

    data.forEach(row => {
      const values = dataKeys.map(key => {
        const value = row[key];
        // Handle special characters and commas in values
        if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
          return `"${value.replace(/"/g, '""')}"`;
        }
        return value ?? '';
      });
      csvRows.push(values.join(','));
    });

    const csvContent = csvRows.join('\n');

    // Download CSV
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `${fileName}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div>
      {(title || showExport) && (
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          {title && <h3 style={{ margin: 0 }}>{title}</h3>}
          {showExport && (
            <Button
              icon={<DownloadOutlined />}
              size="small"
              onClick={handleExportCSV}
            >
              Export CSV
            </Button>
          )}
        </div>
      )}
      <Table
        dataSource={data}
        columns={columns}
        pagination={false}
        size="small"
        bordered
        style={{ overflowX: 'auto' }}
      />
    </div>
  );
};

/**
 * Helper function to create standard numeric column
 */
export const createNumericColumn = (
  title: string,
  dataIndex: string,
  decimals: number = 2
): ColumnsType<any>[0] => ({
  title,
  dataIndex,
  key: dataIndex,
  align: 'right' as const,
  render: (value: number) =>
    typeof value === 'number' ? formatNumber(value, decimals) : value ?? 'N/A',
});

/**
 * Helper function to create standard text column
 */
export const createTextColumn = (
  title: string,
  dataIndex: string
): ColumnsType<any>[0] => ({
  title,
  dataIndex,
  key: dataIndex,
  align: 'left' as const,
});
