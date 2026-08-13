"""Tests for SQLite HistoryRepository."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from quotation.domain.historical import HistoricalFeature
from quotation.infrastructure.database.repository import HistoryRepository


@pytest.fixture
def repo():
    """Create a repository backed by a temp SQLite file."""
    import gc
    tmp = tempfile.TemporaryDirectory()
    db_path = Path(tmp.name) / "test_history.db"
    r = HistoryRepository(str(db_path))
    yield r
    # Ensure all connections are closed before cleanup
    gc.collect()
    tmp.cleanup()


@pytest.fixture
def sample_records():
    return [
        HistoricalFeature(
            id="hf-001",
            part_no="UC1000005854",
            part_code="J003",
            material="S50C",
            overall_length=928.0,
            overall_width=796.0,
            overall_height=15.0,
            weight_kg=86.91,
            surface_treatment="熱處理",
            historical_price=1425.0,
            source_bom="BOM.xlsx",
            source_bom_row=158,
            project_name="GCS",
            created_at="2026-08-01T10:00:00",
        ),
        HistoricalFeature(
            id="hf-002",
            part_no="UC1002009711",
            part_code="R001",
            material="A6061-T6",
            overall_length=250.0,
            overall_height=15.0,
            weight_kg=1.99,
            surface_treatment="陽極氧化",
            historical_price=209.0,
            source_bom="BOM.xlsx",
            source_bom_row=120,
            project_name="GCS",
            created_at="2026-08-01T10:00:00",
        ),
        HistoricalFeature(
            id="hf-003",
            part_no="UC1004001529",
            part_code="W002",
            material="SPCC",
            overall_length=56.0,
            overall_width=50.0,
            overall_height=44.0,
            surface_treatment="噴塗(RAL9003)",
            historical_price=16.0,
            source_bom="BOM.xlsx",
            source_bom_row=200,
            project_name="GCS",
            created_at="2026-08-01T10:00:00",
        ),
    ]


class TestRepositoryBasic:
    def test_insert_and_retrieve(self, repo, sample_records):
        repo.insert(sample_records[0])
        assert repo.count() == 1
        found = repo.get_by_part_no("UC1000005854")
        assert found is not None
        assert found.material == "S50C"
        assert found.historical_price == 1425.0

    def test_insert_batch(self, repo, sample_records):
        count = repo.insert_batch(sample_records)
        assert count == 3
        assert repo.count() == 3

    def test_get_by_part_no_not_found(self, repo):
        assert repo.get_by_part_no("NONEXISTENT") is None

    def test_get_all_pagination(self, repo, sample_records):
        repo.insert_batch(sample_records)
        results = repo.get_all(limit=2, offset=0)
        assert len(results) == 2

    def test_get_by_material(self, repo, sample_records):
        repo.insert_batch(sample_records)
        s50c_parts = repo.get_by_material("S50C")
        assert len(s50c_parts) == 1
        assert s50c_parts[0].part_no == "UC1000005854"

    def test_get_by_project(self, repo, sample_records):
        repo.insert_batch(sample_records)
        gcs_parts = repo.get_by_project("GCS")
        assert len(gcs_parts) == 3

    def test_count_by_material(self, repo, sample_records):
        repo.insert_batch(sample_records)
        counts = repo.count_by_material()
        assert counts["S50C"] == 1
        assert counts["A6061-T6"] == 1
        assert counts["SPCC"] == 1

    def test_insert_or_replace(self, repo, sample_records):
        """Re-inserting same ID should replace."""
        repo.insert(sample_records[0])
        # Modify and re-insert
        modified = sample_records[0].model_copy(update={"historical_price": 1500.0})
        repo.insert(modified)
        assert repo.count() == 1
        found = repo.get_by_part_no("UC1000005854")
        assert found.historical_price == 1500.0

    def test_empty_repo(self, repo):
        assert repo.count() == 0
        assert repo.get_all() == []
