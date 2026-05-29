"""Rebalance answer distributions to ~25% per letter."""
import os
import random
import re

from .utils import get_distribution, swap_choices


def cmd_rebalance(base: str, subjects_filter: list[str], seed: int) -> None:
    random.seed(seed)

    for key in subjects_filter:
        fname = f"mcq-{key}.html"
        path = os.path.join(base, fname)
        if not os.path.exists(path):
            print(f"  SKIP {fname} — not found")
            continue

        with open(path, encoding="utf-8") as f:
            lines = f.read().split("\n")

        four_choice = []
        for i, line in enumerate(lines):
            if not re.search(r'type:\s*"(mcq|code)"', line):
                continue
            m_correct = re.search(r'correct:\s*"([A-D])"', line)
            m_id = re.search(r"id:\s*(\d+)", line)
            if m_correct and m_id:
                four_choice.append({"line_num": i, "qid": int(m_id.group(1)), "correct": m_correct.group(1)})

        total = len(four_choice)
        if not total:
            print(f"  {fname} — no questions found, skipping")
            continue

        target = total // 4
        remainder = total % 4
        targets_per_letter = {l: target + (1 if j < remainder else 0) for j, l in enumerate("ABCD")}

        by_letter: dict[str, list] = {"A": [], "B": [], "C": [], "D": []}
        for q in four_choice:
            by_letter[q["correct"]].append(q)

        before = {l: len(by_letter[l]) for l in "ABCD"}

        pool: list = []
        need: dict[str, int] = {}
        for letter in "ABCD":
            t = targets_per_letter[letter]
            if len(by_letter[letter]) > t:
                random.shuffle(by_letter[letter])
                pool.extend(by_letter[letter][t:])
            elif len(by_letter[letter]) < t:
                need[letter] = t - len(by_letter[letter])

        random.shuffle(pool)
        swaps = []
        idx = 0
        for letter in sorted(need):
            for _ in range(need[letter]):
                swaps.append((pool[idx], pool[idx]["correct"], letter))
                idx += 1

        applied = skipped = 0
        for q, old_letter, new_letter in swaps:
            result = swap_choices(lines[q["line_num"]], old_letter, new_letter)
            if result is None:
                print(f"    WARN Q{q['qid']}: could not parse choices, skipping")
                skipped += 1
            else:
                lines[q["line_num"]] = result
                applied += 1

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        final, _, _ = get_distribution("\n".join(lines))
        print(f"  {fname} — before: {before} | after: {final} | swaps: {applied} ok, {skipped} skipped")
