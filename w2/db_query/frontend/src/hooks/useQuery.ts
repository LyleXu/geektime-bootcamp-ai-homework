import { useState } from 'react';
import { client } from '../api/client';
import type { QueryRequest, QueryResponse } from '../types/query';
import { isErrorResponse } from '../types/query';

interface UseQueryReturn {
  executeQuery: (databaseName: string, sql: string) => Promise<void>;
  data: QueryResponse | null;
  loading: boolean;
  error: string | null;
  clearResults: () => void;
}

export const useQuery = (): UseQueryReturn => {
  const [data, setData] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const executeQuery = async (databaseName: string, sql: string) => {
    if (!sql.trim()) {
      setError('SQL query cannot be empty');
      return;
    }

    setLoading(true);
    setError(null);
    setData(null);

    try {
      const request: QueryRequest = { sql };
      const response = await client.post<QueryResponse>(
        `/dbs/${databaseName}/query`,
        request
      );
      setData(response.data);
    } catch (err: any) {
      const errorData = err.response?.data;
      
      if (isErrorResponse(errorData)) {
        setError(errorData.message);
      } else if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError(err.message || 'Failed to execute query');
      }
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  const clearResults = () => {
    setData(null);
    setError(null);
  };

  return {
    executeQuery,
    data,
    loading,
    error,
    clearResults,
  };
};
