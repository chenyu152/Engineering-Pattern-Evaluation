import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from core.schema import DecisionSlice
from storage.hybrid_repository import HybridRepository
from evaluator.sandbox_runner import SandboxRunner
from evaluator.evidence_scorer import EvidenceScorer
from .reverse_adr_miner import ReverseADRMiner
from .ast_slicer import ASTCodeSlicer

logger = logging.getLogger(__name__)

class RepositoryMiner:
    """
    Automated Architecture Decision Record (ADR) and Post-Mortem miner.
    Scans repositories for architecture decisions, refactoring docs, and design notes,
    extracts structured DecisionSlices, validates them in sandbox, and saves to repository.
    """
    def __init__(self, repository: Optional[HybridRepository] = None, sandbox: Optional[SandboxRunner] = None):
        self.repository = repository or HybridRepository()
        self.sandbox = sandbox or SandboxRunner()
        self.scorer = EvidenceScorer()
        self.adr_miner = ReverseADRMiner()
        self.ast_slicer = ASTCodeSlicer()

    def find_adr_files(self, repo_dir: Path) -> List[Path]:
        """Discovers potential ADR and architecture markdown files in a repository."""
        adr_files = []
        target_subdirs = ["docs/adr", "doc/adr", "docs/architecture", "decisions", ".adr", "doc/decisions"]
        
        # 1. Search in conventional ADR directories
        for sub in target_subdirs:
            target_path = repo_dir / sub
            if target_path.exists() and target_path.is_dir():
                for p in target_path.glob("**/*.md"):
                    if p.is_file():
                        adr_files.append(p)

        # 2. Search for *.adr.md or ADR-*.md anywhere in the repo (up to depth 4)
        for p in repo_dir.glob("*/**"):
            if any(part.startswith((".", "node_modules", "venv", ".git")) for part in p.parts):
                continue
            for md in p.glob("*.md"):
                if "adr" in md.name.lower() or "decision" in md.name.lower() or "postmortem" in md.name.lower():
                    if md not in adr_files:
                        adr_files.append(md)

        return adr_files

    def mine_file(self, file_path: Path) -> Optional[DecisionSlice]:
        """Parses a single ADR markdown file into a verified DecisionSlice."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            slice_id = f"mined_{file_path.stem.lower().replace('-', '_').replace(' ', '_')}"
            decision = self.adr_miner.parse_markdown_madr(content, slice_id)
            if not decision:
                return None

            # Test in sandbox
            test_res = self.sandbox.run_code_slice_test(decision.reference_code)
            is_valid = test_res.get("success", False)
            decision.confidence_score = self.scorer.calculate_confidence(decision, test_success=is_valid)

            return decision
        except Exception as e:
            logger.error(f"Failed to mine file {file_path}: {e}")
            return None

    def mine_directory(self, repo_dir_str: str) -> Dict[str, Any]:
        """Batch mines all ADRs in a given local directory or repository."""
        repo_path = Path(repo_dir_str)
        if not repo_path.exists():
            raise FileNotFoundError(f"Repository directory does not exist: {repo_dir_str}")

        adr_files = self.find_adr_files(repo_path)
        mined_slices: List[DecisionSlice] = []
        errors: List[str] = []

        for fpath in adr_files:
            logger.info(f"Mining ADR file: {fpath}")
            slice_obj = self.mine_file(fpath)
            if slice_obj:
                self.repository.save_decision_slice(slice_obj)
                mined_slices.append(slice_obj)
            else:
                errors.append(str(fpath))

        return {
            "scanned_directory": str(repo_path),
            "adr_files_found": len(adr_files),
            "successfully_mined_count": len(mined_slices),
            "mined_slice_ids": [s.id for s in mined_slices],
            "failed_files": errors
        }
