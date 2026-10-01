import json
import os
import re
from dotenv import load_dotenv

load_dotenv()

def _create_fallback_outline(prompt: str, character_name: str, setting: str, tone: str, art_style: str) -> list:
    """Fallback generator when Gemini API is unavailable or key is not provided."""
    name = character_name.strip() if character_name else "The Hero"
    loc = setting.strip() if setting else "Enchanted Realm"
    t = tone.strip() if tone else "Dramatic"
    style = art_style.strip() if art_style else "comic book"

    return [
        {
            "panel_number": 1,
            "title": f"Panel 1: Journey Into {loc.title()}",
            "scene_description": f"{name} steps into {loc} with purpose, while the sky flickers with magical energy. The tension is high and the setting feels alive with mystery.",
            "image_prompt": f"Wide cinematic comic panel of {name} entering {loc}, dramatic lighting, bold ink outlines, glowing magical atmosphere, epic hero pose, {style} art style, detailed background, vibrant colors, dynamic composition"
        },
        {
            "panel_number": 2,
            "title": "Panel 2: The Hidden Relic",
            "scene_description": f"Deep within {loc}, {name} discovers a luminous artifact that changes everything. The room glows in soft amber and blue with a sense of awe and danger.",
            "image_prompt": f"Close-up dramatic comic panel of {name} discovering a glowing ancient relic in {loc}, magical light rays, intense expression, highly detailed {style} artwork, cinematic depth, rich colors, ornate fantasy environment"
        },
        {
            "panel_number": 3,
            "title": "Panel 3: The Rising Threat",
            "scene_description": f"A shadowy force rises around {name}, turning the calm scene into a brutal confrontation. The emotional stakes erupt into motion and chaos.",
            "image_prompt": f"Dynamic action comic panel showing {name} facing a shadowy enemy in {loc}, explosive motion lines, suspenseful pose, dramatic contrast, {style} art style, atmospheric fog, high energy composition"
        },
        {
            "panel_number": 4,
            "title": "Panel 4: The Heroic Breakthrough",
            "scene_description": f"{name} unleashes courage and wit at the perfect moment, forcing the conflict to turn in favor of the light. The power of the moment feels explosive.",
            "image_prompt": f"Epic climax comic panel of {name} using a powerful move in {loc}, massive energy burst, swirling motion, heroic pose, vibrant cinematic lighting, detailed {style} illustration, bold comic-book composition"
        },
        {
            "panel_number": 5,
            "title": "Panel 5: A New Legend Begins",
            "scene_description": f"The danger fades and the sky opens into a breathtaking sunrise. {name} stands victorious, ready for the next chapter of the adventure.",
            "image_prompt": f"Inspirational wide-angle comic finale with {name} standing victoriously in {loc} at sunrise, golden light, triumphant pose, majestic landscape, polished {style} art style, highly detailed background, epic storytelling composition"
        }
    ]


def generate_outline(prompt: str, character_name: str = "Hero", setting: str = "Forest", tone: str = "Dramatic", art_style: str = "Comic Book") -> list:
    """
    Generates a structured 5-panel comic outline using Google Gemini Flash.
    Returns a list of 5 dictionaries containing panel_number, title, scene_description, and image_prompt.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.strip() in ("", "your_gemini_api_key_here"):
        print("[ComicCraft] GEMINI_API_KEY not configured. Using high-quality procedural outline fallback.")
        return _create_fallback_outline(prompt, character_name, setting, tone, art_style)

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)

        # Primary model is gemini-1.5-flash, with fallback to gemini-2.5-flash or gemini-2.0-flash if needed
        model_names = ["gemini-1.5-flash", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
        
        system_instructions = (
            "You are a master comic book creator and story architect. "
            "Your task is to create a structured 5-panel comic outline based on the user's premise. "
            "You must return ONLY a valid JSON array of exactly 5 panel objects. "
            "Do not include any introductory or concluding text. "
            "Each object must have these exact keys:\n"
            "- panel_number: integer (1 to 5)\n"
            "- title: string (e.g., 'Panel 1: The Whispering Woods')\n"
            "- scene_description: string (1-2 sentences setting the scene and context)\n"
            "- image_prompt: string (vivid visual prompt for Stable Diffusion, including character name, action, setting, lighting, and art style)\n"
        )

        user_content = (
            f"Story Prompt: {prompt}\n"
            f"Main Character: {character_name}\n"
            f"Setting: {setting}\n"
            f"Tone: {tone}\n"
            f"Art Style: {art_style}\n\n"
            "Generate the 5-panel comic outline JSON array:"
        )

        response_text = None
        for m_name in model_names:
            try:
                model = genai.GenerativeModel(m_name, system_instruction=system_instructions)
                result = model.generate_content(user_content)
                if result and result.text:
                    response_text = result.text.strip()
                    break
            except Exception as model_err:
                print(f"[ComicCraft] Note: Model {m_name} failed: {model_err}. Trying next if available...")
                continue

        if not response_text:
            print("[ComicCraft] Gemini response was empty. Falling back to procedural outline.")
            return _create_fallback_outline(prompt, character_name, setting, tone, art_style)

        # Clean JSON markdown fences
        cleaned = re.sub(r"^```(?:json)?\s*", "", response_text, flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()

        # Parse JSON
        data = json.loads(cleaned)
        if isinstance(data, list) and len(data) >= 5:
            # Ensure proper typing and structure
            outline = []
            for idx, item in enumerate(data[:5], start=1):
                outline.append({
                    "panel_number": item.get("panel_number", idx),
                    "title": item.get("title", f"Panel {idx}"),
                    "scene_description": item.get("scene_description", ""),
                    "image_prompt": item.get("image_prompt", f"{character_name} in {setting}, {art_style} style")
                })
            return outline
        elif isinstance(data, dict) and "panels" in data and isinstance(data["panels"], list):
            outline = []
            for idx, item in enumerate(data["panels"][:5], start=1):
                outline.append({
                    "panel_number": item.get("panel_number", idx),
                    "title": item.get("title", f"Panel {idx}"),
                    "scene_description": item.get("scene_description", ""),
                    "image_prompt": item.get("image_prompt", f"{character_name} in {setting}, {art_style} style")
                })
            return outline
        else:
            print("[ComicCraft] Unexpected JSON format from Gemini Flash. Falling back.")
            return _create_fallback_outline(prompt, character_name, setting, tone, art_style)

    except Exception as e:
        print(f"[ComicCraft] Gemini Flash generation exception: {e}. Using procedural fallback.")
        return _create_fallback_outline(prompt, character_name, setting, tone, art_style)
