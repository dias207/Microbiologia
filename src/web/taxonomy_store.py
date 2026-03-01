from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

# файл, где будем хранить пользовательскую таксономию
TAXONOMY_PATH = Path(__file__).resolve().parents[2] / "artifacts" / "taxonomy.json"

# базовый словарь, тот же что раньше находился в app.py
DEFAULT_TAXONOMY: Dict[str, Dict[str, str]] = {
    "escherichia_coli": {
        "family": "Enterobacteriaceae",
        "genus": "Escherichia",
        "species": "E. coli",
    },
    "salmonella_enterica": {
        "family": "Enterobacteriaceae",
        "genus": "Salmonella",
        "species": "S. enterica",
    },
    "shigella_dysenteriae": {
        "family": "Enterobacteriaceae",
        "genus": "Shigella",
        "species": "S. dysenteriae",
    },
    "yersinia_pestis": {
        "family": "Enterobacteriaceae",
        "genus": "Yersinia",
        "species": "Y. pestis",
    },
    "campylobacter_jejuni": {
        "family": "Campylobacteraceae",
        "genus": "Campylobacter",
        "species": "C. jejuni",
    },
    "helicobacter_pylori": {
        "family": "Helicobacteraceae",
        "genus": "Helicobacter",
        "species": "H. pylori",
    },
    "staphylococcus_aureus": {
        "family": "Micrococcaceae",
        "genus": "Staphylococcus",
        "species": "S. aureus",
    },
}


def load_taxonomy() -> Dict[str, Dict[str, str]]:
    """Загружает словарь таксономии из файла, если он есть.
    При наличии возвращает DEFAULT_TAXONOMY обновлённый пользовательскими записями.
    """

    if TAXONOMY_PATH.exists():
        try:
            with TAXONOMY_PATH.open("r", encoding="utf-8") as f:
                data = json.load(f)
            merged = DEFAULT_TAXONOMY.copy()
            merged.update(data)
            return merged
        except Exception:  # pragma: no cover - fail safe
            return DEFAULT_TAXONOMY.copy()
    else:
        return DEFAULT_TAXONOMY.copy()


def save_taxonomy(taxonomy: Dict[str, Dict[str, str]]) -> None:
    """Сохраняет текущую таксономию в JSON-файл."""

    TAXONOMY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TAXONOMY_PATH.open("w", encoding="utf-8") as f:
        json.dump(taxonomy, f, ensure_ascii=False, indent=2)
