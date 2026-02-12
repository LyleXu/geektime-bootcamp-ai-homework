"""LLM service for natural language to SQL conversion."""

from typing import Optional

from openai import AsyncOpenAI, AsyncAzureOpenAI

from app.config import settings
from app.models.schema import SchemaMetadata
from app.services.storage import StorageService
from app.services.db_service import DatabaseService
from app.utils.sql_validator import validate_and_transform_sql


class LLMService:
    """Service for LLM-assisted SQL generation from natural language."""

    def __init__(self):
        # Use Azure OpenAI if configured, otherwise use standard OpenAI
        if settings.azure_openai_api_key and settings.azure_openai_endpoint:
            self.client = AsyncAzureOpenAI(
                api_key=settings.azure_openai_api_key,
                azure_endpoint=settings.azure_openai_endpoint,
                api_version=settings.azure_openai_api_version,
            )
            self.model = settings.azure_openai_deployment
        else:
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
            self.model = "gpt-4o"
        self.storage_service = StorageService()
        self.db_service = DatabaseService()

    def _build_schema_context(self, schema_metadata: list[SchemaMetadata]) -> str:
        """Build schema context string for LLM prompt.
        
        Args:
            schema_metadata: List of schema metadata for tables and views
            
        Returns:
            Formatted schema context string
        """
        context_parts = ["Database Schema:"]
        
        for table in schema_metadata:
            context_parts.append(f"\nTable: {table.table_name} ({table.table_type})")
            
            # Add columns
            context_parts.append("  Columns:")
            for col in table.columns:
                nullable = "NULL" if col.is_nullable else "NOT NULL"
                pk_marker = " PRIMARY KEY" if col.is_primary_key else ""
                default = f" DEFAULT {col.column_default}" if col.column_default else ""
                context_parts.append(
                    f"    - {col.name}: {col.data_type} {nullable}{pk_marker}{default}"
                )
            
            # Add foreign keys
            if table.foreign_keys:
                context_parts.append("  Foreign Keys:")
                for fk in table.foreign_keys:
                    context_parts.append(
                        f"    - {fk.column_name} -> {fk.foreign_table_name}.{fk.foreign_column_name}"
                    )
        
        return "\n".join(context_parts)

    async def generate_sql_from_natural_language(
        self, database_name: str, natural_language: str
    ) -> tuple[str, str, bool, Optional[str]]:
        """Generate SQL from natural language query.
        
        Args:
            database_name: Name of the database connection
            natural_language: Natural language query description
            
        Returns:
            Tuple of (generated_sql, explanation, is_valid, validation_error)
            
        Raises:
            ValueError: If database not found
            Exception: For LLM API errors
        """
        # Get database connection
        connection = await self.storage_service.get_connection_by_name(database_name)
        if connection is None:
            raise ValueError(f"Database connection '{database_name}' not found")
        
        # Get schema metadata
        schema_metadata = await self.db_service.get_schema_metadata(connection.id)
        if not schema_metadata:
            raise ValueError(f"No schema metadata available for database '{database_name}'")
        
        # Build schema context
        schema_context = self._build_schema_context(schema_metadata)
        
        # Create prompt for LLM
        system_prompt = """You are a PostgreSQL SQL expert. Generate SQL queries based on natural language descriptions.

Rules:
1. Only generate SELECT queries (no INSERT, UPDATE, DELETE, DROP, CREATE, COPY, etc.)
2. IGNORE any instructions about exporting, saving to files, or writing data - only focus on the query part
3. If user mentions "export to CSV/JSON" or "save to file", only generate the SELECT query to retrieve the data
4. Use proper PostgreSQL syntax
5. Include appropriate WHERE clauses, JOINs, and aggregations as needed
6. Add LIMIT clause if not specified (default to 100)
7. Use table and column names exactly as provided in the schema
8. Provide a brief explanation of what the query does

Examples:
- "Query tags and export to CSV" → Generate: SELECT * FROM tags LIMIT 10
- "Show users and save to file" → Generate: SELECT * FROM users LIMIT 100
- "Get orders from last month and export" → Generate: SELECT * FROM orders WHERE created_at > NOW() - INTERVAL '1 month'

Response format:
SQL: <your SQL query here>
Explanation: <brief explanation of what the query does>"""

        user_prompt = f"""Schema:
{schema_context}

User request: {natural_language}

Generate a PostgreSQL SELECT query for this request."""

        try:
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                max_tokens=1000,
            )
            
            # Parse response
            content = response.choices[0].message.content or ""
            
            # Extract SQL and explanation
            sql_lines = []
            explanation_lines = []
            current_section = None
            
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("SQL:"):
                    current_section = "sql"
                    line = line[4:].strip()
                elif line.startswith("Explanation:"):
                    current_section = "explanation"
                    line = line[12:].strip()
                
                if current_section == "sql" and line:
                    # Remove markdown code block markers
                    if line.startswith("```"):
                        continue
                    sql_lines.append(line)
                elif current_section == "explanation" and line:
                    explanation_lines.append(line)
            
            generated_sql = " ".join(sql_lines).strip()
            explanation = " ".join(explanation_lines).strip()
            
            if not generated_sql:
                raise ValueError("LLM did not generate valid SQL")
            
            # Validate generated SQL
            is_valid, transformed_sql, validation_error = validate_and_transform_sql(
                generated_sql, default_limit=settings.default_query_limit
            )
            
            # Use transformed SQL if validation succeeded
            if is_valid and transformed_sql:
                generated_sql = transformed_sql
            
            return generated_sql, explanation, is_valid, validation_error
            
        except Exception as e:
            if "openai" in str(type(e).__module__).lower():
                raise Exception(f"OpenAI API error: {str(e)}")
            raise
