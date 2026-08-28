import pytest
from pathlib import Path
from storage.hybrid_repository import HybridRepository
from ingestion.swe_bench_extractor import SWEBenchExtractor

def test_swe_bench_jsonl_ingestion():
    repo = HybridRepository()
    extractor = SWEBenchExtractor(repository=repo)

    jsonl_file = Path(__file__).parent.parent / "seeds" / "swe_cases" / "sample_swe_trajectories.jsonl"
    assert jsonl_file.exists()

    res = extractor.ingest_jsonl_file(str(jsonl_file))
    assert res["ingested_count"] == 3
    assert len(res["ingested_ids"]) == 3
    
    # Verify in repository
    slice_id = res["ingested_ids"][0]
    decision = repo.get_by_id(slice_id)
    assert decision is not None
    assert decision.standard_reference.value == "SWE-bench Industrial Trajectory Format"
    assert decision.category.value == "Fault_Tolerance"
