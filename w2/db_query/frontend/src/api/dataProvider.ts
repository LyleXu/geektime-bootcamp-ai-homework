/**
 * Refine data provider implementation.
 * Provides CRUD operations for database connections via Refine framework.
 */
import type { DataProvider } from '@refinedev/core';
import { apiClient } from './client';
import type { DatabaseConnection, DatabaseListResponse } from '../types/database';

export const dataProvider: DataProvider = {
  getList: async ({ resource }) => {
    if (resource === 'databases') {
      const { data } = await apiClient.get<DatabaseListResponse>('/dbs');
      return {
        data: data.databases,
        total: data.databases.length,
      };
    }
    throw new Error(`Resource ${resource} not implemented`);
  },

  getOne: async ({ resource, id }) => {
    if (resource === 'databases') {
      const { data } = await apiClient.get(`/dbs/${id}`);
      return { data };
    }
    throw new Error(`Resource ${resource} not implemented`);
  },

  create: async ({ resource, variables, meta }) => {
    if (resource === 'databases') {
      // Use name from meta if provided, otherwise from variables
      const name = meta?.name || variables.name;
      if (!name) {
        throw new Error('Database name is required');
      }
      const { data } = await apiClient.put(`/dbs/${name}`, variables);
      return { data };
    }
    throw new Error(`Resource ${resource} not implemented`);
  },

  update: async ({ resource, id, variables }) => {
    if (resource === 'databases') {
      const { data } = await apiClient.put(`/dbs/${id}`, variables);
      return { data };
    }
    throw new Error(`Resource ${resource} not implemented`);
  },

  deleteOne: async ({ resource, id }) => {
    if (resource === 'databases') {
      await apiClient.delete(`/dbs/${id}`);
      return { data: {} as any };
    }
    throw new Error(`Resource ${resource} not implemented`);
  },

  getApiUrl: () => apiClient.defaults.baseURL || '',
};
