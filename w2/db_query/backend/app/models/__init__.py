"""
Base Pydantic configuration for all models.
Ensures camelCase JSON serialization per Constitution Principle IV & V.
"""
from pydantic import ConfigDict
from pydantic.alias_generators import to_camel


# Base configuration for all Pydantic models
BaseModelConfig = ConfigDict(
    alias_generator=to_camel,
    populate_by_name=True,
    from_attributes=True,
)
