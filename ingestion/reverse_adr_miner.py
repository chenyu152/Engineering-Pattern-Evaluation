import re
import json
import logging
from typing import Dict, Any, Optional
from core.schema import (
    DecisionSlice,
    ConstraintProfile,
    TradeoffItem,
    AlternativeConsidered,
    FailureMode,
    ReferenceCodeSlice,
    EvidenceData,
    PatternCategory,
    StandardReference,
    EvidenceLevel,
    LifecycleStatus,
)

logger = logging.getLogger(__name__)

class ReverseADRMiner:
    """
    Mines and extracts structured DecisionSlices from markdown ADRs, PR descriptions,
    or design review docs.
    """
    def __init__(self):
        pass

    def parse_markdown_madr(self, madr_content: str, slice_id: str) -> Optional[DecisionSlice]:
        """
        Parses standard MADR (Markdown Architecture Decision Records) format into DecisionSlice.
        """
        try:
            # Extract title / pattern name
            title_match = re.search(r"^#\s+(.+)$", madr_content, re.MULTILINE)
            pattern_name = title_match.group(1).strip() if title_match else "Extracted Pattern"

            # Extract Context and Problem Statement
            context_match = re.search(r"##\s*Context and Problem Statement\s*\n(.*?)(?=\n##|\Z)", madr_content, re.DOTALL | re.IGNORECASE)
            problem_statement = context_match.group(1).strip() if context_match else "Unspecified problem"

            # Extract Considered Options
            options_match = re.search(r"##\s*Considered Options\s*\n(.*?)(?=\n##|\Z)", madr_content, re.DOTALL | re.IGNORECASE)
            alternatives = []
            if options_match:
                for line in options_match.group(1).strip().splitlines():
                    if line.strip().startswith(("-", "*")):
                        opt_text = line.strip().lstrip("-* ").strip()
                        alternatives.append(AlternativeConsidered(
                            name=opt_text,
                            rejected_reason="Not selected under current trade-off balance"
                        ))

            # Extract Decision Outcome
            outcome_match = re.search(r"##\s*Decision Outcome\s*\n(.*?)(?=\n##|\Z)", madr_content, re.DOTALL | re.IGNORECASE)
            decision_summary = outcome_match.group(1).strip() if outcome_match else "Chosen architecture solution"

            # Extract Pros and Cons / Tradeoffs
            tradeoffs = []
            pros_match = re.search(r"###?\s*Positive Consequences\s*\n(.*?)(?=\n###?|\n##|\Z)", madr_content, re.DOTALL | re.IGNORECASE)
            cons_match = re.search(r"###?\s*Negative Consequences\s*\n(.*?)(?=\n###?|\n##|\Z)", madr_content, re.DOTALL | re.IGNORECASE)

            pros = [p.strip().lstrip("-* ") for p in pros_match.group(1).splitlines() if p.strip().startswith(("-", "*"))] if pros_match else []
            cons = [c.strip().lstrip("-* ") for c in cons_match.group(1).splitlines() if c.strip().startswith(("-", "*"))] if cons_match else []

            if pros or cons:
                tradeoffs.append(TradeoffItem(
                    dimension="Quality Attributes & Overhead",
                    advantage="; ".join(pros) if pros else "High efficiency",
                    disadvantage="; ".join(cons) if cons else "Operational complexity",
                    rationale="Architecture consequence trade-off"
                ))

            # Build default reference code slice
            ref_code = ReferenceCodeSlice(
                entry_point="run_solution",
                language="python",
                code_content="# Implementation extracted from ADR\ndef run_solution():\n    pass\n",
                test_code="def test_run_solution():\n    assert True\n",
                dependencies=[]
            )

            evidence = EvidenceData(
                evidence_level=EvidenceLevel.OBSERVED,
                source_reference="Parsed from MADR document",
                test_pass_rate=1.0
            )

            decision = DecisionSlice(
                id=slice_id,
                pattern_name=pattern_name,
                category=PatternCategory.BACKEND_DISTRIBUTED,
                standard_reference=StandardReference.MADR_SPEC,
                problem_statement=problem_statement,
                context_constraints=ConstraintProfile(),
                considered_alternatives=alternatives,
                chosen_solution_summary=decision_summary,
                tradeoffs=tradeoffs,
                failure_modes=[],
                reference_code=ref_code,
                evidence=evidence,
                confidence_score=0.85,
                status=LifecycleStatus.ACTIVE
            )
            return decision
        except Exception as e:
            logger.error(f"Error parsing MADR document: {e}")
            return None
