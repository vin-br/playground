# MCQ Generator

---

[![Python](https://img.shields.io/badge/Python-3.14+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org) [![uv](https://img.shields.io/badge/uv-latest-261230?style=for-the-badge&logo=uv&logoColor=DE5FE9)](https://docs.astral.sh/uv/)

---

## Overview

Generate self-contained HTML quiz files from JSON question banks. Each HTML file is a standalone, mobile-friendly quiz that works offline — no server needed to take the quiz.

## Table of contents

- [Setup](#setup)
- [Quick start](#quick-start)
- [Folder structure](#folder-structure)
- [How it works](#how-it-works)
- [Creating questions](#creating-questions)
- [Question types](#question-types)

## Setup

```bash
# Install Python 3.14.5 via uv (if not already installed)
uv python install 3.14.5

# No dependencies to install — stdlib only
```

## Quick start

```bash
# Place JSON question files in input/
# Run the CLI — it processes all files automatically
python3 cli.py

# Option 1: Serve locally via Docker + nginx
python3 -m tools.serve output

# Option 2: Open a generated file directly
open output/mcq-javascript.html
```

## Folder structure

```
mcq-generator/
  cli.py                  ← entry point (processes all input/*.json)
  question_template.json  ← template to give an AI when generating questions
  preprompt.md            ← prompt to paste into an AI alongside course content
  example.json            ← sample question file to test the pipeline
  input/                  ← put your JSON question files here
  output/                 ← generated HTML quiz files go here
  tools/                  ← internal modules (config, template, generate, etc.)
```

## How it works

The CLI processes every `*.json` file in `input/` through three steps:

1. **Import** — validates the JSON and converts questions into a standalone HTML quiz
2. **Rebalance** — shuffles answer positions so correct answers are evenly spread across A, B, C, D (~25% each)
3. **Verify** — prints the answer distribution for each generated quiz

```bash
python3 cli.py              # default seed (42)
python3 cli.py --seed 123   # custom random seed
```

## Serving locally

Serve generated quiz files via Docker + nginx:

```bash
# Serve the output/ folder on port 8080 (requires Docker)
python3 tools/serve.py

# Serve a different folder on a custom port
python3 tools/serve.py /path/to/folder --port 3000
```

This will:
- Display local URL: `http://localhost:8080`
- Display LAN URL: `http://{your-ip}:8080` (for sharing with others on the network)
- Serve files read-only from a lightweight nginx container

Press `Ctrl+C` to stop.

## Creating questions

<details>
<summary>

### Option 1: Write JSON by hand

</summary>

Use `question_template.json` as a reference. Create a JSON file with:

```json
{
  "subject": "My Subject",
  "subject_key": "mysubject",
  "questions": [ ... ]
}
```

The `subject_key` is used for the output filename (`mcq-{subject_key}.html`) and for localStorage. Any key works — no configuration needed.

</details>

<details>
<summary>

### Option 2: Generate with AI

</summary>

1. Open `PREPROMPT.md` and copy the prompt
2. Fill in `[N]` (number of questions), `[SUBJECT]`, `[KEY]`, and `[START_ID]`
3. Paste `question_template.json` where indicated
4. Paste your course content (Markdown) where indicated or put it in the content folder. The AI will generate questions based strictly on this content.
5. Send to an AI — the output is a ready-to-use JSON file
6. Save the AI output in `input/` and run:

```bash
python3 cli.py
```

</details>

## Question types

| Type | Description | Choices |
|------|-------------|---------|
| `mcq` | Multiple choice | 4 (A–D) |
| `truefalse` | True or False | True / False |
| `code` | Multiple choice with code snippet | 4 (A–D) |
