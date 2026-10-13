"""API input/output models and telemetry structures."""

from typing import Any, List, Optional
from pydantic import BaseModel, Field
from app.schemas.resume import ParsedResume


class ResumeParseRequest(BaseModel):
    """Payload sent by the client to parse raw resume text."""

    resume_text: str = Field(
        ...,
        min_length=20,
        description="Raw, unstructured text extracted from candidate's resume (PDF, Word, or plain text)",
    )


class ValidationErrorDetail(BaseModel):
    """Structured breakdown of individual schema validation errors."""

    field: str = Field(..., description="Path to the offending field (e.g. personal_info.email)")
    error_type: str = Field(..., description="Pydantic validation error code")
    message: str = Field(..., description="Human-readable explanation of why validation failed")
    input_value: Optional[Any] = Field(None, description="The raw erroneous value provided by the LLM")


class ResumeParseResponse(BaseModel):
    """Standardized response returned after structured extraction & validation."""

    success: bool = Field(..., description="Whether extraction passed all Pydantic schema validations")
    attempts_made: int = Field(..., description="Number of attempts executed by the self-healing retry loop")
    processing_time_ms: float = Field(..., description="Total execution latency in milliseconds")
    data: Optional[ParsedResume] = Field(None, description="Fully validated structured resume data")
    validation_failures: Optional[List[ValidationErrorDetail]] = Field(
        default=None,
        description="List of validation errors if the agent exhausted retry attempts",
    )


class HealthCheckResponse(BaseModel):
    """Health check endpoint status for Render monitoring."""

    status: str = Field(default="healthy", description="Application operational status")
    app_name: str = Field(..., description="Service identifier")
    version: str = Field(..., description="Semantic version string")
    gemini_configured: bool = Field(..., description="True if GEMINI_API_KEY is detected in environment")
