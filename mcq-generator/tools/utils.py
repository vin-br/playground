"""Shared helpers: choice parsing, swap logic, question extraction, distribution."""
import os
import re

from .config import FIXES, JS_REPLACEMENTS


def _files_for_keys(base: str, keys: list[str]) -> list[tuple[str, str]]:
    """Return list of (key, filepath) for the given subject keys."""
    return [(k, os.path.join(base, f"mcq-{k}.html")) for k in keys]


# ── Question extraction and fixing ───────────────────────────────────────────

def replace_question(content: str, qid: int, replacement: str) -> str:
    marker = f"{{ id: {qid},"
    start = content.index(marker)
    next_q = content.find(f"{{ id: {qid + 1},", start + 1)
    chunk = content[start:next_q] if next_q != -1 else content[start:content.index("];", start)]
    last_brace = chunk.rfind("},")
    end_pos = start + (last_brace + 2 if last_brace != -1 else chunk.rfind("}") + 1)
    while end_pos < len(content) and content[end_pos] in " \t\r":
        end_pos += 1
    return content[:start] + replacement + "\n            " + content[end_pos:]


def extract_questions_block(content: str) -> str:
    start = content.index("const QUESTIONS = [")
    engine_idx = content.index("// ============ QUIZ ENGINE", start)
    end_idx = content.rindex("];", start, engine_idx)
    return content[start : end_idx + 2]


def fix_questions(content: str, filename: str) -> str:
    for qid, replacement in FIXES.get(filename, []):
        content = replace_question(content, qid, replacement)
    if filename == "mcq-javascript.html":
        for old, new in JS_REPLACEMENTS:
            content = content.replace(old, new)
    return content


# ── Choice parsing and swapping ──────────────────────────────────────────────

def parse_choices_block(line: str):
    idx = line.index("choices:")
    bracket_start = line.index("[", idx)
    depth, in_string, i = 1, False, bracket_start + 1
    while i < len(line) and depth > 0:
        c = line[i]
        if c == "\\" and in_string:
            i += 2
            continue
        if c == '"':
            in_string = not in_string
        elif not in_string:
            if c == "[":
                depth += 1
            elif c == "]":
                depth -= 1
        i += 1
    return bracket_start, i


def parse_choice_texts(choices_str: str) -> dict:
    return {m.group(1): m.group(2) for m in re.finditer(r'"([A-D])\.\s*((?:[^"\\]|\\.)*)"', choices_str)}


def swap_choices(line: str, old_letter: str, new_letter: str) -> str | None:
    """Swap two choice texts in a question line and update the correct answer.

    Returns the modified line, or None if the choices could not be parsed.
    """
    cm = re.search(r"choices:\s*\[([^\]]+)\]", line)
    if cm:
        choice_dict = parse_choice_texts(cm.group(1))
        if len(choice_dict) != 4:
            return None
        choice_dict[old_letter], choice_dict[new_letter] = choice_dict[new_letter], choice_dict[old_letter]
        new_choices = ", ".join(f'"{l}. {choice_dict[l]}"' for l in "ABCD")
        new_line = line[: cm.start()] + "choices: [" + new_choices + "]" + line[cm.end() :]
    else:
        start, end = parse_choices_block(line)
        choice_dict = parse_choice_texts(line[start + 1 : end - 1])
        if len(choice_dict) != 4:
            return None
        choice_dict[old_letter], choice_dict[new_letter] = choice_dict[new_letter], choice_dict[old_letter]
        new_choices = ", ".join(f'"{l}. {choice_dict[l]}"' for l in "ABCD")
        new_line = line[:start] + "[" + new_choices + "]" + line[end:]

    return re.sub(r'correct:\s*"[A-D]"', f'correct: "{new_letter}"', new_line)


# ── Distribution ─────────────────────────────────────────────────────────────

def get_distribution(content: str) -> tuple[dict[str, int], int, int]:
    """Return (letter_dist, mcq_code_total, truefalse_count)."""
    dist: dict[str, int] = {"A": 0, "B": 0, "C": 0, "D": 0}
    mcq_total = 0
    tf_total = 0
    for m in re.finditer(r'type:\s*"(mcq|code)".*?correct:\s*"([A-D])"', content):
        dist[m.group(2)] += 1
        mcq_total += 1
    for _ in re.finditer(r'type:\s*"truefalse"', content):
        tf_total += 1
    return dist, mcq_total, tf_total


def cmd_verify(base: str, subjects_filter: list[str]) -> None:
    for key, path in _files_for_keys(base, subjects_filter):
        if not os.path.exists(path):
            print(f"  SKIP mcq-{key}.html — not found")
            continue
        with open(path, encoding="utf-8") as f:
            content = f.read()
        dist, mcq_total, tf_total = get_distribution(content)
        total = mcq_total + tf_total
        if mcq_total:
            pcts = {k: f"{v / mcq_total * 100:.1f}%" for k, v in dist.items()}
            line = (
                f"  mcq-{key}.html: "
                f"A={dist['A']}({pcts['A']}) B={dist['B']}({pcts['B']}) "
                f"C={dist['C']}({pcts['C']}) D={dist['D']}({pcts['D']}) "
                f"mcq+code={mcq_total}"
            )
            if tf_total:
                line += f" truefalse={tf_total}"
            line += f" total={total}"
            print(line)
        else:
            print(f"  mcq-{key}.html: {tf_total} truefalse questions (no mcq/code)")
