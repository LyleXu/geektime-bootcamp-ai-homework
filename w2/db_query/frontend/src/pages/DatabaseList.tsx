import React, { useState, useEffect } from 'react';
import { useCreate, useDelete } from '@refinedev/core';
import { Card, Button, List, Typography, Space, Tag, Modal, Spin, Empty, message, Popconfirm } from 'antd';
import { PlusOutlined, DatabaseOutlined, CheckCircleOutlined, DeleteOutlined, ReloadOutlined } from '@ant-design/icons';
import type { DatabaseConnection, DatabaseConnectionRequest } from '../types/database';
import { ConnectionForm } from '../components/ConnectionForm';
import { SchemaTree } from '../components/SchemaTree';
import { client } from '../api/client';
import type { SchemaBrowserResponse } from '../types/schema';

const { Title, Text } = Typography;

export const DatabaseList: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedDatabase, setSelectedDatabase] = useState<string | null>(null);
  const [schemaData, setSchemaData] = useState<SchemaBrowserResponse | null>(null);
  const [schemaLoading, setSchemaLoading] = useState(false);
  const [databases, setDatabases] = useState<DatabaseConnection[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshKey, setRefreshKey] = useState(0);

  // Fetch databases
  useEffect(() => {
    const fetchDatabases = async () => {
      setIsLoading(true);
      try {
        const response = await client.get<{ databases: DatabaseConnection[]; total: number }>('/dbs');
        setDatabases(response.data.databases);
      } catch (error: any) {
        message.error(error.response?.data?.message || 'Failed to load databases');
        setDatabases([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDatabases();
  }, [refreshKey]);

  const refresh = () => {
    setRefreshKey(prev => prev + 1);
  };

  const { mutate: createConnection } = useCreate();
  const { mutate: deleteConnection } = useDelete();

  const handleAddConnection = async (name: string, connectionData: DatabaseConnectionRequest) => {
    return new Promise<void>((resolve, reject) => {
      createConnection(
        {
          resource: 'databases',
          values: connectionData,
          meta: {
            name,
          },
        },
        {
          onSuccess: () => {
            setIsModalOpen(false);
            refresh();
            resolve();
          },
          onError: (error: any) => {
            reject(error);
          },
        }
      );
    });
  };

  const handleDeleteConnection = (id: number) => {
    deleteConnection(
      {
        resource: 'databases',
        id,
      },
      {
        onSuccess: () => {
          message.success('Database connection deleted successfully');
          refresh();
          if (selectedDatabase) {
            setSelectedDatabase(null);
            setSchemaData(null);
          }
        },
        onError: (error: any) => {
          message.error(error.message || 'Failed to delete database connection');
        },
      }
    );
  };

  const handleViewSchema = async (name: string) => {
    setSelectedDatabase(name);
    setSchemaLoading(true);
    try {
      const response = await client.get<SchemaBrowserResponse>(`/dbs/${name}`);
      setSchemaData(response.data);
    } catch (error: any) {
      message.error(error.response?.data?.message || 'Failed to load schema metadata');
      setSchemaData(null);
    } finally {
      setSchemaLoading(false);
    }
  };

  const handleRefreshSchema = async () => {
    if (selectedDatabase) {
      await handleViewSchema(selectedDatabase);
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Card>
          <Space style={{ width: '100%', justifyContent: 'space-between' }}>
            <Title level={2} style={{ margin: 0 }}>
              <DatabaseOutlined /> Database Connections
            </Title>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setIsModalOpen(true)}
            >
              Add Connection
            </Button>
          </Space>
        </Card>

        <Card>
          {isLoading ? (
            <div style={{ textAlign: 'center', padding: '48px' }}>
              <Spin size="large" />
            </div>
          ) : databases.length === 0 ? (
            <Empty
              description="No database connections"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            >
              <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalOpen(true)}>
                Add Your First Connection
              </Button>
            </Empty>
          ) : (
            <List
              dataSource={databases}
              renderItem={(db) => (
                <List.Item
                  key={db.id}
                  actions={[
                    <Button
                      type="link"
                      onClick={() => handleViewSchema(db.name)}
                    >
                      View Schema
                    </Button>,
                    <Popconfirm
                      title="Delete Connection"
                      description="Are you sure you want to delete this connection? All schema metadata will be removed."
                      onConfirm={() => handleDeleteConnection(db.id!)}
                      okText="Delete"
                      cancelText="Cancel"
                      okButtonProps={{ danger: true }}
                    >
                      <Button type="link" danger icon={<DeleteOutlined />}>
                        Delete
                      </Button>
                    </Popconfirm>,
                  ]}
                >
                  <List.Item.Meta
                    avatar={<DatabaseOutlined style={{ fontSize: '24px' }} />}
                    title={
                      <Space>
                        <Text strong>{db.name}</Text>
                        {db.isActive && (
                          <Tag icon={<CheckCircleOutlined />} color="success">
                            Active
                          </Tag>
                        )}
                      </Space>
                    }
                    description={
                      <Space direction="vertical" size="small">
                        <Text type="secondary">
                          Created: {new Date(db.createdAt!).toLocaleString()}
                        </Text>
                        {db.updatedAt && db.updatedAt !== db.createdAt && (
                          <Text type="secondary">
                            Updated: {new Date(db.updatedAt).toLocaleString()}
                          </Text>
                        )}
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          )}
        </Card>

        {selectedDatabase && (
          <Card
            title={
              <Space>
                <Text>Schema: {selectedDatabase}</Text>
                <Button
                  type="link"
                  icon={<ReloadOutlined />}
                  onClick={handleRefreshSchema}
                  loading={schemaLoading}
                >
                  Refresh
                </Button>
              </Space>
            }
          >
            {schemaLoading ? (
              <div style={{ textAlign: 'center', padding: '48px' }}>
                <Spin size="large" tip="Loading schema metadata..." />
              </div>
            ) : schemaData ? (
              <>
                <Text type="secondary" style={{ marginBottom: '16px', display: 'block' }}>
                  {schemaData.total} tables and views
                </Text>
                <SchemaTree tables={schemaData.tables} />
              </>
            ) : (
              <Empty description="No schema data available" />
            )}
          </Card>
        )}
      </Space>

      <Modal
        title="Add Database Connection"
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        footer={null}
        width={600}
      >
        <ConnectionForm
          onSubmit={handleAddConnection}
          onCancel={() => setIsModalOpen(false)}
        />
      </Modal>
    </div>
  );
};
