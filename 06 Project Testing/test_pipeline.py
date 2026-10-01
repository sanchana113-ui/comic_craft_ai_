import hashlib
import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "05 Project Development"))
sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient
from app.main import app
from app.gemini_flash import generate_outline
from app.gemini_pro import generate_story
from app.image_generator import generate_image
from app.layout_builder import build_comic_layout
from app.exporters import save_pdf


class TestComicCraftPipeline(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.sample_prompt = "A brave fox exploring an enchanted forest"
        self.character_name = "Finn"
        self.setting = "Enchanted Forest"
        self.tone = "Dramatic"
        self.art_style = "Anime"

    def test_01_gemini_flash_outline(self):
        """Test outline generation returns exactly 5 panels with correct keys."""
        outline = generate_outline(
            prompt=self.sample_prompt,
            character_name=self.character_name,
            setting=self.setting,
            tone=self.tone,
            art_style=self.art_style
        )
        self.assertIsInstance(outline, list)
        self.assertEqual(len(outline), 5)
        for panel in outline:
            self.assertIn("panel_number", panel)
            self.assertIn("title", panel)
            self.assertIn("scene_description", panel)
            self.assertIn("image_prompt", panel)

    def test_02_gemini_pro_story(self):
        """Test story generation creates captions, narration, and dialogues."""
        outline = generate_outline(self.sample_prompt, self.character_name, self.setting, self.tone, self.art_style)
        story_data = generate_story(outline, self.character_name, self.setting, self.tone, self.art_style)
        self.assertIsInstance(story_data, list)
        self.assertEqual(len(story_data), 5)
        for panel in story_data:
            self.assertIn("panel_number", panel)
            self.assertIn("caption", panel)
            self.assertIn("narration", panel)
            self.assertIn("dialogue", panel)

    def test_03_image_generation(self):
        """Test image generator creates and saves a PNG file."""
        img_path = generate_image("A brave fox standing in front of a giant glowing oak tree", "Anime", panel_number=1)
        self.assertTrue(img_path.startswith("/static/panels/"))
        clean_path = img_path.lstrip("/")
        abs_path = os.path.join(PROJECT_ROOT, clean_path)
        self.assertTrue(os.path.exists(abs_path), f"File {abs_path} was not created.")
        self.assertGreater(os.path.getsize(abs_path), 1000)

    def test_03b_unique_panel_generation(self):
        """Repeated generation for the same panel should not overwrite the previous image."""
        prompt = "A brave fox exploring an enchanted forest"
        path_a = generate_image(prompt, "Anime", panel_number=1)
        path_b = generate_image(prompt, "Anime", panel_number=1)

        self.assertNotEqual(path_a, path_b)

        abs_a = os.path.join(PROJECT_ROOT, path_a.lstrip("/"))
        abs_b = os.path.join(PROJECT_ROOT, path_b.lstrip("/"))
        self.assertTrue(os.path.exists(abs_a))
        self.assertTrue(os.path.exists(abs_b))

        with open(abs_a, "rb") as f:
            hash_a = hashlib.sha256(f.read()).hexdigest()
        with open(abs_b, "rb") as f:
            hash_b = hashlib.sha256(f.read()).hexdigest()
        self.assertNotEqual(hash_a, hash_b)

    def test_04_layout_builder_and_pdf(self):
        """Test layout builder binds data and exporter generates multi-page PDF."""
        outline = generate_outline(self.sample_prompt, self.character_name, self.setting, self.tone, self.art_style)
        story_data = generate_story(outline, self.character_name, self.setting, self.tone, self.art_style)
        img_path = generate_image(outline[0]["image_prompt"], self.art_style, panel_number=1)
        images = [img_path] * 5

        layout = build_comic_layout(outline, story_data, images)
        self.assertEqual(len(layout), 5)
        self.assertEqual(layout[0]["panel_number"], 1)
        self.assertEqual(layout[0]["image_path"], img_path)

        pdf_path = save_pdf(layout, "Finn's Legend", self.character_name, self.setting, self.tone, self.art_style)
        self.assertTrue(pdf_path.startswith("/static/exports/"))
        clean_pdf_path = pdf_path.lstrip("/")
        abs_pdf = os.path.join(PROJECT_ROOT, clean_pdf_path)
        self.assertTrue(os.path.exists(abs_pdf), f"PDF {abs_pdf} was not created.")
        self.assertGreater(os.path.getsize(abs_pdf), 2000)

    def test_05_api_routes(self):
        """Test FastAPI endpoints."""
        # 1. Homepage
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("ComicCraft", resp.text)
        self.assertIn("story_prompt", resp.text)

        # 2. Test-image route
        resp = self.client.get("/test-image?prompt=Fox+running&art_style=Anime&panel_number=1")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("image_path", data)

        # 3. JSON Generation route
        resp = self.client.post("/generate-comic/json", json={
            "story_prompt": "A brave fox exploring an enchanted forest",
            "character_name": "Finn",
            "setting": "Enchanted Forest",
            "tone": "Dramatic",
            "art_style": "Anime"
        })
        self.assertEqual(resp.status_code, 200)
        json_data = resp.json()
        self.assertEqual(json_data["status"], "success")
        self.assertEqual(len(json_data["layout"]), 5)
        self.assertTrue(json_data["pdf_path"].startswith("/static/exports/"))

        # 4. Export success route
        pdf_path = json_data["pdf_path"]
        resp = self.client.get(f"/export-success?pdf_path={pdf_path}")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("EXPORT COMPLETE", resp.text)

        # 5. Direct Download route
        resp = self.client.get(f"/download-pdf?pdf_path={pdf_path}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers["content-type"], "application/pdf")

        # 6. Form Generation Route (POST /generate)
        resp = self.client.post("/generate", data={
            "story_prompt": "A clumsy robot trying to bake a cake",
            "character_name": "Robo-Chip",
            "setting": "City Kitchen",
            "tone": "Funny",
            "art_style": "Comic Book"
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Robo-Chip", resp.text)
        self.assertIn("Panel 1 of 5", resp.text)
        self.assertIn("Download Your Comic as PDF", resp.text)


if __name__ == "__main__":
    unittest.main()
