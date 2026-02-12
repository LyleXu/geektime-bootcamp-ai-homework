/**
 * Query request/response types matching backend Pydantic models.
 */

export interface QueryRequest {
  sql: string;
}

export interface QueryResponse {
  sql: string;
  rows: Record<string, any>[];
  rowCount: number;
  executionTimeMs: number;
  columns: string[];
}

export interface NaturalQueryRequest {
  natural_language: string;
}

export interface NaturalQueryResponse {
  generatedSql: string;
  explanation: string;
  isValid: boolean;
  validationError?: string | null;
}

export interface ErrorResponse {
  error: string;
  message?: string;
  details?: any;
}

// Type guards
export function isErrorResponse(response: any): response is ErrorResponse {
  return response && typeof response.error === 'string';
}
