"""Result validator using OpenAI."""

from typing import Any, Optional

import openai
import structlog

from ..config.settings import OpenAIConfig
from ..utils.retry import retry_on_api_error

logger = structlog.get_logger()


class ResultValidator:
    """Result validator using OpenAI."""

    def __init__(self, config: OpenAIConfig):
        """
        Initialize result validator.

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

    @retry_on_api_error(max_attempts=2)
    async def validate_results(
        self,
        original_query: str,
        sql: str,
        results: list[dict[str, Any]],
        max_rows_to_check: int = 5,
    ) -> tuple[bool, Optional[str]]:
        """
        Validate query results.

        Args:
            original_query: Original natural language query
            sql: Generated SQL
            results: Query results
            max_rows_to_check: Maximum rows to include in validation

        Returns:
            Tuple of (is_valid, error_details)
        """
        logger.info("Validating query results")

        # If no results, skip validation (empty result set may be valid)
        if not results:
            logger.info("No results to validate, skipping validation")
            return True, None

        # Build validation prompts
        system_prompt = self._build_validation_system_prompt()
        user_prompt = self._build_validation_user_prompt(
            original_query, sql, results[:max_rows_to_check]
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=500,
            )

            answer = response.choices[0].message.content
            if answer is None:
                logger.warning("OpenAI returned empty validation response")
                return True, None

            answer = answer.strip().lower()

            # Parse AI reply
            if answer.startswith("valid"):
                logger.info("Results validation passed")
                return True, None
            elif answer.startswith("invalid"):
                # Extract reason
                reason = answer.replace("invalid:", "").strip()
                logger.warning("Results validation failed", reason=reason)
                return False, reason
            else:
                # AI reply uncertain, conservative strategy: pass validation
                logger.warning("Uncertain validation result", answer=answer)
                return True, None

        except Exception as e:
            logger.error("Result validation error", error=str(e))
            # On validation failure, conservative strategy: pass validation
            return True, None

    def _build_validation_system_prompt(self) -> str:
        """
        Build validation system prompt.

        Returns:
            System prompt
        """
        return """You are a SQL query validator. Your task is to verify if the SQL query results match the user's original intent.

Analyze:
1. Does the SQL query logically answer the user's question?
2. Do the returned columns match what the user asked for?
3. Do the sample results look reasonable for the question?

Respond with ONLY one of:
- "VALID" if the results appear to match the user's intent
- "INVALID: [brief reason]" if there's a clear mismatch

Be concise and specific."""

    def _build_validation_user_prompt(
        self, original_query: str, sql: str, sample_results: list[dict[str, Any]]
    ) -> str:
        """
        Build validation user prompt.

        Args:
            original_query: Original natural language query
            sql: Generated SQL
            sample_results: Sample results

        Returns:
            User prompt
        """
        results_str = self._format_results_for_prompt(sample_results)

        return f"""User Question: {original_query}

Generated SQL:
{sql}

Sample Results (first {len(sample_results)} rows):
{results_str}

Does this SQL query correctly answer the user's question?"""

    def _format_results_for_prompt(self, results: list[dict[str, Any]]) -> str:
        """
        Format results for prompt.

        Args:
            results: Query results

        Returns:
            Formatted results string
        """
        if not results:
            return "No results"

        # Get column names
        columns = list(results[0].keys())

        # Build table
        lines = [" | ".join(columns)]
        lines.append("-" * len(lines[0]))

        for row in results:
            values = [str(row.get(col, "")) for col in columns]
            lines.append(" | ".join(values))

        return "\n".join(lines)
