"""
intent_service.py — CRUD sederhana untuk data/intents_magang_v3.json.

Dipakai oleh admin_handler.py supaya intent (FAQ) bisa diedit langsung
dari command Telegram, tanpa buka file manual. Sumber data sama persis
dengan yang dipakai FaqMatcher (app/ml/faq_matcher.py) -- path-nya di-
reuse dari sana supaya tidak ada dua definisi path yang bisa beda.

Tidak ada database terpisah untuk intent -- baca/tulis langsung ke file
JSON. Untuk data sekecil FAQ ini cukup aman; kalau nanti butuh multi-
admin edit bersamaan / riwayat perubahan, baru pertimbangkan pindah ke
tabel database.
"""

import json

from app.ml.faq_matcher import DATA_PATH


def _load() -> dict:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict) -> None:
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _find(data: dict, tag: str):
    for intent in data["intents"]:
        if intent["tag"] == tag:
            return intent
    return None


def list_intents() -> list:
    """Return [{tag, category, n_patterns, n_keywords}, ...]."""
    data = _load()
    return [
        {
            "tag": intent["tag"],
            "category": intent.get("category", "-"),
            "n_patterns": len(intent.get("patterns", [])),
            "n_keywords": len(intent.get("keywords", [])),
        }
        for intent in data["intents"]
    ]


def get_intent(tag: str):
    """Return intent dict (patterns/responses/keywords) atau None."""
    data = _load()
    return _find(data, tag)


def add_intent(tag: str, patterns: list, response: str, category: str = "Umum") -> None:
    """Raise ValueError kalau tag sudah ada."""
    data = _load()
    if _find(data, tag) is not None:
        raise ValueError(f"Intent '{tag}' sudah ada.")

    data["intents"].append({
        "tag": tag,
        "category": category,
        "patterns": patterns,
        "responses": [response],
        "keywords": [],
    })
    _save(data)


def delete_intent(tag: str) -> bool:
    """Return True kalau berhasil dihapus, False kalau tag tidak ditemukan."""
    data = _load()
    intent = _find(data, tag)
    if intent is None:
        return False

    data["intents"].remove(intent)
    _save(data)
    return True


def set_response(tag: str, response: str) -> bool:
    data = _load()
    intent = _find(data, tag)
    if intent is None:
        return False

    intent["responses"] = [response]
    _save(data)
    return True


def add_keyword(tag: str, keyword: str) -> str:
    """Tambah keyword ke intent. Return status:
    - "not_found"  -> tag tidak ada
    - "duplicate"  -> keyword sudah ada di intent itu, tidak ada perubahan
    - "added"      -> keyword baru berhasil ditambahkan & disimpan
    """
    data = _load()
    intent = _find(data, tag)
    if intent is None:
        return "not_found"

    keywords = intent.setdefault("keywords", [])
    keyword = keyword.strip()
    if not keyword or keyword in keywords:
        return "duplicate"

    keywords.append(keyword)
    _save(data)
    return "added"


def add_patterns(tag: str, patterns: list):
    """Tambah 1+ pattern ke intent yang SUDAH ADA (tidak menyentuh jawaban/
    keyword sama sekali). Return (added, duplicate, not_found):
    - not_found  -> True kalau tag tidak ada
    - added      -> list pattern baru yang berhasil ditambahkan & disimpan
    - duplicate  -> list pattern yang sudah ada sebelumnya, dilewati (tidak digandakan)
    """
    data = _load()
    intent = _find(data, tag)
    if intent is None:
        return [], [], True

    existing = intent.setdefault("patterns", [])
    added, duplicate = [], []
    for p in patterns:
        p = p.strip()
        if not p:
            continue
        if p in existing:
            duplicate.append(p)
        else:
            existing.append(p)
            added.append(p)

    if added:
        _save(data)

    return added, duplicate, False


def remove_keyword(tag: str, keyword: str) -> bool:
    """Return True kalau tag ditemukan (keyword dihapus kalau ada)."""
    data = _load()
    intent = _find(data, tag)
    if intent is None:
        return False

    keywords = intent.get("keywords", [])
    keyword = keyword.strip()
    if keyword in keywords:
        keywords.remove(keyword)
        _save(data)
    return True