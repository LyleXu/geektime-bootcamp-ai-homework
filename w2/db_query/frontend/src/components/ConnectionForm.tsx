import React, { useState } from 'react';
import { Form, Input, Button, Switch, message } from 'antd';
import type { DatabaseConnectionRequest } from '../types/database';

interface ConnectionFormProps {
  initialName?: string;
  initialUrl?: string;
  initialIsActive?: boolean;
  onSubmit: (name: string, data: DatabaseConnectionRequest) => Promise<void>;
  onCancel?: () => void;
  submitText?: string;
  isUpdate?: boolean;
}

export const ConnectionForm: React.FC<ConnectionFormProps> = ({
  initialName = '',
  initialUrl = '',
  initialIsActive = false,
  onSubmit,
  onCancel,
  submitText = 'Connect',
  isUpdate = false,
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (values: { name: string; url: string; isActive: boolean }) => {
    setLoading(true);
    try {
      await onSubmit(values.name, {
        url: values.url,
        isActive: values.isActive,
      });
      message.success(`Database connection ${isUpdate ? 'updated' : 'created'} successfully`);
      if (!isUpdate) {
        form.resetFields();
      }
    } catch (error: any) {
      message.error(error.message || 'Failed to save database connection');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleSubmit}
      initialValues={{
        name: initialName,
        url: initialUrl,
        isActive: initialIsActive,
      }}
    >
      <Form.Item
        label="Connection Name"
        name="name"
        rules={[
          { required: true, message: 'Please enter a connection name' },
          { 
            pattern: /^[a-zA-Z0-9_-]+$/, 
            message: 'Name must contain only alphanumeric characters, underscores, and hyphens' 
          },
          { min: 1, max: 100, message: 'Name must be between 1 and 100 characters' },
        ]}
        extra={isUpdate ? 'Connection name cannot be changed' : 'Use only letters, numbers, underscores, and hyphens'}
      >
        <Input 
          placeholder="my_database" 
          disabled={isUpdate}
          autoComplete="off"
        />
      </Form.Item>

      <Form.Item
        label="PostgreSQL Connection URL"
        name="url"
        rules={[
          { required: true, message: 'Please enter a connection URL' },
          {
            pattern: /^(postgresql|postgres):\/\/.+/,
            message: 'URL must start with postgresql:// or postgres://',
          },
        ]}
        extra="Format: postgresql://user:password@host:port/database"
      >
        <Input.Password 
          placeholder="postgresql://user:password@localhost:5432/mydb"
          autoComplete="off"
        />
      </Form.Item>

      <Form.Item
        label="Set as Active Connection"
        name="isActive"
        valuePropName="checked"
        extra="Only one connection can be active at a time"
      >
        <Switch />
      </Form.Item>

      <Form.Item>
        <Button type="primary" htmlType="submit" loading={loading} style={{ marginRight: 8 }}>
          {submitText}
        </Button>
        {onCancel && (
          <Button onClick={onCancel} disabled={loading}>
            Cancel
          </Button>
        )}
      </Form.Item>
    </Form>
  );
};
