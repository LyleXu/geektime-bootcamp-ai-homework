import React, { useState, useEffect, useRef } from 'react';
import { Card, Button, Space, Typography, Alert, Select, Spin, message, Input } from 'antd';
import { SendOutlined, ClearOutlined, DatabaseOutlined, BulbOutlined, DownloadOutlined } from '@ant-design/icons';
import { SqlApproval } from '../components/SqlApproval';
import { ResultsTable } from '../components/ResultsTable';
import { ExportDialog } from '../components/ExportDialog';
import { useQuery } from '../hooks/useQuery';
import { useActiveDb } from '../hooks/useActiveDb';
import { client } from '../api/client';
import type { DatabaseConnection } from '../types/database';
import type { NaturalQueryRequest, NaturalQueryResponse } from '../types/query';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

export const NaturalQuery: React.FC = () => {
  const [naturalLanguage, setNaturalLanguage] = useState('Show me all users who registered in the last 30 days');
  const [databases, setDatabases] = useState<DatabaseConnection[]>([]);
  const [selectedDb, setSelectedDb] = useState<string | null>(null);
  const [loadingDbs, setLoadingDbs] = useState(true);
  const [generatingSQL, setGeneratingSQL] = useState(false);
  const [sqlResponse, setSqlResponse] = useState<NaturalQueryResponse | null>(null);
  const [approvedSql, setApprovedSql] = useState<string | null>(null);
  const [exportDialogVisible, setExportDialogVisible] = useState(false);
  
  // Use ref to track if we should auto-open export dialog
  const shouldAutoExportRef = useRef(false);

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

  // Auto-open export dialog when data is loaded and shouldAutoExport flag is set
  useEffect(() => {
    if (shouldAutoExportRef.current && data && data.rows && data.rows.length > 0 && !loading) {
      console.log('Auto-opening export dialog...');
      // Small delay to ensure UI is updated
      const timer = setTimeout(() => {
        setExportDialogVisible(true);
        shouldAutoExportRef.current = false; // Reset flag
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [data, loading]);

  const handleGenerateSQL = async () => {
    if (!selectedDb) {
      message.warning('Please select a database first');
      return;
    }

    if (!naturalLanguage.trim()) {
      message.warning('Please enter a natural language query');
      return;
    }

    // Check if user mentioned export/save in their request
    const exportKeywords = ['导出', 'export', '保存', 'save', 'csv', 'json', '文件'];
    const containsExport = exportKeywords.some(keyword => 
      naturalLanguage.toLowerCase().includes(keyword.toLowerCase())
    );

    if (containsExport) {
      message.info({
        content: '提示：检测到导出需求。系统将先执行查询，查询完成后可使用"导出"按钮保存结果',
        duration: 5,
      });
    }

    setGeneratingSQL(true);
    setSqlResponse(null);
    setApprovedSql(null);
    clearResults();

    try {
      const request: NaturalQueryRequest = { natural_language: naturalLanguage };
      const response = await client.post<NaturalQueryResponse>(
        `/dbs/${selectedDb}/query/natural`,
        request
      );
      setSqlResponse(response.data);

      if (!response.data.isValid) {
        message.warning('Generated SQL has validation errors. Please review and edit.');
      }
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Failed to generate SQL');
    } finally {
      setGeneratingSQL(false);
    }
  };

  const handleApprove = async () => {
    if (!selectedDb || !sqlResponse) return;

    // Check if user mentioned export/save in their original request
    const exportKeywords = ['导出', 'export', '保存', 'save', 'csv', 'json', '文件'];
    const containsExport = exportKeywords.some(keyword => 
      naturalLanguage.toLowerCase().includes(keyword.toLowerCase())
    );

    // Set flag to auto-open export dialog after query completes
    if (containsExport) {
      console.log('Setting auto-export flag...');
      shouldAutoExportRef.current = true;
    }

    setApprovedSql(sqlResponse.generatedSql);
    await executeQuery(selectedDb, sqlResponse.generatedSql);
  };

  const handleReject = () => {
    setSqlResponse(null);
    setApprovedSql(null);
    clearResults();
  };

  const handleEditSql = (newSql: string) => {
    if (sqlResponse) {
      setSqlResponse({
        ...sqlResponse,
        generatedSql: newSql,
        isValid: true, // Assume edited SQL is intended to be valid
        validationError: null,
      });
    }
  };

  const handleClear = () => {
    setNaturalLanguage('');
    setSqlResponse(null);
    setApprovedSql(null);
    shouldAutoExportRef.current = false;
    clearResults();
  };

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Card>
          <Space style={{ width: '100%', justifyContent: 'space-between' }}>
            <Title level={2} style={{ margin: 0 }}>
              <BulbOutlined /> Natural Language Query
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
          title="Natural Language Input"
          extra={
            <Space>
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={handleGenerateSQL}
                loading={generatingSQL}
                disabled={!selectedDb || loadingDbs}
              >
                Generate SQL
              </Button>
              <Button icon={<ClearOutlined />} onClick={handleClear}>
                Clear
              </Button>
            </Space>
          }
        >
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Paragraph type="secondary" style={{ margin: 0 }}>
              Describe your query in plain English. The AI will generate a SQL query based on your database schema.
            </Paragraph>
            <TextArea
              value={naturalLanguage}
              onChange={(e) => setNaturalLanguage(e.target.value)}
              placeholder="Example: Show me all orders from the last month with customer names"
              rows={4}
              disabled={generatingSQL}
            />
          </Space>
        </Card>

        {sqlResponse && (
          <SqlApproval
            generatedSql={sqlResponse.generatedSql}
            explanation={sqlResponse.explanation}
            isValid={sqlResponse.isValid}
            validationError={sqlResponse.validationError}
            onApprove={handleApprove}
            onReject={handleReject}
            onEdit={handleEditSql}
            approveLoading={loading}
          />
        )}

        {approvedSql && !error && !data && (
          <Card>
            <Alert
              message="Executing Query"
              description={
                <Space direction="vertical">
                  <Text>Natural Language: {naturalLanguage}</Text>
                  <Text code>{approvedSql}</Text>
                </Space>
              }
              type="info"
              showIcon
            />
          </Card>
        )}

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
          <Card 
            title="Query Results"
            extra={
              <Button
                type="primary"
                icon={<DownloadOutlined />}
                onClick={() => setExportDialogVisible(true)}
                disabled={!data.rows || data.rows.length === 0}
              >
                Export
              </Button>
            }
          >
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <Alert
                message="Original Request"
                description={naturalLanguage}
                type="info"
                showIcon
              />
              <ResultsTable
                data={data.rows}
                columns={data.columns}
                loading={loading}
                executionTimeMs={data.executionTimeMs}
                rowCount={data.rowCount}
              />
            </Space>
          </Card>
        )}

        {!sqlResponse && !data && !error && !generatingSQL && (
          <Card>
            <Alert
              message="Ready to generate SQL"
              description="Describe your query in natural language and click Generate SQL to see the AI-generated query."
              type="info"
              showIcon
            />
          </Card>
        )}
      </Space>

      <ExportDialog
        visible={exportDialogVisible}
        onCancel={() => setExportDialogVisible(false)}
        data={data?.rows || null}
        naturalLanguage={naturalLanguage}
      />
    </div>
  );
};
