"""TaskBar Hero IL2CPP dump automation.

Usage:
    python tools/dump_game.py                 # auto-detect paths, run dump
    python tools/dump_game.py --dry-run       # show what would happen
    python tools/dump_game.py --game-dir "X:\\path\\to\\TaskbarHero"
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DUMP_DIR = ROOT / "リソース" / "dump"

# Default search paths for Il2CppDumper
IL2CPP_DUMPER_SEARCH = [
    Path.home() / "Desktop" / "Il2CppDumper-net7-win-v6.7.46" / "Il2CppDumper.exe",
    ROOT / "tools" / "Il2CppDumper" / "Il2CppDumper.exe",
    ROOT / "tools" / "Il2CppDumper.exe",
]

# Default Steam library locations to search for the game
STEAM_SEARCH = [
    Path("E:/SteamLibrary/steamapps/common/TaskbarHero"),
    Path("C:/Program Files (x86)/Steam/steamapps/common/TaskbarHero"),
    Path("D:/SteamLibrary/steamapps/common/TaskbarHero"),
]

GAME_ASSEMBLY = "GameAssembly.dll"
METADATA_REL = Path("TaskBarHero_Data/il2cpp_data/Metadata/global-metadata.dat")

EXPECTED_OUTPUTS = [
    "dump.cs",
    "script.json",
    "il2cpp.h",
    "stringliteral.json",
]


def sha256_file(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def find_il2cpp_dumper(override: str | None = None) -> Path | None:
    """Locate Il2CppDumper executable."""
    if override:
        p = Path(override)
        return p if p.is_file() else None
    for candidate in IL2CPP_DUMPER_SEARCH:
        if candidate.is_file():
            return candidate
    return None


def find_game_dir(override: str | None = None) -> Path | None:
    """Locate the TaskbarHero game directory."""
    if override:
        p = Path(override)
        return p if p.is_dir() else None
    for candidate in STEAM_SEARCH:
        if candidate.is_dir() and (candidate / GAME_ASSEMBLY).is_file():
            return candidate
    return None


def count_classes_methods(dump_cs: Path) -> dict[str, int]:
    """Quick count of classes and methods in dump.cs for diff summary."""
    classes = 0
    methods = 0
    try:
        with open(dump_cs, encoding="utf-8", errors="replace") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("public class ") or stripped.startswith("internal class ") or stripped.startswith("private class "):
                    classes += 1
                elif "// RVA:" in stripped:
                    methods += 1
    except Exception:
        pass
    return {"classes": classes, "methods": methods}


def run_dump(
    dumper_exe: Path,
    game_assembly: Path,
    metadata: Path,
    output_dir: Path,
    dry_run: bool = False,
) -> bool:
    """Execute Il2CppDumper and copy results to the dump directory."""
    # Il2CppDumper outputs files relative to the output directory argument,
    # but some versions have issues with non-ASCII paths. We use a temp dir
    # next to the dumper itself to be safe.
    dumper_dir = dumper_exe.parent
    tmp_out = dumper_dir / "_tbh_dump_tmp"
    if tmp_out.exists():
        shutil.rmtree(tmp_out)
    tmp_out.mkdir(parents=True)

    cmd = [str(dumper_exe), str(game_assembly), str(metadata), str(tmp_out)]
    print(f"[dump] Command: {' '.join(cmd)}")

    if dry_run:
        print("[dump] DRY RUN — skipping execution")
        shutil.rmtree(tmp_out)
        return True

    print("[dump] Running Il2CppDumper...")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=600,
        cwd=str(dumper_dir),
    )

    stdout = result.stdout or ""
    stderr = result.stderr or ""

    # Il2CppDumper v6.7.46 crashes on ReadKey when stdin is redirected,
    # but the dump is already complete at that point. Check for "Done!" in stdout.
    dump_done = "Done!" in stdout and "Dumping..." in stdout

    if not dump_done:
        print(f"[dump] ERROR: Il2CppDumper did not complete successfully")
        print(f"  Exit code: {result.returncode}")
        print(stdout[-2000:] if stdout else "(no stdout)")
        print(stderr[-2000:] if stderr else "(no stderr)")
        if tmp_out.exists():
            shutil.rmtree(tmp_out)
        return False

    if result.returncode != 0:
        print(f"[dump] Note: Il2CppDumper exited with code {result.returncode} (ReadKey crash, harmless)")

    print("[dump] Il2CppDumper completed successfully")

    # Verify expected output files exist
    missing = [name for name in EXPECTED_OUTPUTS if not (tmp_out / name).is_file()]
    if missing:
        print(f"[dump] WARNING: Missing expected files: {missing}")
        # Check if files ended up in dumper dir instead
        for name in missing:
            alt = dumper_dir / name
            if alt.is_file():
                shutil.move(str(alt), str(tmp_out / name))
                print(f"  → Found {name} in dumper directory, moved to output")

    # Also grab DummyDll directory if it exists
    for extra_dir_name in ["DummyDll"]:
        alt_dir = dumper_dir / extra_dir_name
        tmp_dir = tmp_out / extra_dir_name
        if alt_dir.is_dir() and not tmp_dir.is_dir():
            shutil.copytree(str(alt_dir), str(tmp_dir))
            shutil.rmtree(str(alt_dir))

    # Copy results to dump directory
    output_dir.mkdir(parents=True, exist_ok=True)

    for item in tmp_out.iterdir():
        dest = output_dir / item.name
        if item.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(str(item), str(dest))
        else:
            shutil.copy2(str(item), str(dest))
        size_str = f" ({item.stat().st_size:,} bytes)" if item.is_file() else ""
        print(f"  → {item.name}{size_str}")

    shutil.rmtree(tmp_out)
    return True


def build_metadata(
    game_assembly: Path,
    metadata_file: Path,
    dump_dir: Path,
) -> dict[str, Any]:
    """Build metadata JSON about the dump."""
    dump_cs = dump_dir / "dump.cs"
    stats = count_classes_methods(dump_cs) if dump_cs.is_file() else {}

    return {
        "dumped_at": datetime.now(timezone.utc).isoformat(),
        "game_assembly": {
            "path": str(game_assembly),
            "size": game_assembly.stat().st_size,
            "modified": datetime.fromtimestamp(
                game_assembly.stat().st_mtime, tz=timezone.utc
            ).isoformat(),
            "sha256": sha256_file(game_assembly),
        },
        "global_metadata": {
            "path": str(metadata_file),
            "size": metadata_file.stat().st_size,
            "modified": datetime.fromtimestamp(
                metadata_file.stat().st_mtime, tz=timezone.utc
            ).isoformat(),
            "sha256": sha256_file(metadata_file),
        },
        "dump_stats": stats,
        "output_files": [
            {"name": f.name, "size": f.stat().st_size}
            for f in sorted(dump_dir.iterdir())
            if f.is_file() and f.name != "dump_metadata.json"
        ],
    }


def show_diff(old_meta_path: Path, new_meta: dict[str, Any]) -> None:
    """Show a brief diff between old and new dump."""
    if not old_meta_path.is_file():
        print("[dump] No previous metadata — skipping diff")
        return

    try:
        old = json.loads(old_meta_path.read_text(encoding="utf-8"))
    except Exception:
        return

    old_stats = old.get("dump_stats", {})
    new_stats = new_meta.get("dump_stats", {})

    print("\n[dump] === Diff Summary ===")
    for key in ("classes", "methods"):
        old_v = old_stats.get(key, 0)
        new_v = new_stats.get(key, 0)
        delta = new_v - old_v
        sign = "+" if delta > 0 else ""
        print(f"  {key}: {old_v} → {new_v} ({sign}{delta})")

    old_ga_hash = old.get("game_assembly", {}).get("sha256", "")
    new_ga_hash = new_meta.get("game_assembly", {}).get("sha256", "")
    if old_ga_hash == new_ga_hash:
        print("  GameAssembly.dll: unchanged")
    else:
        print("  GameAssembly.dll: CHANGED")

    old_time = old.get("dumped_at", "unknown")
    print(f"  Previous dump: {old_time}")
    print(f"  Current dump:  {new_meta['dumped_at']}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Automate IL2CPP dump for TaskBar Hero."
    )
    parser.add_argument(
        "--game-dir",
        help="Path to the TaskbarHero game directory",
    )
    parser.add_argument(
        "--dumper",
        help="Path to Il2CppDumper.exe",
    )
    parser.add_argument(
        "--output",
        default=str(DUMP_DIR),
        help="Output directory for dump files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing",
    )
    args = parser.parse_args()

    # Resolve paths
    dumper = find_il2cpp_dumper(args.dumper)
    if not dumper:
        print("[dump] ERROR: Could not find Il2CppDumper.exe")
        print("  Searched:")
        for p in IL2CPP_DUMPER_SEARCH:
            print(f"    {p}")
        print("  Use --dumper to specify the path.")
        sys.exit(1)
    print(f"[dump] Il2CppDumper: {dumper}")

    game_dir = find_game_dir(args.game_dir)
    if not game_dir:
        print("[dump] ERROR: Could not find TaskbarHero game directory")
        print("  Searched:")
        for p in STEAM_SEARCH:
            print(f"    {p}")
        print("  Use --game-dir to specify the path.")
        sys.exit(1)

    game_assembly = game_dir / GAME_ASSEMBLY
    metadata_file = game_dir / METADATA_REL
    output_dir = Path(args.output)
    meta_path = output_dir / "dump_metadata.json"

    print(f"[dump] Game directory: {game_dir}")
    print(f"[dump] GameAssembly.dll: {game_assembly} ({game_assembly.stat().st_size:,} bytes)")
    print(f"[dump] global-metadata.dat: {metadata_file} ({metadata_file.stat().st_size:,} bytes)")
    print(f"[dump] Output: {output_dir}")

    if not game_assembly.is_file():
        print(f"[dump] ERROR: {game_assembly} not found")
        sys.exit(1)
    if not metadata_file.is_file():
        print(f"[dump] ERROR: {metadata_file} not found")
        sys.exit(1)

    # Save old metadata for diff
    old_meta_path = meta_path if meta_path.is_file() else None

    if args.dry_run:
        print("\n[dump] DRY RUN — would execute dump with above parameters")
        return

    # Execute dump
    success = run_dump(dumper, game_assembly, metadata_file, output_dir)
    if not success:
        sys.exit(1)

    # Build and save metadata
    meta = build_metadata(game_assembly, metadata_file, output_dir)
    meta_path.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\n[dump] Metadata saved to {meta_path}")

    # Show diff
    if old_meta_path:
        show_diff(output_dir.parent / "dump_backup_20260609" / "dump_metadata.json", meta)

    show_diff(meta_path, meta)

    print("\n[dump] Done! Next steps:")
    print("  python build.py        # regenerate wiki data + frontend")


if __name__ == "__main__":
    main()
