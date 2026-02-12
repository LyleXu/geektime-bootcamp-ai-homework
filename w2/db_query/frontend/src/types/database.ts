/**
 * Database connection types matching backend Pydantic models.
 * Per Constitution Principle V: camelCase JSON convention.
 */

export interface DatabaseConnection {
  id?: number;
  name: string;
  url: string;
  isActive: boolean;
  createdAt?: string;
  lastConnectedAt?: string;
}

export interface DatabaseConnectionRequest {
  url: string;
  isActive?: boolean;
}

export interface DatabaseListResponse {
  databases: DatabaseConnection[];
  activeDatabase?: string;
}
