import os
import re
from fastapi import APIRouter, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.gemini_flash import generate_outline
from app.gemini_pro import generate_story
from app.image_generator import generate_image
from app.layout_builder import build_comic_layout
from app.exporters import save_pdf

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

router = APIRouter()


class PromptRequest(BaseModel):
    story_prompt: str = Field(..., description="Main story premise or prompt")
    character_name: str = Field("Finn", description="Hero of the comic")
    setting: str = Field("Enchanted Forest", description="Location/Setting")
    tone: str = Field("Dramatic", description="Tone (e.g. dramatic, funny, light-hearted)")
    art_style: str = Field("Comic Book", description="Art Style (e.g. anime, comic book, pixel art)")


def _derive_comic_title(prompt: str, character_name: str) -> str:
    """Creates an engaging title from prompt and character name."""
    clean_p = re.sub(r"[^\w\s]", "", prompt).strip()
    words = clean_p.split()
    short_theme = " ".join(words[:4]).title() if words else "The Great Journey"
    return f"{character_name}: {short_theme}"


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Loads the homepage with the comic generator form."""
    return templates.TemplateResponse(request, "index.html", {})


@router.post("/generate", response_class=HTMLResponse)
async def generate_comic_form(
    request: Request,
    story_prompt: str = Form(...),
    character_name: str = Form("Hero"),
    setting: str = Form("Enchanted Forest"),
    tone: str = Form("Dramatic"),
    art_style: str = Form("Comic Book")
):
    """
    Form submission handler: runs the complete 5-panel comic generation pipeline
    and renders the comic preview page.
    """
    try:
        # 1. Derive comic title
        comic_title = _derive_comic_title(story_prompt, character_name)

        # 2. Generate 5-panel structured outline with Gemini Flash
        print(f"[ComicCraft] Generating outline for '{comic_title}'...")
        outline = generate_outline(
            prompt=story_prompt,
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style
        )

        # 3. Generate detailed narration, captions, and dialogues with Gemini Pro
        print(f"[ComicCraft] Generating story script and dialogues...")
        story_data = generate_story(
            outline=outline,
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style
        )

        # 4. Generate illustrations for each panel with Stable Diffusion
        image_paths = []
        for panel in outline:
            panel_num = panel.get("panel_number", 1)
            img_prompt = panel.get("image_prompt", f"{character_name} in {setting}")
            print(f"[ComicCraft] Generating illustration for panel {panel_num}...")
            img_path = generate_image(
                prompt=img_prompt,
                art_style=art_style,
                panel_number=panel_num
            )
            image_paths.append(img_path)

        # 5. Build structured layout
        layout = build_comic_layout(outline, story_data, image_paths)

        # 6. Compile and save PDF
        pdf_path = save_pdf(
            layout=layout,
            comic_title=comic_title,
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style
        )

        return templates.TemplateResponse(
            request,
            "comic_preview.html",
            {
                "comic_title": comic_title,
                "story_prompt": story_prompt,
                "character_name": character_name,
                "setting": setting,
                "tone": tone,
                "art_style": art_style,
                "layout": layout,
                "pdf_path": pdf_path
            }
        )

    except Exception as e:
        print(f"[ComicCraft] Error during generation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate comic: {str(e)}")


@router.post("/generate-comic/json")
async def generate_comic_json(payload: PromptRequest):
    """
    API endpoint that accepts a JSON payload, executes the comic generation pipeline,
    and returns the structured layout data and exportable PDF path.
    """
    try:
        comic_title = _derive_comic_title(payload.story_prompt, payload.character_name)

        outline = generate_outline(
            prompt=payload.story_prompt,
            character_name=payload.character_name,
            setting=payload.setting,
            tone=payload.tone,
            art_style=payload.art_style
        )

        story_data = generate_story(
            outline=outline,
            character_name=payload.character_name,
            setting=payload.setting,
            tone=payload.tone,
            art_style=payload.art_style
        )

        image_paths = []
        for panel in outline:
            p_num = panel.get("panel_number", 1)
            img_prompt = panel.get("image_prompt", "")
            img_path = generate_image(prompt=img_prompt, art_style=payload.art_style, panel_number=p_num)
            image_paths.append(img_path)

        layout = build_comic_layout(outline, story_data, image_paths)

        pdf_path = save_pdf(
            layout=layout,
            comic_title=comic_title,
            character_name=payload.character_name,
            setting=payload.setting,
            tone=payload.tone,
            art_style=payload.art_style
        )

        return JSONResponse({
            "status": "success",
            "comic_title": comic_title,
            "pdf_path": pdf_path,
            "layout": layout
        })

    except Exception as e:
        print(f"[ComicCraft] API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-image")
async def test_image(
    prompt: str = Query("A brave adventurer stepping into a glowing cave", description="Image prompt to test"),
    art_style: str = Query("comic book", description="Art style"),
    panel_number: int = Query(1, description="Panel number")
):
    """
    Developer utility route to test image generation directly from a prompt.
    """
    try:
        img_path = generate_image(prompt=prompt, art_style=art_style, panel_number=panel_number)
        return JSONResponse({
            "status": "success",
            "prompt": prompt,
            "art_style": art_style,
            "panel_number": panel_number,
            "image_path": img_path
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export-success", response_class=HTMLResponse)
async def export_success(
    request: Request,
    pdf_path: str = Query("", description="Relative path of the generated PDF")
):
    """
    Displays the export confirmation page after downloading or creating the comic PDF.
    """
    return templates.TemplateResponse(
        request,
        "export_success.html",
        {
            "pdf_path": pdf_path
        }
    )


@router.get("/download-pdf")
async def download_pdf(pdf_path: str = Query(..., description="Path to download")):
    """
    Direct file download helper for exported PDFs.
    """
    clean_path = pdf_path.lstrip("/")
    abs_path = os.path.join(BASE_DIR, clean_path)
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="Requested PDF file not found")
    filename = os.path.basename(abs_path)
    return FileResponse(
        path=abs_path,
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
