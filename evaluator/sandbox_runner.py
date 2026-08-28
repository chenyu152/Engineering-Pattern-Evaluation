import sys
import tempfile
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any
from core.schema import ReferenceCodeSlice
from config.settings import settings

logger = logging.getLogger(__name__)

class SandboxRunner:
    """
    Subprocess & Container sandbox runner that compiles and executes reference code slices
    and their test suites (Voyager executable verification loop).
    """
    def __init__(self, work_dir: Path = settings.SANDBOX_WORK_DIR, timeout: int = settings.SANDBOX_TIMEOUT_SECONDS):
        self.work_dir = work_dir
        self.timeout = timeout
        self.work_dir.mkdir(parents=True, exist_ok=True)

    def run_code_slice_test(self, code_slice: ReferenceCodeSlice) -> Dict[str, Any]:
        """
        Executes code slice + test code in an isolated temporary directory using pytest.
        """
        with tempfile.TemporaryDirectory(dir=str(self.work_dir)) as tmp_dir:
            tmp_path = Path(tmp_dir)
            impl_file = tmp_path / "solution.py"
            test_file = tmp_path / "test_solution.py"

            # Write solution code
            with open(impl_file, "w", encoding="utf-8") as f:
                f.write(code_slice.code_content)

            # Write test code with import hook
            test_wrapper = (
                "import sys\n"
                f"sys.path.insert(0, r'{str(tmp_path)}')\n"
                "from solution import *\n\n"
                + code_slice.test_code
            )
            with open(test_file, "w", encoding="utf-8") as f:
                f.write(test_wrapper)

            try:
                cmd = [sys.executable, "-m", "pytest", str(test_file), "-q", "--no-header"]
                result = subprocess.run(
                    cmd,
                    cwd=str(tmp_path),
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
                success = (result.returncode == 0)
                combined_output = f"{result.stdout}\n{result.stderr}".strip()
                return {
                    "success": success,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "error": None if success else combined_output
                }
            except subprocess.TimeoutExpired:
                logger.error(f"Sandbox execution timed out after {self.timeout}s.")
                return {
                    "success": False,
                    "returncode": -1,
                    "stdout": "",
                    "stderr": f"Execution timed out after {self.timeout}s",
                    "error": f"Execution timed out after {self.timeout}s"
                }
            except Exception as e:
                logger.error(f"Sandbox execution failed with exception: {e}")
                return {
                    "success": False,
                    "returncode": -1,
                    "stdout": "",
                    "stderr": str(e),
                    "error": str(e)
                }
