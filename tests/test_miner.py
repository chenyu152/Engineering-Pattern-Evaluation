import tempfile
from pathlib import Path
from ingestion.github_miner import RepositoryMiner
from storage.hybrid_repository import HybridRepository

SAMPLE_MADR_DOC = """# 1. Use PostgreSQL for Relational Entity Storage

## Context and Problem Statement
We need an ACID compliant relational store for user profiles and financial ledgers.

## Considered Options
* PostgreSQL
* MongoDB
* MySQL

## Decision Outcome
Chosen option: "PostgreSQL", because it has robust JSONB support and transactional integrity.

### Positive Consequences
* High transactional reliability
* Rich indexing features

### Negative Consequences
* Vertical scaling ceiling compared to NoSQL
"""

def test_repository_miner():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_dir = Path(tmpdir)
        adr_dir = repo_dir / "docs" / "adr"
        adr_dir.mkdir(parents=True, exist_ok=True)
        
        sample_file = adr_dir / "0001-use-postgresql.md"
        with open(sample_file, "w", encoding="utf-8") as f:
            f.write(SAMPLE_MADR_DOC)

        repo = HybridRepository()
        miner = RepositoryMiner(repository=repo)
        results = miner.mine_directory(str(repo_dir))

        assert results["adr_files_found"] == 1
        assert results["successfully_mined_count"] == 1
        
        mined_id = results["mined_slice_ids"][0]
        stored_slice = repo.get_by_id(mined_id)
        assert stored_slice is not None
        assert "PostgreSQL" in stored_slice.pattern_name
