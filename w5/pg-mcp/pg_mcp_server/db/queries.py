"""SQL queries for schema introspection."""

# Query to get all tables
QUERY_TABLES = """
    SELECT 
        table_schema,
        table_name,
        table_type,
        obj_description((table_schema || '.' || table_name)::regclass) as comment
    FROM information_schema.tables
    WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
    ORDER BY table_schema, table_name;
"""

# Query to get columns for a table
QUERY_COLUMNS = """
    SELECT 
        c.column_name,
        c.data_type,
        c.is_nullable,
        c.column_default,
        col_description((c.table_schema || '.' || c.table_name)::regclass, c.ordinal_position) as comment,
        CASE WHEN pk.column_name IS NOT NULL THEN true ELSE false END as is_primary_key,
        CASE WHEN fk.column_name IS NOT NULL THEN true ELSE false END as is_foreign_key,
        fk.foreign_table_schema || '.' || fk.foreign_table_name || '.' || fk.foreign_column_name as foreign_key_ref
    FROM information_schema.columns c
    LEFT JOIN (
        SELECT ku.table_schema, ku.table_name, ku.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage ku
            ON tc.constraint_name = ku.constraint_name
            AND tc.table_schema = ku.table_schema
        WHERE tc.constraint_type = 'PRIMARY KEY'
    ) pk ON c.table_schema = pk.table_schema 
        AND c.table_name = pk.table_name 
        AND c.column_name = pk.column_name
    LEFT JOIN (
        SELECT 
            ku.table_schema,
            ku.table_name,
            ku.column_name,
            ccu.table_schema as foreign_table_schema,
            ccu.table_name as foreign_table_name,
            ccu.column_name as foreign_column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage ku
            ON tc.constraint_name = ku.constraint_name
        JOIN information_schema.constraint_column_usage ccu
            ON tc.constraint_name = ccu.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
    ) fk ON c.table_schema = fk.table_schema 
        AND c.table_name = fk.table_name 
        AND c.column_name = fk.column_name
    WHERE c.table_schema = $1 AND c.table_name = $2
    ORDER BY c.ordinal_position;
"""

# Query to get indexes for a table
QUERY_INDEXES = """
    SELECT
        i.relname as index_name,
        a.attname as column_name,
        ix.indisunique as is_unique,
        ix.indisprimary as is_primary,
        am.amname as index_type
    FROM pg_class t
    JOIN pg_index ix ON t.oid = ix.indrelid
    JOIN pg_class i ON i.oid = ix.indexrelid
    JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
    JOIN pg_am am ON i.relam = am.oid
    JOIN pg_namespace n ON t.relnamespace = n.oid
    WHERE n.nspname = $1 AND t.relname = $2
    ORDER BY i.relname, a.attnum;
"""

# Query to get foreign keys for a table
QUERY_FOREIGN_KEYS = """
    SELECT
        kcu.column_name,
        ccu.table_name AS foreign_table,
        ccu.column_name AS foreign_column,
        tc.constraint_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage ccu
        ON ccu.constraint_name = tc.constraint_name
        AND ccu.table_schema = tc.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_schema = $1
        AND tc.table_name = $2;
"""

# Query to get custom types (enums)
QUERY_CUSTOM_TYPES = """
    SELECT 
        t.typname as type_name,
        e.enumlabel as enum_value
    FROM pg_type t
    JOIN pg_enum e ON t.oid = e.enumtypid
    JOIN pg_namespace n ON t.typnamespace = n.oid
    WHERE n.nspname = 'public'
    ORDER BY t.typname, e.enumsortorder;
"""

# Collection of all schema queries
SCHEMA_QUERIES = {
    "tables": QUERY_TABLES,
    "columns": QUERY_COLUMNS,
    "indexes": QUERY_INDEXES,
    "foreign_keys": QUERY_FOREIGN_KEYS,
    "custom_types": QUERY_CUSTOM_TYPES,
}
