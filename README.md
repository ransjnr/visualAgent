# visualAgent (MVP)

An **always-on, context-aware visual AI assistant** that:

- Observes your screen in real time (periodic screenshots)
- Extracts context (OCR + active window title)
- Produces **step-by-step guidance without prompts**
- Shows suggestions in a small always-on-top overlay and/or the terminal

This repo is an MVP scaffold you can extend with richer UI understanding (UI element detection, app-specific skills, safer redaction, etc.).

## What “without prompts” means here

The agent runs continuously and **proactively suggests next steps** when it detects a likely task (rule-based, optionally LLM-refined). You can tune how “chatty” it is by:

- Using `agent.analyze_on_window_change_only`
- Increasing `agent.interval_s`
- Adding `privacy.redact_rects`

## Quick start (Linux)

### 1) Install OS prerequisites

- **Tesseract OCR** (required for OCR):

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr
```

- **Optional active-window detection on X11** (better app context):

```bash
sudo apt-get install -y xdotool x11-utils
```

### 2) Install Python deps

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3) Create a config

```bash
cp config.example.yaml config.yaml
```

### 4) Run

```bash
python main.py --config config.yaml
```

## Optional: LLM refinement (OpenAI-compatible)

1) Set in `config.yaml`:

- `llm.provider: "openai_compatible"`
- `llm.base_url`: your provider base URL
- `llm.model`: model name
- `llm.api_key_env`: env var name for the API key

2) Export your key (example):

```bash
export OPENAI_API_KEY="..."
```

## Current built-in skill examples

- `excel_charts`: if the screen/window looks like Excel + chart/graph intent, it suggests a chart creation flow.

You can add more skills in `visual_agent/rules/` and register them in `visual_agent/rules/registry.py`.

## Privacy & safety notes (important)

- This tool **captures screenshots**. Use `privacy.redact_rects` to blur sensitive regions.
- Avoid enabling `agent.debug_save_frames` unless you really need it (it writes screenshots to disk).
- UI automation (clicking/typing) is intentionally **not included** in this MVP; it only provides guidance.