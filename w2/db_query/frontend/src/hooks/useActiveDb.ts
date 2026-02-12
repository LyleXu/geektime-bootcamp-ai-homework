import { useState, useEffect } from 'react';
import { client } from '../api/client';
import type { DatabaseConnection } from '../types/database';

interface UseActiveDbReturn {
  activeDb: DatabaseConnection | null;
  loading: boolean;
  error: string | null;
  refreshActiveDb: () => Promise<void>;
}

export const useActiveDb = (): UseActiveDbReturn => {
  const [activeDb, setActiveDb] = useState<DatabaseConnection | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchActiveDb = async () => {
    setLoading(true);
    setError(null);
    try {
      // Get all databases and find the active one
      const response = await client.get<{ databases: DatabaseConnection[]; total: number }>('/dbs');
      const active = response.data.databases.find((db) => db.isActive);
      setActiveDb(active || null);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch active database');
      setActiveDb(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchActiveDb();
  }, []);

  return {
    activeDb,
    loading,
    error,
    refreshActiveDb: fetchActiveDb,
  };
};
