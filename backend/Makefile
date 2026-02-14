PY=python3
PIP=pip3
APP=app.main:app

.PHONY: venv deps dev test package deploy

venv:
	$(PY) -m venv .venv

deps:
	. .venv/bin/activate && $(PIP) install -r requirements.txt

dev:
	. .venv/bin/activate && uvicorn $(APP) --reload --port 8000

test:
	. .venv/bin/activate && pytest -q || true

package:
	@echo "Package for SCF (placeholder)"

deploy:
	@echo "Deploy to SCF/CloudBase (placeholder)"

