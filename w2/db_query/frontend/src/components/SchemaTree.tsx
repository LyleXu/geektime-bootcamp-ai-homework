import React, { useState, useMemo, useEffect } from 'react';
import { Tree, Typography, Space, Tag, Input, Badge, Tooltip } from 'antd';
import type { DataNode } from 'antd/es/tree';
import { DatabaseOutlined, TableOutlined, EyeOutlined, KeyOutlined, LinkOutlined, SearchOutlined } from '@ant-design/icons';
import type { SchemaMetadata, ColumnDef } from '../types/schema';

const { Text } = Typography;
const { Search } = Input;

interface SchemaTreeProps {
  tables: SchemaMetadata[];
  loading?: boolean;
  showSearch?: boolean;
  expandAll?: boolean;
}

export const SchemaTree: React.FC<SchemaTreeProps> = ({ 
  tables, 
  loading = false, 
  showSearch = false,
  expandAll = false 
}) => {
  const [searchText, setSearchText] = useState('');
  const [expandedKeys, setExpandedKeys] = useState<React.Key[]>([]);
  const [autoExpandParent, setAutoExpandParent] = useState(false);

  // Auto-expand all tables when expandAll is true
  useEffect(() => {
    if (expandAll && tables.length > 0) {
      const allKeys = tables.map((table) => table.tableName);
      setExpandedKeys(allKeys);
    }
  }, [tables, expandAll]);

  // Filter tables based on search text
  const filteredTables = useMemo(() => {
    if (!searchText) return tables;
    
    const lowerSearch = searchText.toLowerCase();
    return tables.filter((table) => {
      // Check table name
      if (table.tableName.toLowerCase().includes(lowerSearch)) {
        return true;
      }
      // Check column names
      return table.columns.some((col) => 
        col.name.toLowerCase().includes(lowerSearch)
      );
    });
  }, [tables, searchText]);

  const highlightMatch = (text: string, search: string): React.ReactNode => {
    if (!search) return text;

    const lowerText = text.toLowerCase();
    const lowerSearch = search.toLowerCase();
    const index = lowerText.indexOf(lowerSearch);

    if (index === -1) return text;

    return (
      <>
        {text.substring(0, index)}
        <Text mark>{text.substring(index, index + search.length)}</Text>
        {text.substring(index + search.length)}
      </>
    );
  };

  const renderColumnTitle = (column: ColumnDef, table: SchemaMetadata, search: string): React.ReactNode => {
    const isPK = column.isPrimaryKey;
    const fk = table.foreignKeys.find((fk) => fk.columnName === column.name);

    return (
      <Space size="small" wrap>
        <Text code style={{ fontSize: '13px', color: '#1d1d1f' }}>{highlightMatch(column.name, search)}</Text>
        <Text type="secondary" style={{ fontSize: '13px', color: '#86868b' }}>{column.dataType}</Text>
        {!column.isNullable && <Tag color="#ff3b30" style={{ fontSize: '10px', borderRadius: '4px', border: 'none' }}>NOT NULL</Tag>}
        {isPK && (
          <Tag icon={<KeyOutlined />} color="#ff9500" style={{ fontSize: '10px', borderRadius: '4px', border: 'none' }}>
            PK
          </Tag>
        )}
        {fk && (
          <Tag icon={<LinkOutlined />} color="#af52de" style={{ fontSize: '10px', borderRadius: '4px', border: 'none' }}>
            FK → {fk.foreignTableName}.{fk.foreignColumnName}
          </Tag>
        )}
        {column.columnDefault && (
          <Text type="secondary" style={{ fontSize: '12px' }}>
            default: {column.columnDefault}
          </Text>
        )}
      </Space>
    );
  };

  const buildTreeData = (): DataNode[] => {
    return filteredTables.map((table) => {
      const tableIcon = table.tableType === 'TABLE' ? <TableOutlined /> : <EyeOutlined />;
      
      const pkCount = table.columns.filter(col => col.isPrimaryKey).length;
      const fkCount = table.foreignKeys.length;
      
      const tableTitle = (
        <Space>
          <Text strong style={{ fontSize: '14px', color: '#1d1d1f' }}>{highlightMatch(table.tableName, searchText)}</Text>
          <Tag 
            color={table.tableType === 'TABLE' ? '#0071e3' : '#34c759'} 
            style={{ 
              fontSize: '11px',
              borderRadius: '6px',
              border: 'none',
              fontWeight: 500,
            }}
          >
            {table.tableType}
          </Tag>
          <Badge count={table.columns.length} showZero color="#0071e3" title="Columns" style={{ fontSize: '11px' }} />
          {pkCount > 0 && (
            <Tooltip title="Primary Keys">
              <Badge count={pkCount} showZero color="#ff9500" style={{ fontSize: '11px' }} />
            </Tooltip>
          )}
          {fkCount > 0 && (
            <Tooltip title="Foreign Keys">
              <Badge count={fkCount} showZero color="#af52de" style={{ fontSize: '11px' }} />
            </Tooltip>
          )}
        </Space>
      );

      const columnNodes: DataNode[] = table.columns.map((column) => {
        return {
          key: `${table.tableName}-${column.name}`,
          title: renderColumnTitle(column, table, searchText),
          isLeaf: true,
        };
      });

      return {
        key: table.tableName,
        title: tableTitle,
        icon: tableIcon,
        children: columnNodes,
      };
    });
  };

  const treeData = buildTreeData();

  const handleSearch = (value: string) => {
    setSearchText(value);
    if (value) {
      // Auto-expand all filtered nodes when searching
      const keys = filteredTables.map((table) => table.tableName);
      setExpandedKeys(keys);
      setAutoExpandParent(true);
    } else {
      setExpandedKeys([]);
      setAutoExpandParent(false);
    }
  };

  const handleExpand = (keys: React.Key[]) => {
    setExpandedKeys(keys);
    setAutoExpandParent(false);
  };

  if (tables.length === 0 && !loading) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <DatabaseOutlined style={{ fontSize: '48px', color: '#d9d9d9', marginBottom: '16px' }} />
        <Text type="secondary">No schema metadata available</Text>
      </div>
    );
  }

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="middle">
      {showSearch && (
        <Search
          placeholder="Search tables and columns..."
          allowClear
          size="large"
          onSearch={handleSearch}
          onChange={(e) => handleSearch(e.target.value)}
          style={{ 
            width: '100%',
          }}
          styles={{
            input: {
              borderRadius: '10px',
              border: '1px solid #e5e5e7',
              background: 'white',
            }
          }}
        />
      )}
      {filteredTables.length === 0 && searchText ? (
        <div style={{ padding: '24px', textAlign: 'center' }}>
          <SearchOutlined style={{ fontSize: '48px', color: '#d9d9d9', marginBottom: '16px' }} />
          <Text type="secondary">No tables or columns match "{searchText}"</Text>
        </div>
      ) : (
        <Tree
          showIcon
          expandedKeys={expandedKeys}
          autoExpandParent={autoExpandParent}
          onExpand={handleExpand}
          defaultExpandAll={expandAll}
          treeData={treeData}
          style={{ 
            background: 'transparent',
            fontSize: '14px',
          }}
        />
      )}
    </Space>
  );
};
