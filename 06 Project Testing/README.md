# 6. Project Testing

`test_pipeline.py` contains integration tests for outline generation, script generation, image creation, unique image output, panel layout, PDF export, and the main HTTP routes.

## Run the Tests

Open a terminal in `05 Project Development`, install its dependencies, then run:

```powershell
python -m unittest discover -s "../06 Project Testing" -p "test_pipeline.py"
```

These tests may contact Gemini and Pollinations.ai and create panel/PDF outputs in the Development folder. Gemini text fallbacks are available; image generation contacts the image service before using its local fallback. Run the tests with internet access for the complete integration path.

## Manual Checks

1. Open `http://127.0.0.1:8000/` and generate a comic.
2. Confirm the preview contains five panels with text and images.
3. Download and open the generated PDF.
4. Send a request to `/generate-comic/json` and check its layout and PDF path.
5. Check fallback behavior when external generation services are unavailable.

Record the date, Python version, command, result, and external-service status when reporting test outcomes. This document does not claim the tests have been run.