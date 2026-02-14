from ..repositories.interfaces import Repository


def seed(repo: Repository) -> None:
    # Seed a few content items if empty
    items, total = repo.query("content", None, limit=1, offset=0)
    if total > 0:
        return
    samples = [
        {
            "type": "sentence",
            "level": "A1",
            "tags": ["greeting"],
            "text": "Hello, world!",
            "audio_url": None,
            "segments": ["Hello, world!"],
        },
        {
            "type": "sentence",
            "level": "A1",
            "tags": ["intro"],
            "text": "Nice to meet you.",
            "audio_url": None,
            "segments": ["Nice to meet you."],
        },
    ]
    for it in samples:
        repo.put("content", it)

