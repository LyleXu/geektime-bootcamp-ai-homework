"""Error types and exception definitions."""

from enum import Enum


class ErrorType(str, Enum):
    """Error type enumeration."""

    SCHEMA_NOT_LOADED = "schema_not_loaded"
    AI_GENERATION_FAILED = "ai_generation_failed"
    VALIDATION_FAILED = "validation_failed"
    EXECUTION_FAILED = "execution_failed"
    TIMEOUT = "timeout"
    INTERNAL_ERROR = "internal_error"
    CONFIG_INVALID = "config_invalid"
    DATABASE_CONNECTION_FAILED = "database_connection_failed"
    RESULT_VALIDATION_FAILED = "result_validation_failed"


class ValidationError(Exception):
    """SQL validation error."""

    pass


class ExecutionError(Exception):
    """SQL execution error."""

    pass


class AIError(Exception):
    """AI service call error."""

    pass


class ConfigurationError(Exception):
    """Configuration error."""

    pass
