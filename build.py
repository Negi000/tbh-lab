from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TOOLS = ROOT / "tools"
SITE = ROOT / "site"
DUMP_DIR = ROOT / "リソース" / "dump"
DUMP_META = DUMP_DIR / "dump_metadata.json"

# Default game paths for freshness check
STEAM_GAME_DIRS = [
    Path("E:/SteamLibrary/steamapps/common/TaskbarHero"),
    Path("C:/Program Files (x86)/Steam/steamapps/common/TaskbarHero"),
    Path("D:/SteamLibrary/steamapps/common/TaskbarHero"),
]


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


def check_dump_freshness() -> bool:
    """Check if the dump is outdated compared to the game files.
    Returns True if the dump is fresh, False if stale or missing."""
    if not DUMP_META.is_file():
        print("[build] WARNING: No dump metadata found. Run 'python tools/dump_game.py' first.")
        return False

    try:
        meta = json.loads(DUMP_META.read_text(encoding="utf-8"))
    except Exception:
        print("[build] WARNING: Could not read dump metadata.")
        return False

    # Find game directory
    game_dir = None
    for candidate in STEAM_GAME_DIRS:
        ga = candidate / "GameAssembly.dll"
        if ga.is_file():
            game_dir = candidate
            break

    if not game_dir:
        return True  # Can't check, assume OK

    ga_path = game_dir / "GameAssembly.dll"
    ga_mtime = ga_path.stat().st_mtime
    dump_ga_modified = meta.get("game_assembly", {}).get("modified", "")

    if dump_ga_modified:
        from datetime import datetime, timezone
        try:
            dump_time = datetime.fromisoformat(dump_ga_modified)
            game_time = datetime.fromtimestamp(ga_mtime, tz=timezone.utc)
            if game_time > dump_time:
                print(f"[build] ⚠️  WARNING: GameAssembly.dll has been updated since last dump!")
                print(f"         Game file:  {game_time.isoformat()}")
                print(f"         Last dump:  {dump_time.isoformat()}")
                print(f"         Run 'python tools/dump_game.py' to update the dump.")
                return False
        except Exception:
            pass

    return True


def ensure_site_dependencies() -> None:
    node_modules = SITE / "node_modules"
    if node_modules.exists():
        return
    run_step("install site dependencies", ["npm", "install"], cwd=SITE)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build TBH Lab wiki and frontend.")
    parser.add_argument(
        "--force-dump",
        action="store_true",
        help="Run dump_game.py before building to refresh IL2CPP dump.",
    )
    parser.add_argument(
        "--skip-dump-check",
        action="store_true",
        help="Skip the dump freshness check.",
    )
    args = parser.parse_args()

    # Optionally run dump first
    if args.force_dump:
        run_step("refresh IL2CPP dump", [sys.executable, str(TOOLS / "dump_game.py")])

    # Check dump freshness
    if not args.skip_dump_check:
        check_dump_freshness()

    run_step("export wiki data", [sys.executable, str(TOOLS / "build_wiki_export.py")])
    run_step("generate site payload", [sys.executable, str(TOOLS / "build_site_payload.py")])
    ensure_site_dependencies()
    run_step("build frontend", ["npm", "run", "build"], cwd=SITE)
    print("[build] [OK] complete")


if __name__ == "__main__":
    main()
