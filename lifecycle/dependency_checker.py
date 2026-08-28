import re
import logging
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class DependencyChecker:
    """
    Monitors pattern dependencies on PyPI / upstream package registries.
    Detects major version bumps on pinned dependencies, deprecations, and potential breaking changes.
    """
    def __init__(self, timeout_sec: int = 5):
        self.timeout = timeout_sec
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get_latest_pypi_version(self, package_name: str) -> Optional[str]:
        pkg_clean = re.split(r"[><=~]", package_name)[0].strip()
        if not pkg_clean:
            return None

        if pkg_clean in self._cache:
            return self._cache[pkg_clean].get("latest_version")

        try:
            url = f"https://pypi.org/pypi/{pkg_clean}/json"
            resp = requests.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                latest = data.get("info", {}).get("version")
                self._cache[pkg_clean] = {"latest_version": latest, "checked_at": datetime.now(timezone.utc).isoformat()}
                return latest
        except Exception as e:
            logger.warning(f"Failed to check PyPI for {pkg_clean}: {e}")

        return None

    def check_pattern_dependencies(self, dependencies: List[str]) -> List[Dict[str, Any]]:
        """
        Analyzes a list of declared dependencies for potential staleness.
        Only flags stale if pinned to an older major version (e.g. ==4.0, <5.0, ~=4.0).
        Open lower bounds (>=5.0) are considered compatible with newer releases.
        """
        results = []
        for dep in dependencies:
            pkg_name = re.split(r"[><=~]", dep)[0].strip()
            specified_op_version = dep[len(pkg_name):].strip()
            
            latest_version = self.get_latest_pypi_version(pkg_name)
            is_stale = False
            warning = None

            if latest_version and specified_op_version:
                # Check for pinned major version restrictions like '==4.x', '<5.0', '~=4.0'
                if specified_op_version.startswith(("==", "<", "~=")):
                    spec_major = re.search(r"\d+", specified_op_version)
                    latest_major = re.search(r"\d+", latest_version)
                    if spec_major and latest_major and int(latest_major.group(0)) > int(spec_major.group(0)):
                        is_stale = True
                        warning = f"Pinned to legacy major version (Specified: {specified_op_version}, Latest: {latest_version})"

            results.append({
                "package": pkg_name,
                "specified": dep,
                "latest": latest_version or "unknown",
                "is_stale": is_stale,
                "warning": warning
            })
        return results
