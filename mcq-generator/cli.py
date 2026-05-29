#!/usr/bin/env python3
"""MCQ CLI — processes all JSON files in input/ and produces quiz HTML files.

Usage:
    python3 cli.py              # process all input/*.json → output/*.html
    python3 cli.py --seed 89    # custom random seed for rebalancing
"""
import glob
import os
import sys

from tools.generate import cmd_import
from tools.rebalance import cmd_rebalance
from tools.utils import cmd_verify

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(SCRIPT_DIR, "input")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")


def main() -> None:
    seed = 42
    if "--seed" in sys.argv:
        idx = sys.argv.index("--seed")
        seed = int(sys.argv[idx + 1])

    json_files = sorted(glob.glob(os.path.join(INPUT_DIR, "*.json")))
    if not json_files:
        print(f"No JSON files found in {INPUT_DIR}/")
        raise SystemExit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    imported_keys: list[str] = []
    for path in json_files:
        fname = os.path.basename(path)
        print(f"Importing {fname}...")
        key = cmd_import(OUTPUT_DIR, path)
        if key:
            imported_keys.append(key)
        else:
            print(f"  SKIP {fname}")

    if not imported_keys:
        print("No files imported successfully.")
        raise SystemExit(1)

    print("Rebalancing...")
    cmd_rebalance(OUTPUT_DIR, imported_keys, seed)

    print("Verifying...")
    cmd_verify(OUTPUT_DIR, imported_keys)

    print("Done.")


if __name__ == "__main__":
    main()
