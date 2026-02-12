import React, { useState } from 'react';
import { Modal, Radio, Input, Space, message, Button, Typography, Alert } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';
import { client } from '../api/client';

const { Text } = Typography;

interface ExportDialogProps {
  visible: boolean;
  onCancel: () => void;
  data: any[] | null;
  filename?: string;
  suggestedFormat?: 'csv' | 'json';
  naturalLanguage?: string;
}

export const ExportDialog: React.FC<ExportDialogProps> = ({ 
  visible, 
  onCancel, 
  data, 
  filename,
  suggestedFormat,
  naturalLanguage 
}) => {
  const [format, setFormat] = useState<'csv' | 'json'>('csv');
  const [customFilename, setCustomFilename] = useState(filename || '');
  const [exporting, setExporting] = useState(false);

  // Auto-detect format and filename from natural language
  React.useEffect(() => {
    if (naturalLanguage) {
      // Detect format from natural language
      const lowerNL = naturalLanguage.toLowerCase();
      if (lowerNL.includes('csv')) {
        setFormat('csv');
      } else if (lowerNL.includes('json')) {
        setFormat('json');
      } else if (suggestedFormat) {
        setFormat(suggestedFormat);
      }

      // Try to extract filename from patterns like "保存到c:\temp\export-{date-time}.csv"
      // or "save to export-data.json"
      const filenamePatterns = [
        /(?:保存到|save to|导出到|export to)\s+(?:[a-z]:\\\\?)?(?:[\w\\\/.-]+\\)?([^\\/\s.]+)(?:\.\w+)?/i,
        /(?:文件名|filename)[:\s]+([^\s.]+)/i,
      ];

      for (const pattern of filenamePatterns) {
        const match = naturalLanguage.match(pattern);
        if (match && match[1]) {
          let extractedName = match[1];
          // Replace {date-time} or {datetime} with actual timestamp
          const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
          extractedName = extractedName.replace(/\{date-time\}|\{datetime\}/gi, timestamp);
          setCustomFilename(extractedName);
          break;
        }
      }
    }
  }, [naturalLanguage, suggestedFormat]);


  const handleExport = async () => {
    if (!data || data.length === 0) {
      message.warning('No data to export');
      return;
    }

    setExporting(true);

    try {
      let blob: Blob;
      let downloadFilename: string;

      if (format === 'csv') {
        // Generate CSV in frontend with proper UTF-8 BOM encoding
        const csvContent = generateCSV(data);
        // Add UTF-8 BOM (0xEF, 0xBB, 0xBF) at the beginning for Excel
        const BOM = '\uFEFF';
        blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' });
        
        // Generate filename
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
        let extractedName = customFilename || `export_${timestamp}`;
        // Replace {date-time} with actual timestamp if present
        extractedName = extractedName.replace(/\{date-time\}|\{datetime\}/gi, timestamp);
        downloadFilename = `${extractedName}.csv`;
      } else {
        // For JSON, use backend API
        const response = await client.post(
          '/dbs/export',
          {
            data,
            format,
            filename: customFilename || undefined,
          },
          {
            responseType: 'blob',
          }
        );

        blob = new Blob([response.data], {
          type: 'application/json;charset=utf-8;',
        });

        // Extract filename from Content-Disposition header
        const contentDisposition = response.headers['content-disposition'];
        downloadFilename = `export.${format}`;
        
        if (contentDisposition) {
          const filenameMatch = contentDisposition.match(/filename="(.+)"/);
          if (filenameMatch && filenameMatch[1]) {
            downloadFilename = filenameMatch[1];
          }
        }
      }

      // Try to use File System Access API (Chrome/Edge) to let user choose location
      if ('showSaveFilePicker' in window) {
        try {
          const handle = await (window as any).showSaveFilePicker({
            suggestedName: downloadFilename,
            types: [
              {
                description: format === 'csv' ? 'CSV Files' : 'JSON Files',
                accept: {
                  [format === 'csv' ? 'text/csv' : 'application/json']: [`.${format}`],
                },
              },
            ],
          });
          
          const writable = await handle.createWritable();
          await writable.write(blob);
          await writable.close();
          
          message.success(`Successfully saved to ${downloadFilename}`);
          onCancel();
          setExporting(false);
          return;
        } catch (err: any) {
          // User cancelled the picker or API not supported, fall back to default download
          if (err.name !== 'AbortError') {
            console.warn('File System Access API failed:', err);
          }
        }
      }

      // Fallback: Standard download to Downloads folder
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = downloadFilename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      message.success(`Successfully exported to ${downloadFilename}`);
      onCancel();
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Failed to export data');
    } finally {
      setExporting(false);
    }
  };

  // Helper function to generate CSV content
  const generateCSV = (data: any[]): string => {
    if (data.length === 0) return '';

    // Get column headers
    const headers = Object.keys(data[0]);
    
    // Create CSV rows
    const csvRows = [];
    
    // Add header row
    csvRows.push(headers.map(escapeCSVValue).join(','));
    
    // Add data rows
    for (const row of data) {
      const values = headers.map(header => {
        const value = row[header];
        return escapeCSVValue(value != null ? String(value) : '');
      });
      csvRows.push(values.join(','));
    }
    
    return csvRows.join('\n');
  };

  // Helper function to escape CSV values
  const escapeCSVValue = (value: string): string => {
    // If value contains comma, newline, or double quote, wrap in quotes
    if (value.includes(',') || value.includes('\n') || value.includes('"')) {
      // Escape double quotes by doubling them
      return `"${value.replace(/"/g, '""')}"`;
    }
    return value;
  };

  return (
    <Modal
      title={
        <Space>
          <DownloadOutlined />
          Export Query Results
        </Space>
      }
      open={visible}
      onCancel={onCancel}
      footer={[
        <Button key="cancel" onClick={onCancel}>
          Cancel
        </Button>,
        <Button key="export" type="primary" icon={<DownloadOutlined />} onClick={handleExport} loading={exporting}>
          Export
        </Button>,
      ]}
    >
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        <div>
          <Text strong>Export Format:</Text>
          <Radio.Group
            value={format}
            onChange={(e) => setFormat(e.target.value)}
            style={{ marginTop: 8, display: 'block' }}
          >
            <Space direction="vertical">
              <Radio value="csv">CSV (Comma-Separated Values)</Radio>
              <Radio value="json">JSON (JavaScript Object Notation)</Radio>
            </Space>
          </Radio.Group>
        </div>

        <div>
          <Text strong>Filename (optional):</Text>
          <Input
            placeholder={`Leave empty for auto-generated filename`}
            value={customFilename}
            onChange={(e) => setCustomFilename(e.target.value)}
            style={{ marginTop: 8 }}
            suffix={`.${format}`}
          />
          <Text type="secondary" style={{ fontSize: 12 }}>
            {customFilename
              ? `Will export as: ${customFilename}.${format}`
              : `Will auto-generate with timestamp`}
          </Text>
        </div>

        {data && (
          <div>
            <Text type="secondary">
              {data.length} row{data.length !== 1 ? 's' : ''} will be exported
            </Text>
          </div>
        )}

        <Alert
          message="Save Location"
          description={
            'showSaveFilePicker' in window
              ? 'You will be prompted to choose where to save the file.'
              : 'File will be saved to your browser\'s default Downloads folder.'
          }
          type="info"
          showIcon
          style={{ marginTop: 8 }}
        />
      </Space>
    </Modal>
  );
};
