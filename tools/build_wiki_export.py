from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mono_extract import extract_mono_info


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "wiki"
DATA_OUT = OUT / "data"
PAGES_OUT = OUT / "pages"

SKIP_TEXT_FILES = {
    "LineBreaking Following Characters.txt",
    "LineBreaking Leading Characters.txt",
    "nv-constant-template.txt",
    "nv-emphasis-template.txt",
    "nv-pattern-template.txt",
    "PerformanceTestRunInfo.txt",
    "PerformanceTestRunSettings.txt",
    "Steamworks.NET.txt",
}

CURATED_RELATIONSHIPS = [
    {
        "from": "HeroInfoData.SkillKey",
        "to": "SkillInfoData.SkillKey",
        "note": "Hero base attack skill.",
    },
    {
        "from": "HeroInfoData.SelectSoundKey, HeroInfoData.DeadSoundKey",
        "to": "SoundInfoData.SoundKey",
        "note": "Hero UI/death sound assets.",
    },
    {
        "from": "SkillInfoData.SkillLevelKey",
        "to": "SkillLevelInfoData.SkillLevelKey",
        "note": "Per-level skill value table. Most active skills have 10 levels.",
    },
    {
        "from": "SkillInfoData.BuffGroupKey",
        "to": "BuffGroupInfoData.BuffGroupKey -> BuffInfoData.BuffKey",
        "note": "Only SkillBuffType=Buff rows use this.",
    },
    {
        "from": "SkillInfoData.AttributeKey",
        "to": "AttributeInfoData.AttributeKey",
        "note": "Unlock/attribute node attached to the skill.",
    },
    {
        "from": "AttributeInfoData.Value",
        "to": "PassiveSkillInfoData.PassiveSkillKey or SkillInfoData.SkillKey",
        "note": "Polymorphic by ATTRIBUTETYPE. PASSIVESKILL rows resolve to passive skills, ACTIVESKILL rows resolve to active skills.",
    },
    {
        "from": "StageInfoData.Monsters",
        "to": "MonsterInfoData.MonsterKey",
        "note": "Space-separated monsterKey_weight pairs.",
    },
    {
        "from": "StageInfoData.BossMonsterKey",
        "to": "MonsterInfoData.MonsterKey",
        "note": "Boss row for NORMAL/ACTBOSS stage data.",
    },
    {
        "from": "StageInfoData.MonsterDropItemKey, StageInfoData.BossDropItemKey",
        "to": "ItemInfoData.ItemKey",
        "note": "Box item granted by stage monsters or boss.",
    },
    {
        "from": "StageInfoData.FirstClearDropKey",
        "to": "DropInfoData.DropKey",
        "note": "First-clear reward drop table.",
    },
    {
        "from": "DropInfoData.RewardKey",
        "to": "ItemInfoData.ItemKey / ItemGroupInfoData.ItemGroupKey / MonsterInfoData.MonsterKey",
        "note": "Resolved by REWARDTYPE.",
    },
    {
        "from": "ItemInfoData.GearKey",
        "to": "GearInfoData.GearKey",
        "note": "Gear rows usually use ItemKey == GearKey.",
    },
    {
        "from": "ItemInfoData.DropKey",
        "to": "DropInfoData.DropKey",
        "note": "Openable chest/material generator contents.",
    },
    {
        "from": "ItemGroupInfoData.ItemKey",
        "to": "ItemInfoData.ItemKey",
        "note": "Drop groups expand to concrete item ids.",
    },
    {
        "from": "GearInfoData.UniqueModKey",
        "to": "UniqueModInfoData.UniqueModKey",
        "note": "Legendary-plus unique/special modifiers and skill-altering affixes.",
    },
    {
        "from": "MaterialInfoData.StatModGroupKey",
        "to": "StatModGroupInfoData.StatModGroupKey -> StatModInfoData.StatModKey",
        "note": "Material-driven decoration/engraving/inscription stat pools.",
    },
    {
        "from": "SynthesisDropInfoData.DropKey, CraftingRecipeInfoData.DropKey, CubeSubRecipeInfoData.DropKey",
        "to": "DropInfoData.DropKey",
        "note": "Recipes use drop tables for results.",
    },
    {
        "from": "RuneInfoData.LevelDataKey",
        "to": "RuneLevelInfoData.LevelKey",
        "note": "Rune level rows share LevelKey with RuneKey/LevelDataKey.",
    },
    {
        "from": "PetInfoData.StatDataKey",
        "to": "PetStatInfoData.PetStatKey",
        "note": "Pet stat bonus lookup.",
    },
]


def configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def find_resource_dir() -> Path:
    for child in ROOT.iterdir():
        if child.is_dir() and (child / "text").exists() and (child / "dump").exists():
            return child
    raise FileNotFoundError("Could not find resource directory with text/ and dump/.")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_tables(text_dir: Path) -> dict[str, list[dict[str, str]]]:
    tables: dict[str, list[dict[str, str]]] = {}
    for path in sorted(text_dir.glob("*.txt")):
        if path.name in SKIP_TEXT_FILES:
            continue
        rows = read_csv(path)
        if rows:
            tables[path.stem] = rows
    return tables


def blank_to_none(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        return value if value != "" else None
    return value


def int_or_none(value: Any) -> int | None:
    value = blank_to_none(value)
    if value is None:
        return None
    try:
        return int(str(value))
    except ValueError:
        return None


def float_or_none(value: Any) -> float | None:
    value = blank_to_none(value)
    if value is None:
        return None
    try:
        return float(str(value))
    except ValueError:
        return None


def bool_or_none(value: Any) -> bool | None:
    value = blank_to_none(value)
    if value is None:
        return None
    text = str(value).strip().lower()
    if text == "true":
        return True
    if text == "false":
        return False
    return None


def infer_scalar(value: str) -> Any:
    stripped = blank_to_none(value)
    if stripped is None:
        return None
    bool_value = bool_or_none(stripped)
    if bool_value is not None:
        return bool_value
    int_value = int_or_none(stripped)
    if int_value is not None:
        return int_value
    float_value = float_or_none(stripped)
    if float_value is not None:
        return float_value
    return stripped


def normalized_row(row: dict[str, str]) -> dict[str, Any]:
    return {key: infer_scalar(value) for key, value in row.items()}


def as_index(rows: list[dict[str, str]], key: str) -> dict[int, dict[str, str]]:
    indexed: dict[int, dict[str, str]] = {}
    for row in rows:
        row_key = int_or_none(row.get(key))
        if row_key is not None:
            indexed[row_key] = row
    return indexed


def group_by(rows: list[dict[str, str]], key: str) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row.get(key, "")].append(row)
    return dict(grouped)


def parse_int_list(value: str | None) -> list[int]:
    if not value:
        return []
    output: list[int] = []
    for part in re.split(r"[\s;]+", value.strip()):
        if not part:
            continue
        if part.lstrip("-").isdigit():
            output.append(int(part))
    return output


def parse_key_weight_pairs(value: str | None) -> list[dict[str, int]]:
    if not value:
        return []
    parsed: list[dict[str, int]] = []
    for part in value.split():
        if "_" not in part:
            continue
        key, weight = part.split("_", 1)
        if key.isdigit() and weight.isdigit():
            parsed.append({"key": int(key), "weight": int(weight)})
    return parsed


def pct(part: int | float, total: int | float) -> float | None:
    if not total:
        return None
    return round(float(part) * 100.0 / float(total), 6)


def localized_pair(values: dict[str, str] | None, fallback: Any = None) -> dict[str, str]:
    fallback_text = str(fallback) if fallback not in (None, "") else ""
    values = values or {}
    en = values.get("en") or values.get("en-US") or fallback_text
    ja = values.get("ja") or values.get("ja-JP") or en or fallback_text
    return {"en": en, "ja": ja}


def localized_string_key(mono_info: dict[str, Any], key: Any, fallback: Any = None) -> dict[str, str]:
    if key in (None, ""):
        return localized_pair(None, fallback)
    values = mono_info.get("string_table", {}).get("by_key", {}).get(str(key), {})
    return localized_pair(values, fallback)


def localized_item_table_key(mono_info: dict[str, Any], table_key: Any, fallback: Any = None) -> dict[str, str]:
    if table_key in (None, ""):
        return localized_pair(None, fallback)
    values = mono_info.get("item_table", {}).get("by_key", {}).get(str(table_key), {})
    return localized_pair(values, fallback)


def localized_item_field(mono_info: dict[str, Any], item_key: int | None, field: str, fallback: Any = None) -> dict[str, str]:
    if item_key is None:
        return localized_pair(None, fallback)
    item_localization = mono_info.get("item_localization", {})
    values = (
        item_localization.get(item_key, {}).get(field)
        or item_localization.get(str(item_key), {}).get(field)
        or {}
    )
    return localized_pair(values, fallback)


def fallback_material_name(mono_info: dict[str, Any], grade: Any, material_type: Any) -> dict[str, str]:
    grade_name = localized_string_key(mono_info, f"Grade_{grade}", grade)
    material_labels = {
        "CRAFTING": {"en": "Crafting Material", "ja": "クラフト素材"},
        "DECORATION": {"en": "Decoration Material", "ja": "装飾素材"},
        "ENGRAVING": {"en": "Engraving Material", "ja": "刻印素材"},
        "INSCRIPTION": {"en": "Inscription Material", "ja": "刻文素材"},
        "OFFERING": {"en": "Offering Material", "ja": "奉納素材"},
        "SOULSTONE": {"en": "Soulstone", "ja": "ソウルストーン"},
    }
    material_name = material_labels.get(str(material_type), {"en": str(material_type or "Material"), "ja": str(material_type or "素材")})
    return {
        "en": f"{grade_name['en']} {material_name['en']}".strip(),
        "ja": f"{grade_name['ja']} {material_name['ja']}".strip(),
    }


def fallback_stage_box_name(mono_info: dict[str, Any], name_key: Any) -> dict[str, str] | None:
    text = str(name_key or "")
    if text.startswith("Normal Monster Box"):
        base = localized_string_key(mono_info, "TreasureChest_Normal", "Common Treasure Chest")
    elif text.startswith("Stage Boss Box"):
        base = localized_string_key(mono_info, "TreasureChest_StageBoss", "Stage Treasure Chest")
    elif text.startswith("Act Boss Box"):
        base = localized_string_key(mono_info, "TreasureChest_ActBoss", "Act Boss Treasure Chest")
    else:
        return None
    suffix = ""
    match = re.search(r"(Lv\d+|\d+)$", text)
    if match:
        suffix = f" {match.group(1)}"
    return {"en": f"{base['en']}{suffix}", "ja": f"{base['ja']}{suffix}"}


def inventory_name_lookup(mono_info_or_names: dict[Any, Any] | None) -> dict[int, str]:
    if not mono_info_or_names:
        return {}
    if "inventory_names" in mono_info_or_names:
        return mono_info_or_names.get("inventory_names", {})
    return mono_info_or_names  # type: ignore[return-value]


def display_item(row: dict[str, str] | None, mono_names: dict[Any, Any] | None = None) -> str | None:
    if not row:
        return None
    key = int_or_none(row.get("ItemKey"))
    if mono_names and "item_table" in mono_names:
        localized_name = localized_item_table_key(mono_names, row.get("NameKey"))
        if localized_name["en"]:
            return localized_name["en"]
    if mono_names and "item_localization" in mono_names and key is not None:
        localized_name = localized_item_field(mono_names, key, "name")
        if localized_name["en"]:
            return localized_name["en"]
    inventory_names = inventory_name_lookup(mono_names)
    if inventory_names and key in inventory_names:
        return inventory_names[key]
    for column in ("NameKey", "GroupName"):
        value = blank_to_none(row.get(column))
        if value:
            return str(value)
    return str(key) if key is not None else None


def display_monster(row: dict[str, str] | None) -> str | None:
    if not row:
        return None
    path = blank_to_none(row.get("PrefabPath"))
    if path:
        return str(path).split("/")[-1]
    key = blank_to_none(row.get("MonsterKey"))
    return f"Monster {key}" if key else None


def display_skill(row: dict[str, str] | None) -> str | None:
    if not row:
        return None
    name = blank_to_none(row.get("SkillNameKey"))
    if name:
        return str(name)
    key = blank_to_none(row.get("SkillKey"))
    return f"Skill {key}" if key else None


def display_stage(row: dict[str, str] | None) -> str | None:
    if not row:
        return None
    act = row.get("Act")
    no = row.get("StageNo")
    diff = row.get("STAGEDIFFICULITY") or row.get("STAGEDIFFICULTY")
    stage_type = row.get("STAGETYPE")
    return f"Act {act}-{no} {diff} {stage_type}".strip()


def parse_mono_names(mono_dir: Path) -> dict[str, Any]:
    return extract_mono_info(mono_dir)


def find_asset_files(resource_dir: Path) -> dict[str, Any]:
    image_dir = resource_dir / "image"
    hero_images: dict[str, list[str]] = defaultdict(list)
    if image_dir.exists():
        for path in sorted((image_dir / "hero").glob("*.png")) if (image_dir / "hero").exists() else []:
            match = re.search(r"ChaAnim_([^_]+)_", path.name)
            if match:
                hero_images[match.group(1)].append(str(path.relative_to(ROOT)))
    return {"hero_images": dict(hero_images)}


def parse_dump_enums(dump_cs: Path) -> dict[str, Any]:
    enums: dict[str, Any] = {}
    current: str | None = None
    brace = 0
    values: list[dict[str, Any]] = []
    line_start = 0
    for line_no, line in enumerate(dump_cs.open("r", encoding="utf-8", errors="ignore"), start=1):
        match = re.match(r"public enum (\w+)\b", line)
        if match:
            current = match.group(1)
            brace = line.count("{") - line.count("}")
            values = []
            line_start = line_no
            continue
        if current:
            brace += line.count("{") - line.count("}")
            const_match = re.search(r"public const \w+\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([^;]+);", line)
            if const_match:
                raw_value = const_match.group(2).strip()
                values.append({"name": const_match.group(1), "value": infer_scalar(raw_value)})
            if brace <= 0 and "}" in line:
                enums[current] = {"line": line_start, "values": values}
                current = None
    return enums


def parse_info_classes(dump_cs: Path) -> dict[str, Any]:
    classes: dict[str, Any] = {}
    current: str | None = None
    for line_no, line in enumerate(dump_cs.open("r", encoding="utf-8", errors="ignore"), start=1):
        class_match = re.match(r"public class (\w+InfoData)\b", line)
        if class_match:
            current = class_match.group(1)
            classes[current] = {"line": line_no, "fields": []}
            continue
        if current:
            if re.match(r"(public|private sealed|internal|protected) class ", line) and current not in line:
                current = None
                continue
            field_match = re.match(r"\s*public\s+([^;{]+?)\s+(\w+);\s*//\s*(0x[0-9A-Fa-f]+)", line)
            if field_match:
                field_type, field_name, offset = field_match.groups()
                classes[current]["fields"].append(
                    {"name": field_name, "type": field_type.strip(), "offset": offset}
                )
    return classes


def parse_data_manager(dump_cs: Path) -> dict[str, Any]:
    in_yq = False
    fields: list[dict[str, str]] = []
    methods: list[dict[str, str]] = []
    for line_no, line in enumerate(dump_cs.open("r", encoding="utf-8", errors="ignore"), start=1):
        if re.match(r"public class yq : nn<yq>", line):
            in_yq = True
            continue
        if in_yq and line.startswith("}"):
            break
        if not in_yq:
            continue
        field_match = re.match(r"\s*(public|private|internal)\s+([^;{]+?)\s+(\w+);\s*//", line)
        if field_match:
            visibility, field_type, field_name = field_match.groups()
            fields.append(
                {
                    "line": line_no,
                    "visibility": visibility,
                    "type": field_type.strip(),
                    "name": field_name,
                }
            )
            continue
        method_match = re.match(r"\s*(public|private|internal)\s+([^;{]+?)\s+(\w+)\(([^)]*)\)\s*\{", line)
        if method_match:
            visibility, return_type, method_name, args = method_match.groups()
            methods.append(
                {
                    "line": line_no,
                    "visibility": visibility,
                    "return_type": return_type.strip(),
                    "name": method_name,
                    "args": args.strip(),
                }
            )
    return {"class": "yq", "fields": fields, "methods": methods}


def infer_column_type(values: list[str]) -> str:
    nonblank = [value for value in values if blank_to_none(value) is not None]
    if not nonblank:
        return "blank"
    if all(bool_or_none(value) is not None for value in nonblank):
        return "bool"
    if all(int_or_none(value) is not None for value in nonblank):
        return "int"
    if all(float_or_none(value) is not None for value in nonblank):
        return "float"
    if all(re.fullmatch(r"[-\d_ ]+", value.strip()) for value in nonblank):
        return "encoded-list"
    return "string"


def build_schema_reference(
    tables: dict[str, list[dict[str, str]]],
    info_classes: dict[str, Any],
    enums: dict[str, Any],
    resource_dir: Path,
) -> dict[str, Any]:
    table_info: dict[str, Any] = {}
    for name, rows in sorted(tables.items()):
        columns = list(rows[0].keys()) if rows else []
        column_info = []
        for column in columns:
            values = [row.get(column, "") for row in rows]
            column_info.append(
                {
                    "name": column,
                    "inferred_type": infer_column_type(values),
                    "non_empty": sum(1 for value in values if blank_to_none(value) is not None),
                    "unique": len({value for value in values if blank_to_none(value) is not None}),
                    "examples": [value for value in values if blank_to_none(value) is not None][:3],
                }
            )
        primary_candidates = []
        if columns:
            first_column = columns[0]
            values = [row.get(first_column, "") for row in rows]
            nonblank = [value for value in values if blank_to_none(value) is not None]
            if nonblank and len(nonblank) == len(rows) and len(set(nonblank)) == len(nonblank):
                if first_column.endswith("Key") or first_column in {
                    "Index",
                    "Level",
                    "StageLevel",
                    "GearType",
                    "GRADE",
                    "ItemType",
                }:
                    primary_candidates.append(first_column)
        table_info[name] = {
            "source_file": str((resource_dir / "text" / f"{name}.txt").relative_to(ROOT)),
            "row_count": len(rows),
            "columns": column_info,
            "primary_key_candidates": primary_candidates,
            "dump_class": info_classes.get(name),
        }
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_root": str(resource_dir.relative_to(ROOT)),
        "table_count": len(table_info),
        "tables": table_info,
        "relationships": CURATED_RELATIONSHIPS,
        "enums": enums,
    }


def export_raw_tables(tables: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    manifest: dict[str, Any] = {}
    tables_dir = DATA_OUT / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)
    for name, rows in sorted(tables.items()):
        normalized = [normalized_row(row) for row in rows]
        path = tables_dir / f"{name}.json"
        write_json(path, normalized)
        manifest[name] = {
            "path": str(path.relative_to(OUT)),
            "row_count": len(rows),
            "columns": list(rows[0].keys()) if rows else [],
        }
    return manifest


def validate_references(tables: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    item_keys = set(as_index(tables.get("ItemInfoData", []), "ItemKey"))
    gear_keys = set(as_index(tables.get("GearInfoData", []), "GearKey"))
    hero_keys = set(as_index(tables.get("HeroInfoData", []), "HeroKey"))
    monster_keys = set(as_index(tables.get("MonsterInfoData", []), "MonsterKey"))
    skill_keys = set(as_index(tables.get("SkillInfoData", []), "SkillKey"))
    skill_level_keys = {int_or_none(row.get("SkillLevelKey")) for row in tables.get("SkillLevelInfoData", [])}
    skill_level_keys.discard(None)
    sound_keys = set(as_index(tables.get("SoundInfoData", []), "SoundKey"))
    drop_keys = {int_or_none(row.get("DropKey")) for row in tables.get("DropInfoData", [])}
    drop_keys.discard(None)
    item_group_keys = {int_or_none(row.get("ItemGroupKey")) for row in tables.get("ItemGroupInfoData", [])}
    item_group_keys.discard(None)
    buff_group_keys = set(as_index(tables.get("BuffGroupInfoData", []), "BuffGroupKey"))
    buff_keys = set(as_index(tables.get("BuffInfoData", []), "BuffKey"))
    attr_keys = set(as_index(tables.get("AttributeInfoData", []), "AttributeKey"))
    passive_keys = set(as_index(tables.get("PassiveSkillInfoData", []), "PassiveSkillKey"))
    unique_mod_keys = set(as_index(tables.get("UniqueModInfoData", []), "UniqueModKey"))
    stat_group_keys = {int_or_none(row.get("StatModGroupKey")) for row in tables.get("StatModGroupInfoData", [])}
    stat_group_keys.discard(None)
    stat_mod_keys = {int_or_none(row.get("StatModKey")) for row in tables.get("StatModInfoData", [])}
    stat_mod_keys.discard(None)
    rune_keys = set(as_index(tables.get("RuneInfoData", []), "RuneKey"))
    rune_level_keys = {int_or_none(row.get("LevelKey")) for row in tables.get("RuneLevelInfoData", [])}
    rune_level_keys.discard(None)
    pet_stat_keys = {int_or_none(row.get("PetStatKey")) for row in tables.get("PetStatInfoData", [])}
    pet_stat_keys.discard(None)

    checks: list[dict[str, Any]] = []

    def add_check(name: str, missing: list[dict[str, Any]], note: str = "") -> None:
        checks.append(
            {
                "name": name,
                "missing_count": len(missing),
                "examples": missing[:20],
                "note": note,
            }
        )

    missing = []
    for row in tables.get("HeroInfoData", []):
        hero = int_or_none(row.get("HeroKey"))
        for column, target in [("SkillKey", skill_keys), ("SelectSoundKey", sound_keys), ("DeadSoundKey", sound_keys)]:
            value = int_or_none(row.get(column))
            if value is not None and value not in target:
                missing.append({"hero": hero, "column": column, "value": value})
    add_check("Hero references", missing)

    missing = []
    for row in tables.get("SkillInfoData", []):
        skill = int_or_none(row.get("SkillKey"))
        for column, target in [
            ("SkillLevelKey", skill_level_keys),
            ("BuffGroupKey", buff_group_keys),
            ("AttributeKey", attr_keys),
            ("SoundKey", sound_keys),
        ]:
            value = int_or_none(row.get(column))
            if value is not None and value not in target:
                missing.append({"skill": skill, "column": column, "value": value})
    add_check("Skill references", missing, "Blank SkillLevelKey/BuffGroupKey is valid for base or non-buff skills.")

    missing = []
    for row in tables.get("AttributeInfoData", []):
        attr = int_or_none(row.get("AttributeKey"))
        hero = int_or_none(row.get("HeroKey"))
        group = int_or_none(row.get("GroupKey"))
        value = int_or_none(row.get("Value"))
        attr_type = row.get("ATTRIBUTETYPE")
        if hero is not None and hero not in hero_keys:
            missing.append({"attribute": attr, "column": "HeroKey", "value": hero})
        if group is not None and group not in set(as_index(tables.get("AttributeGroupInfoData", []), "AttributeGroupKey")):
            missing.append({"attribute": attr, "column": "GroupKey", "value": group})
        if attr_type == "PASSIVESKILL" and value is not None and value not in passive_keys:
            missing.append({"attribute": attr, "column": "Value", "type": attr_type, "value": value})
        if attr_type == "ACTIVESKILL" and value is not None and value not in skill_keys:
            missing.append({"attribute": attr, "column": "Value", "type": attr_type, "value": value})
    add_check("Attribute references", missing)

    missing = []
    for row in tables.get("StageInfoData", []):
        stage = int_or_none(row.get("StageKey"))
        for pair in parse_key_weight_pairs(row.get("Monsters")):
            if pair["key"] not in monster_keys:
                missing.append({"stage": stage, "column": "Monsters", "value": pair["key"]})
        for column, target in [
            ("BossMonsterKey", monster_keys),
            ("MonsterDropItemKey", item_keys),
            ("BossDropItemKey", item_keys),
            ("FirstClearDropKey", drop_keys),
            ("SoulstoneItemKey", item_keys),
            ("BGMSoundKey", sound_keys),
        ]:
            value = int_or_none(row.get(column))
            if value is not None and value not in target:
                missing.append({"stage": stage, "column": column, "value": value})
    add_check("Stage references", missing, "Review remaining examples as possible missing MonsterInfo rows or intentionally unused stage tokens.")

    missing = []
    for row in tables.get("DropInfoData", []):
        drop_key = int_or_none(row.get("DropKey"))
        reward_type = row.get("REWARDTYPE")
        reward_key = int_or_none(row.get("RewardKey"))
        target: set[int]
        if reward_type == "ITEM":
            target = item_keys
        elif reward_type == "ITEMGROUP":
            target = item_group_keys
        elif reward_type == "MONSTER":
            target = monster_keys
        else:
            target = set()
        if reward_key is not None and reward_key not in target:
            missing.append({"drop": drop_key, "reward_type": reward_type, "reward_key": reward_key})
    add_check("Drop reward references", missing)

    missing = []
    for row in tables.get("ItemInfoData", []):
        item = int_or_none(row.get("ItemKey"))
        gear = int_or_none(row.get("GearKey"))
        drop = int_or_none(row.get("DropKey"))
        if gear is not None and gear not in gear_keys:
            missing.append({"item": item, "column": "GearKey", "value": gear})
        if drop is not None and drop not in drop_keys:
            missing.append({"item": item, "column": "DropKey", "value": drop})
    add_check("Item references", missing)

    missing = []
    for row in tables.get("GearInfoData", []):
        gear = int_or_none(row.get("GearKey"))
        unique = int_or_none(row.get("UniqueModKey"))
        if unique is not None and unique != 0 and unique not in unique_mod_keys:
            missing.append({"gear": gear, "column": "UniqueModKey", "value": unique})
    add_check("Gear unique mod references", missing, "UniqueModKey=0 is the enum None sentinel and is treated as valid.")

    missing = []
    for row in tables.get("MaterialInfoData", []):
        item = int_or_none(row.get("ItemKey"))
        group = int_or_none(row.get("StatModGroupKey"))
        if item is not None and item not in item_keys:
            missing.append({"material": item, "column": "ItemKey", "value": item})
        if group is not None and group not in stat_group_keys:
            missing.append({"material": item, "column": "StatModGroupKey", "value": group})
    for row in tables.get("StatModGroupInfoData", []):
        group = int_or_none(row.get("StatModGroupKey"))
        mod = int_or_none(row.get("StatModKey"))
        if mod is not None and mod not in stat_mod_keys:
            missing.append({"stat_group": group, "column": "StatModKey", "value": mod})
    add_check("Material/stat mod references", missing)

    missing = []
    for row in tables.get("RuneInfoData", []):
        rune = int_or_none(row.get("RuneKey"))
        level_data = int_or_none(row.get("LevelDataKey"))
        if level_data is not None and level_data not in rune_level_keys:
            missing.append({"rune": rune, "column": "LevelDataKey", "value": level_data})
        for column in ("NextRuneKey", "PreviewRuneKey"):
            for value in parse_int_list(row.get(column)):
                if value not in rune_keys:
                    missing.append({"rune": rune, "column": column, "value": value})
    add_check("Rune references", missing)

    missing = []
    for row in tables.get("PetInfoData", []):
        pet = int_or_none(row.get("PetKey"))
        stat = int_or_none(row.get("StatDataKey"))
        if stat is not None and stat not in pet_stat_keys:
            missing.append({"pet": pet, "column": "StatDataKey", "value": stat})
    add_check("Pet references", missing)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "missing_total": sum(check["missing_count"] for check in checks),
        "status": "ok" if all(check["missing_count"] == 0 for check in checks) else "review",
    }


def build_drops(
    tables: dict[str, list[dict[str, str]]],
    mono_names: dict[Any, Any],
) -> dict[str, Any]:
    item_by_key = as_index(tables.get("ItemInfoData", []), "ItemKey")
    monster_by_key = as_index(tables.get("MonsterInfoData", []), "MonsterKey")
    item_groups = group_by(tables.get("ItemGroupInfoData", []), "ItemGroupKey")
    drops = group_by(tables.get("DropInfoData", []), "DropKey")
    output: dict[str, Any] = {}

    for drop_key, rows in sorted(drops.items(), key=lambda pair: int_or_none(pair[0]) or 0):
        total_weight = sum(int_or_none(row.get("Weight")) or 0 for row in rows)
        entries = []
        for row in rows:
            reward_type = row.get("REWARDTYPE")
            reward_key = int_or_none(row.get("RewardKey"))
            weight = int_or_none(row.get("Weight")) or 0
            resolved: dict[str, Any] = {}
            if reward_type == "ITEM" and reward_key is not None:
                item = item_by_key.get(reward_key)
                resolved = {
                    "kind": "item",
                    "item_key": reward_key,
                    "name": display_item(item, mono_names),
                    "item_type": item.get("ITEMTYPE") if item else None,
                    "grade": item.get("GRADE") if item else None,
                }
            elif reward_type == "ITEMGROUP" and reward_key is not None:
                group_rows = item_groups.get(str(reward_key), [])
                resolved_items = [
                    {
                        "item_key": int_or_none(group_row.get("ItemKey")),
                        "name": display_item(item_by_key.get(int_or_none(group_row.get("ItemKey")) or -1), mono_names),
                    }
                    for group_row in group_rows[:50]
                ]
                resolved = {
                    "kind": "item_group",
                    "item_group_key": reward_key,
                    "group_name": group_rows[0].get("GroupName") if group_rows else None,
                    "item_count": len(group_rows),
                    "items_preview": resolved_items,
                }
            elif reward_type == "MONSTER" and reward_key is not None:
                monster = monster_by_key.get(reward_key)
                resolved = {
                    "kind": "monster",
                    "monster_key": reward_key,
                    "name": display_monster(monster),
                }
            entries.append(
                {
                    "drop_type": row.get("DropType"),
                    "reward_type": reward_type,
                    "reward_key": reward_key,
                    "hero_key_condition": int_or_none(row.get("HeroKeyCondition")),
                    "weight": weight,
                    "weight_percent": pct(weight, total_weight),
                    "resolved": resolved,
                }
            )
        output[str(drop_key)] = {
            "drop_key": int_or_none(drop_key),
            "entry_count": len(entries),
            "total_weight": total_weight,
            "entries": entries,
        }
    return output


def resolve_drop_summary(drop_key: int | None, drops: dict[str, Any], limit: int = 8) -> dict[str, Any] | None:
    if drop_key is None:
        return None
    group = drops.get(str(drop_key))
    if not group:
        return None
    return {
        "drop_key": drop_key,
        "entry_count": group["entry_count"],
        "total_weight": group["total_weight"],
        "entries_preview": group["entries"][:limit],
    }


def build_heroes(
    tables: dict[str, list[dict[str, str]]],
    drops: dict[str, Any],
    asset_info: dict[str, Any],
    mono_info: dict[str, Any],
) -> list[dict[str, Any]]:
    skills_by_key = as_index(tables.get("SkillInfoData", []), "SkillKey")
    sounds_by_key = as_index(tables.get("SoundInfoData", []), "SoundKey")
    attrs_by_hero = group_by(tables.get("AttributeInfoData", []), "HeroKey")
    passives_by_key = as_index(tables.get("PassiveSkillInfoData", []), "PassiveSkillKey")
    skill_levels = group_by(tables.get("SkillLevelInfoData", []), "SkillLevelKey")
    buff_groups_by_key = as_index(tables.get("BuffGroupInfoData", []), "BuffGroupKey")
    buffs_by_key = as_index(tables.get("BuffInfoData", []), "BuffKey")

    heroes: list[dict[str, Any]] = []
    for row in tables.get("HeroInfoData", []):
        hero_key = int_or_none(row.get("HeroKey"))
        class_type = row.get("ClassType")
        prefix = hero_key // 100 if hero_key else None
        hero_skills = []
        for skill in tables.get("SkillInfoData", []):
            skill_key = int_or_none(skill.get("SkillKey"))
            if prefix is None or skill_key is None:
                continue
            if skill_key // 10000 != prefix:
                continue
            buff_group_key = int_or_none(skill.get("BuffGroupKey"))
            buff_rows: list[dict[str, Any]] = []
            if buff_group_key is not None and buff_group_key in buff_groups_by_key:
                buff_keys = parse_int_list(buff_groups_by_key[buff_group_key].get("BuffKeys"))
                for buff_key in buff_keys:
                    buff = buffs_by_key.get(buff_key)
                    if buff:
                        buff_rows.append(normalized_row(buff))
            hero_skills.append(
                {
                    **normalized_row(skill),
                    "display_name": display_skill(skill),
                    "localized_name": localized_string_key(mono_info, skill.get("SkillNameKey"), display_skill(skill)),
                    "localized_description": localized_string_key(mono_info, skill.get("SkillDescriptionKey")),
                    "sound": normalized_row(sounds_by_key.get(int_or_none(skill.get("SoundKey")) or -1, {})),
                    "levels": [normalized_row(item) for item in skill_levels.get(skill.get("SkillLevelKey", ""), [])],
                    "buffs": buff_rows,
                }
            )

        attributes = []
        for attr in attrs_by_hero.get(str(hero_key), []):
            attr_type = attr.get("ATTRIBUTETYPE")
            value_key = int_or_none(attr.get("Value"))
            resolved: dict[str, Any] | None = None
            if attr_type == "PASSIVESKILL" and value_key is not None:
                passive = passives_by_key.get(value_key)
                resolved = normalized_row(passive) if passive else None
            elif attr_type == "ACTIVESKILL" and value_key is not None:
                skill = skills_by_key.get(value_key)
                resolved = {
                    "skill_key": value_key,
                    "display_name": display_skill(skill),
                    "slot_type": skill.get("SLOTTYPE") if skill else None,
                }
            attributes.append({**normalized_row(attr), "resolved": resolved})

        heroes.append(
            {
                **normalized_row(row),
                "display_name": class_type,
                "localized_name": localized_string_key(mono_info, row.get("HeroNameKey"), class_type),
                "localized_description": localized_string_key(mono_info, row.get("DescriptionKey")),
                "base_stats": {
                    "AttackDamage": int_or_none(row.get("AttackDamage")),
                    "AttackSpeed": int_or_none(row.get("AttackSpeed")),
                    "CastSpeed": int_or_none(row.get("CastSpeed")),
                    "CriticalChance": int_or_none(row.get("CriticalChance")),
                    "CriticalDamage": int_or_none(row.get("CriticalDamage")),
                    "MaxHp": int_or_none(row.get("MaxHp")),
                    "Armor": int_or_none(row.get("Armor")),
                    "CooldownReduction": int_or_none(row.get("CooldownReduction")),
                    "MovementSpeed": int_or_none(row.get("MovementSpeed")),
                },
                "select_sound": normalized_row(sounds_by_key.get(int_or_none(row.get("SelectSoundKey")) or -1, {})),
                "dead_sound": normalized_row(sounds_by_key.get(int_or_none(row.get("DeadSoundKey")) or -1, {})),
                "skills": sorted(hero_skills, key=lambda item: item.get("SkillKey") or 0),
                "attributes": attributes,
                "image_assets": asset_info.get("hero_images", {}).get(class_type, []),
                "dlc_required": bool_or_none(row.get("HasDLCDrop")),
                "drop_unlock_hint": resolve_drop_summary(int_or_none(row.get("DropKey")), drops),
            }
        )
    return heroes


def build_stages(
    tables: dict[str, list[dict[str, str]]],
    drops: dict[str, Any],
    mono_stage_assets: dict[int, dict[str, Any]],
    mono_names: dict[Any, Any],
) -> list[dict[str, Any]]:
    monster_by_key = as_index(tables.get("MonsterInfoData", []), "MonsterKey")
    item_by_key = as_index(tables.get("ItemInfoData", []), "ItemKey")
    sound_by_key = as_index(tables.get("SoundInfoData", []), "SoundKey")
    stage_level_by_level = as_index(tables.get("StageLevelInfoData", []), "StageLevel")
    stages: list[dict[str, Any]] = []

    for row in tables.get("StageInfoData", []):
        stage_key = int_or_none(row.get("StageKey"))
        monsters = []
        for pair in parse_key_weight_pairs(row.get("Monsters")):
            monster = monster_by_key.get(pair["key"])
            monsters.append(
                {
                    "monster_key": pair["key"],
                    "weight": pair["weight"],
                    "display_name": display_monster(monster),
                    "base": normalized_row(monster) if monster else None,
                }
            )
        boss_key = int_or_none(row.get("BossMonsterKey"))
        boss = monster_by_key.get(boss_key or -1)
        monster_drop_key = int_or_none(row.get("MonsterDropItemKey"))
        boss_drop_key = int_or_none(row.get("BossDropItemKey"))
        first_clear_drop_key = int_or_none(row.get("FirstClearDropKey"))
        stages.append(
            {
                **normalized_row(row),
                "display_name": display_stage(row),
                "stage_asset": mono_stage_assets.get(stage_key or -1),
                "stage_level_scaling": normalized_row(stage_level_by_level.get(int_or_none(row.get("StageLevel")) or -1, {})),
                "monsters_resolved": monsters,
                "boss_resolved": {
                    "monster_key": boss_key,
                    "display_name": display_monster(boss),
                    "base": normalized_row(boss) if boss else None,
                }
                if boss_key is not None
                else None,
                "monster_drop_item": {
                    "item_key": monster_drop_key,
                    "name": display_item(item_by_key.get(monster_drop_key or -1), mono_names),
                    "rate": int_or_none(row.get("MonsterDropItemRate")),
                }
                if monster_drop_key is not None
                else None,
                "boss_drop_item": {
                    "item_key": boss_drop_key,
                    "name": display_item(item_by_key.get(boss_drop_key or -1), mono_names),
                    "rate": int_or_none(row.get("BossDropItemRate")),
                }
                if boss_drop_key is not None
                else None,
                "first_clear_drop": resolve_drop_summary(first_clear_drop_key, drops),
                "bgm": normalized_row(sound_by_key.get(int_or_none(row.get("BGMSoundKey")) or -1, {})),
            }
        )
    return sorted(stages, key=lambda item: (item.get("STAGEDIFFICULITY") or "", item.get("Act") or 0, item.get("StageNo") or 0))


def build_items(
    tables: dict[str, list[dict[str, str]]],
    drops: dict[str, Any],
    mono_names: dict[Any, Any],
) -> list[dict[str, Any]]:
    gear_by_key = as_index(tables.get("GearInfoData", []), "GearKey")
    unique_by_key = as_index(tables.get("UniqueModInfoData", []), "UniqueModKey")
    material_by_key = as_index(tables.get("MaterialInfoData", []), "ItemKey")
    stat_groups = group_by(tables.get("StatModGroupInfoData", []), "StatModGroupKey")
    stat_mod_by_key = as_index(tables.get("StatModInfoData", []), "StatModKey")
    groups_by_item = group_by(tables.get("ItemGroupInfoData", []), "ItemKey")
    item_rows = []
    for row in tables.get("ItemInfoData", []):
        item_key = int_or_none(row.get("ItemKey"))
        gear_key = int_or_none(row.get("GearKey"))
        gear = gear_by_key.get(gear_key or -1)
        unique_key = int_or_none(gear.get("UniqueModKey")) if gear else None
        unique = unique_by_key.get(unique_key or -1)
        material = material_by_key.get(item_key or -1)
        stat_group_entries = []
        if material:
            group_key = material.get("StatModGroupKey")
            for group_row in stat_groups.get(group_key, []):
                stat_mod = stat_mod_by_key.get(int_or_none(group_row.get("StatModKey")) or -1)
                stat_group_entries.append(
                    {
                        **normalized_row(group_row),
                        "stat_mod": normalized_row(stat_mod) if stat_mod else None,
                    }
                )
        inventory_names = inventory_name_lookup(mono_names)
        inventory_fields = {}
        if "inventory_fields" in mono_names:
            inventory_fields = (
                mono_names.get("inventory_fields", {}).get(item_key or -1)
                or mono_names.get("inventory_fields", {}).get(str(item_key))
                or {}
            )
        fallback_name = display_item(row, mono_names)
        fallback_description = inventory_fields.get("description") or row.get("DescriptionKey")
        localized_name = localized_item_table_key(mono_names, row.get("NameKey"), fallback_name)
        if not localized_name["en"] or localized_name["en"] == str(row.get("NameKey")):
            localized_name = localized_item_field(mono_names, item_key, "name", fallback_name)
        if localized_name["en"] == str(row.get("NameKey")) and material:
            localized_name = fallback_material_name(mono_names, row.get("GRADE"), material.get("MATERIALTYPE"))
        if row.get("ITEMTYPE") == "STAGEBOX":
            localized_name = fallback_stage_box_name(mono_names, row.get("NameKey")) or localized_name
        localized_description = localized_item_table_key(mono_names, row.get("DescriptionKey"), fallback_description)
        if not localized_description["en"] or localized_description["en"] == str(row.get("DescriptionKey")):
            localized_description = localized_item_field(mono_names, item_key, "description", fallback_description)
        if localized_description["en"] == str(row.get("DescriptionKey")) and material:
            localized_description = {
                "en": f"Used as {localized_name['en'].lower()}.",
                "ja": f"{localized_name['ja']}として使用します。",
            }
        item_rows.append(
            {
                **normalized_row(row),
                "display_name": fallback_name,
                "localized_name": localized_name,
                "localized_description": localized_description,
                "mono_name": inventory_names.get(item_key or -1),
                "mono_fields": inventory_fields,
                "gear": normalized_row(gear) if gear else None,
                "unique_mod": normalized_row(unique) if unique else None,
                "drop_table": resolve_drop_summary(int_or_none(row.get("DropKey")), drops),
                "material": normalized_row(material) if material else None,
                "material_stat_group": stat_group_entries,
                "item_groups": [normalized_row(group) for group in groups_by_item.get(str(item_key), [])],
            }
        )
    return item_rows


def build_recipes(tables: dict[str, list[dict[str, str]]], drops: dict[str, Any]) -> dict[str, Any]:
    def with_drop(row: dict[str, str]) -> dict[str, Any]:
        return {**normalized_row(row), "drop_table": resolve_drop_summary(int_or_none(row.get("DropKey")), drops)}

    return {
        "synthesis_recipes": [normalized_row(row) for row in tables.get("SynthesisRecipeInfoData", [])],
        "synthesis_drops": [with_drop(row) for row in tables.get("SynthesisDropInfoData", [])],
        "crafting_recipes": [with_drop(row) for row in tables.get("CraftingRecipeInfoData", [])],
        "cube_recipes": [normalized_row(row) for row in tables.get("CubeRecipeInfoData", [])],
        "cube_sub_recipes": [with_drop(row) for row in tables.get("CubeSubRecipeInfoData", [])],
        "extraction_costs": [normalized_row(row) for row in tables.get("ExtractionCostInfoData", [])],
    }


def build_growth(tables: dict[str, list[dict[str, str]]], mono_info: dict[str, Any]) -> dict[str, Any]:
    rune_levels = group_by(tables.get("RuneLevelInfoData", []), "LevelKey")
    runes = []
    for row in tables.get("RuneInfoData", []):
        runes.append(
            {
                **normalized_row(row),
                "localized_name": localized_string_key(mono_info, row.get("NameKey"), row.get("NameKey") or row.get("RuneKey")),
                "next_runes": parse_int_list(row.get("NextRuneKey")),
                "preview_runes": parse_int_list(row.get("PreviewRuneKey")),
                "levels": [normalized_row(level) for level in rune_levels.get(row.get("LevelDataKey", ""), [])],
            }
        )
    return {
        "levels": [normalized_row(row) for row in tables.get("LevelInfoData", [])],
        "cube_levels": [normalized_row(row) for row in tables.get("CubeLevelInfoData", [])],
        "offline_rewards": [normalized_row(row) for row in tables.get("OfflineRewardInfoData", [])],
        "attributes": [normalized_row(row) for row in tables.get("AttributeInfoData", [])],
        "attribute_groups": [normalized_row(row) for row in tables.get("AttributeGroupInfoData", [])],
        "passive_skills": [
            {
                **normalized_row(row),
                "localized_name": localized_string_key(mono_info, row.get("SkillNameKey"), row.get("SkillNameKey")),
            }
            for row in tables.get("PassiveSkillInfoData", [])
        ],
        "runes": runes,
        "pets": [
            {
                **normalized_row(row),
                "localized_name": localized_string_key(mono_info, row.get("NameKey"), row.get("NameKey") or row.get("PetKey")),
            }
            for row in tables.get("PetInfoData", [])
        ],
        "pet_stats": [normalized_row(row) for row in tables.get("PetStatInfoData", [])],
        "storage": {
            "inventory": [normalized_row(row) for row in tables.get("InventoryInfoData", [])],
            "stash": [normalized_row(row) for row in tables.get("StashInfoData", [])],
            "storage": [normalized_row(row) for row in tables.get("StorageInfoData", [])],
            "trading_stash": [normalized_row(row) for row in tables.get("TradingStashInfoData", [])],
        },
    }


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    def cell(value: Any) -> str:
        if value is None:
            return ""
        text = str(value).replace("\n", " ").replace("|", "\\|")
        return text

    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(cell(value) for value in row) + " |")
    return "\n".join(lines)


def write_page(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def top_counts(rows: list[dict[str, str]], column: str) -> list[tuple[str, int]]:
    counts = Counter((row.get(column) or "(blank)") for row in rows)
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


def build_pages(
    tables: dict[str, list[dict[str, str]]],
    heroes: list[dict[str, Any]],
    stages: list[dict[str, Any]],
    items: list[dict[str, Any]],
    drops: dict[str, Any],
    recipes: dict[str, Any],
    growth: dict[str, Any],
    schema: dict[str, Any],
    data_manager: dict[str, Any],
    mono_info: dict[str, Any],
    validation: dict[str, Any],
    raw_manifest: dict[str, Any],
) -> None:
    table_rows = [
        [name, info["row_count"], len(info["columns"]), ", ".join(info["primary_key_candidates"])]
        for name, info in sorted(schema["tables"].items())
    ]
    write_page(
        OUT / "README.md",
        f"""# TBH Lab Data Pack

Generated from the resource `text` and `dump` folders.

## What is included

- `data/schema_reference.json` - table inventory, inferred column types, curated relationships, dump enums, and InfoData class notes.
- `data/heroes.json` - heroes joined with skills, skill levels, buffs, attributes, sounds, and hero image asset paths.
- `data/stages.json` - all 120 stage rows joined with monsters, boss data, drop boxes, first-clear drops, stage-level scaling, BGM, and Mono stage assets.
- `data/items.json` - all 5,944 item rows joined with gear stats, unique mods, material stat pools, item groups, and chest drop tables.
- `data/drops.json` - drop tables grouped by DropKey with resolved ITEM/ITEMGROUP/MONSTER rewards and normalized weights.
- `data/recipes.json` - synthesis, crafting, cube, sub-recipe, and extraction-cost data.
- `data/growth.json` - levels, cube levels, hero attributes, passive skills, runes, pets, offline rewards, and storage costs.
- `data/tables/*.json` - normalized raw table exports for every parsed InfoData CSV.
- `data/validation_report.json` - unresolved-reference checks across the curated relationship graph.
- `pages/*.md` - wiki-friendly summaries and page scaffolding.

Start with `pages/wiki_summary_ja.md` for a Japanese investigation summary.

## Recommended wiki sections

1. Heroes and skills
2. Stages and monsters
3. Items, gear, materials, and unique mods
4. Drops, chests, crafting, cube, and synthesis
5. Progression systems: attributes, passives, runes, levels, storage
6. Schema reference and reverse-engineering notes

## Important source note

`dump.cs` and `script.json` expose type signatures, fields, enum values, addresses, and the central DB manager shape, but method bodies are empty in this IL2CPP dump. Treat CSV tables as the canonical database source and dump-derived information as type/index evidence. Exact runtime formulas that require method bodies still need binary disassembly or runtime tracing.
""",
    )

    hero_rows = [
        [
            hero["HeroKey"],
            hero["display_name"],
            hero["MainWeaponGearType"],
            hero["SubWeaponGearType"],
            hero["base_stats"]["AttackDamage"],
            hero["base_stats"]["AttackSpeed"],
            hero["base_stats"]["MaxHp"],
            hero["base_stats"]["Armor"],
            "yes" if hero.get("HasDLCDrop") else "",
        ]
        for hero in heroes
    ]
    hero_sections = []
    for hero in heroes:
        skill_rows = [
            [
                skill.get("SkillKey"),
                skill.get("display_name"),
                skill.get("SLOTTYPE"),
                skill.get("ACTIVATIONTYPE"),
                skill.get("ActivationValue"),
                skill.get("DamageType") or skill.get("DamageAttribute"),
                skill.get("DamageDeliveryType"),
                skill.get("Range"),
                len(skill.get("levels") or []),
            ]
            for skill in hero["skills"]
        ]
        attr_count = Counter(attr.get("ATTRIBUTETYPE") for attr in hero["attributes"])
        hero_sections.append(
            f"""## {hero['display_name']} ({hero['HeroKey']})

Base stats: AttackDamage {hero['base_stats']['AttackDamage']}, AttackSpeed {hero['base_stats']['AttackSpeed']}, Critical {hero['base_stats']['CriticalChance']}%/{hero['base_stats']['CriticalDamage']}, MaxHp {hero['base_stats']['MaxHp']}, Armor {hero['base_stats']['Armor']}, MovementSpeed {hero['base_stats']['MovementSpeed']}.

Weapons: `{hero['MainWeaponGearType']}` / `{hero['SubWeaponGearType']}`. Attribute nodes: {dict(attr_count)}.

{markdown_table(['SkillKey', 'NameKey', 'Slot', 'Activation', 'ActVal', 'Attr', 'Delivery', 'Range', 'Levels'], skill_rows)}
"""
        )
    write_page(
        PAGES_OUT / "heroes.md",
        "# Heroes And Skills\n\n"
        + markdown_table(
            ["HeroKey", "Class", "Main", "Sub", "Atk", "AtkSpd", "HP", "Armor", "DLC"],
            hero_rows,
        )
        + "\n\n"
        + "\n".join(hero_sections),
    )

    stage_rows = [
        [
            stage.get("StageKey"),
            stage.get("STAGEDIFFICULITY"),
            stage.get("Act"),
            stage.get("StageNo"),
            stage.get("STAGETYPE"),
            stage.get("StageLevel"),
            len(stage.get("monsters_resolved") or []),
            (stage.get("boss_resolved") or {}).get("display_name"),
            (stage.get("monster_drop_item") or {}).get("name"),
            (stage.get("boss_drop_item") or {}).get("name"),
        ]
        for stage in stages
    ]
    stage_counts = Counter((stage.get("STAGEDIFFICULITY"), stage.get("STAGETYPE")) for stage in stages)
    write_page(
        PAGES_OUT / "stages.md",
        "# Stages And Monsters\n\n"
        f"Stage rows: {len(stages)}. Difficulty/type distribution: {dict(stage_counts)}.\n\n"
        "Monster lists use `monsterKey_weight` pairs. Drop item rates are preserved as raw integer table values.\n\n"
        + markdown_table(
            ["StageKey", "Difficulty", "Act", "No", "Type", "Lv", "Monsters", "Boss", "Monster box", "Boss box"],
            stage_rows,
        ),
    )

    item_counter_type = Counter(item.get("ITEMTYPE") or "(blank)" for item in items)
    item_counter_grade = Counter(item.get("GRADE") or "(blank)" for item in items)
    grade_rows = [
        [
            row["GRADE"],
            row["InherentSlotAmount"],
            row["ExtraSlotAmount_Decoration"],
            row["ExtraSlotAmount_Engraving"],
            row["ExtraSlotAmount_Inscription"],
            row["BaseAlchemyGold"],
            row["BaseCubeExp"],
        ]
        for row in tables.get("GradeInfoData", [])
    ]
    gear_type_rows = [
        [
            row["GearType"],
            row["BaseStat1_STATTYPE"],
            row["BaseStat1_MODTYPE"],
            row["BaseStat2_STATTYPE"],
            row["BaseStat2_MODTYPE"],
        ]
        for row in tables.get("GearTypeInfoData", [])
    ]
    write_page(
        PAGES_OUT / "items_and_gear.md",
        "# Items And Gear\n\n"
        f"Items: {len(items)}. By type: {dict(item_counter_type)}. By grade: {dict(item_counter_grade)}.\n\n"
        "Full item rows are in `data/items.json`; this Markdown page keeps the high-value tables small enough for editing.\n\n"
        "## Grades\n\n"
        + markdown_table(
            ["Grade", "Inherent", "Decoration", "Engraving", "Inscription", "Base gold", "Base cube exp"],
            grade_rows,
        )
        + "\n\n## Gear Type Base Stats\n\n"
        + markdown_table(["GearType", "Base stat 1", "Mod", "Base stat 2", "Mod"], gear_type_rows),
    )

    drop_type_counts = Counter()
    reward_type_counts = Counter()
    for group in drops.values():
        for entry in group["entries"]:
            drop_type_counts[entry["drop_type"]] += 1
            reward_type_counts[entry["reward_type"]] += 1
    recipe_counts = {name: len(value) for name, value in recipes.items()}
    write_page(
        PAGES_OUT / "drops_and_recipes.md",
        "# Drops And Recipes\n\n"
        f"Unique DropKey count: {len(drops)}. DropType rows: {dict(drop_type_counts)}. RewardType rows: {dict(reward_type_counts)}.\n\n"
        "Drop entries are grouped in `data/drops.json`. Each entry includes raw weight and `weight_percent` within that DropKey.\n\n"
        f"Recipe row counts: {recipe_counts}.\n\n"
        "## Reward Resolution Rules\n\n"
        + markdown_table(
            ["REWARDTYPE", "RewardKey target", "Wiki handling"],
            [
                ["ITEM", "ItemInfoData.ItemKey", "Link directly to item page."],
                ["ITEMGROUP", "ItemGroupInfoData.ItemGroupKey", "Expand group into one or more item links."],
                ["MONSTER", "MonsterInfoData.MonsterKey", "Link to monster page if present."],
            ],
        ),
    )

    rune_count = len(growth["runes"])
    attr_counter = Counter(attr["ATTRIBUTETYPE"] for attr in growth["attributes"])
    storage_counts = {key: len(value) for key, value in growth["storage"].items()}
    write_page(
        PAGES_OUT / "growth_systems.md",
        "# Growth Systems\n\n"
        f"Level rows: {len(growth['levels'])}. Cube level rows: {len(growth['cube_levels'])}. Runes: {rune_count}. Attribute rows: {len(growth['attributes'])} {dict(attr_counter)}. Passive skills: {len(growth['passive_skills'])}. Pets: {len(growth['pets'])}. Storage tables: {storage_counts}.\n\n"
        "Rune graph data is in `data/growth.json` as `next_runes` and `preview_runes`. Attribute `Value` is polymorphic: passive nodes point to PassiveSkillInfoData, active skill nodes point to SkillInfoData.\n\n"
        "## Offline Rewards\n\n"
        + markdown_table(
            ["StageLevel", "BaseGold", "BaseExp", "KillCount", "ClearCount"],
            [[row["StageLevel"], row["BaseGold"], row["BaseExp"], row["KillCount"], row["ClearCount"]] for row in tables.get("OfflineRewardInfoData", [])[:30]],
        ),
    )

    data_manager_fields = [
        [field["name"], field["type"], field["visibility"], field["line"]]
        for field in data_manager["fields"]
        if "InfoData" in field["type"] or "Dictionary" in field["type"] or "HashSet" in field["type"]
    ]
    schema_rows = [[row[0], row[1], row[2], row[3]] for row in table_rows]
    write_page(
        PAGES_OUT / "schema_reference.md",
        "# Schema Reference\n\n"
        "CSV files are cleanly parseable as comma-separated tables except known non-DB text/template files. `dump.cs` confirms the InfoData class names, enum values, and central manager indexes.\n\n"
        + markdown_table(["Table", "Rows", "Columns", "Primary key candidates"], schema_rows)
        + "\n\n## Curated Relationships\n\n"
        + markdown_table(["From", "To", "Note"], [[rel["from"], rel["to"], rel["note"]] for rel in CURATED_RELATIONSHIPS])
        + "\n\n## Validation Report\n\n"
        + f"Status: `{validation['status']}`. Missing references: {validation['missing_total']}.\n\n"
        + markdown_table(
            ["Check", "Missing", "Note"],
            [[check["name"], check["missing_count"], check.get("note", "")] for check in validation["checks"]],
        )
        + "\n\nRaw normalized table JSON files are available under `data/tables/`. Parsed raw table count: "
        + str(len(raw_manifest))
        + ".\n"
        + "\n\n## Central DB Manager Evidence\n\n"
        "The class `yq : nn<yq>` contains the loaded lists and dictionaries used by the game. Method names are obfuscated and bodies are empty in the dump, but signatures reveal lookup surfaces.\n\n"
        + markdown_table(["Field", "Type", "Visibility", "dump.cs line"], data_manager_fields[:80])
        + "\n\n## Mono Asset Notes\n\n"
        f"Inventory Mono name files parsed: {len(mono_info['inventory_names'])}. Stage Mono assets parsed: {len(mono_info['stage_assets'])}. DLC asset files: {len(mono_info['dlc_assets'])}.\n",
    )

    unresolved_stage_values = []
    for check in validation["checks"]:
        if check["name"] == "Stage references":
            unresolved_stage_values = check["examples"]
            break
    unresolved_stage_text = ", ".join(
        f"Stage {item.get('stage')} -> {item.get('value')}" for item in unresolved_stage_values
    )
    if not unresolved_stage_text:
        unresolved_stage_text = "なし"

    write_page(
        PAGES_OUT / "wiki_summary_ja.md",
        f"""# タスクバーヒーロー Wiki調査まとめ

## 調査対象

- `リソース/text`: ゲーム内DBとして読み込まれるCSV系InfoData。45テーブルを正規化済み。
- `リソース/dump`: IL2CPP dump。`dump.cs` からInfoData型、enum、中央DBマネージャ `yq` のリスト/辞書構造を抽出。
- `リソース/Mono`: `[Inv] itemId name.dat` と `Stagexxxx_Actx_x.dat` から表示名・ステージ資産名を補助的に抽出。
- `リソース/image`: hero/skill画像の存在確認に利用。

## 主要データ量

| 分類 | 件数 | 出力 |
| --- | --- | --- |
| ヒーロー | {len(heroes)} | `data/heroes.json`, `pages/heroes.md` |
| ステージ | {len(stages)} | `data/stages.json`, `pages/stages.md` |
| アイテム | {len(items)} | `data/items.json`, `pages/items_and_gear.md` |
| DropKey | {len(drops)} | `data/drops.json`, `pages/drops_and_recipes.md` |
| 正規化rawテーブル | {len(raw_manifest)} | `data/tables/*.json` |
| 参照検証 | missing {validation['missing_total']} | `data/validation_report.json`, `pages/schema_reference.md` |

## Wiki向けページ構成

1. **Heroes And Skills**: ヒーロー6種、基礎ステータス、武器種、アクティブ/通常攻撃スキル、スキルレベル、バフ、属性ノード。
2. **Stages And Monsters**: 4難易度 x 30ステージ、Act/StageNo、通常モンスター候補、ボス、箱ドロップ、初回クリア報酬、BGM。
3. **Items And Gear**: 5,944アイテム、グレード別スロット、ギア種別基礎ステータス、UniqueMod、素材StatModプール。
4. **Drops And Recipes**: DropKey単位の重み付き報酬、ITEM/ITEMGROUP/MONSTER解決、合成・クラフト・キューブ・抽出コスト。
5. **Growth Systems**: Level/CubeLevel、ルーンツリー、属性ノード、パッシブ、ペット、倉庫/インベントリ拡張、オフライン報酬。
6. **Schema Reference**: テーブル一覧、主キー候補、関係定義、dump.csの型/enum/DBマネージャ証拠、検証結果。

## 重要な関係モデル

- `StageInfoData.Monsters` は `monsterKey_weight` の空白区切り。基本的には `MonsterInfoData.MonsterKey` にリンク。
- `DropInfoData.RewardKey` は `REWARDTYPE` で意味が変わる。`ITEM` は `ItemInfoData.ItemKey`、`ITEMGROUP` は `ItemGroupInfoData.ItemGroupKey`、`MONSTER` は `MonsterInfoData.MonsterKey`。
- `ItemInfoData.GearKey` は `GearInfoData.GearKey` にリンクし、多くのギアは `ItemKey == GearKey`。
- `AttributeInfoData.Value` は `ATTRIBUTETYPE` 依存。`PASSIVESKILL` は `PassiveSkillInfoData`、`ACTIVESKILL` は `SkillInfoData`。
- `RuneInfoData.LevelDataKey` は `RuneLevelInfoData.LevelKey`、`NextRuneKey`/`PreviewRuneKey` はルーンノードリンク。

## 残っている未解決点

- 参照検証で残るのはStageInfoの `Monsters` に出る `20101` のみ。該当: {unresolved_stage_text}
- `20101` は `SkillInfoData` と `SkillLevelInfoData`、`image/skills/Skill_20101.png` には存在するが、`MonsterInfoData.MonsterKey` としては存在しない。
- そのため、現段階では「StageInfo側の未抽出/誤記/特殊トークン候補」としてwiki注記に残すのが安全。

## dump解析上の制約

`dump.cs` と `script.json` からは型、enum、関数シグネチャ、RVA、DBマネージャの辞書構造を確認できる一方、メソッド本体は空です。正確なランタイム計算式は、このデータセットだけでは復元できません。現時点のwikiではCSV値とdump由来の型/参照関係を正として扱い、式が必要な箇所は追加のバイナリ解析かランタイムトレース対象として分離してください。
""",
    )


def main() -> None:
    configure_stdout()
    resource_dir = find_resource_dir()
    text_dir = resource_dir / "text"
    dump_dir = resource_dir / "dump"
    mono_dir = resource_dir / "Mono"

    tables = read_tables(text_dir)
    mono_info = parse_mono_names(mono_dir)
    asset_info = find_asset_files(resource_dir)
    enums = parse_dump_enums(dump_dir / "dump.cs")
    info_classes = parse_info_classes(dump_dir / "dump.cs")
    data_manager = parse_data_manager(dump_dir / "dump.cs")

    schema = build_schema_reference(tables, info_classes, enums, resource_dir)
    schema["data_manager"] = data_manager
    schema["asset_sources"] = {
        "mono_inventory_names": len(mono_info["inventory_names"]),
        "mono_stage_assets": len(mono_info["stage_assets"]),
        "hero_image_classes": sorted(asset_info.get("hero_images", {}).keys()),
    }
    validation = validate_references(tables)
    raw_manifest = export_raw_tables(tables)
    schema["raw_table_manifest"] = raw_manifest
    schema["validation_summary"] = {
        "status": validation["status"],
        "missing_total": validation["missing_total"],
    }

    drops = build_drops(tables, mono_info)
    heroes = build_heroes(tables, drops, asset_info, mono_info)
    stages = build_stages(tables, drops, mono_info["stage_assets"], mono_info)
    items = build_items(tables, drops, mono_info)
    recipes = build_recipes(tables, drops)
    growth = build_growth(tables, mono_info)

    write_json(DATA_OUT / "schema_reference.json", schema)
    write_json(DATA_OUT / "enums.json", enums)
    write_json(DATA_OUT / "heroes.json", heroes)
    write_json(DATA_OUT / "stages.json", stages)
    write_json(DATA_OUT / "items.json", items)
    write_json(DATA_OUT / "drops.json", drops)
    write_json(DATA_OUT / "recipes.json", recipes)
    write_json(DATA_OUT / "growth.json", growth)
    write_json(DATA_OUT / "mono_assets.json", mono_info)
    write_json(
        DATA_OUT / "mono_localization.json",
        {
            "supported_locales": mono_info.get("supported_locales", []),
            "string_table": mono_info.get("string_table", {}),
            "item_table": mono_info.get("item_table", {}),
            "item_localization": mono_info.get("item_localization", {}),
        },
    )
    write_json(DATA_OUT / "validation_report.json", validation)

    build_pages(tables, heroes, stages, items, drops, recipes, growth, schema, data_manager, mono_info, validation, raw_manifest)

    print("Generated wiki export:")
    print(f"  {OUT}")
    print(f"  tables={len(tables)} heroes={len(heroes)} stages={len(stages)} items={len(items)} drops={len(drops)}")


if __name__ == "__main__":
    main()
