# Testing Guide

## Quick Start

- Backend tests
  - cd backend
  - python3 -m venv .venv && . .venv/bin/activate
  - pip install -r requirements.txt
  - pytest -q

## Notes

- Default repo provider is `memory` with seeded content; tests rely on this.
- Write endpoints require `x-openid` header (middleware enforced). Tests include examples.
- TCB client tests stub `_request` to validate payload shape and ID normalization; no real network calls.
- Export longshot writes images to `exports/` when Pillow is available; otherwise creates an empty file placeholder.
- Target coverage: ≥80% on write paths (auth/vocab/study/import/export).
- Import URL extraction tests monkeypatch `requests.get` and require `beautifulsoup4` (already in requirements).
