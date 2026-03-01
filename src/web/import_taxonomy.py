from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict

# Ensure project root is on sys.path so `src` package is importable when the
# script is executed directly.
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.web.taxonomy_store import load_taxonomy, save_taxonomy

FAMILY_KEYS = ["тұқымдастық", "тұқымдастығы", "family", "тұқымдастығы:"]
GENUS_KEYS = ["тұйстастық", "туыстастық", "туыстастығы", "тұйстастығы", "genus", "род", "туыст"]
SPECIES_KEYS = ["түрі", "type", "species", "типи", "тypi", "tүpi", "typi"]


def extract_after_colon(line: str) -> str:
    if ":" in line:
        return line.split(":", 1)[1].strip()
    parts = line.split()
    if len(parts) > 1:
        return " ".join(parts[1:]).strip()
    return ""


def normalize_key(filename: str) -> str:
    # remove path, strip extension
    return Path(filename.strip()).stem


def parse_blocks(text: str) -> Dict[str, Dict[str, str]]:
    lines = [ln.strip() for ln in text.splitlines()]
    entries: Dict[str, Dict[str, str]] = {}

    current_key = None
    buffer = []

    def flush():
        nonlocal current_key, buffer
        if not current_key:
            buffer = []
            return
        fam = gen = spec = ""
        for ln in buffer:
            low = ln.lower()
            # family
            if any(k in low for k in ["тұқымдастық", "тұқымдастығы", "family"]):
                fam = extract_after_colon(ln)
                continue
            if any(k in low for k in ["тұйстастық", "туыстастық", "род", "genus"]) or "туы" in low or "род" in low:
                gen = extract_after_colon(ln)
                continue
            if any(k in low for k in ["түрі", "species", "type", "typi", "тypi", "tүpi"]) or "вид" in low:
                spec = extract_after_colon(ln)
                continue
            # if line looks like a value without label, try assign heuristically
            if not fam and re.search(r'[A-Za-z]', ln):
                # if contains 'aceae' or endswith 'aceae' -> family
                if 'aceae' in ln.lower() or ln.lower().endswith('ae'):
                    fam = ln
                    continue
                # if capitalized single word -> genus
                if re.match(r'^[A-Z][a-zA-Z\.-]+$', ln):
                    gen = ln
                    continue
                # else treat as species
                if ',' in ln or ' ' in ln:
                    spec = ln
                    continue
        entries[current_key] = {"family": fam, "genus": gen, "species": spec}
        buffer = []

    # find lines that contain filenames
    for ln in lines:
        if not ln:
            continue
        # detect filename by extension
        if re.search(r'\.(jpg|jpeg|png|bmp|tif|tiff)\b', ln, flags=re.I):
            # flush previous
            if current_key:
                flush()
            # extract filename token
            token = ln.split()[-1]
            # remove numbering like '1.' prefix
            token = re.sub(r'^\d+\.?', '', token).strip()
            current_key = normalize_key(token)
            buffer = []
            continue
        # maybe lines that start with path without extension? skip
        # accumulate
        if current_key:
            buffer.append(ln)
    # flush at end
    if current_key:
        flush()
    return entries


def main(argv=None):
    argv = argv or sys.argv[1:]
    if not argv:
        print("Usage: import_taxonomy.py <input_text_file> [--reload]")
        return 2
    path = Path(argv[0])
    if not path.exists():
        print("Input file not found:", path)
        return 2
    text = path.read_text(encoding='utf-8')
    parsed = parse_blocks(text)
    if not parsed:
        print("No entries parsed.")
        return 1
    print(f"Parsed {len(parsed)} entries. Sample:")
    for k, v in list(parsed.items())[:5]:
        print(k, v)

    taxonomy = load_taxonomy()
    taxonomy.update(parsed)
    save_taxonomy(taxonomy)
    print("Saved taxonomy.json with", len(taxonomy), "entries")

    if '--reload' in argv:
        # try to notify running server to reload (try common ports)
        import urllib.request
        import json
        for port in (8000, 8001):
            try:
                url = f'http://127.0.0.1:{port}/taxonomy/reload'
                req = urllib.request.Request(url, method='POST')
                with urllib.request.urlopen(req, timeout=2) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    print('Reloaded server on port', port, '->', data)
                    break
            except Exception:
                continue
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
