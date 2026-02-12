"""SQL generator using OpenAI."""

from typing import Optional

import openai
import structlog

from ..config.settings import OpenAIConfig
from ..models.schema import DatabaseSchema
from ..utils.retry import retry_on_api_error

logger = structlog.get_logger()


class SQLGenerator:
    """SQL generator using OpenAI."""

    def __init__(self, config: OpenAIConfig):
        """
        Initialize SQL generator.

        Args:
            config: OpenAI configuration
        """
        self.config = config
        
        # Initialize OpenAI or Azure OpenAI client based on configuration
        if config.use_azure:
            if not config.azure_endpoint or not config.azure_deployment:
                raise ValueError(
                    "azure_endpoint and azure_deployment are required when use_azure=True"
                )
            self.client = openai.AsyncAzureOpenAI(
                api_key=config.api_key.get_secret_value(),
                azure_endpoint=config.azure_endpoint,
                api_version=config.api_version,
                timeout=config.timeout,
            )
            self.model_name = config.azure_deployment
        else:
            self.client = openai.AsyncOpenAI(
                api_key=config.api_key.get_secret_value(),
                base_url=config.api_base,
                timeout=config.timeout,
            )
            self.model_name = config.model

    @retry_on_api_error(max_attempts=3)
    async def generate_sql(
        self,
        natural_query: str,
        schema: DatabaseSchema,
        relevant_tables: Optional[list[str]] = None,
    ) -> str:
        """
        Generate SQL from natural language query.

        Args:
            natural_query: Natural language query
            schema: Database schema
            relevant_tables: Relevant table names (optional)

        Returns:
            Generated SQL statement
        """
        logger.info("Generating SQL", query=natural_query)

        # Build schema context
        if relevant_tables:
            schema_context = self._build_filtered_schema_context(schema, relevant_tables)
        else:
            schema_context = schema.to_context_string(max_tables=50)

        # Build prompts
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(natural_query, schema_context)

        # Call OpenAI API
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,  # Low temperature for deterministic results
                max_tokens=1000,
            )

            sql = response.choices[0].message.content
            if sql is None:
                raise ValueError("OpenAI returned empty response")

            sql = sql.strip()

            # Clean SQL
            sql = self._clean_sql(sql)

            logger.info("SQL generated successfully", sql=sql)
            return sql

        except Exception as e:
            logger.error("Failed to generate SQL", error=str(e))
            raise

    def _build_system_prompt(self) -> str:
        """
        Build system prompt.

        Returns:
            System prompt
        """
        return """You are an expert PostgreSQL query generator. 
Your task is to convert natural language queries into valid PostgreSQL SQL SELECT statements.

Requirements:
1. Generate ONLY SELECT queries - no INSERT, UPDATE, DELETE, or DDL statements
2. Use proper PostgreSQL syntax and functions
3. Format the SQL clearly with proper indentation
4. Include appropriate JOINs, WHERE clauses, GROUP BY, ORDER BY as needed
5. Use table and column names exactly as provided in the schema
6. Return ONLY the SQL query without any explanation or markdown formatting
7. If the query is ambiguous, make reasonable assumptions based on the schema

Important:
- Do NOT include markdown code blocks (```)
- Do NOT add explanatory text before or after the SQL
- The output should be directly executable SQL"""

    def _build_user_prompt(self, query: str, schema_context: str) -> str:
        """
        Build user prompt.

        Args:
            query: Natural language query
            schema_context: Schema context string

        Returns:
            User prompt
        """
        return f"""Database Schema:
{schema_context}

User Query: {query}

Generate a PostgreSQL SELECT query to answer this question. Return only the SQL query."""

    def _clean_sql(self, sql: str) -> str:
        """
        Clean SQL statement.

        Args:
            sql: Raw SQL string

        Returns:
            Cleaned SQL
        """
        # Remove markdown code blocks
        sql = sql.strip()
        if sql.startswith("```sql"):
            sql = sql[6:]
        elif sql.startswith("```"):
            sql = sql[3:]

        if sql.endswith("```"):
            sql = sql[:-3]

        return sql.strip()

    def _build_filtered_schema_context(
        self, schema: DatabaseSchema, table_names: list[str]
    ) -> str:
        """
        Build filtered schema context.

        Args:
            schema: Database schema
            table_names: List of table names to include

        Returns:
            Filtered schema context string
        """
        context_parts = [f"Database: {schema.database_name}\n"]

        for table_name in table_names:
            table = schema.get_table(table_name)
            if not table:
                continue

            context_parts.append(f"\nTable: {table.schema}.{table.name}")
            if table.comment:
                context_parts.append(f"  Description: {table.comment}")

            context_parts.append("  Columns:")
            for col in table.columns:
                pk = " (PK)" if col.is_primary_key else ""
                fk = f" -> {col.foreign_key_ref}" if col.is_foreign_key else ""
                comment = f" # {col.comment}" if col.comment else ""
                context_parts.append(
                    f"    - {col.name}: {col.data_type}{pk}{fk}{comment}"
                )

        return "\n".join(context_parts)
