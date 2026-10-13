"""Unit tests verifying Pydantic schema validation rules and error trapping."""

import pytest
from pydantic import ValidationError
from app.schemas.resume import (
    PersonalInfo,
    EducationItem,
    ExperienceItem,
    ParsedResume,
)
from app.agent.validator import PydanticValidator


def test_personal_info_valid():
    """Ensure PersonalInfo succeeds when provided with a valid email and name."""
    info = PersonalInfo(
        full_name="Jane Doe",
        email="jane.doe@example.com",
        phone="+123456789",
        location="New York, NY",
    )
    assert info.full_name == "Jane Doe"
    assert info.email == "jane.doe@example.com"


def test_personal_info_invalid_email():
    """Ensure PersonalInfo raises ValidationError when email format is invalid."""
    with pytest.raises(ValidationError) as exc_info:
        PersonalInfo(
            full_name="Jane Doe",
            email="invalid-not-an-email",
        )
    errors = exc_info.value.errors()
    assert any("email" in ".".join(str(x) for x in err["loc"]) for err in errors)


def test_negative_experience_rejected():
    """Verify that total_years_experience enforces ge=0 constraint."""
    with pytest.raises(ValidationError):
        ParsedResume(
            personal_info=PersonalInfo(full_name="Alex Smith"),
            total_years_experience=-2.5,
        )


def test_validator_cleans_markdown_fences():
    """Ensure PydanticValidator strips markdown ```json ``` code fences cleanly."""
    raw_payload = """
    ```json
    {
        "personal_info": {
            "full_name": "Marcus Aurelius",
            "email": "marcus@rome.gov"
        },
        "total_years_experience": 10.0,
        "skills": {
            "technical_skills": ["Philosophy", "Strategy"],
            "soft_skills": ["Stoicism"],
            "tools_and_platforms": [],
            "languages": ["Latin", "Greek"]
        },
        "work_experience": [],
        "education": [],
        "certifications": []
    }
    ```
    """
    is_valid, parsed_obj, errors = PydanticValidator.validate(raw_payload, ParsedResume)
    assert is_valid is True
    assert parsed_obj is not None
    assert parsed_obj.personal_info.full_name == "Marcus Aurelius"
    assert len(errors) == 0


def test_validator_catches_syntax_errors():
    """Ensure malformed JSON syntax is caught and reports json_syntax error."""
    malformed_json = '{"personal_info": {"full_name": "Alice"'  # Missing closing braces
    is_valid, parsed_obj, errors = PydanticValidator.validate(malformed_json, ParsedResume)
    assert is_valid is False
    assert parsed_obj is None
    assert len(errors) == 1
    assert errors[0].error_type == "json_decode_error"
