/**
 * Schema metadata types matching backend Pydantic models.
 */

export type TableType = "TABLE" | "VIEW";

export interface ColumnDef {
  name: string;
  dataType: string;
  isNullable: boolean;
  columnDefault?: string;
  isPrimaryKey?: boolean;
}

export interface ForeignKeyDef {
  columnName: string;
  foreignTableName: string;
  foreignColumnName: string;
}

export interface SchemaMetadata {
  id?: number;
  databaseId?: number;
  tableName: string;
  tableType: TableType;
  columns: ColumnDef[];
  primaryKeys?: string[];
  foreignKeys: ForeignKeyDef[];
  estimatedRows?: number;
  updatedAt?: string;
}

export interface SchemaBrowserResponse {
  databaseName: string;
  tables: SchemaMetadata[];
  views: SchemaMetadata[];
}

