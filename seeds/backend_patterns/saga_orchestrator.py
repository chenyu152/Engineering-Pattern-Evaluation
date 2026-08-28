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

SAGA_CODE = '''
from typing import List, Dict, Any, Callable

class SagaStep:
    def __init__(
        self,
        name: str,
        action: Callable[[Dict[str, Any]], Any],
        compensate: Callable[[Dict[str, Any]], Any]
    ):
        self.name = name
        self.action = action
        self.compensate = compensate

class SagaOrchestrator:
    """
    Saga Pattern (Orchestrator-based) for Distributed Transactions.
    Executes a sequence of local transactions; if one fails, runs compensating transactions in reverse order.
    """
    def __init__(self, steps: List[SagaStep]):
        self.steps = steps

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        executed_steps: List[SagaStep] = []
        context = dict(payload)

        for step in self.steps:
            try:
                res = step.action(context)
                context[f"{step.name}_result"] = res
                executed_steps.append(step)
            except Exception as e:
                # Step failed: initiate reverse compensation
                compensation_logs = []
                for comp_step in reversed(executed_steps):
                    try:
                        comp_res = comp_step.compensate(context)
                        compensation_logs.append({"step": comp_step.name, "status": "compensated", "result": comp_res})
                    except Exception as comp_err:
                        compensation_logs.append({"step": comp_step.name, "status": "compensation_failed", "error": str(comp_err)})

                return {
                    "status": "rolled_back",
                    "failed_step": step.name,
                    "error": str(e),
                    "compensations": compensation_logs
                }

        return {
            "status": "committed",
            "context": context
        }
'''

SAGA_TEST = '''
def test_saga_orchestrator_success_and_rollback():
    # Mock services
    balance = 100
    inventory = 5
    order_created = False

    def deduct_money(ctx):
        nonlocal balance
        if balance < ctx["price"]:
            raise RuntimeError("Insufficient funds")
        balance -= ctx["price"]
        return balance

    def refund_money(ctx):
        nonlocal balance
        balance += ctx["price"]
        return balance

    def reserve_item(ctx):
        nonlocal inventory
        if inventory <= 0:
            raise RuntimeError("Out of stock")
        inventory -= 1
        return inventory

    def release_item(ctx):
        nonlocal inventory
        inventory += 1
        return inventory

    step1 = SagaStep("Payment", deduct_money, refund_money)
    step2 = SagaStep("Inventory", reserve_item, release_item)
    saga = SagaOrchestrator([step1, step2])

    # 1. Successful transaction
    res1 = saga.execute({"price": 30})
    assert res1["status"] == "committed"
    assert balance == 70
    assert inventory == 4

    # 2. Failing second step triggers rollback of step 1
    inventory = 0  # Force out of stock
    res2 = saga.execute({"price": 30})
    assert res2["status"] == "rolled_back"
    assert res2["failed_step"] == "Inventory"
    # Balance should be refunded back to 70
    assert balance == 70
'''

SEED_SAGA_ORCHESTRATOR = DecisionSlice(
    id="backend_saga_distributed_transaction",
    pattern_name="Saga Orchestrator Pattern",
    category=PatternCategory.BACKEND_DISTRIBUTED,
    standard_reference=StandardReference.MADR_SPEC,
    problem_statement="Maintain data consistency across multiple isolated microservice databases without using blocking, unscalable Two-Phase Commit (2PC) protocols.",
    context_constraints=ConstraintProfile(
        scale="cluster",
        consistency_level="eventual",
        infra_dependencies=[]
    ),
    considered_alternatives=[
        AlternativeConsidered(
            name="Two-Phase Commit (2PC / XA Transactions)",
            rejected_reason="Heavy synchronous locking across services causing high latency and coordinator single point of failure"
        )
    ],
    chosen_solution_summary="Decompose distributed transaction into a series of local transactions with explicit forward Actions and backward Compensations orchestrated sequentially.",
    tradeoffs=[
        TradeoffItem(
            dimension="Eventual Consistency vs System Decoupling",
            advantage="Non-blocking, highly scalable consistency across decoupled microservices",
            disadvantage="Must design and test compensating business logic for every transaction step",
            rationale="Compensating actions guarantee eventual convergence without long-lived distributed locks"
        )
    ],
    failure_modes=[
        FailureMode(
            trigger_condition="A compensation action itself fails due to downstream crash or bug",
            consequence="Inconsistent intermediate state",
            mitigation_strategy="Ensure all compensation actions are strictly idempotent with automatic retry queues"
        )
    ],
    reference_code=ReferenceCodeSlice(
        entry_point="SagaOrchestrator",
        language="python",
        code_content=SAGA_CODE,
        test_code=SAGA_TEST,
        dependencies=[]
    ),
    evidence=EvidenceData(
        evidence_level=EvidenceLevel.CONTROLLED_SANDBOX,
        source_reference="Microservices Patterns (Chris Richardson) / Sagas (Hector Garcia-Molina)",
        test_pass_rate=1.0,
        benchmark_metrics={"rollback_success_rate": "100%"}
    ),
    confidence_score=0.98,
    status=LifecycleStatus.ACTIVE
)
