import sys
import typer
from pathlib import Path
from typing import Optional

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from storage.hybrid_repository import HybridRepository
from seeds.loader import seed_database
from engine.cbr_orchestrator import CBROrchestrator
from evaluator.stale_detector import StaleDetector
from evaluator.sandbox_runner import SandboxRunner
from evaluator.evidence_scorer import EvidenceScorer
from ingestion.github_miner import RepositoryMiner

app = typer.Typer(help="Engineering Pattern Evaluation & Decision Engine CLI")
console = Console(highlight=False)

@app.command()
def seed():
    """Seed the hybrid repository with authoritative golden decision slices."""
    repo = HybridRepository()
    count = seed_database(repo)
    console.print(f"[bold green]Successfully seeded {count} golden decision slices into repository![/bold green]")

@app.command(name="list")
def list_patterns():
    """List all stored decision slices with evidence levels and confidence."""
    repo = HybridRepository()
    patterns = repo.list_all()
    if not patterns:
        console.print("[yellow]No patterns found in database. Run 'python cli.py seed' first.[/yellow]")
        return

    table = Table(title="Engineering Decision Slices & Pattern Library")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Pattern Name", style="bold")
    table.add_column("Category", style="magenta")
    table.add_column("Standard", style="blue")
    table.add_column("Evidence Level", style="green")
    table.add_column("Confidence", justify="right")
    table.add_column("Status", style="bold")

    for p in patterns:
        status_style = "green" if p.status.value == "Active" else ("yellow" if p.status.value == "Stale" else "red")
        table.add_row(
            p.id,
            p.pattern_name,
            p.category.value,
            p.standard_reference.value,
            p.evidence.evidence_level.value,
            f"{p.confidence_score:.2f}",
            f"[{status_style}]{p.status.value}[/{status_style}]"
        )

    console.print(table)

@app.command()
def evaluate(query: str = typer.Option(..., "--query", "-q", help="Engineering task query")):
    """Analyze a task and output the comparative Trade-off Matrix across candidate patterns."""
    repo = HybridRepository()
    patterns = repo.list_all()
    if not patterns:
        seed_database(repo)

    orchestrator = CBROrchestrator(repository=repo)
    report = orchestrator.process_task(query, auto_verify_sandbox=False)

    console.print(Panel(f"[bold]Query:[/bold] {query}\n[bold]Inferred Category:[/bold] {report.task_analysis.inferred_category.value}", title="Task Analysis", border_style="cyan"))

    table = Table(title="Architecture Candidates & Trade-off Matrix")
    table.add_column("Candidate Pattern", style="bold cyan")
    table.add_column("Score", justify="right", style="bold")
    table.add_column("Key Advantages", style="green")
    table.add_column("Trade-off Drawbacks / Costs", style="yellow")
    table.add_column("Failure Boundaries", style="red")
    table.add_column("Verdict", style="bold")

    for c in report.top_candidates:
        verdict_color = "green" if "STRONGLY" in c.recommendation_verdict else ("yellow" if "VIABLE" in c.recommendation_verdict else "red")
        table.add_row(
            c.pattern_name,
            f"{c.suitability_score:.2f}",
            "\n".join([f"- {p}" for p in c.pros[:2]]),
            "\n".join([f"- {co}" for co in c.cons[:2]]),
            "\n".join([f"- {f}" for f in c.critical_failure_risks[:2]]),
            f"[{verdict_color}]{c.recommendation_verdict}[/{verdict_color}]"
        )
    console.print(table)

    console.print(Panel(f"[bold green]Selected Pattern:[/bold green] {report.selected_pattern_id}\n[bold]Rationale:[/bold] {report.decision_rationale}", title="Final Decision & Recommendation", border_style="green"))

@app.command()
def solve(
    query: str = typer.Option(..., "--query", "-q", help="Engineering task query"),
    output_dir: Optional[str] = typer.Option(None, "--output", "-o", help="Directory to save generated solution code")
):
    """End-to-End CBR execution: Selects pattern, adapts reference code, verifies in sandbox, and generates solution."""
    repo = HybridRepository()
    if not repo.list_all():
        seed_database(repo)

    orchestrator = CBROrchestrator(repository=repo)
    report = orchestrator.process_task(query, auto_verify_sandbox=True)

    console.print(f"[bold green]Optimal Pattern Selected:[/bold green] {report.selected_pattern_id}")
    console.print(f"[bold]Decision Rationale:[/bold] {report.decision_rationale}")

    if report.lifecycle_warning:
        console.print(f"[yellow]Warning: {report.lifecycle_warning}[/yellow]")
    else:
        console.print("[bold green]Sandbox Test Verification Passed (100%)[/bold green]")

    if output_dir:
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        
        sol_file = out_path / "solution.py"
        test_file = out_path / "test_solution.py"
        doc_file = out_path / "ARCHITECTURE_DECISION.md"

        adapter = orchestrator.adapter
        decision_slice = repo.get_by_id(report.selected_pattern_id)
        adaptation_res = adapter.adapt_reference_slice(decision_slice, report.task_analysis)

        with open(sol_file, "w", encoding="utf-8") as f:
            f.write(adaptation_res["adapted_code"])
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(adaptation_res["adapted_test"])
        with open(doc_file, "w", encoding="utf-8") as f:
            f.write(f"# Architecture Decision Record\n\n## Task\n{query}\n\n## Selected Pattern\n{decision_slice.pattern_name}\n\n## Rationale\n{report.decision_rationale}\n\n## Trade-offs\n" + "\n".join([f"- **{t.dimension}**: {t.advantage} (Cost: {t.disadvantage})" for t in decision_slice.tradeoffs]))

        console.print(f"[bold green]Solution successfully generated in {out_path}:[/bold green]")
        console.print(f"  - {sol_file.name}\n  - {test_file.name}\n  - {doc_file.name}")

@app.command()
def audit():
    """Audits all patterns in sandbox, re-scores confidence, and marks stale items."""
    repo = HybridRepository()
    if not repo.list_all():
        seed_database(repo)

    sandbox = SandboxRunner()
    scorer = EvidenceScorer()
    detector = StaleDetector(repository=repo, sandbox=sandbox, scorer=scorer)
    results = detector.audit_all_patterns()

    table = Table(title="Pattern Lifecycle Audit & Sandbox Re-testing")
    table.add_column("ID", style="cyan")
    table.add_column("Pattern Name", style="bold")
    table.add_column("Sandbox Test", style="bold")
    table.add_column("Updated Confidence", justify="right")
    table.add_column("Status", style="bold")

    for r in results:
        test_str = "[green]PASSED[/green]" if r["test_passed"] else "[red]FAILED[/red]"
        status_color = "green" if r["status"] == "Active" else "yellow"
        table.add_row(r["id"], r["pattern_name"], test_str, f"{r['new_confidence']:.2f}", f"[{status_color}]{r['status']}[/{status_color}]")

    console.print(table)

@app.command()
def mine(path: str = typer.Argument(..., help="Path to repository or ADR folder to mine")):
    """Mine ADRs and architecture decisions from a local directory or repository."""
    repo = HybridRepository()
    miner = RepositoryMiner(repository=repo)
    results = miner.mine_directory(path)

    console.print(Panel(
        f"[bold]Scanned Path:[/bold] {results['scanned_directory']}\n"
        f"[bold]ADRs Found:[/bold] {results['adr_files_found']}\n"
        f"[bold green]Successfully Mined & Ingested:[/bold green] {results['successfully_mined_count']}\n"
        f"[bold]Mined IDs:[/bold] {', '.join(results['mined_slice_ids']) if results['mined_slice_ids'] else 'None'}",
        title="Repository ADR Mining Results",
        border_style="green"
    ))

@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host address to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port number for web server")
):
    """Launch the FastAPI interactive web dashboard and Evidence Graph visualizer."""
    import uvicorn
    console.print(f"[bold green]Starting Web UI at http://{host}:{port}[/bold green]")
    uvicorn.run("web.app:app", host=host, port=port, reload=False)

if __name__ == "__main__":
    app()
