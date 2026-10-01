# 5. Project Development

This folder contains the complete runnable ComicCraft application source.

## Source Files

- `app/main.py`: FastAPI startup and static-file mounting.
- `app/routes.py`: form, JSON, image-test, preview, and PDF routes.
- `app/gemini_flash.py`: five-panel outline generation and fallback.
- `app/gemini_pro.py`: panel script generation and fallback.
- `app/image_generator.py`: Pollinations.ai image requests and local placeholder generation.
- `app/layout_builder.py`: panel layout assembly.
- `app/exporters.py`: multi-page PDF generation.
- `templates/`: input form, comic preview, and export-success pages.
- `requirements.txt`: Python dependencies.
- `.env.example`: example environment variable names; replace placeholder values locally.

## Run

From this directory, install dependencies and start the app:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/`. Configure `GEMINI_API_KEY` locally for Gemini text generation. `POLLINATIONS_TOKEN` is optional for images. Do not commit `.env` or real credentials.

## Generation Flow

The routes request the outline, script, and illustrations; pass those results to the layout builder; then render the preview or return JSON and a PDF path. The image generator uses Pollinations.ai and creates a local fallback image if requests fail.