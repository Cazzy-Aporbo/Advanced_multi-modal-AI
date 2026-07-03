from __future__ import annotations

from pathlib import Path

import pyarrow.compute as pc
import pyarrow.dataset as ds

from .contracts import MusicFeatureSlice, MusicFeatureWarehouseRun


def slice_feature_rows(
    runs: list[MusicFeatureWarehouseRun],
    *,
    manifest_id: str = "",
    run_id: str = "",
    limit: int = 32,
) -> MusicFeatureSlice:
    selected_runs = [
        item
        for item in runs
        if (not manifest_id or item.manifest_id == manifest_id)
        and (not run_id or item.run_id == run_id)
    ]
    paths = [Path(item.feature_table_path) for item in selected_runs if item.feature_table_path]
    existing_paths = [path for path in paths if path.exists()]
    if not existing_paths:
        return MusicFeatureSlice(row_count=0, source_paths=[], rows=[])

    dataset = ds.dataset([str(path) for path in existing_paths], format="parquet")
    scan_filter = pc.equal(pc.field("manifest_id"), manifest_id) if manifest_id else None
    table = dataset.scanner(filter=scan_filter).to_table()
    row_count = table.num_rows
    rows = table.slice(0, limit).to_pylist()
    return MusicFeatureSlice(
        row_count=row_count,
        source_paths=[str(path) for path in existing_paths],
        rows=rows,
    )
