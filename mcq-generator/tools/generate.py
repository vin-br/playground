"""Generate HTML quiz files from existing question data or from JSON."""
import json
import os

from .config import get_highlight
from .template import render_html


def _escape_js(s: str) -> str:
    """Escape a string for embedding in a JS double-quoted string inside HTML."""
    return (
        s.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("<", "\\x3C")
    )


def json_to_js_questions(questions: list[dict]) -> str:
    """Convert a list of question dicts to a ``const QUESTIONS = [...]`` JS block."""
    lines = ["const QUESTIONS = ["]
    for q in questions:
        parts = [
            f'id: {q["id"]}',
            f'type: "{q["type"]}"',
            f'difficulty: "{q["difficulty"]}"',
            f'question: "{_escape_js(q["question"])}"',
        ]
        if q.get("code"):
            parts.append(f'code: "{_escape_js(q["code"])}"')
        if q.get("choices"):
            choices_str = ", ".join(f'"{_escape_js(c)}"' for c in q["choices"])
            parts.append(f"choices: [{choices_str}]")
        parts.append(f'correct: "{_escape_js(q["correct"])}"')
        parts.append(f'explanation: "{_escape_js(q["explanation"])}"')
        lines.append("            { " + ", ".join(parts) + " },")
    lines.append("        ];")
    return "\n".join(lines)


def cmd_import(base: str, json_path: str) -> str | None:
    """Import questions from a JSON file and produce a fresh HTML quiz file.

    Returns the subject key on success, or None on failure.
    """
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    for field in ("subject_key", "questions"):
        if field not in data:
            print(f"  ERROR: JSON file is missing required field '{field}'")
            return None

    key = data["subject_key"]
    title = data.get("subject", key.capitalize())
    code_css, highlight_fn = get_highlight(key)

    # Strip _comment fields from questions
    questions = [{k: v for k, v in q.items() if not k.startswith("_comment")} for q in data["questions"]]

    questions_block = json_to_js_questions(questions)
    output = render_html(title, key, questions_block, code_css, highlight_fn)

    out_path = os.path.join(base, f"mcq-{key}.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"  mcq-{key}.html — {len(questions)} questions, {len(output):,} chars written")
    return key
