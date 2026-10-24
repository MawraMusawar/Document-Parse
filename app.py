"""Hugging Face Spaces Entrypoint for AI Resume Parser.

Runs natively on Hugging Face ZeroGPU with native Gradio launch, while providing
a modern, sleek, custom-designed light aesthetic matching the local experience.
"""

import os
import html
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
Location: San Francisco, CA | LinkedIn: https://linkedin.com/in/johndoe | GitHub: https://github.com/johndoe

PROFESSIONAL SUMMARY
Senior Software Engineer with over 6 years of experience architecting distributed cloud systems, high-throughput microservices, and AI-enabled workflows.

TECHNICAL SKILLS
- Programming Languages: Python, Go, TypeScript, SQL
- Frameworks & Libraries: FastAPI, Django, React, Pydantic, PyTorch
- Cloud & DevOps: AWS (EC2, S3, Lambda), Docker, Kubernetes, Terraform, GitHub Actions
- Databases: PostgreSQL, Redis, MongoDB
- Languages: English (Fluent), Spanish (Conversational)

WORK EXPERIENCE
Senior Backend Engineer | CloudScale Inc. | San Francisco, CA
March 2021 - Present
- Designed and maintained high-performance microservices processing over 40M daily API requests with 99.99% uptime.
- Led migration of legacy monolith to containerized FastAPI services on Kubernetes, reducing p99 latency by 35%.
- Implemented real-time telemetry pipelines using Redis Streams and Prometheus.
- Tech Stack: Python, FastAPI, Docker, Kubernetes, PostgreSQL, AWS

Software Engineer | NextGen Analytics | San Jose, CA
July 2018 - February 2021
- Developed ETL pipelines ingesting 500GB+ telemetry data daily using Python and Apache Kafka.
- Collaborated with frontend team to design clean RESTful and GraphQL APIs for client dashboards.

EDUCATION
University of California, Berkeley
Bachelor of Science in Computer Science
Graduated: 2018 | GPA: 3.8 / 4.0

CERTIFICATIONS
- AWS Certified Solutions Architect - Associate | Amazon Web Services | 2022
- Certified Kubernetes Administrator (CKA) | Linux Foundation | 2023"""

# Hugging Face ZeroGPU compatibility
try:
    import spaces
except ImportError:
    class spaces:
        @staticmethod
        def GPU(fn=None, *args, **kwargs):
            if fn is not None:
                return fn
            def wrapper(f):
                return f
            return wrapper


CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
  --bg-page: #f8fafc !important;
  --bg-surface: #ffffff !important;
  --border-color: #e2e8f0 !important;
  --text-main: #0f172a !important;
  --text-muted: #64748b !important;
}

body, .gradio-container {
  background-color: #f8fafc !important;
  font-family: 'Inter', -apple-system, sans-serif !important;
  color: #0f172a !important;
  max-width: 1240px !important;
  margin: 0 auto !important;
}

.gradio-container {
  padding: 16px 24px !important;
}

/* Header Banner */
.custom-header {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px 24px;
  margin-bottom: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.brand-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-icon {
  width: 36px;
  height: 36px;
  background: #0f172a;
  color: #ffffff;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.brand-name {
  font-size: 1.05rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.01em;
}

.brand-desc {
  font-size: 0.78rem;
  color: #64748b;
}

.badge-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.pill-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
}

.pill-green {
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  color: #059669;
}

.pill-blue {
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  color: #2563eb;
}

.dot-green {
  width: 6px;
  height: 6px;
  background: #059669;
  border-radius: 50%;
}

/* Gradio Card Overrides */
.block {
  background: #ffffff !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 12px !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03) !important;
}

/* Primary Button */
button.primary-btn, button.primary {
  background: #0f172a !important;
  color: #ffffff !important;
  border-radius: 8px !important;
  font-weight: 600 !important;
  border: none !important;
  padding: 10px 18px !important;
  transition: all 0.15s ease !important;
}

button.primary-btn:hover, button.primary:hover {
  background: #1e293b !important;
}

/* Visual Profile Elements */
.placeholder-view {
  background: #ffffff;
  border: 1.5px dashed #cbd5e1;
  border-radius: 12px;
  padding: 60px 24px;
  text-align: center;
  color: #64748b;
}

.metrics-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  background: #f1f5f9;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.m-card {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.m-title {
  font-size: 0.7rem;
  text-transform: uppercase;
  font-weight: 600;
  color: #64748b;
}

.m-value {
  font-size: 1rem;
  font-weight: 700;
  color: #0f172a;
}

.profile-container {
  background: #ffffff;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.c-name {
  font-size: 1.35rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.01em;
}

.c-summary {
  font-size: 0.86rem;
  color: #475569;
  line-height: 1.55;
}

.chips-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.contact-chip {
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 0.78rem;
  color: #334155;
  text-decoration: none;
  font-weight: 500;
}

.sec-heading {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 700;
  color: #94a3b8;
  border-bottom: 1px solid #f1f5f9;
  padding-bottom: 6px;
  margin-top: 6px;
}

.skill-tag {
  display: inline-block;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  color: #0f172a;
  border-radius: 6px;
  padding: 3px 9px;
  font-size: 0.76rem;
  font-weight: 500;
  margin: 2px 4px 2px 0;
}

.skill-tag-blue {
  background: #eff6ff;
  border-color: #dbeafe;
  color: #1e40af;
}

.timeline-item {
  border-left: 2px solid #e2e8f0;
  padding-left: 14px;
  margin-left: 4px;
  margin-bottom: 14px;
  position: relative;
}

.timeline-item::before {
  content: '';
  position: absolute;
  left: -5px;
  top: 4px;
  width: 8px;
  height: 8px;
  background: #0f172a;
  border-radius: 50%;
}

.t-role {
  font-size: 0.88rem;
  font-weight: 600;
  color: #0f172a;
}

.t-company {
  font-size: 0.78rem;
  color: #64748b;
  margin-bottom: 4px;
}

.t-bullets {
  padding-left: 16px;
  font-size: 0.8rem;
  color: #334155;
  line-height: 1.45;
  margin: 0;
}

.edu-row {
  margin-bottom: 8px;
}

.e-degree {
  font-size: 0.85rem;
  font-weight: 600;
  color: #0f172a;
}

.e-inst {
  font-size: 0.78rem;
  color: #64748b;
}

.cert-pill {
  display: inline-block;
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  color: #047857;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 500;
  margin: 3px 4px 3px 0;
}
"""

HEADER_HTML = """
<div class="custom-header">
  <div class="brand-group">
    <div class="brand-icon">📄</div>
    <div>
      <div class="brand-name">Resume Parser — Structured Output Agent</div>
      <div class="brand-desc">Converts messy resumes into validated JSON using Google Gemini</div>
    </div>
  </div>
  <div class="badge-group">
    <div class="pill-badge pill-blue">⚡ Powered by Gemini 2.5</div>
    <div class="pill-badge pill-green"><span class="dot-green"></span> Self-Healing Loop Active</div>
  </div>
</div>
"""

PLACEHOLDER_HTML = """
<div class="placeholder-view">
  <div style="font-size: 32px; margin-bottom: 10px;">📋</div>
  <h3 style="font-size: 1rem; font-weight: 600; color: #0f172a; margin-bottom: 4px;">Structured Profile Breakdown</h3>
  <p style="font-size: 0.82rem; color: #64748b; max-width: 380px; margin: 0 auto;">Upload a PDF, Word document, or paste candidate text on the left, then click <strong>Extract Structured Resume</strong>.</p>
</div>
"""


def render_visual_profile(data: Dict[str, Any], metrics: Dict[str, Any]) -> str:
    """Format structured resume JSON into a clean, aesthetic visual presentation."""
    p_info = data.get("personal_info") or {}
    full_name = html.escape(str(p_info.get("full_name") or "Candidate"))
    summary = html.escape(str(data.get("summary") or "No summary provided."))

    # Contact chips
    contact_chips = []
    if p_info.get("email"):
        contact_chips.append(f'<a href="mailto:{html.escape(p_info["email"])}" class="contact-chip">✉️ {html.escape(p_info["email"])}</a>')
    if p_info.get("phone"):
        contact_chips.append(f'<span class="contact-chip">📞 {html.escape(p_info["phone"])}</span>')
    if p_info.get("location"):
        contact_chips.append(f'<span class="contact-chip">📍 {html.escape(p_info["location"])}</span>')
    if p_info.get("linkedin_url"):
        contact_chips.append(f'<a href="{html.escape(p_info["linkedin_url"])}" target="_blank" class="contact-chip">LinkedIn ↗</a>')
    if p_info.get("github_url"):
        contact_chips.append(f'<a href="{html.escape(p_info["github_url"])}" target="_blank" class="contact-chip">GitHub ↗</a>')
    contact_chips_html = "".join(contact_chips)

    # Skills
    skills_obj = data.get("skills") or {}
    tech_skills = skills_obj.get("technical_skills") or []
    tools_skills = skills_obj.get("tools_and_platforms") or []
    skills_html = "".join([f'<span class="skill-tag skill-tag-blue">{html.escape(str(s))}</span>' for s in tech_skills])
    skills_html += "".join([f'<span class="skill-tag">{html.escape(str(t))}</span>' for t in tools_skills])

    # Work Experience Timeline
    work_exp = data.get("work_experience") or []
    timeline_html = ""
    for exp in work_exp:
        role = html.escape(str(exp.get("role") or ""))
        company = html.escape(str(exp.get("company") or ""))
        dates = html.escape(f"{exp.get('start_date') or ''} - {exp.get('end_date') or ''}".strip(" -"))
        bullets = "".join([f"<li>{html.escape(str(b))}</li>" for b in (exp.get("responsibilities") or [])])
        timeline_html += f"""
        <div class="timeline-item">
          <div class="t-role">{role}</div>
          <div class="t-company">{company} • {dates}</div>
          <ul class="t-bullets">{bullets}</ul>
        </div>
        """

    # Education
    education_list = data.get("education") or []
    edu_html = ""
    for edu in education_list:
        degree = html.escape(f"{edu.get('degree') or ''} in {edu.get('field_of_study') or ''}".strip(" in"))
        inst = html.escape(f"{edu.get('institution') or ''} ({edu.get('end_year') or ''})".strip(" ()"))
        edu_html += f"""
        <div class="edu-row">
          <div class="e-degree">{degree}</div>
          <div class="e-inst">{inst}</div>
        </div>
        """

    # Certifications
    certs = data.get("certifications") or []
    cert_html = "".join([f'<span class="cert-pill">🏅 {html.escape(str(c.get("title") or ""))} ({html.escape(str(c.get("issuer") or ""))})</span>' for c in certs])

    years_exp = data.get("total_years_experience") or 0
    latency = metrics.get("latency", 0)
    attempts = metrics.get("attempts", 1)

    return f"""
    <div class="profile-container">
      <div class="metrics-strip">
        <div class="m-card">
          <div class="m-title">Latency</div>
          <div class="m-value">{latency:.0f} ms</div>
        </div>
        <div class="m-card">
          <div class="m-title">Attempts</div>
          <div class="m-value">{attempts} / 3</div>
        </div>
        <div class="m-card">
          <div class="m-title">Experience</div>
          <div class="m-value">{years_exp} Yrs</div>
        </div>
        <div class="m-card">
          <div class="m-title">Validation</div>
          <div class="m-value" style="color: #059669;">Passed ✓</div>
        </div>
      </div>

      <div>
        <div class="c-name">{full_name}</div>
        <div class="c-summary">{summary}</div>
      </div>

      <div class="chips-row">
        {contact_chips_html}
      </div>

      <div class="sec-heading">Skills & Technologies</div>
      <div>
        {skills_html if skills_html else '<span style="color:#94a3b8; font-size:0.8rem;">No skills specified</span>'}
      </div>

      <div class="sec-heading">Work Experience</div>
      <div>
        {timeline_html if timeline_html else '<span style="color:#94a3b8; font-size:0.8rem;">No work experience specified</span>'}
      </div>

      <div class="sec-heading">Education & Certifications</div>
      <div>
        {edu_html if edu_html else '<span style="color:#94a3b8; font-size:0.8rem;">No education specified</span>'}
        <div style="margin-top: 6px;">{cert_html}</div>
      </div>
    </div>
    """


@spaces.GPU
def parse_resume_action(
    file_obj: Any,
    raw_text: str,
) -> Tuple[str, Optional[Dict[str, Any]], str]:
    """ZeroGPU handler: extracts text, invokes self-healing Gemini agent, and returns visual profile and JSON."""
    if not gemini_client.is_configured:
        err_html = """
        <div class="placeholder-view" style="border-color: #fca5a5; color: #b91c1c;">
          <div style="font-size: 28px; margin-bottom: 8px;">⚠️</div>
          <div style="font-weight: 600;">Gemini API Key Missing</div>
          <div style="font-size: 0.8rem; margin-top: 4px;">Please configure <code>GEMINI_API_KEY</code> in Space Settings under <strong>Variables and secrets</strong>.</div>
        </div>
        """
        return err_html, None, "⚠️ Gemini API key is not configured in Space secrets."

    content = ""
    if file_obj is not None:
        try:
            path = file_obj.name if hasattr(file_obj, "name") else str(file_obj)
            with open(path, "rb") as f:
                content = extract_text_from_file(f.read(), os.path.basename(path))
        except Exception as e:
            err_html = f"""
            <div class="placeholder-view" style="border-color: #fca5a5; color: #b91c1c;">
              <div style="font-size: 28px; margin-bottom: 8px;">❌</div>
              <div style="font-weight: 600;">Error Reading File</div>
              <div style="font-size: 0.8rem; margin-top: 4px;">{html.escape(str(e))}</div>
            </div>
            """
            return err_html, None, f"❌ Error reading file: {str(e)}"
    elif raw_text and len(raw_text.strip()) >= 20:
        content = raw_text.strip()
    else:
        warn_html = """
        <div class="placeholder-view" style="border-color: #fcd34d; color: #b45309;">
          <div style="font-size: 28px; margin-bottom: 8px;">⚠️</div>
          <div style="font-weight: 600;">Insufficient Input</div>
          <div style="font-size: 0.8rem; margin-top: 4px;">Please upload a resume (PDF, Word DOCX, or TXT) or paste resume text (minimum 20 characters).</div>
        </div>
        """
        return warn_html, None, "⚠️ Please provide a resume file or text."

    if len(content) < 20:
        warn_html = """
        <div class="placeholder-view" style="border-color: #fcd34d; color: #b45309;">
          <div style="font-size: 28px; margin-bottom: 8px;">⚠️</div>
          <div style="font-weight: 600;">Text Too Short</div>
          <div style="font-size: 0.8rem; margin-top: 4px;">The extracted document content has less than 20 characters.</div>
        </div>
        """
        return warn_html, None, "⚠️ Content is too short."

    # Execute structured parsing with self-healing retry loop
    result = agent.parse(content)

    if result.success and result.data:
        data_dict = result.data.model_dump()
        metrics = {
            "latency": result.processing_time_ms,
            "attempts": result.attempts_made,
        }
        visual_html = render_visual_profile(data_dict, metrics)
        status_msg = f"✅ Extracted successfully in {result.processing_time_ms:.0f} ms (Attempt {result.attempts_made} of 3)"
        return visual_html, data_dict, status_msg
    else:
        failures = result.validation_failures or []
        err_items = "".join([f"<li><strong>{html.escape(e.field)}</strong>: {html.escape(e.message)}</li>" for e in failures])
        err_html = f"""
        <div class="placeholder-view" style="border-color: #fca5a5; color: #b91c1c;">
          <div style="font-size: 28px; margin-bottom: 8px;">❌</div>
          <div style="font-weight: 600;">Validation Failed After {result.attempts_made} Attempts</div>
          <ul style="text-align: left; font-size: 0.8rem; margin-top: 8px; display: inline-block;">{err_items}</ul>
        </div>
        """
        return err_html, None, f"❌ Failed after {result.attempts_made} validation attempts."


def set_sample_resume():
    """Populate input textbox with sample resume text."""
    return SAMPLE_RESUME


# Build Sleek Gradio Interface
theme = gr.themes.Default(font=gr.themes.GoogleFont("Inter"))

with gr.Blocks(title="AI Resume Parser") as demo:
    gr.HTML(HEADER_HTML)

    with gr.Row(equal_height=False):
        # Left: Input Controls
        with gr.Column(scale=1):
            with gr.Tabs():
                with gr.TabItem("📁 Upload Document"):
                    file_input = gr.File(
                        label="Drop PDF, DOCX, or TXT Resume",
                        file_types=[".pdf", ".docx", ".txt"],
                        type="filepath",
                    )
                with gr.TabItem("📝 Paste Text"):
                    text_input = gr.Textbox(
                        label="Resume Text",
                        lines=10,
                        placeholder="Paste plain resume text here...",
                    )
                    sample_btn = gr.Button("📋 Load Sample Resume", variant="secondary", size="sm")

            submit_btn = gr.Button("🚀 Extract Structured Resume", variant="primary", elem_classes=["primary-btn"])
            status_toast = gr.Markdown("")

        # Right: Rich Output View & Raw JSON
        with gr.Column(scale=1):
            visual_output = gr.HTML(value=PLACEHOLDER_HTML)
            with gr.Accordion("🎯 Raw Validated JSON", open=False):
                json_output = gr.JSON(label="Structured Resume JSON")

    # Wire handlers
    sample_btn.click(fn=set_sample_resume, inputs=[], outputs=[text_input])
    submit_btn.click(
        fn=parse_resume_action,
        inputs=[file_input, text_input],
        outputs=[visual_output, json_output, status_toast],
    )

if __name__ == "__main__":
    try:
        demo.launch(server_name="0.0.0.0", server_port=7860, css=CUSTOM_CSS, theme=theme)
    except TypeError:
        demo.launch(server_name="0.0.0.0", server_port=7860)

