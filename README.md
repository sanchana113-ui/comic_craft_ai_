# ComicCraft AI Comic Story Creator

This is a clean, self-contained copy of the ComicCraft project organized into the eight requested project topics. The runnable source code is grouped in **05 Project Development**; testing, setup, and demonstration materials are in their corresponding folders.

## Project Topics

1. [Brainstorming and Ideation](01%20Brainstorming%20and%20Ideation/README.md)
2. [Requirement Analysis](02%20Requirement%20Analysis/README.md)
3. [Project Design](03%20Project%20Design/README.md)
4. [Project Planning](04%20Project%20Planning/README.md)
5. [Project Development and Source Code](05%20Project%20Development/README.md)
6. [Project Testing](06%20Project%20Testing/README.md)
7. [Project Documentation](07%20Project%20Documentation/README.md)
8. [Project Demonstration](08%20Project%20Demonstration/README.md)

## Run the Application

Open a terminal in `05 Project Development` and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open `http://127.0.0.1:8000/`.

Set `GEMINI_API_KEY` locally to enable Gemini text generation. Text fallbacks are available without it. Panel images use Pollinations.ai; `POLLINATIONS_TOKEN` is optional. Never commit `.env` or API credentials.