"""FastAPI application entrypoint for AI Resume Parser Structured Output Agent."""

import json
import os
from typing import Any, Dict, List
from fastapi import Body, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.schemas.request import (
    HealthCheckResponse,
    ResumeParseRequest,
    ResumeParseResponse,
)
from app.agent.gemini_client import GeminiClient
from app.agent.retry_agent import ResumeStructuredAgent
from app.utils.logger import FAILURE_LOG_PATH, logger

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Production-grade Resume Parser microservice enforcing strict Pydantic v2 schemas, "
        "validating LLM outputs, and automatically self-healing parsing errors via targeted feedback retries."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for cross-origin frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent singleton
gemini_client = GeminiClient()
agent = ResumeStructuredAgent(gemini_client=gemini_client)


@app.get(
    "/",
    tags=["Root"],
    summary="Root Service Status",
    response_description="Basic service introduction and interactive documentation link",
)
def read_root() -> Dict[str, Any]:
    """Root endpoint welcoming clients and directing to interactive Swagger documentation."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "documentation": "/docs",
        "health_check": "/health",
        "tagline": "Make LLMs reliable, not random",
    }


@app.get(
    "/health",
    tags=["Monitoring"],
    response_model=HealthCheckResponse,
    summary="Service Health Check",
    description="Endpoint utilized by cloud platforms (Render, Kubernetes, AWS) for uptime monitoring.",
)
def health_check() -> HealthCheckResponse:
    """Check health and verify whether the Gemini API key is configured."""
    return HealthCheckResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        gemini_configured=gemini_client.is_configured,
    )


@app.post(
    "/api/v1/parse-resume-text",
    tags=["Resume Extraction"],
    response_model=ResumeParseResponse,
    summary="Parse Resume (Plain Text - Easy Copy/Paste)",
    description=(
        "Paste raw multi-line resume text directly into the text box below. "
        "No JSON formatting, curly braces, or escaping required!"
    ),
)
async def parse_resume_from_text(
    resume_text: str = Body(
        ...,
        media_type="text/plain",
        description="Paste raw candidate resume text directly here",
        openapi_examples={
            "Clean Sample Resume": {
                "summary": "Standard Clean Resume",
                "value": (
                    "Johnathan Doe\n"
                    "Email: johnathan.doe@example.com | Phone: +1 (555) 234-5678\n"
                    "Location: San Francisco, CA | LinkedIn: https://linkedin.com/in/johndoe\n\n"
                    "Senior Software Engineer with 6 years experience in Python, FastAPI, Docker, and AWS.\n"
                    "Education: UC Berkeley, BS in Computer Science (2018)"
                ),
            }
        },
    )
) -> JSONResponse:
    """Parse raw plain text resume directly."""
    if not gemini_client.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini API key is not configured. Please supply GEMINI_API_KEY in .env.",
        )

    text = resume_text.strip()
    if len(text) < 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume text must contain at least 20 characters.",
        )

    logger.info(f"Received plain text resume parse request ({len(text)} characters)")
    result = agent.parse(text)
    return JSONResponse(
        status_code=status.HTTP_200_OK if result.success else status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=result.model_dump(),
    )


@app.post(
    "/api/v1/parse-resume",
    tags=["Resume Extraction"],
    response_model=ResumeParseResponse,
    summary="Parse Resume (JSON Payload)",
    description="Extracts structured resume data from a JSON payload containing `resume_text`.",
)
async def parse_resume_from_json(payload: ResumeParseRequest) -> JSONResponse:
    """Parse resume provided via JSON body."""
    if not gemini_client.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini API key is not configured. Please supply GEMINI_API_KEY in .env.",
        )

    logger.info(f"Received JSON resume parse request ({len(payload.resume_text)} characters)")
    result = agent.parse(payload.resume_text)
    return JSONResponse(
        status_code=status.HTTP_200_OK if result.success else status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=result.model_dump(),
    )


@app.get(
    "/api/v1/telemetry/failures",
    tags=["Telemetry"],
    summary="Retrieve Recent Validation Failures",
    description="Returns the recent history of validation failures logged during LLM parsing.",
)
def get_failure_logs(limit: int = 50) -> Dict[str, Any]:
    """Retrieve telemetry log entries of schema validation failures."""
    if not os.path.exists(FAILURE_LOG_PATH):
        return {"total_logs": 0, "entries": []}

    try:
        with open(FAILURE_LOG_PATH, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        recent_lines = lines[-limit:]
        return {
            "total_logs": len(lines),
            "displayed": len(recent_lines),
            "entries": recent_lines,
        }
    except Exception as e:
        logger.error(f"Error reading failure telemetry log: {e}")
        return {"error": str(e), "entries": []}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
    )
