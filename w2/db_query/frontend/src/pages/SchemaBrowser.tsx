import React, { useState, useEffect } from 'react';
import { Card, Button, Space, Typography, Alert, Select, Spin, message, Statistic, Row, Col, Divider } from 'antd';
import { DatabaseOutlined, ReloadOutlined, TableOutlined, EyeOutlined } from '@ant-design/icons';
import { SchemaTree } from '../components/SchemaTree';
import { useActiveDb } from '../hooks/useActiveDb';
import { client } from '../api/client';
import type { DatabaseConnection } from '../types/database';
import type { SchemaBrowserResponse } from '../types/schema';

const { Title, Text } = Typography;

export const SchemaBrowser: React.FC = () => {
  const [databases, setDatabases] = useState<DatabaseConnection[]>([]);
  const [selectedDb, setSelectedDb] = useState<string | null>(null);
  const [loadingDbs, setLoadingDbs] = useState(true);
  const [loadingSchema, setLoadingSchema] = useState(false);
  const [schemaData, setSchemaData] = useState<SchemaBrowserResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

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

  // Load schema when database is selected
  useEffect(() => {
    if (selectedDb) {
      loadSchema(selectedDb);
    }
  }, [selectedDb]);

  const loadSchema = async (dbName: string) => {
    setLoadingSchema(true);
    setError(null);
    setSchemaData(null);

    try {
      const response = await client.get<SchemaBrowserResponse>(`/dbs/${dbName}`);
      setSchemaData(response.data);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to load schema metadata';
      setError(errorMsg);
      message.error(errorMsg);
    } finally {
      setLoadingSchema(false);
    }
  };

  const handleRefresh = () => {
    if (selectedDb) {
      message.info('Refreshing schema metadata...');
      loadSchema(selectedDb);
    }
  };

  const handleDatabaseChange = (value: string) => {
    setSelectedDb(value);
  };

  const totalTables = schemaData?.tables.filter(t => t.tableType === 'TABLE').length || 0;
  const totalViews = schemaData?.tables.filter(t => t.tableType === 'VIEW').length || 0;
  const totalColumns = schemaData?.tables.reduce((sum, t) => sum + t.columns.length, 0) || 0;
  const totalPKs = schemaData?.tables.reduce((sum, t) => sum + t.columns.filter(c => c.isPrimaryKey).length, 0) || 0;
  const totalFKs = schemaData?.tables.reduce((sum, t) => sum + t.foreignKeys.length, 0) || 0;

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Card>
          <Space style={{ width: '100%', justifyContent: 'space-between' }}>
            <Title level={2} style={{ margin: 0 }}>
              <DatabaseOutlined /> Schema Browser
            </Title>
            {selectedDb && (
              <Button
                type="primary"
                icon={<ReloadOutlined />}
                onClick={handleRefresh}
                loading={loadingSchema}
              >
                Refresh Schema
              </Button>
            )}
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
                placeholder="Choose a database to browse"
                value={selectedDb}
                onChange={handleDatabaseChange}
                loading={loadingDbs}
                options={databases.map((db) => ({
                  label: (
                    <Space>
                      <DatabaseOutlined />
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

        {error && (
          <Alert
            message="Error Loading Schema"
            description={error}
            type="error"
            showIcon
            closable
            onClose={() => setError(null)}
          />
        )}

        {loadingSchema && (
          <Card>
            <div style={{ textAlign: 'center', padding: '48px' }}>
              <Spin size="large" />
              <div style={{ marginTop: '16px' }}>
                <Text type="secondary">Loading schema metadata...</Text>
              </div>
            </div>
          </Card>
        )}

        {schemaData && !loadingSchema && (
          <>
            <Card title="Schema Statistics">
              <Row gutter={16}>
                <Col span={8}>
                  <Statistic
                    title="Tables"
                    value={totalTables}
                    prefix={<TableOutlined />}
                    valueStyle={{ color: '#1890ff' }}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="Views"
                    value={totalViews}
                    prefix={<EyeOutlined />}
                    valueStyle={{ color: '#52c41a' }}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="Total Columns"
                    value={totalColumns}
                    valueStyle={{ color: '#722ed1' }}
                  />
                </Col>
              </Row>
              <Divider />
              <Row gutter={16}>
                <Col span={12}>
                  <Statistic
                    title="Primary Keys"
                    value={totalPKs}
                    valueStyle={{ color: '#faad14' }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="Foreign Keys"
                    value={totalFKs}
                    valueStyle={{ color: '#722ed1' }}
                  />
                </Col>
              </Row>
            </Card>

            <Card title="Schema Details">
              <SchemaTree 
                tables={schemaData.tables} 
                loading={loadingSchema}
                showSearch={true}
                expandAll={false}
              />
            </Card>
          </>
        )}

        {!selectedDb && !loadingDbs && databases.length > 0 && (
          <Card>
            <Alert
              message="Select a database"
              description="Choose a database from the dropdown above to browse its schema."
              type="info"
              showIcon
            />
          </Card>
        )}
      </Space>
    </div>
  );
};
