"""Speech evaluation service — recognizes audio and scores against reference text."""

from __future__ import annotations

import io
import logging
import tempfile

import speech_recognition as sr

logger = logging.getLogger(__name__)


def evaluate(audio_bytes: bytes, reference: str) -> dict:
    """Evaluate pronunciation: recognize speech from MP3 audio, compare to reference.

    Returns {"recognized": str, "score": int, "level": str, "color": str}.
    """
    try:
        from pydub import AudioSegment

        # MP3 → WAV in memory
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
        wav_io = io.BytesIO()
        audio.export(wav_io, format="wav")
        wav_io.seek(0)

        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_io) as source:
            audio_data = recognizer.record(source)

        recognized: str = recognizer.recognize_google(audio_data, language="en-US")
    except sr.UnknownValueError:
        return _result("", 0, "未识别到语音", "#999")
    except Exception:
        logger.warning("Speech recognition failed", exc_info=True)
        return _result("", 0, "识别失败", "#999")

    score = _calc_similarity(recognized, reference)
    level, color = _score_label(score)
    return _result(recognized, score, level, color)


def _result(recognized: str, score: int, level: str, color: str) -> dict:
    return {"recognized": recognized, "score": score, "level": level, "color": color}


def _score_label(score: int) -> tuple[str, str]:
    if score >= 90:
        return "完美", "#4caf50"
    if score >= 70:
        return "不错", "#667eea"
    if score >= 50:
        return "继续加油", "#ffa726"
    return "再试一次", "#ef5350"


def _calc_similarity(recognized: str, reference: str) -> int:
    """Word-level ordered matching similarity (0–100)."""
    def normalize(s: str) -> list[str]:
        return [w for w in s.lower().replace("'", "'")
                .translate(str.maketrans("", "", ".,!?;:\"()-"))
                .split() if w]

    rec_words = normalize(recognized)
    ref_words = normalize(reference)

    if not ref_words:
        return 0
    if not rec_words:
        return 0

    matched = 0
    ri = 0
    for word in ref_words:
        while ri < len(rec_words):
            if rec_words[ri] == word:
                matched += 1
                ri += 1
                break
            ri += 1

    return round(matched / len(ref_words) * 100)
