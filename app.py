"""Hugging Face Spaces Entrypoint for AI Resume Parser.

Serves the exact custom-designed Web UI (HTML/CSS) at root, while maintaining
ZeroGPU compatibility and Gradio integration.
"""

import os
import uvicorn
import gradio as gr
from app.main import app as fastapi_app

# Hugging Face ZeroGPU compatibility
try:
    import spaces

    @spaces.GPU
    def _hf_zerogpu_detect():
        """Ensure Hugging Face ZeroGPU runtime discovers GPU decorator."""
        pass

except ImportError:
    pass

# Mount minimal Gradio app at /gradio for Hugging Face Gradio SDK compatibility
demo = gr.Blocks(title="AI Resume Parser - Gradio Interface")
with demo:
    gr.Markdown("# 📄 AI Resume Parser")
    gr.Markdown("Direct REST API & interactive Swagger documentation available at `/docs`.")

# Mount onto root FastAPI app:
# Root '/' serves the sleek, modern HTML/CSS interface (app/static/index.html)
# '/api/v1/...' handles file uploads and plain text extraction
# '/docs' serves the interactive OpenAPI documentation
# '/gradio' serves the fallback Gradio interface
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
