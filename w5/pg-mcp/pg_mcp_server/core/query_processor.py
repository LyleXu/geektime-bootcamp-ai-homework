"""Query processor - main processing pipeline."""

import time
from typing import Any, Optional

import structlog

from ..models.errors import ErrorType
from ..models.query import QueryError, QueryMetadata, QueryRequest, QueryResponse
from .result_validator import ResultValidator
from .schema_cache import SchemaCache
from .sql_executor import SQLExecutor
from .sql_generator import SQLGenerator
from .sql_validator import SQLValidator

logger = structlog.get_logger()


class QueryProcessor:
    """Query processor - main processing pipeline."""

    def __init__(
        self,
        schema_cache: SchemaCache,
        sql_generator: SQLGenerator,
        sql_validator: SQLValidator,
        sql_executor: SQLExecutor,
        result_validator: ResultValidator,
        database_name: Optional[str] = None,
        metrics_collector: Optional[Any] = None,
    ):
        """
        Initialize query processor.

        Args:
            schema_cache: Schema cache
            sql_generator: SQL generator
            sql_validator: SQL validator
            sql_executor: SQL executor
            result_validator: Result validator
            database_name: Name of the database being queried
            metrics_collector: Optional metrics collector
        """
        self.schema_cache = schema_cache
        self.sql_generator = sql_generator
        self.sql_validator = sql_validator
        self.sql_executor = sql_executor
        self.result_validator = result_validator
        self.database_name = database_name or "unknown"
        self.metrics = metrics_collector

    async def process_query(self, request: QueryRequest) -> QueryResponse | QueryError:
        """
        Process query request.

        Pipeline:
        1. Get schema context
        2. Generate SQL (OpenAI)
        3. Validate SQL (SQLGlot)
        4. Execute SQL (Asyncpg)
        5. Validate results (OpenAI)
        6. Return response

        Args:
            request: Query request

        Returns:
            QueryResponse or QueryError
        """
        logger.info("Processing query", query=request.query)

        try:
            # 1. Get schema
            schema = self.schema_cache.schema
            if not schema:
                return QueryError(
                    error=ErrorType.SCHEMA_NOT_LOADED,
                    message="Database schema not loaded",
                    suggestion="Please restart the server to load schema",
                )

            # 2. Generate SQL
            if self.metrics:
                from ..utils.metrics import StandardMetrics
                self.metrics.increment(
                    StandardMetrics.SQL_GENERATION_TOTAL,
                    labels={"database": self.database_name}
                )
            
            sql_gen_start = time.time()
            try:
                sql = await self.sql_generator.generate_sql(
                    natural_query=request.query, schema=schema
                )
                
                if self.metrics:
                    sql_gen_duration = (time.time() - sql_gen_start) * 1000
                    self.metrics.increment(
                        StandardMetrics.SQL_GENERATION_SUCCESS,
                        labels={"database": self.database_name}
                    )
                    self.metrics.record_timer(
                        StandardMetrics.SQL_GENERATION_DURATION,
                        sql_gen_duration,
                        labels={"database": self.database_name}
                    )
            except Exception as e:
                logger.error("SQL generation failed", error=str(e))
                if self.metrics:
                    self.metrics.increment(
                        StandardMetrics.SQL_GENERATION_ERROR,
                        labels={"database": self.database_name}
                    )
                return QueryError(
                    error=ErrorType.AI_GENERATION_FAILED,
                    message=f"SQL generation failed: {str(e)}",
                    suggestion="Please try again later, or simplify your query description",
                )

            # 3. Validate SQL
            is_valid, error_msg = self.sql_validator.validate_sql(sql)
            if not is_valid:
                logger.warning("SQL validation failed", error=error_msg, sql=sql)
                return QueryError(
                    error=ErrorType.VALIDATION_FAILED,
                    message=error_msg or "SQL validation failed",
                    suggestion="This system only supports SELECT queries. Please rephrase your query.",
                    sql=sql,
                )

            # Format SQL
            formatted_sql = self.sql_validator.format_sql(sql)

            # 4. Execute SQL
            if self.metrics:
                from ..utils.metrics import StandardMetrics
                self.metrics.increment(
                    StandardMetrics.SQL_EXECUTION_TOTAL,
                    labels={"database": self.database_name}
                )
            
            sql_exec_start = time.time()
            try:
                results, columns, execution_time = await self.sql_executor.execute_query(
                    formatted_sql
                )
                
                if self.metrics:
                    sql_exec_duration = (time.time() - sql_exec_start) * 1000
                    self.metrics.increment(
                        StandardMetrics.SQL_EXECUTION_SUCCESS,
                        labels={"database": self.database_name}
                    )
                    self.metrics.record_timer(
                        StandardMetrics.SQL_EXECUTION_DURATION,
                        sql_exec_duration,
                        labels={"database": self.database_name}
                    )
                    self.metrics.record_histogram(
                        StandardMetrics.SQL_EXECUTION_ROWS,
                        len(results),
                        labels={"database": self.database_name}
                    )
            except Exception as e:
                logger.error("SQL execution failed", error=str(e), sql=formatted_sql)
                if self.metrics:
                    self.metrics.increment(
                        StandardMetrics.SQL_EXECUTION_ERROR,
                        labels={"database": self.database_name}
                    )
                return QueryError(
                    error=ErrorType.EXECUTION_FAILED,
                    message=str(e),
                    suggestion="Please verify table and column names are correct, or try rephrasing your query",
                    sql=formatted_sql,
                )

            # 5. Validate results (optional but recommended)
            if self.metrics:
                from ..utils.metrics import StandardMetrics
                self.metrics.increment(
                    StandardMetrics.VALIDATION_TOTAL,
                    labels={"database": self.database_name}
                )
            
            val_start = time.time()
            is_valid, validation_details = await self.result_validator.validate_results(
                original_query=request.query, sql=formatted_sql, results=results
            )
            
            if self.metrics:
                val_duration = (time.time() - val_start) * 1000
                self.metrics.record_timer(
                    StandardMetrics.VALIDATION_DURATION,
                    val_duration,
                    labels={"database": self.database_name}
                )

            if not is_valid:
                logger.warning(
                    "Result validation failed",
                    details=validation_details,
                    sql=formatted_sql,
                )
                if self.metrics:
                    self.metrics.increment(
                        StandardMetrics.VALIDATION_FAILED,
                        labels={"database": self.database_name}
                    )
                return QueryError(
                    error=ErrorType.RESULT_VALIDATION_FAILED,
                    message="AI validation found that query results may not match the request",
                    suggestion="The generated SQL may have misunderstood. Please try describing your query in more detail, or provide table and field names.",
                    sql=formatted_sql,
                    validation_details=validation_details,
                )
            
            if self.metrics:
                self.metrics.increment(
                    StandardMetrics.VALIDATION_SUCCESS,
                    labels={"database": self.database_name}
                )

            # 6. Return successful response
            response = QueryResponse(
                sql=formatted_sql,
                results=results,
                metadata=QueryMetadata(
                    rows=len(results),
                    execution_time_ms=execution_time,
                    columns=columns,
                ),
                database=self.database_name,
            )

            logger.info("Query processed successfully", rows=len(results))
            return response

        except Exception as e:
            logger.error("Unexpected error in query processing", error=str(e))
            return QueryError(
                error=ErrorType.INTERNAL_ERROR,
                message=f"Internal error: {str(e)}",
                suggestion="Please contact system administrator",
            )

