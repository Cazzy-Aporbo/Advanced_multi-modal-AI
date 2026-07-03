PYTHON ?= python3

.PHONY: install lint test run benchmark openapi sdk acceptance examples

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e .[dev]

lint:
	ruff check src tests

test:
	pytest

run:
	uvicorn advanced_multimodal_ai.api:create_app --factory --host 0.0.0.0 --port 8000

benchmark:
	$(PYTHON) -m advanced_multimodal_ai.cli benchmark --iterations 5

openapi:
	$(PYTHON) scripts/export_openapi.py

sdk: openapi
	$(PYTHON) scripts/generate_sdk_surfaces.py

acceptance:
	$(PYTHON) scripts/run_acceptance_spine.py

examples:
	$(PYTHON) scripts/export_example_bundle.py
