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

/* Force light color scheme */
:root, html, body, .gradio-container, .dark {
  color-scheme: light !important;
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
  --bg-page: #f8fafc !important;
  --bg-surface: #ffffff !important;
  --border-color: #e2e8f0 !important;
  --body-text-color: #0f172a !important;
  --block-label-text-color: #0f172a !important;
  --block-title-text-color: #0f172a !important;
  --body-text-color-subdued: #475569 !important;
}

body, .gradio-container {
  background-color: #f8fafc !important;
  font-family: 'Inter', -apple-system, sans-serif !important;
  color: #0f172a !important;
  max-width: 1240px !important;
  margin: 0 auto !important;
}

.dark, .dark * {
  color-scheme: light !important;
}

.gradio-container {
  padding: 16px 24px !important;
}

/* Header Banner */
.custom-header {
  background: #ffffff !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 12px !important;
  padding: 16px 24px !important;
  margin-bottom: 24px !important;
  display: flex !important;
  justify-content: space-between !important;
  align-items: center !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
}

.brand-group {
  display: flex !important;
  align-items: center !important;
  gap: 12px !important;
}

.brand-icon {
  width: 36px !important;
  height: 36px !important;
  background: #0f172a !important;
  color: #ffffff !important;
  border-radius: 8px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  font-size: 18px !important;
}

.brand-name {
  font-size: 1.05rem !important;
  font-weight: 700 !important;
  color: #0f172a !important;
  letter-spacing: -0.01em !important;
}

.brand-desc {
  font-size: 0.78rem !important;
  color: #475569 !important;
}

.badge-group {
  display: flex !important;
  align-items: center !important;
  gap: 10px !important;
}

.pill-badge {
  display: flex !important;
  align-items: center !important;
  gap: 6px !important;
  padding: 5px 12px !important;
  border-radius: 999px !important;
  font-size: 0.75rem !important;
  font-weight: 600 !important;
}

.pill-green {
  background: #ecfdf5 !important;
  border: 1px solid #a7f3d0 !important;
  color: #047857 !important;
}

.pill-blue {
  background: #eff6ff !important;
  border: 1px solid #bfdbfe !important;
  color: #1d4ed8 !important;
}

.dot-green {
  width: 6px !important;
  height: 6px !important;
  background: #047857 !important;
  border-radius: 50% !important;
}

/* Tabs: High Contrast */
.tabs > div, .tab-nav {
  border-bottom: 1px solid #e2e8f0 !important;
  background: transparent !important;
}

button[role="tab"], .tab-nav button, .tabs > div > button {
  color: #475569 !important;
  font-weight: 600 !important;
  font-size: 0.88rem !important;
  background: transparent !important;
  border: none !important;
  padding: 10px 16px !important;
  opacity: 1 !important;
}

button[role="tab"].selected, .tab-nav button.selected, .tabs > div > button.selected {
  color: #0f172a !important;
  border-bottom: 2.5px solid #0f172a !important;
  font-weight: 700 !important;
}

/* Dropzone & Labels */
label span, .block-title, .block-label {
  color: #0f172a !important;
  font-weight: 600 !important;
  font-size: 0.84rem !important;
}

.file-preview-holder, .drop-file, .upload-container, .upload-container * {
  color: #334155 !important;
}

/* Accordion */
.accordion, .label-wrap, .label-wrap span, button.accordion-header {
  color: #0f172a !important;
  font-weight: 600 !important;
  font-size: 0.88rem !important;
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
  padding: 12px 18px !important;
  font-size: 0.92rem !important;
  transition: all 0.15s ease !important;
}

button.primary-btn:hover, button.primary:hover {
  background: #1e293b !important;
}

/* Secondary Button */
button.secondary {
  background: #ffffff !important;
  color: #0f172a !important;
  border: 1px solid #cbd5e1 !important;
  font-weight: 600 !important;
  font-size: 0.78rem !important;
}

button.secondary:hover {
  background: #f1f5f9 !important;
}

/* Visual Profile Elements */
.placeholder-view {
  background: #ffffff !important;
  border: 1.5px dashed #cbd5e1 !important;
  border-radius: 12px !important;
  padding: 60px 24px !important;
  text-align: center !important;
  color: #475569 !important;
}

.placeholder-view h3 {
  color: #0f172a !important;
  font-weight: 700 !important;
}

.placeholder-view p {
  color: #64748b !important;
}

.metrics-strip {
  display: grid !important;
  grid-template-columns: repeat(4, 1fr) !important;
  gap: 12px !important;
  background: #f1f5f9 !important;
  padding: 12px 16px !important;
  border-radius: 8px !important;
  margin-bottom: 20px !important;
}

.m-card {
  display: flex !important;
  flex-direction: column !important;
  gap: 2px !important;
}

.m-title {
  font-size: 0.7rem !important;
  text-transform: uppercase !important;
  font-weight: 600 !important;
  color: #64748b !important;
}

.m-value {
  font-size: 1rem !important;
  font-weight: 700 !important;
  color: #0f172a !important;
}

.profile-container {
  background: #ffffff !important;
  display: flex !important;
  flex-direction: column !important;
  gap: 18px !important;
}

.c-name {
  font-size: 1.35rem !important;
  font-weight: 700 !important;
  color: #0f172a !important;
  letter-spacing: -0.01em !important;
}

.c-summary {
  font-size: 0.86rem !important;
  color: #334155 !important;
  line-height: 1.55 !important;
}

.chips-row {
  display: flex !important;
  flex-wrap: wrap !important;
  gap: 8px !important;
}

.contact-chip {
  background: #f1f5f9 !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 6px !important;
  padding: 5px 10px !important;
  font-size: 0.78rem !important;
  color: #1e293b !important;
  text-decoration: none !important;
  font-weight: 500 !important;
}

.sec-heading {
  font-size: 0.75rem !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
  font-weight: 700 !important;
  color: #475569 !important;
  border-bottom: 1px solid #e2e8f0 !important;
  padding-bottom: 6px !important;
  margin-top: 6px !important;
}

.skill-tag {
  display: inline-block !important;
  background: #f8fafc !important;
  border: 1px solid #e2e8f0 !important;
  color: #0f172a !important;
  border-radius: 6px !important;
  padding: 3px 9px !important;
  font-size: 0.76rem !important;
  font-weight: 500 !important;
  margin: 2px 4px 2px 0 !important;
}

.skill-tag-blue {
  background: #eff6ff !important;
  border-color: #dbeafe !important;
  color: #1e40af !important;
}

.timeline-item {
  border-left: 2px solid #cbd5e1 !important;
  padding-left: 14px !important;
  margin-left: 4px !important;
  margin-bottom: 14px !important;
  position: relative !important;
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
  font-size: 0.88rem !important;
  font-weight: 600 !important;
  color: #0f172a !important;
}

.t-company {
  font-size: 0.78rem !important;
  color: #475569 !important;
  margin-bottom: 4px !important;
}

.t-bullets {
  padding-left: 16px !important;
  font-size: 0.8rem !important;
  color: #334155 !important;
  line-height: 1.45 !important;
  margin: 0 !important;
}

.edu-row {
  margin-bottom: 8px !important;
}

.e-degree {
  font-size: 0.85rem !important;
  font-weight: 600 !important;
  color: #0f172a !important;
}

.e-inst {
  font-size: 0.78rem !important;
  color: #475569 !important;
}

.cert-pill {
  display: inline-block !important;
  background: #ecfdf5 !important;
  border: 1px solid #a7f3d0 !important;
  color: #047857 !important;
  padding: 3px 8px !important;
  border-radius: 6px !important;
  font-size: 0.75rem !important;
  font-weight: 500 !important;
  margin: 3px 4px 3px 0 !important;
}
"""

HEADER_HTML = """
<div class="custom-header" style="background:#ffffff !important; border:1px solid #e2e8f0; border-radius:12px; padding:16px 24px; margin-bottom:20px; display:flex; justify-content:space-between; align-items:center;">
  <div class="brand-group" style="display:flex; align-items:center; gap:12px;">
    <div class="brand-icon" style="width:36px; height:36px; background:#0f172a; color:#ffffff; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:18px;">📄</div>
    <div>
      <div class="brand-name" style="font-size:1.05rem; font-weight:700; color:#0f172a !important; letter-spacing:-0.01em;">Resume Parser — Structured Output Agent</div>
      <div class="brand-desc" style="font-size:0.78rem; color:#475569 !important;">Converts messy resumes into validated JSON using Google Gemini</div>
    </div>
  </div>
  <div class="badge-group" style="display:flex; align-items:center; gap:10px;">
    <div class="pill-badge pill-blue" style="background:#eff6ff !important; border:1px solid #bfdbfe; color:#1d4ed8 !important; padding:5px 12px; border-radius:999px; font-size:0.75rem; font-weight:600;">⚡ Powered by Gemini 2.5</div>
    <div class="pill-badge pill-green" style="background:#ecfdf5 !important; border:1px solid #a7f3d0; color:#047857 !important; padding:5px 12px; border-radius:999px; font-size:0.75rem; font-weight:600;"><span class="dot-green" style="display:inline-block; width:6px; height:6px; background:#047857; border-radius:50%; margin-right:4px;"></span> Self-Healing Loop Active</div>
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
FORCE_LIGHT_JS = "() => { document.documentElement.classList.remove('dark'); document.body.classList.remove('dark'); }"

with gr.Blocks(title="AI Resume Parser", js=FORCE_LIGHT_JS) as demo:
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
        demo.launch(server_name="0.0.0.0", server_port=7860, css=CUSTOM_CSS, theme=theme, js=FORCE_LIGHT_JS)
    except TypeError:
        demo.launch(server_name="0.0.0.0", server_port=7860)


