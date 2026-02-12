import React, { useState, useEffect } from 'react';
import { Card, Button, Space, Typography, Alert, Select, Spin, message } from 'antd';
import { PlayCircleOutlined, ClearOutlined, DatabaseOutlined } from '@ant-design/icons';
import { SqlEditor } from '../components/SqlEditor';
import { ResultsTable } from '../components/ResultsTable';
import { useQuery } from '../hooks/useQuery';
import { useActiveDb } from '../hooks/useActiveDb';
import { client } from '../api/client';
import type { DatabaseConnection } from '../types/database';

const { Title, Text, Paragraph } = Typography;

export const QueryEditor: React.FC = () => {
  const [sql, setSql] = useState('SELECT * FROM users LIMIT 10;');
  const [databases, setDatabases] = useState<DatabaseConnection[]>([]);
  const [selectedDb, setSelectedDb] = useState<string | null>(null);
  const [loadingDbs, setLoadingDbs] = useState(true);
  
  const { executeQuery, data, loading, error, clearResults } = useQuery();
  const { activeDb } = useActiveDb();

  // Load databases on mount
  useEffect(() => {
    const loadDatabases = async () => {
      try {
        const response = await client.get<{ databases: DatabaseConnection[]; total: number }>('/dbs');
        setDatabases(response.data.databases);
        
        // Auto-select active database or first database
        if (activeDb) {
          setSelectedDb(activeDb.name);
        } else if (response.data.databases.length > 0) {
          setSelectedDb(response.data.databases[0].name);
        }
      } catch (err: any) {
        message.error('Failed to load databases');
      } finally {
        setLoadingDbs(false);
      }
    };
    loadDatabases();
  }, [activeDb]);

  const handleExecute = async () => {
    if (!selectedDb) {
      message.warning('Please select a database first');
      return;
    }
    
    await executeQuery(selectedDb, sql);
  };

  const handleClear = () => {
    setSql('');
    clearResults();
  };

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Card>
          <Space style={{ width: '100%', justifyContent: 'space-between' }}>
            <Title level={2} style={{ margin: 0 }}>
              <DatabaseOutlined /> SQL Query Editor
            </Title>
          </Space>
        </Card>

        <Card title="Database Selection">
          {loadingDbs ? (
            <Spin />
          ) : databases.length === 0 ? (
            <Alert
              message="No databases available"
              description="Please add a database connection first."
              type="warning"
              showIcon
            />
          ) : (
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text strong>Select Database:</Text>
              <Select
                style={{ width: '100%', maxWidth: '400px' }}
                placeholder="Choose a database"
                value={selectedDb}
                onChange={setSelectedDb}
                options={databases.map((db) => ({
                  label: (
                    <Space>
                      {db.name}
                      {db.isActive && <Text type="success">(Active)</Text>}
                    </Space>
                  ),
                  value: db.name,
                }))}
              />
            </Space>
          )}
        </Card>

        <Card
          title="SQL Editor"
          extra={
            <Space>
              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                onClick={handleExecute}
                loading={loading}
                disabled={!selectedDb || loadingDbs}
              >
                Execute (Ctrl+Enter)
              </Button>
              <Button icon={<ClearOutlined />} onClick={handleClear}>
                Clear
              </Button>
            </Space>
          }
        >
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Paragraph type="secondary" style={{ margin: 0 }}>
              Write your SQL query below. Only SELECT statements are allowed. Queries are automatically
              limited to 1000 rows if no LIMIT clause is specified.
            </Paragraph>
            <SqlEditor
              value={sql}
              onChange={setSql}
              onExecute={handleExecute}
              height="250px"
            />
          </Space>
        </Card>

        {error && (
          <Card>
            <Alert
              message="Query Error"
              description={error}
              type="error"
              showIcon
              closable
              onClose={clearResults}
            />
          </Card>
        )}

        {data && (
          <Card title="Query Results">
            <ResultsTable
              data={data.rows}
              columns={data.columns}
              loading={loading}
              executionTimeMs={data.executionTimeMs}
              rowCount={data.rowCount}
            />
          </Card>
        )}

        {!data && !error && !loading && (
          <Card>
            <Alert
              message="Ready to execute"
              description="Write a SQL query and click Execute to see results here."
              type="info"
              showIcon
            />
          </Card>
        )}
      </Space>
    </div>
  );
};
