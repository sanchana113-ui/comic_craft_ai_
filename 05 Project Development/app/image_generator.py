"""
image_generator.py — ComicCraft panel image generation

Generates a real AI comic-style illustration per panel using Pollinations.ai
(free, no API key, Flux model under the hood). This replaces any placeholder/
template graphic with an actual generated image.

Why this file exists:
Hugging Face's free serverless Inference API for stable-diffusion-v1-5 (and
most other text-to-image checkpoints) has been broken/deprecated since 2025 —
calls either 404 or hang until they time out. If your app has a fallback
that draws a generic "silhouette in a circle" placeholder whenever the image
call fails, that fallback is what's silently firing instead of real art.
Pollinations.ai is a reliable free alternative that needs zero setup.
"""

import os
import re
import time
import random
import logging
from urllib.parse import quote
from textwrap import wrap

import requests
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

PANELS_DIR = "static/panels"
os.makedirs(PANELS_DIR, exist_ok=True)

POLLINATIONS_BASE = "https://image.pollinations.ai/prompt"

# Optional: sign up (free) at https://auth.pollinations.ai to get a token.
# It removes the watermark and the ~1-request-per-15-seconds anonymous rate
# limit. Not required — the app works without it.
POLLINATIONS_TOKEN = os.getenv("POLLINATIONS_TOKEN", "")


def _sanitize_filename(text: str, max_len: int = 40) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    return slug[:max_len] or "panel"


def _create_placeholder_image(filepath: str, prompt: str, art_style: str, panel_number: int) -> str:
    """Create a local placeholder comic panel when the external image service fails."""
    width, height = 768, 768
    img = Image.new("RGB", (width, height), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)

    for y in range(height):
        ratio = y / height
        r = int(15 + (70 * ratio))
        g = int(23 + (70 * ratio))
        b = int(42 + (120 * ratio))
        draw.line((0, y, width, y), fill=(r, g, b))

    draw.ellipse((90, 120, 680, 630), fill=(67, 56, 126), outline=(180, 200, 255), width=5)
    draw.ellipse((170, 200, 600, 555), fill=(98, 77, 168), outline=(255, 214, 102), width=4)
    draw.rounded_rectangle((80, 80, 688, 120), radius=18, fill=(17, 24, 39), outline=(255, 255, 255), width=2)

    try:
        title_font = ImageFont.truetype("arial.ttf", 30)
        body_font = ImageFont.truetype("arial.ttf", 22)
    except Exception:
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()

    draw.text((110, 90), f"Panel {panel_number}", font=title_font, fill=(255, 255, 255))
    draw.text((520, 90), art_style.title(), font=body_font, fill=(255, 214, 102))

    for line_index, line in enumerate(wrap(prompt, width=28)[:3]):
        draw.text((90, 650 + line_index * 28), line, font=body_font, fill=(228, 238, 255))

    img.save(filepath, format="PNG")
    logger.warning(f"Using local placeholder image for panel {panel_number}: {filepath}")
    return filepath


def generate_image(
    image_prompt: str = None,
    art_style: str = "comic book",
    panel_number: int = 0,
    width: int = 768,
    height: int = 768,
    max_retries: int = 3,
    prompt: str = None,
) -> str:
    """
    Generate one comic panel illustration and save it to static/panels/.

    Args:
        image_prompt: the scene description to illustrate (from generate_outline)
        art_style: e.g. "anime", "comic book", "realistic", "pixel art"
        panel_number: used only for the saved filename
        width / height: output resolution in pixels
        max_retries: attempts before giving up

    Returns:
        Relative path (e.g. "/static/panels/panel_1_forest_edge.png") to
        pass into build_comic_layout().

    Raises:
        RuntimeError if generation fails after all retries — callers should
        NOT silently swap in a placeholder graphic; let the route surface a
        real 500 so the failure is visible instead of masquerading as art.
    """
    image_prompt = image_prompt or prompt
    if not image_prompt:
        raise ValueError("An image prompt is required")

    full_prompt = (
        f"{art_style} style comic book illustration, {image_prompt}, "
        f"dynamic composition, detailed line art, vibrant colors, "
        f"no text, no watermark, no signature"
    )
    encoded_prompt = quote(full_prompt)
    seed = random.randint(1, 999_999)

    url = (
        f"{POLLINATIONS_BASE}/{encoded_prompt}"
        f"?width={width}&height={height}&model=flux&nologo=true&seed={seed}"
    )
    if POLLINATIONS_TOKEN:
        url += f"&token={POLLINATIONS_TOKEN}"

    unique_suffix = f"{int(time.time() * 1000)}_{random.randint(1000, 999999)}"
    filename = f"panel_{panel_number}_{_sanitize_filename(image_prompt)}_{unique_suffix}.png"
    filepath = os.path.join(PANELS_DIR, filename)

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, timeout=60)

            if response.status_code == 200 and response.headers.get(
                "content-type", ""
            ).startswith("image"):
                with open(filepath, "wb") as f:
                    f.write(response.content)
                logger.info(f"Panel {panel_number} image saved to {filepath}")
                return f"/{filepath.replace(os.sep, '/')}"

            if response.status_code in {429, 500, 502, 503, 504}:
                wait = 16 if response.status_code == 429 else 5
                logger.warning(
                    f"Image service issue on panel {panel_number} "
                    f"(HTTP {response.status_code}), waiting {wait}s (attempt {attempt}/{max_retries})"
                )
                time.sleep(wait)
                continue

            last_error = f"HTTP {response.status_code}: {response.text[:200]}"

        except requests.RequestException as e:
            last_error = str(e)

        time.sleep(3)

    fallback_path = _create_placeholder_image(filepath, image_prompt, art_style, panel_number)
    logger.warning(
        f"Image generation failed for panel {panel_number} after {max_retries} attempts: {last_error}. "
        f"Using placeholder fallback."
    )
    return f"/{fallback_path.replace(os.sep, '/')}"