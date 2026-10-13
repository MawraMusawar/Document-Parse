"""Validation engine for parsing and extracting granular Pydantic schema errors."""

import json
import re
from typing import Any, List, Optional, Tuple, Type
from pydantic import BaseModel, ValidationError
from app.schemas.request import ValidationErrorDetail


class PydanticValidator:
    """Handles strict JSON parsing, Pydantic model validation, and error introspection."""

    @staticmethod
    def clean_json_string(raw_text: str) -> str:
        """Strip markdown code fence blocks (```json ... ```) or whitespace from LLM output.

        Args:
            raw_text: The raw output text returned by the language model.

        Returns:
            A clean JSON string candidate.
        """
        text = raw_text.strip()
        # Remove markdown code fences if present
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if fence_match:
            text = fence_match.group(1).strip()
        return text

    @classmethod
    def validate(
        cls,
        raw_text: str,
        target_model: Type[BaseModel],
    ) -> Tuple[bool, Optional[BaseModel], List[ValidationErrorDetail]]:
        """Validate raw LLM text against a target Pydantic model.

        Args:
            raw_text: Candidate JSON string from LLM.
            target_model: Pydantic model class to validate against.

        Returns:
            Tuple of (is_valid, validated_instance_or_none, list_of_error_details).
        """
        cleaned_text = cls.clean_json_string(raw_text)

        # 1. Check for basic JSON syntax validity
        try:
            parsed_dict = json.loads(cleaned_text)
        except json.JSONDecodeError as decode_err:
            error_detail = ValidationErrorDetail(
                field="root.json_syntax",
                error_type="json_decode_error",
                message=f"Invalid JSON syntax: {str(decode_err)}",
                input_value=cleaned_text[:200],
            )
            return False, None, [error_detail]

        # 2. Check Pydantic schema compliance
        try:
            instance = target_model.model_validate(parsed_dict)
            return True, instance, []
        except ValidationError as val_err:
            errors: List[ValidationErrorDetail] = []
            for err in val_err.errors():
                loc_path = ".".join(str(elem) for elem in err.get("loc", []))
                errors.append(
                    ValidationErrorDetail(
                        field=loc_path or "root",
                        error_type=err.get("type", "validation_error"),
                        message=err.get("msg", "Validation failed"),
                        input_value=err.get("input"),
                    )
                )
            return False, None, errors

    @staticmethod
    def construct_feedback_prompt(errors: List[ValidationErrorDetail]) -> str:
        """Construct an instructive error correction prompt for the next LLM retry attempt.

        Args:
            errors: List of ValidationErrorDetail objects indicating why validation failed.

        Returns:
            A formatted prompt instructing the LLM on specific corrections required.
        """
        issues = "\n".join(
            f"- Field: '{err.field}' -> Issue: {err.message} (You provided: {repr(err.input_value)})"
            for err in errors
        )

        return (
            "CRITICAL: Your previous JSON response failed strict Pydantic validation with the following errors:\n"
            f"{issues}\n\n"
            "Please correct these exact fields, ensure all data types match the required schema, "
            "and output only the corrected valid JSON."
        )
