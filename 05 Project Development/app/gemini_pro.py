import json
import os
import re
from dotenv import load_dotenv

load_dotenv()

def _create_fallback_story(outline: list, character_name: str, setting: str, tone: str, art_style: str) -> list:
    """Fallback generator for story narration and dialogues when Gemini API is unavailable."""
    name = character_name.strip() if character_name else "The Hero"
    loc = setting.strip() if setting else "the realm"
    t = tone.strip() if tone else "Dramatic"

    fallback_stories = [
        {
            "panel_number": 1,
            "caption": f"Deep on the outskirts of {loc}, stillness gives way to footsteps.",
            "narration": f"{name} drew a measured breath. Every legend warned of this place, yet standing here, the air hummed with strange promise.",
            "dialogue": f"{name}: 'No turning back now. The answers are out there.'",
            "text": f"[CAPTION: Deep on the outskirts of {loc}, stillness gives way to footsteps.]\n{name} drew a measured breath. Every legend warned of this place, yet standing here, the air hummed with strange promise.\n{name}: 'No turning back now. The answers are out there.'"
        },
        {
            "panel_number": 2,
            "caption": "A sudden pulse of azure luminescence cuts through the gloom.",
            "narration": f"Beneath roots older than memory, {name}'s eyes caught an iridescent glimmer. An ancient relic lay undisturbed.",
            "dialogue": f"{name}: 'Incredible... it matches the old map exactly.'",
            "text": f"[CAPTION: A sudden pulse of azure luminescence cuts through the gloom.]\nBeneath roots older than memory, {name}'s eyes caught an iridescent glimmer. An ancient relic lay undisturbed.\n{name}: 'Incredible... it matches the old map exactly.'"
        },
        {
            "panel_number": 3,
            "caption": "The air chills without warning. Shadows twist into living shapes.",
            "narration": f"Before {name} could grasp the prize, the ground trembled. Guardians of {loc} awakened, blocking every path.",
            "dialogue": f"{name}: 'I won't let fear stop me today!'",
            "text": f"[CAPTION: The air chills without warning. Shadows twist into living shapes.]\nBefore {name} could grasp the prize, the ground trembled. Guardians of {loc} awakened, blocking every path.\n{name}: 'I won't let fear stop me today!'"
        },
        {
            "panel_number": 4,
            "caption": "A blinding flash of energy detonates across the clearing.",
            "narration": f"Channeling every ounce of determination, {name} anticipated the strike and triggered the relic's resonance, shattering the darkness.",
            "dialogue": f"{name}: 'Stand down! This realm belongs to the light!'",
            "text": f"[CAPTION: A blinding flash of energy detonates across the clearing.]\nChanneling every ounce of determination, {name} anticipated the strike and triggered the relic's resonance, shattering the darkness.\n{name}: 'Stand down! This realm belongs to the light!'"
        },
        {
            "panel_number": 5,
            "caption": "Golden rays break through the canopy as calm returns.",
            "narration": f"The danger had passed. With the artifact secure and the realm safe, {name} took one final look back before marching forward.",
            "dialogue": f"{name}: 'The adventure has only just begun.'",
            "text": f"[CAPTION: Golden rays break through the canopy as calm returns.]\nThe danger had passed. With the artifact secure and the realm safe, {name} took one final look back before marching forward.\n{name}: 'The adventure has only just begun.'"
        }
    ]

    # Ensure match with outline count
    result = []
    for idx, panel in enumerate(outline):
        panel_num = panel.get("panel_number", idx + 1)
        base = fallback_stories[(idx) % len(fallback_stories)]
        result.append({
            "panel_number": panel_num,
            "caption": base["caption"],
            "narration": base["narration"],
            "dialogue": base["dialogue"],
            "text": base["text"]
        })
    return result


def generate_story(outline: list, character_name: str = "Hero", setting: str = "Forest", tone: str = "Dramatic", art_style: str = "Comic Book") -> list:
    """
    Expands the 5-panel comic outline into detailed narration, captions, and character dialogue using Gemini Pro.
    Returns a list of dictionaries with panel_number, caption, narration, dialogue, and full text for each panel.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.strip() in ("", "your_gemini_api_key_here"):
        print("[ComicCraft] GEMINI_API_KEY not configured. Using creative procedural story fallback.")
        return _create_fallback_story(outline, character_name, setting, tone, art_style)

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)

        model_names = ["gemini-1.5-pro", "gemini-2.5-pro", "gemini-1.5-flash"]

        system_instructions = (
            "You are an acclaimed comic book writer and scriptwriter. "
            "Given a 5-panel comic outline, your goal is to write dramatic, immersive comic narration, "
            "captions (ambient sounds, location notes), and punchy character dialogues for each panel. "
            "Tone: " + str(tone) + ". Main Character: " + str(character_name) + ".\n"
            "You MUST respond ONLY with a valid JSON array of 5 objects matching the panels. "
            "Each object must contain:\n"
            "- panel_number: integer (1 to 5)\n"
            "- caption: string (atmospheric scene note or sound effect)\n"
            "- narration: string (story narrative describing actions and feelings)\n"
            "- dialogue: string (character speech, e.g. 'Hero: \"...\"')\n"
            "- text: string (combined caption, narration, and dialogue formatted for the panel)\n"
        )

        user_content = (
            f"Here is the outline of the comic:\n{json.dumps(outline, indent=2)}\n\n"
            f"Character: {character_name}\n"
            f"Setting: {setting}\n"
            f"Tone: {tone}\n"
            f"Art Style: {art_style}\n\n"
            "Write the panel-by-panel script as a JSON array:"
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
                print(f"[ComicCraft] Note: Model {m_name} failed: {model_err}. Trying next...")
                continue

        if not response_text:
            return _create_fallback_story(outline, character_name, setting, tone, art_style)

        cleaned = re.sub(r"^```(?:json)?\s*", "", response_text, flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()

        data = json.loads(cleaned)
        story_list = []
        if isinstance(data, list):
            for idx, item in enumerate(data[:5], start=1):
                p_num = item.get("panel_number", idx)
                cap = item.get("caption", "")
                nar = item.get("narration", "")
                dia = item.get("dialogue", "")
                combo = item.get("text") or f"[CAPTION: {cap}]\n{nar}\n{dia}".strip()
                story_list.append({
                    "panel_number": p_num,
                    "caption": cap,
                    "narration": nar,
                    "dialogue": dia,
                    "text": combo
                })
            return story_list
        else:
            return _create_fallback_story(outline, character_name, setting, tone, art_style)

    except Exception as e:
        print(f"[ComicCraft] Gemini Pro story generation exception: {e}. Using fallback.")
        return _create_fallback_story(outline, character_name, setting, tone, art_style)
