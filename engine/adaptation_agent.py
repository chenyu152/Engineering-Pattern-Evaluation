import re
import logging
from typing import Dict, Any
from core.schema import DecisionSlice, TaskAnalysisResult, ReferenceCodeSlice

logger = logging.getLogger(__name__)

class AdaptationAgent:
    """
    Implements the core 'Genetic Copy + Mutation' principle from 'AI Agent Book':
    Takes an authoritative, verified reference code slice and adapts it to match
    the user's specific domain context while preserving verified architectural invariants.
    """
    def __init__(self):
        pass

    def adapt_reference_slice(
        self,
        decision_slice: DecisionSlice,
        task_analysis: TaskAnalysisResult
    ) -> Dict[str, Any]:
        ref_code = decision_slice.reference_code

        # Generate contextual customization header and adaptation guide
        adaptation_guide = (
            f"# ====================================================================\n"
            f"# ARCHITECTURE PATTERN: {decision_slice.pattern_name}\n"
            f"# STANDARD REFERENCE: {decision_slice.standard_reference.value}\n"
            f"# TARGET TASK: {task_analysis.raw_query}\n"
            f"# INVARIANTS TO PRESERVE:\n"
            + "\n".join([f"#  * {t.dimension}: Maintain {t.advantage}" for t in decision_slice.tradeoffs]) + "\n"
            f"# FAILURE BOUNDARIES TO AVOID:\n"
            + "\n".join([f"#  * GUARD AGAINST: {f.trigger_condition} ({f.mitigation_strategy})" for f in decision_slice.failure_modes]) + "\n"
            f"# ====================================================================\n\n"
        )

        adapted_code = adaptation_guide + ref_code.code_content
        adapted_test = (
            f"# Test suite for adapted solution: {decision_slice.pattern_name}\n"
            + ref_code.test_code
        )

        instructions = (
            f"1. Inherit the core architectural structure from '{decision_slice.pattern_name}'.\n"
            f"2. Customize the domain entities to match '{task_analysis.raw_query}'.\n"
            f"3. Strictly adhere to the failure guardrails: "
            + "; ".join([f.mitigation_strategy for f in decision_slice.failure_modes])
        )

        return {
            "adapted_code": adapted_code,
            "adapted_test": adapted_test,
            "instructions": instructions,
            "entry_point": ref_code.entry_point,
            "dependencies": ref_code.dependencies
        }
