import time
import threading
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from storage.hybrid_repository import HybridRepository
from evaluator.sandbox_runner import SandboxRunner
from evaluator.evidence_scorer import EvidenceScorer
from .dependency_checker import DependencyChecker
from .auto_healer import AutoHealer

logger = logging.getLogger(__name__)

class WatchdogDaemon:
    """
    Continuous Background Daemon for Engineering Pattern Lifecycle Management:
    - Runs periodic health audits and sandbox re-benchmarking in a background worker thread.
    - Monitors dependency version drifts.
    - Maintains real-time status and execution history for Web UI and API consumption.
    """
    def __init__(
        self,
        repository: Optional[HybridRepository] = None,
        check_interval_seconds: int = 3600  # Default: runs every hour (or configurable)
    ):
        self.repository = repository or HybridRepository()
        self.sandbox = SandboxRunner()
        self.scorer = EvidenceScorer()
        self.dep_checker = DependencyChecker()
        self.auto_healer = AutoHealer(self.repository, self.sandbox, self.scorer, self.dep_checker)
        
        self.check_interval = check_interval_seconds
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        self.last_run_time: Optional[str] = None
        self.next_run_time: Optional[str] = None
        self.total_runs_completed: int = 0
        self.recent_events: List[Dict[str, Any]] = []

    def start(self):
        """Starts the watchdog daemon background loop."""
        if self.is_running:
            logger.warning("Watchdog daemon is already running.")
            return

        self.is_running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="EngineeringWatchdogDaemon")
        self._thread.start()
        logger.info(f"Watchdog Daemon started with interval {self.check_interval}s.")

    def stop(self):
        """Stops the watchdog daemon."""
        if not self.is_running:
            return
        self.is_running = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("Watchdog Daemon stopped.")

    def run_cycle_now(self) -> List[Dict[str, Any]]:
        """Manually triggers an immediate lifecycle healing and benchmark cycle."""
        logger.info("Executing immediate watchdog inspection cycle...")
        start_t = time.time()
        results = self.auto_healer.heal_all()
        elapsed = time.time() - start_t
        
        self.last_run_time = datetime.now(timezone.utc).isoformat()
        self.total_runs_completed += 1
        
        event_summary = {
            "timestamp": self.last_run_time,
            "run_number": self.total_runs_completed,
            "duration_sec": round(elapsed, 2),
            "patterns_audited": len(results),
            "stale_count": sum(1 for r in results if r["new_status"] == "Stale"),
            "active_count": sum(1 for r in results if r["new_status"] == "Active"),
            "details": results
        }
        self.recent_events.insert(0, event_summary)
        if len(self.recent_events) > 50:
            self.recent_events.pop()

        return results

    def _run_loop(self):
        while not self._stop_event.is_set():
            try:
                self.run_cycle_now()
            except Exception as e:
                logger.error(f"Error in watchdog cycle: {e}")

            # Sleep in small slices to respond promptly to stop_event
            sleep_chunks = self.check_interval
            for _ in range(sleep_chunks):
                if self._stop_event.is_set():
                    break
                time.sleep(1.0)

    def get_status(self) -> Dict[str, Any]:
        return {
            "daemon_running": self.is_running,
            "check_interval_seconds": self.check_interval,
            "last_run_time": self.last_run_time,
            "total_runs_completed": self.total_runs_completed,
            "recent_events_count": len(self.recent_events),
            "latest_event": self.recent_events[0] if self.recent_events else None
        }
