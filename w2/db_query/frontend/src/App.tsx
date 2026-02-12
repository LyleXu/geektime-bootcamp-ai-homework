/**
 * React app entry with Refine provider and Ant Design.
 * Per Constitution Principle I: TypeScript strict mode enabled.
 */
import { Refine } from '@refinedev/core';
import { notificationProvider } from '@refinedev/antd';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, App as AntdApp } from 'antd';
import { dataProvider } from './api/dataProvider';
import { DatabaseList } from './pages/DatabaseList';
import { QueryEditor } from './pages/QueryEditor';
import { NaturalQuery } from './pages/NaturalQuery';
import { SchemaBrowser } from './pages/SchemaBrowser';
import { DatabaseExplorer } from './pages/DatabaseExplorer';
import { ErrorBoundary } from './components/ErrorBoundary';

function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ minHeight: '100vh', background: '#f5f5f7' }}>
      {children}
    </div>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <ConfigProvider
          theme={{
            token: {
              colorPrimary: '#0071e3',
              colorLink: '#0071e3',
              colorSuccess: '#34c759',
              colorWarning: '#ff9500',
              colorError: '#ff3b30',
              borderRadius: 10,
              fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", sans-serif',
              fontSize: 14,
              colorBgContainer: '#ffffff',
              colorBorder: '#e5e5e7',
              colorText: '#1d1d1f',
              colorTextSecondary: '#86868b',
            },
            components: {
              Button: {
                controlHeight: 40,
                fontWeight: 500,
              },
              Input: {
                controlHeight: 40,
              },
              Select: {
                controlHeight: 40,
              },
            },
          }}
        >
          <AntdApp>
            <Refine
              dataProvider={dataProvider}
              notificationProvider={notificationProvider}
              options={{
                syncWithLocation: false,
                warnWhenUnsavedChanges: false,
                disableTelemetry: true,
              }}
              resources={[
                {
                  name: 'databases',
                  list: '/databases',
                },
                {
                  name: 'schema',
                  list: '/schema',
                },
                {
                  name: 'queries',
                  list: '/query',
                },
                {
                  name: 'natural-queries',
                  list: '/natural-query',
                },
              ]}
            >
              <AppLayout>
                <Routes>
                  <Route path="/" element={<Navigate to="/explorer" replace />} />
                  <Route path="/explorer" element={<DatabaseExplorer />} />
                  <Route path="/databases" element={<DatabaseList />} />
                  <Route path="/schema" element={<SchemaBrowser />} />
                  <Route path="/query" element={<QueryEditor />} />
                  <Route path="/natural-query" element={<NaturalQuery />} />
                </Routes>
              </AppLayout>
            </Refine>
          </AntdApp>
        </ConfigProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
