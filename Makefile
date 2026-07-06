PYTHON ?= python3

.PHONY: install lint test run benchmark openapi sdk acceptance examples proof gateway edge-topology stack-config

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e .[dev]

lint:
	ruff check src tests scripts

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

gateway:
	$(PYTHON) scripts/export_edge_topology.py

edge-topology:
	$(PYTHON) scripts/export_edge_topology.py

proof:
	$(PYTHON) scripts/export_openapi.py
	$(PYTHON) scripts/generate_sdk_surfaces.py
	$(PYTHON) scripts/export_research_surfaces.py
	$(PYTHON) scripts/export_research_influence.py
	$(PYTHON) scripts/export_cymatic_surface.py
	$(PYTHON) scripts/export_repository_pulse.py
	$(PYTHON) scripts/export_repository_file_map.py
	$(PYTHON) scripts/export_repository_growth.py
	$(PYTHON) scripts/export_benchmark_surfaces.py
	$(PYTHON) scripts/export_music_observatory.py
	$(PYTHON) scripts/export_privacy_membrane.py
	$(PYTHON) scripts/export_operator_surfaces.py
	$(PYTHON) scripts/export_industry_profiles.py
	$(PYTHON) scripts/export_industrial_diagnostics.py
	$(PYTHON) scripts/export_edge_topology.py
	$(PYTHON) scripts/export_execution_journal.py
	$(PYTHON) scripts/export_readiness_report.py
	$(PYTHON) scripts/export_example_bundle.py
	$(PYTHON) scripts/build_runtime_proof_bundle.py
	$(PYTHON) scripts/export_readme_visuals.py

stack-config:
	docker compose -f containers/compose.yaml config
