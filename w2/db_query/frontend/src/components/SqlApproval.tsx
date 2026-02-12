import React from 'react';
import { Card, Space, Button, Typography, Alert } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, EditOutlined } from '@ant-design/icons';
import { SqlEditor } from './SqlEditor';

const { Title, Text, Paragraph } = Typography;

interface SqlApprovalProps {
  generatedSql: string;
  explanation: string;
  isValid: boolean;
  validationError?: string | null;
  onApprove: () => void;
  onReject: () => void;
  onEdit: (newSql: string) => void;
  approveLoading?: boolean;
}

export const SqlApproval: React.FC<SqlApprovalProps> = ({
  generatedSql,
  explanation,
  isValid,
  validationError,
  onApprove,
  onReject,
  onEdit,
  approveLoading = false,
}) => {
  const [isEditing, setIsEditing] = React.useState(false);
  const [editedSql, setEditedSql] = React.useState(generatedSql);

  React.useEffect(() => {
    setEditedSql(generatedSql);
    setIsEditing(false);
  }, [generatedSql]);

  const handleSaveEdit = () => {
    onEdit(editedSql);
    setIsEditing(false);
  };

  const handleCancelEdit = () => {
    setEditedSql(generatedSql);
    setIsEditing(false);
  };

  return (
    <Card>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div>
          <Title level={4}>
            {isValid ? (
              <Space>
                <CheckCircleOutlined style={{ color: '#52c41a' }} />
                Generated SQL (Valid)
              </Space>
            ) : (
              <Space>
                <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
                Generated SQL (Invalid)
              </Space>
            )}
          </Title>
          <Paragraph type="secondary">{explanation}</Paragraph>
        </div>

        {!isValid && validationError && (
          <Alert
            message="SQL Validation Error"
            description={validationError}
            type="error"
            showIcon
          />
        )}

        <div>
          <Space style={{ marginBottom: 8 }}>
            <Text strong>SQL Query:</Text>
            {!isEditing && (
              <Button
                type="link"
                icon={<EditOutlined />}
                size="small"
                onClick={() => setIsEditing(true)}
              >
                Edit
              </Button>
            )}
          </Space>
          {isEditing ? (
            <>
              <SqlEditor
                value={editedSql}
                onChange={setEditedSql}
                height="200px"
              />
              <Space style={{ marginTop: 8 }}>
                <Button type="primary" size="small" onClick={handleSaveEdit}>
                  Save
                </Button>
                <Button size="small" onClick={handleCancelEdit}>
                  Cancel
                </Button>
              </Space>
            </>
          ) : (
            <SqlEditor
              value={generatedSql}
              onChange={() => {}}
              readOnly
              height="200px"
            />
          )}
        </div>

        <Space>
          <Button
            type="primary"
            icon={<CheckCircleOutlined />}
            onClick={onApprove}
            loading={approveLoading}
            disabled={!isValid}
          >
            Approve & Execute
          </Button>
          <Button icon={<CloseCircleOutlined />} onClick={onReject}>
            Reject
          </Button>
        </Space>
      </Space>
    </Card>
  );
};
