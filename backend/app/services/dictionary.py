"""Lightweight dictionary lookup via Free Dictionary API."""

from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)

_API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/{word}"


def lookup(word: str) -> dict | None:
    """Look up a word and return {"meaning": "...", "phonetic": "..."} or None."""
    try:
        resp = requests.get(_API_URL.format(word=word), timeout=3)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if not data or not isinstance(data, list):
            return None
        entry = data[0]

        # Extract phonetic
        phonetic = entry.get("phonetic") or ""
        if not phonetic:
            for p in entry.get("phonetics", []):
                if p.get("text"):
                    phonetic = p["text"]
                    break

        # Extract first definition per part of speech
        parts: list[str] = []
        for m in entry.get("meanings", []):
            pos = m.get("partOfSpeech", "")
            defs = m.get("definitions", [])
            if defs:
                abbr = _abbreviate_pos(pos)
                parts.append(f"{abbr} {defs[0]['definition']}")

        meaning = "; ".join(parts) if parts else None

        if not meaning and not phonetic:
            return None

        return {"meaning": meaning, "phonetic": phonetic or None}
    except Exception:
        logger.debug("Dictionary lookup failed for '%s'", word, exc_info=True)
        return None


def _abbreviate_pos(pos: str) -> str:
    """Abbreviate part of speech for compact display."""
    mapping = {
        "noun": "n.",
        "verb": "v.",
        "adjective": "adj.",
        "adverb": "adv.",
        "pronoun": "pron.",
        "preposition": "prep.",
        "conjunction": "conj.",
        "interjection": "interj.",
    }
    return mapping.get(pos.lower(), f"{pos}.")
