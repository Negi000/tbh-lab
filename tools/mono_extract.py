from __future__ import annotations

import argparse
import json
import re
import struct
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_OUT = ROOT / "output" / "wiki" / "data"

SHORT_LOCALE_ALIASES = {
    "en-US": "en",
    "ja-JP": "ja",
}

TABLE_RE = re.compile(r"^(StringTable|ItemTable)_(.+)\.dat$")
INV_RE = re.compile(r"^\[Inv\]\s+(\d+)\s+(.+)\.dat$")
STAGE_RE = re.compile(r"^Stage(\d+)_+Act(\d+)_(\d+)\.dat$")
HERO_RE = re.compile(r"^Hero_(\d+)\.dat$")
ITEM_KEY_RE = re.compile(r"^Item(Name|Description)_(\d+)$")

INVENTORY_FIELD_KEYS = {
    "name",
    "description",
    "display_type",
    "type",
    "rarity",
    "parts",
    "class",
    "level",
}


def align4(value: int) -> int:
    return (value + 3) & ~3


def parse_records_at(data: bytes, count_offset: int) -> tuple[list[dict[str, str]], int]:
    count = struct.unpack_from("<I", data, count_offset)[0]
    pos = count_offset + 4
    records: list[dict[str, str]] = []
    for _ in range(count):
        if pos + 12 > len(data):
            raise ValueError("record header exceeds file length")
        record_id = data[pos : pos + 8].hex()
        length = struct.unpack_from("<I", data, pos + 8)[0]
        start = pos + 12
        end = start + length
        if length > 100_000 or end > len(data):
            raise ValueError("record value exceeds file length")
        value = data[start:end].decode("utf-8")
        records.append({"id": record_id, "value": value})
        pos = align4(end) + 4
    return records, pos


def parse_record_table(path: Path, min_count: int = 10) -> list[dict[str, str]]:
    data = path.read_bytes()
    candidates: list[tuple[int, int, int, list[dict[str, str]]]] = []
    scan_limit = min(512, max(0, len(data) - 4))
    for offset in range(scan_limit):
        count = struct.unpack_from("<I", data, offset)[0]
        if not (min_count <= count <= 20_000):
            continue
        try:
            records, end_pos = parse_records_at(data, offset)
        except (UnicodeDecodeError, ValueError, struct.error):
            continue
        if end_pos <= len(data) and records:
            candidates.append((abs(len(data) - end_pos), -count, offset, records))
    if not candidates:
        return []
    candidates.sort(key=lambda item: (item[0], item[1], item[2]))
    return candidates[0][3]


def locale_alias(locale: str) -> str:
    return SHORT_LOCALE_ALIASES.get(locale, locale)


def add_locale_value(target: dict[str, str], locale: str, value: str) -> None:
    target[locale] = value
    target[locale_alias(locale)] = value


def parse_localized_table(mono_dir: Path, prefix: str) -> dict[str, Any]:
    shared_path = mono_dir / f"{prefix} Shared Data.dat"
    if not shared_path.exists():
        return {"source_locales": [], "by_key": {}, "by_id": {}, "record_count": 0}

    shared_records = parse_record_table(shared_path)
    id_to_key = {record["id"]: record["value"] for record in shared_records}
    by_key: dict[str, dict[str, str]] = {key: {} for key in id_to_key.values()}
    by_id: dict[str, dict[str, str]] = {}
    source_locales: list[str] = []

    for path in sorted(mono_dir.glob(f"{prefix}_*.dat")):
        match = TABLE_RE.match(path.name)
        if not match:
            continue
        locale = match.group(2)
        source_locales.append(locale)
        for record in parse_record_table(path):
            record_id = record["id"]
            value = record["value"]
            add_locale_value(by_id.setdefault(record_id, {}), locale, value)
            key = id_to_key.get(record_id)
            if key:
                add_locale_value(by_key.setdefault(key, {}), locale, value)

    return {
        "source_locales": source_locales,
        "record_count": len(id_to_key),
        "by_key": by_key,
        "by_id": by_id,
    }


def printable_ratio(value: str) -> float:
    if not value:
        return 0.0
    printable = sum(1 for char in value if char.isprintable() or char in "\n\r\t")
    return printable / len(value)


def extract_length_prefixed_strings(data: bytes) -> list[tuple[int, str]]:
    strings: list[tuple[int, str]] = []
    for offset in range(0, max(0, len(data) - 4)):
        length = struct.unpack_from("<I", data, offset)[0]
        if not (1 <= length <= 512) or offset + 4 + length > len(data):
            continue
        raw = data[offset + 4 : offset + 4 + length]
        if b"\x00" in raw:
            continue
        try:
            value = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
        if printable_ratio(value) >= 0.9:
            strings.append((offset, value))
    return strings


def parse_inventory_fields(path: Path) -> dict[str, str]:
    strings = extract_length_prefixed_strings(path.read_bytes())
    fields: dict[str, str] = {}
    for index, (_, value) in enumerate(strings):
        if value not in INVENTORY_FIELD_KEYS or index + 1 >= len(strings):
            continue
        next_value = strings[index + 1][1]
        if next_value not in INVENTORY_FIELD_KEYS and len(next_value) <= 256:
            fields[value] = next_value
    return fields


def parse_mono_assets(mono_dir: Path) -> dict[str, Any]:
    inventory_names: dict[int, str] = {}
    inventory_fields: dict[int, dict[str, str]] = {}
    stage_assets: dict[int, dict[str, Any]] = {}
    heroes: dict[int, str] = {}
    dlc: list[str] = []

    if not mono_dir.exists():
        return {
            "inventory_names": inventory_names,
            "inventory_fields": inventory_fields,
            "stage_assets": stage_assets,
            "hero_assets": heroes,
            "dlc_assets": dlc,
        }

    for path in sorted(mono_dir.glob("*.dat")):
        name = path.name
        inv_match = INV_RE.match(name)
        if inv_match:
            item_key = int(inv_match.group(1))
            inventory_names[item_key] = inv_match.group(2)
            inventory_fields[item_key] = parse_inventory_fields(path)
            continue
        stage_match = STAGE_RE.match(name)
        if stage_match:
            stage_assets[int(stage_match.group(1))] = {
                "file": name,
                "act": int(stage_match.group(2)),
                "stage_no": int(stage_match.group(3)),
            }
            continue
        hero_match = HERO_RE.match(name)
        if hero_match:
            heroes[int(hero_match.group(1))] = name
            continue
        if name.startswith("[DLC]"):
            dlc.append(name)

    return {
        "inventory_names": inventory_names,
        "inventory_fields": inventory_fields,
        "stage_assets": stage_assets,
        "hero_assets": heroes,
        "dlc_assets": sorted(dlc),
    }


def build_item_localization(item_table: dict[str, Any]) -> dict[int, dict[str, dict[str, str]]]:
    by_item_key: dict[int, dict[str, dict[str, str]]] = {}
    for key, localized_values in item_table.get("by_key", {}).items():
        match = ITEM_KEY_RE.match(key)
        if not match:
            continue
        field = "name" if match.group(1) == "Name" else "description"
        item_key = int(match.group(2))
        by_item_key.setdefault(item_key, {})[field] = localized_values
    return by_item_key


def extract_mono_info(mono_dir: Path) -> dict[str, Any]:
    assets = parse_mono_assets(mono_dir)
    string_table = parse_localized_table(mono_dir, "StringTable")
    item_table = parse_localized_table(mono_dir, "ItemTable")
    assets.update(
        {
            "string_table": string_table,
            "item_table": item_table,
            "item_localization": build_item_localization(item_table),
            "supported_locales": sorted(set(string_table.get("source_locales", [])) | set(item_table.get("source_locales", []))),
        }
    )
    return assets


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract Task Bar Hero Mono localization and asset metadata.")
    parser.add_argument("mono_dir", nargs="?", default=str(ROOT / "リソース" / "Mono"))
    parser.add_argument("--out", default=str(DATA_OUT / "mono_assets.json"))
    args = parser.parse_args()

    mono_info = extract_mono_info(Path(args.mono_dir))
    write_json(Path(args.out), mono_info)
    print(
        "Extracted Mono data: "
        f"inventory={len(mono_info['inventory_names'])} "
        f"strings={mono_info['string_table']['record_count']} "
        f"items={mono_info['item_table']['record_count']} "
        f"locales={len(mono_info['supported_locales'])}"
    )


if __name__ == "__main__":
    main()
