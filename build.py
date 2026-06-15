from __future__ import annotations

import subprocess
import sys
from shutil import which
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TOOLS = ROOT / "tools"
SITE = ROOT / "site"


def run_step(title: str, command: list[str], cwd: Path | None = None) -> None:
    print(f"[build] {title}")
    executable = command[0].lower()
    if sys.platform.startswith("win") and executable in {"npm", "npx"}:
        subprocess.run(
            subprocess.list2cmdline(command),
            cwd=str(cwd or ROOT),
            check=True,
            shell=True,
        )
        return
    subprocess.run(command, cwd=str(cwd or ROOT), check=True)


def ensure_site_dependencies() -> None:
    node_modules = SITE / "node_modules"
    if node_modules.exists():
        return
    run_step("install site dependencies", ["npm", "install"], cwd=SITE)


def main() -> None:
    run_step("export wiki data", [sys.executable, str(TOOLS / "build_wiki_export.py")])
    run_step("generate site payload", [sys.executable, str(TOOLS / "build_site_payload.py")])
    ensure_site_dependencies()
    run_step("build frontend", ["npm", "run", "build"], cwd=SITE)
    print("[build] complete")


if __name__ == "__main__":
    main()
