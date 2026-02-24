import json
import logging
from pathlib import Path
from ..repositories.interfaces import Repository

logger = logging.getLogger(__name__)

# Locate data/ directory — works in both local dev and Docker container:
#   Local:  backend/app/infra/bootstrap.py → 4 parents → project-root/data/
#   Docker: /app/app/infra/bootstrap.py    → 3 parents → /app/data/
_THIS_DIR = Path(__file__).resolve().parent
_CANDIDATES = [
    _THIS_DIR.parent.parent.parent.parent / "data",  # local: project-root/data/
    _THIS_DIR.parent.parent.parent / "data",          # docker: /app/data/
    _THIS_DIR.parent.parent / "data",                 # fallback
    Path("/app/data"),                                 # absolute fallback for Docker
]
DATA_DIR = next((p for p in _CANDIDATES if p.is_dir()), _CANDIDATES[0])


def _load_json(filename: str) -> list:
    """Load a JSON array file from the data directory."""
    path = DATA_DIR / filename
    if not path.exists():
        logger.warning("Data file not found: %s", path)
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def seed(repo: Repository) -> None:
    """Seed the in-memory repository with real data from data/*.json files."""

    # 1. Seed content with real learning material
    items, total = repo.query("content", None, limit=1, offset=0)
    if total == 0:
        samples = [
            {
                "type": "dialog",
                "level": "A1",
                "tags": ["greeting", "daily"],
                "text": "Hello! How are you? I'm fine, thank you. Nice to meet you! See you later.",
                "audio_url": None,
                "segments": [
                    "Hello! How are you?",
                    "I'm fine, thank you.",
                    "And you? How are you doing?",
                    "Pretty good! Thanks for asking.",
                    "Nice to meet you!",
                    "Nice to meet you too.",
                    "See you later! Goodbye!",
                ],
            },
            {
                "type": "dialog",
                "level": "A1",
                "tags": ["shopping", "daily"],
                "text": "Can I help you? I'm looking for a shirt. What size are you? Medium, please.",
                "audio_url": None,
                "segments": [
                    "Excuse me, can I help you?",
                    "Yes, I'm looking for a shirt.",
                    "What size are you?",
                    "I'm a medium, please.",
                    "How about this one? It's on sale.",
                    "That looks great! How much is it?",
                    "It's twenty dollars.",
                    "I'll take it. Thank you!",
                ],
            },
            {
                "type": "dialog",
                "level": "A2",
                "tags": ["restaurant", "food"],
                "text": "Are you ready to order? I'd like the pasta. And to drink?",
                "audio_url": None,
                "segments": [
                    "Good evening! Welcome to our restaurant.",
                    "Thank you! A table for two, please.",
                    "Right this way. Are you ready to order?",
                    "Yes. I'd like the grilled chicken, please.",
                    "Excellent choice! And for you?",
                    "I'll have the pasta with tomato sauce.",
                    "And what would you like to drink?",
                    "Two glasses of water, please.",
                    "Of course. Your food will be ready shortly.",
                ],
            },
            {
                "type": "dialog",
                "level": "A2",
                "tags": ["travel", "directions"],
                "text": "Excuse me, how do I get to the station? Turn left at the corner.",
                "audio_url": None,
                "segments": [
                    "Excuse me, could you help me?",
                    "Of course! What do you need?",
                    "How do I get to the train station from here?",
                    "It's not far. Go straight down this street.",
                    "Then turn left at the traffic lights.",
                    "After that, walk about two blocks.",
                    "The station will be on your right side.",
                    "Thank you so much! That's very helpful.",
                    "You're welcome! Have a safe trip.",
                ],
            },
            {
                "type": "dialog",
                "level": "B1",
                "tags": ["work", "office"],
                "text": "Tell me about yourself. I have three years of experience in marketing.",
                "audio_url": None,
                "segments": [
                    "Good morning! Please have a seat.",
                    "Thank you for seeing me today.",
                    "Can you tell me a little about yourself?",
                    "Sure. I have three years of experience in digital marketing.",
                    "I managed social media campaigns for a tech startup.",
                    "What are your greatest strengths?",
                    "I'm very detail-oriented and work well under pressure.",
                    "I also enjoy collaborating with cross-functional teams.",
                    "Why are you interested in this position?",
                    "I'm excited about your company's innovative approach.",
                ],
            },
        ]
        for it in samples:
            repo.put("content", it)

    # 2. Seed assessment questions from data/assessment_questions.json
    items, total = repo.query("assessment_questions", None, limit=1, offset=0)
    if total == 0:
        questions = _load_json("assessment_questions.json")
        for q in questions:
            # Use _id from the JSON as the document id
            q["id"] = q.pop("_id", q.get("id"))
            repo.put("assessment_questions", q)
        logger.info("Seeded %d assessment questions", len(questions))

    # 3. Seed scenarios from data/scenarios.json
    items, total = repo.query("scenarios", None, limit=1, offset=0)
    if total == 0:
        scenarios = _load_json("scenarios.json")
        for s in scenarios:
            repo.put("scenarios", s)
        logger.info("Seeded %d scenarios", len(scenarios))

    # 4. Seed dialogues from data/dialogues.json
    items, total = repo.query("dialogues", None, limit=1, offset=0)
    if total == 0:
        dialogues = _load_json("dialogues.json")
        for d in dialogues:
            repo.put("dialogues", d)
        logger.info("Seeded %d dialogues", len(dialogues))
