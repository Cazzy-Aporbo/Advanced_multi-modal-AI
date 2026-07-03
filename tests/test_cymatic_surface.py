from __future__ import annotations

from advanced_multimodal_ai.cymatic_surface import build_cymatic_surface_bundle
from advanced_multimodal_ai.service import AdvancedMultimodalService


def test_cymatic_surface_bundle_stays_bounded_and_connected():
    service = AdvancedMultimodalService()
    route_count = 68

    bundle = build_cymatic_surface_bundle(
        research_bundle=service.research_surface_bundle(route_count=route_count),
        repository_pulse=service.repository_pulse(route_count=route_count),
        benchmark=service.run_reference_benchmark(route_count=route_count),
        execution_journal=service.execution_journal(limit=20),
    )

    assert bundle.service == "advanced-multimodal-ai"
    assert 0.0 <= bundle.baseline_harmony <= 1.0
    assert 0.0 <= bundle.tension_index <= 1.0
    assert bundle.route_count == route_count
    assert bundle.connector_kind_count >= 1
    assert bundle.active_files >= 1
    assert bundle.total_runs >= 1
    assert len(bundle.harmonic_bands) >= 4
    assert len(bundle.stages) >= 5
    assert len(bundle.narratives) == 3

    for band in bundle.harmonic_bands:
        assert 0.0 <= band.intensity <= 1.0
        assert 0.0 <= band.drift <= 1.0
        assert band.note

    for stage in bundle.stages:
        assert 0.0 <= stage.harmony_score <= 1.0
        assert 0.0 <= stage.friction_score <= 1.0
        assert stage.trace_paths
        assert stage.files
        assert stage.human_read
        assert stage.research_read
        assert stage.business_read
        assert stage.improvement_path
        assert len(stage.metrics) >= 3
