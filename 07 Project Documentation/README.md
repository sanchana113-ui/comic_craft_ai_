# 7. Project Documentation

## Prerequisites

- Python installed and available as `python`.
- Dependencies from `05 Project Development/requirements.txt`.
- Internet access for remote text and image generation.
- A Gemini API key for Gemini-backed text generation; procedural text fallback is available without it.
- `POLLINATIONS_TOKEN` is optional for image generation.

## Setup and Run

Follow the commands in `05 Project Development/README.md`. Run the app from inside `05 Project Development` so relative static asset paths resolve correctly.

## Main Routes

- `GET /`: comic form.
- `POST /generate`: form-based generation and HTML preview.
- `POST /generate-comic/json`: JSON generation API.
- `GET /test-image`: direct image generation utility.
- `GET /download-pdf`: exported PDF download.
- `GET /export-success`: export confirmation.

## Environment Safety

The `.env.example` file lists optional environment variables. Copy it to `.env` only for local configuration, provide real secrets locally, and never upload `.env`, API keys, or tokens.

## Current AI Services

Gemini is used for outline and script generation when configured. Illustrations currently use Pollinations.ai, with a locally generated placeholder after request failures.