import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Result, Button, Typography, Card } from 'antd';
import { BugOutlined, ReloadOutlined } from '@ant-design/icons';

const { Paragraph, Text } = Typography;

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div style={{ padding: '48px', maxWidth: '800px', margin: '0 auto' }}>
          <Result
            status="error"
            icon={<BugOutlined />}
            title="Something went wrong"
            subTitle="The application encountered an unexpected error. Please try reloading the page."
            extra={[
              <Button type="primary" key="reload" icon={<ReloadOutlined />} onClick={this.handleReload}>
                Reload Page
              </Button>,
              <Button key="reset" onClick={this.handleReset}>
                Try Again
              </Button>,
            ]}
          />

          {process.env.NODE_ENV === 'development' && this.state.error && (
            <Card
              title="Error Details (Development Only)"
              style={{ marginTop: '24px' }}
              type="inner"
            >
              <Paragraph>
                <Text strong>Error:</Text> {this.state.error.toString()}
              </Paragraph>
              {this.state.errorInfo && (
                <Paragraph>
                  <Text strong>Component Stack:</Text>
                  <pre
                    style={{
                      background: '#f5f5f5',
                      padding: '12px',
                      borderRadius: '4px',
                      overflow: 'auto',
                      fontSize: '12px',
                      marginTop: '8px',
                    }}
                  >
                    {this.state.errorInfo.componentStack}
                  </pre>
                </Paragraph>
              )}
              {this.state.error.stack && (
                <Paragraph>
                  <Text strong>Stack Trace:</Text>
                  <pre
                    style={{
                      background: '#f5f5f5',
                      padding: '12px',
                      borderRadius: '4px',
                      overflow: 'auto',
                      fontSize: '12px',
                      marginTop: '8px',
                    }}
                  >
                    {this.state.error.stack}
                  </pre>
                </Paragraph>
              )}
            </Card>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}
