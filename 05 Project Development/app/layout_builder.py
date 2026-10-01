def build_comic_layout(outline: list, story_data: any, image_paths: list) -> list:
    """
    Binds outline metadata, story dialogue/narration, and image paths together
    into a structured panel-by-panel layout list.
    """
    layout = []

    # Normalize story_data if passed as list of dicts, single string, or dict
    story_panels = []
    if isinstance(story_data, list):
        story_panels = story_data
    elif isinstance(story_data, dict) and "panels" in story_data:
        story_panels = story_data["panels"]
    elif isinstance(story_data, str):
        # If passed as single string, split by panel sections
        chunks = story_data.split("Panel ")
        for c in chunks:
            if c.strip():
                story_panels.append({"text": f"Panel {c.strip()}"})

    for idx, panel_outline in enumerate(outline):
        panel_num = panel_outline.get("panel_number", idx + 1)
        title = panel_outline.get("title", f"Panel {panel_num}")
        scene_desc = panel_outline.get("scene_description", "")
        img_prompt = panel_outline.get("image_prompt", "")

        # Get matching story data
        matching_story = {}
        if idx < len(story_panels):
            matching_story = story_panels[idx]

        caption = matching_story.get("caption", "")
        narration = matching_story.get("narration", "")
        dialogue = matching_story.get("dialogue", "")
        text = matching_story.get("text", "")

        if not text:
            parts = []
            if caption:
                parts.append(f"[{caption}]")
            if narration:
                parts.append(narration)
            if dialogue:
                parts.append(dialogue)
            text = "\n\n".join(parts) if parts else scene_desc

        # Get matching image path
        img_path = image_paths[idx] if idx < len(image_paths) else ""

        layout.append({
            "panel_number": panel_num,
            "title": title,
            "scene_description": scene_desc,
            "image_path": img_path,
            "caption": caption,
            "narration": narration,
            "dialogue": dialogue,
            "text": text,
            "image_prompt": img_prompt
        })

    return layout
