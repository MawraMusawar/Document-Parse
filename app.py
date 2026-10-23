"""Hugging Face Spaces & Gradio Web Application Entrypoint for AI Resume Parser."""

import os
from typing import Any, Dict, Optional, Tuple
import gradio as gr
from app.config import get_settings
from app.agent.gemini_client import GeminiClient
from app.agent.retry_agent import ResumeStructuredAgent
from app.utils.file_extractor import extract_text_from_file

settings = get_settings()
gemini_client = GeminiClient()
agent = ResumeStructuredAgent(gemini_client=gemini_client)

SAMPLE_RESUME = """Johnathan Doe
Email: johnathan.doe@example.com | Phone: +1 (555) 234-5678
Location: San Francisco, CA | LinkedIn: https://linkedin.com/in/johndoe

Professional Summary:
Senior Full Stack Engineer with 6+ years of experience designing, building, and deploying microservices and modern web applications using Python, FastAPI, Docker, and AWS.

Work Experience:
Senior Software Engineer - TechCorp Inc. (Jan 2021 - Present)
- Architected and deployed microservices processing 5M+ daily requests with 99.99% uptime.
- Led migration of legacy monolith to FastAPI and Docker containers on AWS ECS.
- Mentored 4 junior engineers on clean code and automated testing practices.

Software Engineer - StartupHub LLC (Jun 2018 - Dec 2020)
- Built real-time analytics dashboards using React, Python, and PostgreSQL.
- Optimized database query performance, reducing 95th percentile response times by 40%.

Education:
University of California, Berkeley (2014 - 2018)
Bachelor of Science in Computer Science | GPA: 3.8/4.0

Technical Skills:
- Programming: Python, TypeScript, JavaScript, SQL, Bash
- Frameworks: FastAPI, Django, React, Next.js
- Cloud & DevOps: Docker, Kubernetes, AWS (S3, ECS, RDS), CI/CD, Git
- Databases: PostgreSQL, Redis, MongoDB

Certifications:
- AWS Certified Solutions Architect - Associate (2022)
"""


def parse_resume(
    file_obj: Any,
    raw_text: str,
) -> Tuple[Optional[Dict[str, Any]], str]:
    """Parse resume document or raw text and return structured JSON with telemetry status."""
    if not gemini_client.is_configured:
        return None, (
            "⚠️ **Gemini API Key Missing**\n\n"
            "Please configure `GEMINI_API_KEY` in the Space Settings under **Variables and secrets**."
        )

    extracted_text = ""

    # Case 1: Uploaded file
    if file_obj is not None:
        try:
            file_path = file_obj.name if hasattr(file_obj, "name") else str(file_obj)
            with open(file_path, "rb") as f:
                content_bytes = f.read()
            extracted_text = extract_text_from_file(content_bytes, os.path.basename(file_path))
        except Exception as e:
            return None, f"❌ **Error reading file**: `{str(e)}`"
    # Case 2: Pasted text
    elif raw_text and len(raw_text.strip()) >= 20:
        extracted_text = raw_text.strip()
    else:
        return None, "⚠️ Please upload a resume file (PDF, Word DOCX, or TXT) or paste resume text (minimum 20 characters)."

    if len(extracted_text) < 20:
        return None, "⚠️ Extracted text is too short (minimum 20 characters required)."

    # Execute structured parsing with self-healing retries
    result = agent.parse(extracted_text)

    if result.success and result.data:
        status_md = (
            f"### ✅ Parsing Successful!\n"
            f"- **Validation Status**: Passed\n"
            f"- **Attempts Executed**: `{result.attempts_made}`\n"
            f"- **Latency**: `{result.processing_time_ms:.1f} ms`\n"
        )
        return result.data.model_dump(), status_md
    else:
        errors = result.validation_failures or []
        err_list = "\n".join([f"- **`{e.field}`**: {e.message}" for e in errors]) or "Unknown validation issue"
        status_md = (
            f"### ❌ Parsing Failed After `{result.attempts_made}` Attempts\n\n"
            f"**Validation Failures:**\n{err_list}\n\n"
            f"- **Latency**: `{result.processing_time_ms:.1f} ms`"
        )
        return None, status_md


def load_sample_text() -> str:
    """Helper to populate the input textbox with sample resume text."""
    return SAMPLE_RESUME


# Build Gradio UI
with gr.Blocks(title="AI Resume Parser") as demo:
    gr.Markdown(
        """
        # 📄 AI Resume Parser — Structured Output Agent
        Transform unstructured resumes into strictly validated JSON using **Google Gemini** with an automated **self-healing retry loop**.
        """
    )

    with gr.Row():
        with gr.Column(scale=1):
            file_input = gr.File(
                label="📁 Upload Resume Document",
                file_types=[".pdf", ".docx", ".txt"],
                type="filepath",
            )
            text_input = gr.Textbox(
                label="📝 Or Paste Resume Text Directly",
                lines=10,
                placeholder="Paste candidate resume text here...",
            )
            with gr.Row():
                sample_btn = gr.Button("📋 Load Sample Resume", variant="secondary")
                parse_btn = gr.Button("🚀 Parse Resume", variant="primary")

        with gr.Column(scale=1):
            status_box = gr.Markdown("💡 *Upload a document or load sample text and click **Parse Resume**.*")
            json_output = gr.JSON(label="🎯 Validated Structured JSON Output")

    # Wire event handlers
    sample_btn.click(fn=load_sample_text, inputs=[], outputs=[text_input])
    parse_btn.click(
        fn=parse_resume,
        inputs=[file_input, text_input],
        outputs=[json_output, status_box],
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
