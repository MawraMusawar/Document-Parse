"""Hugging Face Spaces Entrypoint for AI Resume Parser.

Serves the exact custom-designed Web UI (HTML/CSS) at root '/', while maintaining
ZeroGPU compatibility and Gradio integration.
"""

import os
import uvicorn
import gradio as gr
from app.main import app as fastapi_app
from app.main import agent, gemini_client
from app.utils.file_extractor import extract_text_from_file

# Hugging Face ZeroGPU compatibility
try:
    import spaces

    gpu_decorator = spaces.GPU
except ImportError:

    def gpu_decorator(fn):
        return fn


@gpu_decorator
def _zerogpu_parse(file_obj, text_input: str) -> str:
    """ZeroGPU registered handler to satisfy Hugging Face startup checks."""
    if not gemini_client.is_configured:
        return "Gemini API key is not configured."
    content = text_input or ""
    if file_obj is not None:
        try:
            path = file_obj.name if hasattr(file_obj, "name") else str(file_obj)
            with open(path, "rb") as f:
                content = extract_text_from_file(f.read(), os.path.basename(path))
        except Exception as e:
            return str(e)
    if len(content) < 20:
        return "Insufficient text."
    result = agent.parse(content)
    return result.model_dump_json() if result else "{}"


# Build Gradio interface with registered function so ZeroGPU startup check passes
with gr.Blocks(title="AI Resume Parser - Backend") as demo:
    gr.Markdown("# 📄 AI Resume Parser API")
    file_in = gr.File(label="Upload Resume", visible=False)
    text_in = gr.Textbox(label="Resume Text", visible=False)
    out = gr.Textbox(label="Result", visible=False)
    btn = gr.Button("Parse", visible=False)
    btn.click(fn=_zerogpu_parse, inputs=[file_in, text_in], outputs=out)

# Mount onto root FastAPI app:
# Root '/' serves the sleek, modern HTML/CSS interface (app/static/index.html)
# '/api/v1/...' handles file uploads and plain text extraction
# '/docs' serves the interactive OpenAPI documentation
# '/gradio' serves the registered Gradio endpoint
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
