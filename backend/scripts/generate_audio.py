#!/usr/bin/env python3
"""
Batch generate TTS audio for all dialogue sentences.

Usage:
    cd backend
    python -m scripts.generate_audio

Reads dialogues.json, generates MP3 via Edge TTS for every sentence,
saves to backend/static/audio/{dialogue_id}-{order:02d}.mp3
"""

import asyncio
import json
import sys
from pathlib import Path

# Resolve paths
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
ROOT_DIR = BACKEND_DIR.parent
DATA_FILE = ROOT_DIR / "data" / "dialogues.json"
AUDIO_DIR = BACKEND_DIR / "static" / "audio"


async def generate_all():
    try:
        import edge_tts
    except ImportError:
        print("ERROR: edge_tts not installed. Run: pip install edge-tts")
        sys.exit(1)

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        dialogues = json.load(f)

    voice = "en-US-JennyNeural"
    total = sum(len(d.get("sentences", [])) for d in dialogues)
    done = 0
    skipped = 0

    print(f"Found {len(dialogues)} dialogues, {total} sentences total")
    print(f"Audio output: {AUDIO_DIR}")
    print(f"Voice: {voice}\n")

    for dialogue in dialogues:
        did = dialogue["id"]
        sentences = dialogue.get("sentences", [])

        for sent in sentences:
            order = sent["order"]
            text = sent["text_en"]
            filename = f"{did}-{order:02d}.mp3"
            filepath = AUDIO_DIR / filename

            if filepath.exists() and filepath.stat().st_size > 0:
                skipped += 1
                done += 1
                continue

            try:
                communicate = edge_tts.Communicate(
                    text, voice, rate="-5%", pitch="+0Hz"
                )
                await communicate.save(str(filepath))
                size_kb = filepath.stat().st_size / 1024
                done += 1
                print(f"  [{done}/{total}] {filename} ({size_kb:.1f} KB)")
            except Exception as e:
                done += 1
                print(f"  [{done}/{total}] FAILED {filename}: {e}")

    print(f"\nDone! Generated: {done - skipped}, Skipped (cached): {skipped}, Total: {total}")


def update_audio_urls():
    """Update dialogues.json audio_url fields to use relative /api/tts/static/ path."""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        dialogues = json.load(f)

    changed = 0
    for dialogue in dialogues:
        did = dialogue["id"]
        for sent in dialogue.get("sentences", []):
            order = sent["order"]
            new_url = f"/static/audio/{did}-{order:02d}.mp3"
            if sent.get("audio_url") != new_url:
                sent["audio_url"] = new_url
                changed += 1

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(dialogues, f, ensure_ascii=False, indent=2)

    print(f"Updated {changed} audio_url entries in dialogues.json")


if __name__ == "__main__":
    print("=== Step 1: Generate TTS audio files ===\n")
    asyncio.run(generate_all())

    print("\n=== Step 2: Update audio_url in dialogues.json ===\n")
    update_audio_urls()

    print("\n=== Complete ===")
