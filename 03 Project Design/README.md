# 3. Project Design

## Application Flow

```text
Browser form or JSON client
            |
            v
       FastAPI routes
            |
            +--> Outline generation (text fallback)
            +--> Script generation (text fallback)
            +--> Panel illustration service (local fallback)
            |
            v
     Panel layout builder
        /           \
 HTML preview      PDF exporter
```

## Component Responsibilities

- `app/main.py`: creates the FastAPI app and mounts static files.
- `app/routes.py`: validates requests and coordinates generation, preview, and downloads.
- `app/gemini_flash.py`: generates the five-panel outline.
- `app/gemini_pro.py`: generates captions, narration, and dialogue.
- `app/image_generator.py`: obtains panel artwork and saves PNG files.
- `app/layout_builder.py`: binds story fields and image paths panel by panel.
- `app/exporters.py`: produces a cover and comic pages in PDF format.
- `templates/`: provides the input form, comic preview, and export confirmation.

## Panel Record

Each panel stores its number, title, scene description, image prompt, image path, caption, narration, dialogue, and combined text. The shared ordering keeps the story and art aligned.

## Runtime Storage

Panel images are written under `static/panels/`; PDF exports are written under `static/exports/`. These directories are created by the application as needed.