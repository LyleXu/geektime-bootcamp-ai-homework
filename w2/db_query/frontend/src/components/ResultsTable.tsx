import React from 'react';
import { Table, Typography, Space, Tag } from 'antd';
import type { ColumnsType } from 'antd/es/table';

const { Text } = Typography;

interface ResultsTableProps {
  data: Record<string, any>[];
  columns: string[];
  loading?: boolean;
  executionTimeMs?: number;
  rowCount?: number;
}

export const ResultsTable: React.FC<ResultsTableProps> = ({
  data,
  columns,
  loading = false,
  executionTimeMs,
  rowCount,
}) => {
  // Generate table columns from data
  const tableColumns: ColumnsType<Record<string, any>> = columns.map((col) => ({
    title: <Text strong style={{ color: '#1d1d1f', fontSize: '13px' }}>{col}</Text>,
    dataIndex: col,
    key: col,
    ellipsis: true,
    render: (value: any) => {
      if (value === null) {
        return <Text type="secondary" style={{ fontSize: '13px' }}>NULL</Text>;
      }
      if (typeof value === 'boolean') {
        return <Tag color={value ? '#34c759' : '#ff3b30'} style={{ borderRadius: '6px', fontSize: '12px' }}>{String(value)}</Tag>;
      }
      if (typeof value === 'object') {
        return <Text code style={{ fontSize: '12px' }}>{JSON.stringify(value)}</Text>;
      }
      return <Text style={{ fontSize: '13px', color: '#1d1d1f' }}>{String(value)}</Text>;
    },
  }));

  return (
    <div>
      <Table
        columns={tableColumns}
        dataSource={data.map((row, idx) => ({ ...row, key: idx }))}
        loading={loading}
        pagination={{
          pageSize: 50,
          showSizeChanger: true,
          showTotal: (total) => `${total} ${total === 1 ? 'row' : 'rows'}`,
          pageSizeOptions: ['10', '20', '50', '100', '500'],
          style: { marginTop: '16px' },
        }}
        scroll={{ x: 'max-content', y: 'calc(100vh - 500px)' }}
        size="small"
        style={{
          background: 'white',
        }}
        className="apple-table"
      />
    </div>
  );
};
