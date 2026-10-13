"""Self-healing Structured Output Agent with automated error-correction retry loop."""

import time
from typing import List, Optional, Tuple
from app.config import get_settings
from app.schemas.resume import ParsedResume
from app.schemas.request import ResumeParseResponse, ValidationErrorDetail
from app.agent.gemini_client import GeminiClient
from app.agent.validator import PydanticValidator
from app.utils.logger import logger, log_validation_failure


class ResumeStructuredAgent:
    """Agent that extracts structured resume data and self-heals parsing errors via targeted feedback retries."""

    SYSTEM_INSTRUCTION = (
        "You are an elite, highly accurate HR data extraction and parsing engine. "
        "Your duty is to parse raw candidate resume text and extract all factual details "
        "strictly conforming to the provided schema. "
        "Rules:\n"
        "1. Do not invent, assume, or hallucinate credentials, dates, or contact info.\n"
        "2. If an optional field is missing from the resume, leave it as null/None.\n"
        "3. Ensure all numbers (years, experience) are valid numeric values.\n"
        "4. Validate email syntax if present.\n"
        "5. Output only strictly valid JSON matching the requested schema."
    )

    def __init__(self, gemini_client: Optional[GeminiClient] = None, max_retries: Optional[int] = None):
        """Initialize the agent with Gemini client and retry constraints.

        Args:
            gemini_client: Optional pre-configured GeminiClient instance.
            max_retries: Maximum number of self-healing attempts (default from settings).
        """
        settings = get_settings()
        self.client = gemini_client or GeminiClient()
        self.max_retries = max_retries or settings.MAX_RETRY_ATTEMPTS

    def parse(self, resume_text: str) -> ResumeParseResponse:
        """Parse raw resume text into a strictly validated ParsedResume object.

        Executes the Self-Healing Loop:
        If Pydantic validation fails, the exact validation error message is injected
        back into the model prompt for an automated correction attempt.

        Args:
            resume_text: Raw unstructured resume text.

        Returns:
            ResumeParseResponse containing validation status, attempt count, and parsed data.
        """
        start_time = time.perf_counter()

        initial_prompt = (
            "Parse the following resume text into the requested structured JSON format:\n\n"
            f"--- BEGIN RESUME TEXT ---\n{resume_text}\n--- END RESUME TEXT ---"
        )

        conversation_history: List[str] = [initial_prompt]
        last_errors: List[ValidationErrorDetail] = []
        raw_response: str = ""

        for attempt in range(1, self.max_retries + 1):
            logger.info(f"Executing extraction attempt {attempt} of {self.max_retries}...")

            try:
                # Call Gemini with strict schema enforcement
                raw_response = self.client.generate(
                    contents=conversation_history,
                    schema=ParsedResume,
                    system_instruction=self.SYSTEM_INSTRUCTION,
                )
            except Exception as api_err:
                logger.error(f"Gemini API invocation failure on attempt {attempt}: {api_err}")
                last_errors = [
                    ValidationErrorDetail(
                        field="gemini_api",
                        error_type="api_error",
                        message=str(api_err),
                        input_value=None,
                    )
                ]
                break

            # Validate against Pydantic schema
            is_valid, parsed_data, errors = PydanticValidator.validate(
                raw_text=raw_response,
                target_model=ParsedResume,
            )

            if is_valid and parsed_data is not None:
                elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
                logger.info(f"Successfully validated structured resume on attempt {attempt} in {elapsed_ms}ms")
                return ResumeParseResponse(
                    success=True,
                    attempts_made=attempt,
                    processing_time_ms=elapsed_ms,
                    data=parsed_data,
                    validation_failures=None,
                )

            # Record failure in telemetry
            last_errors = errors
            log_validation_failure(attempt, errors, raw_response)

            # Generate targeted feedback prompt for next attempt
            if attempt < self.max_retries:
                feedback_prompt = PydanticValidator.construct_feedback_prompt(errors)
                logger.info(f"Self-Healing: Sending error feedback to Gemini for attempt {attempt + 1}")
                # Append bad response and error feedback to conversation turns
                conversation_history.append(raw_response)
                conversation_history.append(feedback_prompt)

        # Retries exhausted
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.error(
            f"Failed to achieve valid structured output after {self.max_retries} attempts ({elapsed_ms}ms)"
        )
        return ResumeParseResponse(
            success=False,
            attempts_made=self.max_retries,
            processing_time_ms=elapsed_ms,
            data=None,
            validation_failures=last_errors,
        )
