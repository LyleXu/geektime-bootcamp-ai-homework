import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Layout, Button, Space, Typography, Alert, message, Spin, Modal, Popconfirm, List, Tabs, Input } from 'antd';
import { PlayCircleOutlined, ClearOutlined, DatabaseOutlined, PlusOutlined, DeleteOutlined, TableOutlined, ReloadOutlined, MessageOutlined, CodeOutlined, DownloadOutlined } from '@ant-design/icons';
import { SqlEditor } from '../components/SqlEditor';
import { ResultsTable } from '../components/ResultsTable';
import { SchemaTree } from '../components/SchemaTree';
import { ConnectionForm } from '../components/ConnectionForm';
import { ExportDialog } from '../components/ExportDialog';
import { useQuery } from '../hooks/useQuery';
import { client } from '../api/client';
import type { DatabaseConnection, DatabaseConnectionRequest } from '../types/database';
import type { SchemaMetadata } from '../types/schema';
import type { NaturalQueryResponse } from '../types/query';

const { Sider, Content } = Layout;
const { Title, Text } = Typography;
const { TextArea } = Input;

export const DatabaseExplorer: React.FC = () => {
  const [sql, setSql] = useState('SELECT * FROM public.users;');
  const [databases, setDatabases] = useState<DatabaseConnection[]>([]);
  const [selectedDb, setSelectedDb] = useState<string | null>(null);
  const [loadingDbs, setLoadingDbs] = useState(true);
  const [schema, setSchema] = useState<SchemaMetadata[]>([]);
  const [loadingSchema, setLoadingSchema] = useState(false);
  const [addModalVisible, setAddModalVisible] = useState(false);
  const [queryMode, setQueryMode] = useState<'sql' | 'natural'>('sql');
  const [naturalLanguageQuery, setNaturalLanguageQuery] = useState('');
  const [exportDialogVisible, setExportDialogVisible] = useState(false);
  
  // Use ref to track if we should auto-open export dialog
  const shouldAutoExportRef = useRef(false);
  
  const { executeQuery, data, loading, error, clearResults } = useQuery();

  // Calculate schema statistics
  const schemaStats = useMemo(() => {
    const tables = schema.filter(s => s.tableType === 'TABLE').length;
    const views = schema.filter(s => s.tableType === 'VIEW').length;
    const totalEstimatedRows = schema.reduce((sum, s) => sum + (s.estimatedRows || 0), 0);
    // Show query result count if available, otherwise show total estimated rows
    const displayRows = data?.rowCount ?? totalEstimatedRows;
    const executionTime = data?.executionTimeMs;
    return { tables, views, displayRows, executionTime };
  }, [schema, data]);

  // Load databases on mount
  const loadDatabases = async () => {
    setLoadingDbs(true);
    try {
      const response = await client.get<{ databases: DatabaseConnection[]; total: number }>('/dbs');
      setDatabases(response.data.databases);
      
      // Auto-select first database if none selected
      if (!selectedDb && response.data.databases.length > 0) {
        setSelectedDb(response.data.databases[0].name);
      }
    } catch (err: any) {
      message.error('Failed to load databases');
    } finally {
      setLoadingDbs(false);
    }
  };

  useEffect(() => {
    loadDatabases();
  }, []);

  // Load schema when database changes
  useEffect(() => {
    if (!selectedDb) {
      setSchema([]);
      return;
    }

    const loadSchema = async () => {
      setLoadingSchema(true);
      try {
        const response = await client.get<{ databaseName: string; tables: SchemaMetadata[]; total: number }>(`/dbs/${selectedDb}`);
        setSchema(response.data.tables);
      } catch (err: any) {
        message.error('Failed to load schema metadata');
        setSchema([]);
      } finally {
        setLoadingSchema(false);
      }
    };
    loadSchema();
  }, [selectedDb]);

  // Auto-open export dialog when data is loaded and shouldAutoExport flag is set
  useEffect(() => {
    if (shouldAutoExportRef.current && data && data.rows && data.rows.length > 0 && !loading) {
      console.log('Auto-opening export dialog from DatabaseExplorer...');
      // Small delay to ensure UI is updated
      const timer = setTimeout(() => {
        setExportDialogVisible(true);
        shouldAutoExportRef.current = false; // Reset flag
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [data, loading]);

  const handleExecute = async () => {
    if (!selectedDb) {
      message.warning('Please select a database first');
      return;
    }
    
    if (queryMode === 'natural') {
      // Handle natural language query
      if (!naturalLanguageQuery.trim()) {
        message.warning('Please enter a natural language query');
        return;
      }
      
      // Check if user mentioned export/save in their request
      const exportKeywords = ['导出', 'export', '保存', 'save', 'csv', 'json', '文件'];
      const containsExport = exportKeywords.some(keyword => 
        naturalLanguageQuery.toLowerCase().includes(keyword.toLowerCase())
      );

      if (containsExport) {
        message.info({
          content: '提示：检测到导出需求。系统将先执行查询，查询完成后自动打开导出对话框',
          duration: 5,
        });
        // Set flag to auto-open export dialog after query completes
        shouldAutoExportRef.current = true;
      }
      
      try {
        // First, convert natural language to SQL
        const nlResponse = await client.post<NaturalQueryResponse>(
          `/dbs/${selectedDb}/query/natural`,
          { natural_language: naturalLanguageQuery }
        );
        
        if (!nlResponse.data.isValid) {
          message.error(nlResponse.data.validationError || 'Failed to generate valid SQL');
          shouldAutoExportRef.current = false; // Reset flag on error
          return;
        }
        
        // Show the generated SQL and explanation
        message.info({
          content: (
            <div>
              <div><strong>Generated SQL:</strong></div>
              <div style={{ fontFamily: 'monospace', fontSize: '12px', marginTop: '4px' }}>
                {nlResponse.data.generatedSql}
              </div>
              {nlResponse.data.explanation && (
                <>
                  <div style={{ marginTop: '8px' }}><strong>Explanation:</strong></div>
                  <div style={{ fontSize: '12px', marginTop: '4px' }}>
                    {nlResponse.data.explanation}
                  </div>
                </>
              )}
            </div>
          ),
          duration: 8,
        });
        
        // Execute the generated SQL
        await executeQuery(selectedDb, nlResponse.data.generatedSql);
      } catch (err: any) {
        shouldAutoExportRef.current = false; // Reset flag on error
        const errorData = err.response?.data;
        if (errorData?.detail) {
          message.error(errorData.detail);
        } else {
          message.error('Failed to process natural language query');
        }
      }
    } else {
      // Handle manual SQL query
      await executeQuery(selectedDb, sql);
    }
  };

  const handleClear = () => {
    shouldAutoExportRef.current = false;
    clearResults();
  };

  const handleAddDatabase = async (name: string, data: DatabaseConnectionRequest) => {
    try {
      await client.put(`/dbs/${name}`, data);
      setAddModalVisible(false);
      await loadDatabases();
      setSelectedDb(name);
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Failed to add database');
    }
  };

  const handleDeleteDatabase = async (dbId: number, dbName: string) => {
    try {
      await client.delete(`/dbs/${dbId}`);
      message.success('Database deleted successfully');
      await loadDatabases();
      if (selectedDb === dbName) {
        setSelectedDb(databases.length > 1 ? databases.find(db => db.name !== dbName)?.name || null : null);
      }
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Failed to delete database');
    }
  };

  const handleRefreshSchema = async () => {
    if (!selectedDb) return;
    setLoadingSchema(true);
    try {
      const response = await client.get<{ databaseName: string; tables: SchemaMetadata[]; total: number }>(`/dbs/${selectedDb}`);
      setSchema(response.data.tables);
      message.success('Schema refreshed successfully');
    } catch (err: any) {
      message.error('Failed to refresh schema');
    } finally {
      setLoadingSchema(false);
    }
  };


  return (
    <>
      <Layout style={{ 
        height: 'calc(100vh - 64px)', 
        background: '#f5f5f7',
      }}>
        {/* Left Sidebar - Database List */}
        <Sider 
          width={280} 
          theme="light" 
          style={{ 
            background: '#fbfbfd',
            borderRight: '1px solid #e5e5e7',
            overflow: 'auto',
            height: '100%',
            boxShadow: '2px 0 8px rgba(0,0,0,0.02)',
          }}
        >
          <div style={{ padding: '24px 16px' }}>
            <Space direction="vertical" style={{ width: '100%' }} size={16}>
              {/* Header */}
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                marginBottom: '8px',
              }}>
                <Text style={{ 
                  fontSize: '15px',
                  fontWeight: 600,
                  color: '#1d1d1f',
                  letterSpacing: '-0.01em',
                }}>
                  DB Query Tool
                </Text>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  size="small"
                  onClick={() => setAddModalVisible(true)}
                  style={{
                    borderRadius: '6px',
                    background: '#0071e3',
                    border: 'none',
                    fontSize: '12px',
                    height: '28px',
                    padding: '0 12px',
                  }}
                >
                  Add
                </Button>
              </div>

              {/* Database List */}
              {loadingDbs ? (
                <div style={{ textAlign: 'center', padding: '40px 0' }}>
                  <Spin />
                </div>
              ) : databases.length === 0 ? (
                <Alert
                  message="No databases"
                  description="Click Add to connect your first database."
                  type="info"
                  showIcon
                  style={{
                    background: '#f0f0f2',
                    border: 'none',
                    borderRadius: '10px',
                    fontSize: '13px',
                  }}
                />
              ) : (
                <List
                  dataSource={databases}
                  renderItem={(db) => (
                    <List.Item
                      key={db.id}
                      style={{
                        border: 'none',
                        padding: '0',
                        marginBottom: '6px',
                      }}
                    >
                      <div
                        onClick={() => setSelectedDb(db.name)}
                        style={{
                          width: '100%',
                          padding: '12px 14px',
                          background: selectedDb === db.name ? '#e8f4fd' : 'white',
                          border: `1px solid ${selectedDb === db.name ? '#0071e3' : '#e5e5e7'}`,
                          borderRadius: '10px',
                          cursor: 'pointer',
                          transition: 'all 0.2s',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                        }}
                        onMouseEnter={(e) => {
                          if (selectedDb !== db.name) {
                            e.currentTarget.style.background = '#f5f5f7';
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (selectedDb !== db.name) {
                            e.currentTarget.style.background = 'white';
                          }
                        }}
                      >
                        <Space size={10}>
                          <DatabaseOutlined style={{ 
                            fontSize: '16px',
                            color: selectedDb === db.name ? '#0071e3' : '#86868b',
                          }} />
                          <div>
                            <Text style={{ 
                              fontSize: '14px',
                              fontWeight: selectedDb === db.name ? 600 : 500,
                              color: selectedDb === db.name ? '#0071e3' : '#1d1d1f',
                              display: 'block',
                            }}>
                              {db.name}
                            </Text>
                            {db.isActive && (
                              <Text style={{ 
                                fontSize: '11px',
                                color: '#34c759',
                                fontWeight: 500,
                              }}>
                                Active
                              </Text>
                            )}
                          </div>
                        </Space>
                        <Popconfirm
                          title="Delete Database"
                          description="Are you sure you want to delete this database connection?"
                          onConfirm={(e) => {
                            e?.stopPropagation();
                            handleDeleteDatabase(db.id!, db.name);
                          }}
                          okText="Delete"
                          cancelText="Cancel"
                          okButtonProps={{ danger: true }}
                        >
                          <Button
                            type="text"
                            danger
                            size="small"
                            icon={<DeleteOutlined />}
                            onClick={(e) => e.stopPropagation()}
                            style={{
                              opacity: 0.6,
                              fontSize: '12px',
                            }}
                          />
                        </Popconfirm>
                      </div>
                    </List.Item>
                  )}
                />
              )}
            </Space>
          </div>
        </Sider>

        {/* Main Content Area */}
        <Layout style={{ background: '#f5f5f7' }}>
          {/* Schema Tree Sidebar */}
          <Sider 
            width={340}
            theme="light" 
            style={{ 
              background: 'white',
              borderRight: '1px solid #e5e5e7',
              overflow: 'hidden',
              height: '100%',
            }}
          >
            <div style={{ 
              padding: '24px 20px',
              height: '100%',
              overflow: 'auto',
            }}>
              <Space direction="vertical" style={{ width: '100%' }} size={16}>
                {selectedDb ? (
                  <div style={{
                    background: 'linear-gradient(135deg, #fef9e7 0%, #fffbeb 100%)',
                    border: '1px solid rgba(245, 158, 11, 0.3)',
                    borderRadius: '12px',
                    padding: '16px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    boxShadow: '0 2px 12px rgba(245, 158, 11, 0.1)',
                  }}>
                    <div>
                      <Text style={{ 
                        fontSize: '11px',
                        color: '#d97706',
                        fontWeight: 600,
                        display: 'block',
                        marginBottom: '6px',
                        letterSpacing: '0.8px',
                        textTransform: 'uppercase',
                      }}>
                        Schema
                      </Text>
                      <Text style={{ 
                        fontSize: '16px',
                        fontWeight: 600,
                        color: '#d97706',
                        letterSpacing: '-0.01em',
                      }}>
                        <DatabaseOutlined style={{ marginRight: '8px', fontSize: '18px' }} />
                        {selectedDb}
                      </Text>
                    </div>
                    <Button
                      type="text"
                      icon={<ReloadOutlined />}
                      onClick={handleRefreshSchema}
                      loading={loadingSchema}
                      style={{
                        color: '#d97706',
                        borderColor: '#f59e0b',
                        border: '1px solid',
                        borderRadius: '8px',
                        height: '32px',
                        background: 'white',
                        fontWeight: 500,
                        transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.background = '#f59e0b';
                        e.currentTarget.style.color = 'white';
                        e.currentTarget.style.transform = 'translateY(-1px)';
                        e.currentTarget.style.boxShadow = '0 4px 8px rgba(245, 158, 11, 0.3)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = 'white';
                        e.currentTarget.style.color = '#d97706';
                        e.currentTarget.style.transform = 'translateY(0)';
                        e.currentTarget.style.boxShadow = 'none';
                      }}
                    >
                      Refresh
                    </Button>
                  </div>
                ) : (
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}>
                    <Text style={{ 
                      fontSize: '15px',
                      fontWeight: 600,
                      color: '#1d1d1f',
                      letterSpacing: '-0.01em',
                    }}>
                      <TableOutlined style={{ marginRight: '8px' }} />
                      Schema
                    </Text>
                  </div>
                )}
                
                {!selectedDb ? (
                  <Alert
                    message="No database selected"
                    description="Select a database to view its schema."
                    type="info"
                    showIcon
                    style={{
                      background: '#f0f0f2',
                      border: 'none',
                      borderRadius: '10px',
                    }}
                  />
                ) : loadingSchema ? (
                  <div style={{ textAlign: 'center', padding: '40px 0' }}>
                    <Spin tip="Loading schema..." />
                  </div>
                ) : (
                  <SchemaTree 
                    tables={schema} 
                    loading={loadingSchema}
                    showSearch={true}
                    expandAll={true}
                  />
                )}
              </Space>
            </div>
          </Sider>

          {/* Query Editor and Results */}
          <Content style={{ 
            display: 'flex', 
            flexDirection: 'column', 
            height: '100%',
            background: '#f5f5f7',
          }}>
            {/* Statistics Section */}
            {selectedDb && schema.length > 0 && (
              <div style={{ 
                flex: '0 0 auto', 
                padding: '24px 24px 0 24px',
              }}>
                <div style={{
                  display: 'flex',
                  gap: '12px',
                }}>
                  {/* Tables Card */}
                  <div style={{
                    flex: 1,
                    background: 'white',
                    border: '1px solid #e5e5e7',
                    borderRadius: '8px',
                    padding: '12px 20px',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                  }}>
                    <div style={{
                      fontSize: '11px',
                      fontWeight: 600,
                      color: '#86868b',
                      letterSpacing: '0.5px',
                      marginBottom: '4px',
                    }}>
                      TABLES
                    </div>
                    <div style={{
                      fontSize: '24px',
                      fontWeight: 600,
                      color: '#1d1d1f',
                    }}>
                      {schemaStats.tables}
                    </div>
                  </div>

                  {/* Views Card */}
                  <div style={{
                    flex: 1,
                    background: 'white',
                    border: '1px solid #e5e5e7',
                    borderRadius: '8px',
                    padding: '12px 20px',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                  }}>
                    <div style={{
                      fontSize: '11px',
                      fontWeight: 600,
                      color: '#86868b',
                      letterSpacing: '0.5px',
                      marginBottom: '4px',
                    }}>
                      VIEWS
                    </div>
                    <div style={{
                      fontSize: '24px',
                      fontWeight: 600,
                      color: '#1d1d1f',
                    }}>
                      {schemaStats.views}
                    </div>
                  </div>

                  {/* Rows Card */}
                  <div style={{
                    flex: 1,
                    background: 'white',
                    border: '1px solid #e5e5e7',
                    borderRadius: '8px',
                    padding: '12px 20px',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                  }}>
                    <div style={{
                      fontSize: '11px',
                      fontWeight: 600,
                      color: '#86868b',
                      letterSpacing: '0.5px',
                      marginBottom: '4px',
                    }}>
                      ROWS
                    </div>
                    <div style={{
                      fontSize: '24px',
                      fontWeight: 600,
                      color: '#1d1d1f',
                    }}>
                      {schemaStats.displayRows.toLocaleString()}
                    </div>
                  </div>

                  {/* Time Card */}
                  <div style={{
                    flex: 1,
                    background: 'white',
                    border: '1px solid #e5e5e7',
                    borderRadius: '8px',
                    padding: '12px 20px',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                  }}>
                    <div style={{
                      fontSize: '11px',
                      fontWeight: 600,
                      color: '#86868b',
                      letterSpacing: '0.5px',
                      marginBottom: '4px',
                    }}>
                      TIME
                    </div>
                    <div style={{
                      fontSize: '24px',
                      fontWeight: 600,
                      color: '#1d1d1f',
                    }}>
                      {schemaStats.executionTime !== undefined 
                        ? `${schemaStats.executionTime.toFixed(2)}ms` 
                        : '-'}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* SQL Editor Section */}
            <div style={{ 
              flex: '0 0 auto', 
              padding: '24px',
            }}>
              <div style={{
                background: 'white',
                borderRadius: '16px',
                padding: '24px',
                boxShadow: '0 2px 16px rgba(0,0,0,0.04)',
                border: '1px solid #e5e5e7',
              }}>
                <Space direction="vertical" style={{ width: '100%' }} size={16}>
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center' 
                  }}>
                    <Title level={5} style={{ 
                      margin: 0,
                      fontSize: '17px',
                      fontWeight: 600,
                      color: '#1d1d1f',
                      letterSpacing: '-0.02em',
                    }}>
                      Query Editor
                    </Title>
                    <Space size={12}>
                      <Button
                        type="primary"
                        icon={<PlayCircleOutlined />}
                        onClick={handleExecute}
                        loading={loading}
                        disabled={!selectedDb}
                        size="large"
                        style={{
                          borderRadius: '8px',
                          background: '#0071e3',
                          border: 'none',
                          fontWeight: 500,
                          height: '40px',
                          boxShadow: '0 2px 8px rgba(0,113,227,0.2)',
                        }}
                      >
                        Execute
                      </Button>
                      <Button 
                        icon={<ClearOutlined />} 
                        onClick={handleClear}
                        size="large"
                        style={{
                          borderRadius: '8px',
                          border: '1px solid #e5e5e7',
                          background: 'white',
                          height: '40px',
                        }}
                      >
                        Clear
                      </Button>
                    </Space>
                  </div>
                  
                  <Tabs
                    activeKey={queryMode}
                    onChange={(key) => setQueryMode(key as 'sql' | 'natural')}
                    items={[
                      {
                        key: 'sql',
                        label: (
                          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <CodeOutlined />
                            Manual SQL
                          </span>
                        ),
                        children: (
                          <div style={{
                            borderRadius: '10px',
                            overflow: 'hidden',
                            border: '1px solid #e5e5e7',
                          }}>
                            <SqlEditor
                              value={sql}
                              onChange={setSql}
                              onExecute={handleExecute}
                              height="200px"
                            />
                          </div>
                        ),
                      },
                      {
                        key: 'natural',
                        label: (
                          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <MessageOutlined />
                            Natural Language
                          </span>
                        ),
                        children: (
                          <div style={{
                            borderRadius: '10px',
                            overflow: 'hidden',
                            border: '1px solid #e5e5e7',
                          }}>
                            <TextArea
                              value={naturalLanguageQuery}
                              onChange={(e) => setNaturalLanguageQuery(e.target.value)}
                              placeholder="Describe your query in natural language, e.g., 'Show me all users created in the last 30 days'"
                              rows={8}
                              style={{
                                fontSize: '14px',
                                fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                                resize: 'none',
                                border: 'none',
                                borderRadius: '10px',
                              }}
                            />
                          </div>
                        ),
                      },
                    ]}
                    style={{
                      marginTop: '16px',
                    }}
                  />

                  {error && (
                    <Alert
                      message="Query Error"
                      description={error}
                      type="error"
                      showIcon
                      closable
                      onClose={clearResults}
                      style={{
                        borderRadius: '10px',
                        border: 'none',
                      }}
                    />
                  )}
                </Space>
              </div>
            </div>

            {/* Results Section */}
            <div style={{ 
              flex: '1 1 auto', 
              overflow: 'auto',
              padding: '0 24px 24px 24px',
            }}>
              {data ? (
                <div style={{
                  background: 'white',
                  borderRadius: '16px',
                  padding: '24px',
                  boxShadow: '0 2px 16px rgba(0,0,0,0.04)',
                  border: '1px solid #e5e5e7',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                }}>
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center',
                    marginBottom: '16px',
                  }}>
                    <Title level={5} style={{ 
                      margin: 0,
                      fontSize: '17px',
                      fontWeight: 600,
                      color: '#1d1d1f',
                      letterSpacing: '-0.02em',
                    }}>
                      Results
                    </Title>
                    <Space size={16}>
                      <Text type="secondary" style={{ fontSize: '14px' }}>
                        {data.rowCount} {data.rowCount === 1 ? 'row' : 'rows'} · {data.executionTimeMs.toFixed(0)}ms
                      </Text>
                      <Button
                        type="primary"
                        icon={<DownloadOutlined />}
                        onClick={() => setExportDialogVisible(true)}
                        disabled={!data.rows || data.rows.length === 0}
                        style={{
                          borderRadius: '6px',
                          background: '#0071e3',
                          border: 'none',
                          fontSize: '13px',
                          height: '32px',
                        }}
                      >
                        Export
                      </Button>
                    </Space>
                  </div>
                  <div style={{ flex: 1, overflow: 'auto' }}>
                    <ResultsTable
                      data={data.rows}
                      columns={data.columns}
                      loading={loading}
                      executionTimeMs={data.executionTimeMs}
                      rowCount={data.rowCount}
                    />
                  </div>
                </div>
              ) : (
                <div style={{
                  height: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: 'white',
                  borderRadius: '16px',
                  border: '1px solid #e5e5e7',
                }}>
                  <div style={{ textAlign: 'center', padding: '60px 40px' }}>
                    <DatabaseOutlined style={{ 
                      fontSize: '48px', 
                      color: '#d2d2d7',
                      marginBottom: '16px',
                      display: 'block',
                    }} />
                    <Text style={{ 
                      fontSize: '17px',
                      color: '#86868b',
                      display: 'block',
                      fontWeight: 500,
                    }}>
                      Execute a query to see results
                    </Text>
                    <Text style={{ 
                      fontSize: '14px',
                      color: '#86868b',
                      display: 'block',
                      marginTop: '8px',
                    }}>
                      Write your SQL query above and click Execute
                    </Text>
                  </div>
                </div>
              )}
            </div>
          </Content>
        </Layout>
      </Layout>

      {/* Add Database Modal */}
      <Modal
        title={
          <Text style={{ fontSize: '17px', fontWeight: 600 }}>
            Add Database Connection
          </Text>
        }
        open={addModalVisible}
        onCancel={() => setAddModalVisible(false)}
        footer={null}
        width={600}
        styles={{
          body: { paddingTop: '24px' },
        }}
      >
        <ConnectionForm
          onSubmit={handleAddDatabase}
          onCancel={() => setAddModalVisible(false)}
          submitText="Add Database"
        />
      </Modal>

      {/* Export Dialog */}
      <ExportDialog
        visible={exportDialogVisible}
        onCancel={() => setExportDialogVisible(false)}
        data={data?.rows || null}
        naturalLanguage={queryMode === 'natural' ? naturalLanguageQuery : undefined}
      />
    </>
  );
};
