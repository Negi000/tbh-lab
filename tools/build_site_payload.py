from __future__ import annotations

import json
import re
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESOURCE_IMAGE = ROOT / "リソース" / "image"
WIKI_DATA = ROOT / "output" / "wiki" / "data"
TABLES = WIKI_DATA / "tables"
PUBLIC_GENERATED = ROOT / "site" / "public" / "generated"
ASSETS_DIR = PUBLIC_GENERATED / "assets"
CATEGORIES_DIR = PUBLIC_GENERATED / "categories"
DETAILS_DIR = PUBLIC_GENERATED / "details"
LOCALES_DIR = PUBLIC_GENERATED / "locales"
RUNE_LAYOUT_PATH = ROOT / "tools" / "rune_layout_reference.json"


ORDERED_CATEGORY_IDS = [
    "my-save",
    "market",
    "farm-planner",
    "progress-planner",
    "lab-status",
    "gear",
    "materials",
    "effects",
    "stage-boxes",
    "heroes",
    "monsters",
    "skills",
    "runes",
    "pets",
    "stages",
    "cube",
    "database",
]

HERO_CLASS_JA = {
    "Knight": "ナイト",
    "Ranger": "レンジャー",
    "Sorcerer": "ソーサラー",
    "Priest": "プリースト",
    "Hunter": "ハンター",
    "Slayer": "スレイヤー",
}

HERO_FLAVOR = {
    "Knight": {
        "ja": "高い防御力と盾で前線を支える近接ヒーロー。",
        "en": "A tanky melee fighter with strong defense and shield equipment.",
    },
    "Ranger": {
        "ja": "弓と矢で安定した遠距離攻撃を行うヒーロー。",
        "en": "A ranged hero using bows and arrows for steady projectile damage.",
    },
    "Sorcerer": {
        "ja": "杖とオーブで広範囲の魔法火力を扱うヒーロー。",
        "en": "A magic damage hero using staff and orb skills.",
    },
    "Priest": {
        "ja": "サポートと耐久を両立する追加ヒーロー。",
        "en": "A support-oriented hero with strong utility and survivability.",
    },
    "Hunter": {
        "ja": "クロスボウとボルトで高い単体火力を狙う追加ヒーロー。",
        "en": "A crossbow hero built for focused ranged pressure.",
    },
    "Slayer": {
        "ja": "斧と手斧で重い一撃を放つ追加ヒーロー。",
        "en": "A heavy weapon hero using axe and hatchet attacks.",
    },
}

CLASS_BY_SKILL_PREFIX = {
    1: "Knight",
    2: "Ranger",
    3: "Sorcerer",
    4: "Priest",
    5: "Hunter",
    6: "Slayer",
}

HERO_KEY_BY_CLASS = {
    "Knight": 101,
    "Ranger": 201,
    "Sorcerer": 301,
    "Priest": 401,
    "Hunter": 501,
    "Slayer": 601,
}

DIFFICULTY_JA = {
    "NORMAL": "ノーマル",
    "NIGHTMARE": "ナイトメア",
    "HELL": "ヘル",
    "TORMENT": "トーメント",
}

GRADE_ORDER = [
    "COMMON",
    "UNCOMMON",
    "RARE",
    "LEGENDARY",
    "IMMORTAL",
    "ARCANA",
    "BEYOND",
    "CELESTIAL",
    "DIVINE",
    "COSMIC",
]

GRADE_COLORS = {
    "COMMON": "#b9c1cc",
    "UNCOMMON": "#30e763",
    "RARE": "#34bce8",
    "LEGENDARY": "#ffb01e",
    "IMMORTAL": "#ff4b4b",
    "ARCANA": "#a651ff",
    "BEYOND": "#ff3bb3",
    "CELESTIAL": "#4de5ff",
    "DIVINE": "#fff1a6",
    "COSMIC": "#ea78ff",
}

RUNE_CATEGORY_COLORS = {
    "Chests": "#a855f7",
    "Combat": "#f97316",
    "Cube": "#818cf8",
    "EXP": "#38bdf8",
    "Gold": "#f5c518",
    "Hero": "#ef4444",
    "Offline": "#22d3ee",
    "Slots": "#4ade80",
    "Other": "#d3a13d",
}

STAGE_DIFFICULTY_ORDER = ["NORMAL", "NIGHTMARE", "HELL", "TORMENT"]
STAGE_DIFFICULTY_COLORS = {
    "NORMAL": "#4ade80",
    "NIGHTMARE": "#38bdf8",
    "HELL": "#f97316",
    "TORMENT": "#ef4444",
}
STAGE_NODE_POSITIONS = {
    1: {
        1: {"x": 12, "y": 75},
        2: {"x": 21, "y": 66},
        3: {"x": 31, "y": 58},
        4: {"x": 41, "y": 50},
        5: {"x": 51, "y": 45},
        6: {"x": 61, "y": 38},
        7: {"x": 70, "y": 31},
        8: {"x": 79, "y": 24},
        9: {"x": 87, "y": 18},
        10: {"x": 92, "y": 12},
    },
    2: {
        1: {"x": 10, "y": 26},
        2: {"x": 20, "y": 34},
        3: {"x": 30, "y": 44},
        4: {"x": 40, "y": 55},
        5: {"x": 51, "y": 50},
        6: {"x": 60, "y": 41},
        7: {"x": 69, "y": 33},
        8: {"x": 78, "y": 41},
        9: {"x": 86, "y": 53},
        10: {"x": 92, "y": 66},
    },
    3: {
        1: {"x": 12, "y": 70},
        2: {"x": 22, "y": 61},
        3: {"x": 34, "y": 53},
        4: {"x": 45, "y": 44},
        5: {"x": 56, "y": 35},
        6: {"x": 66, "y": 40},
        7: {"x": 74, "y": 50},
        8: {"x": 82, "y": 60},
        9: {"x": 89, "y": 51},
        10: {"x": 93, "y": 38},
    },
}

TRANSLATIONS = {
    "ja": {
        "app.title": "TBH Lab",
        "app.subtitle": "ゲームデータから生成する攻略データベース",
        "nav.home": "ホーム",
        "nav.search": "検索",
        "nav.locale": "言語",
        "nav.menu": "メニュー",
        "nav.back": "戻る",
        "nav.database": "データベース",
        "nav.combat": "戦闘",
        "nav.collection": "収集",
        "nav.tools": "ツール",
        "nav.systems": "システム",
        "nav.reference": "リファレンス",
        "home.kicker": "Community database",
        "home.title": "TBH Lab",
        "home.description": "タスクバーで動く小さな放置RPGのヒーロー、装備、スキル、ルーン、ステージ、ドロップをゲームデータから整理したWikiです。",
        "home.cta.gear": "装備を見る",
        "home.cta.stages": "ステージを見る",
        "home.section.jump": "システムへ移動",
        "home.section.heroes": "プレイアブルヒーロー",
        "home.section.research": "調査メモ",
        "home.note.generated": "build.py でテキストDBとダンプ解析結果から再生成できます。",
        "home.note.validation": "参照検証で残っている未解決項目は StageInfo の特殊トークンだけです。",
        "home.stat.items": "アイテムと装備",
        "home.stat.heroes": "プレイアブルクラス",
        "home.stat.stages": "ステージ",
        "home.stat.languages": "対応言語",
        "category.gear.title": "装備",
        "category.gear.description": "武器、防具、アクセサリをグレード、クラス、部位、レベルで検索できます。",
        "category.materials.title": "素材",
        "category.materials.description": "装飾、刻印、銘文などの素材と対応する効果グループを確認できます。",
        "category.effects.title": "素材効果",
        "category.effects.description": "素材グループが付与するステータス、Tier範囲、対象部位を整理しています。",
        "category.stage-boxes.title": "報酬箱",
        "category.stage-boxes.description": "通常箱、ステージボス箱、Actボス箱のレベル帯とドロップテーブルです。",
        "category.heroes.title": "ヒーロー",
        "category.heroes.description": "6人のヒーローの基礎ステータス、武器種、スキル、属性ノード。",
        "category.monsters.title": "モンスター",
        "category.monsters.description": "モンスターの報酬、攻撃、HP、出現ステージ参照のためのデータ。",
        "category.skills.title": "スキル",
        "category.skills.description": "アクティブスキルとパッシブスキルの発動条件、射程、倍率、参照キー。",
        "category.runes.title": "ルーン",
        "category.runes.description": "ルーンノード、最大レベル、前提ノード、接続関係、アイコン。",
        "category.pets.title": "ペット",
        "category.pets.description": "ペットの解放条件とステータスボーナス。",
        "category.stages.title": "ステージ",
        "category.stages.description": "全120ステージの難易度、Act、敵構成、ボス、報酬箱、初回報酬。",
        "category.cube.title": "キューブ",
        "category.cube.description": "合成、錬金、クラフト、装飾、刻印、抽出などキューブ系データ。",
        "category.database.title": "全データ",
        "category.database.description": "正規化した45個のInfoDataテーブルとスキーマ参照。",
        "filter.search.placeholder": "名前、ID、キー、タグで検索",
        "filter.all": "すべて",
        "filter.grade": "グレード",
        "filter.type": "タイプ",
        "filter.class": "クラス",
        "filter.gearType": "ギア種",
        "filter.part": "部位",
        "filter.difficulty": "難易度",
        "filter.act": "Act",
        "filter.materialType": "素材種",
        "filter.slot": "スロット",
        "filter.category": "カテゴリ",
        "filter.reset": "リセット",
        "view.table": "表",
        "view.cards": "カード",
        "pager.previous": "前へ",
        "pager.next": "次へ",
        "pager.page": "ページ",
        "state.loading": "読み込み中",
        "state.empty": "該当するデータがありません。",
        "state.error": "データの読み込みに失敗しました。",
        "detail.section.overview": "概要",
        "detail.section.baseStats": "基礎ステータス",
        "detail.section.skills": "スキル",
        "detail.section.attributes": "属性ノード",
        "detail.section.gearStats": "ギア性能",
        "detail.section.unique": "ユニーク効果",
        "detail.section.materialPool": "素材効果プール",
        "detail.section.dropTable": "ドロップテーブル",
        "detail.section.monsters": "モンスター構成",
        "detail.section.rewards": "報酬",
        "detail.section.scaling": "倍率",
        "detail.section.entries": "データ",
        "detail.section.raw": "Raw fields",
        "detail.open": "詳細",
        "field.id": "ID",
        "field.name": "名前",
        "field.type": "タイプ",
        "field.grade": "グレード",
        "field.class": "クラス",
        "field.gearType": "ギア種",
        "field.part": "部位",
        "field.level": "レベル",
        "field.mainWeapon": "メイン武器",
        "field.subWeapon": "サブ武器",
        "field.unlock": "解放",
        "field.attackDamage": "攻撃力",
        "field.attackSpeed": "攻撃速度",
        "field.castSpeed": "詠唱速度",
        "field.criticalChance": "クリ率",
        "field.criticalDamage": "クリダメ",
        "field.maxHp": "最大HP",
        "field.armor": "防御",
        "field.moveSpeed": "移動速度",
        "field.cooldown": "クールダウン",
        "field.range": "射程",
        "field.activation": "発動条件",
        "field.value": "値",
        "field.tier": "Tier",
        "field.min": "最小",
        "field.max": "最大",
        "field.weight": "重み",
        "field.percent": "比率",
        "field.act": "Act",
        "field.stage": "ステージ",
        "field.stageLevel": "推奨Lv",
        "field.wave": "Wave",
        "field.boss": "ボス",
        "field.monsters": "敵",
        "field.gold": "Gold",
        "field.exp": "EXP",
        "field.count": "件数",
        "field.table": "テーブル",
        "field.records": "レコード数",
        "field.status": "状態",
    },
    "en": {
        "app.title": "TBH Lab",
        "app.subtitle": "A generated database for the tiny taskbar RPG",
        "nav.home": "Home",
        "nav.search": "Search",
        "nav.locale": "Language",
        "nav.menu": "Menu",
        "nav.back": "Back",
        "nav.database": "Database",
        "nav.combat": "Combat",
        "nav.collection": "Collection",
        "nav.tools": "Tools",
        "nav.systems": "Systems",
        "nav.reference": "Reference",
        "home.kicker": "Community database",
        "home.title": "TBH Lab",
        "home.description": "A generated wiki for the tiny idle RPG that runs from the taskbar: heroes, gear, skills, runes, stages, drops, and cube data pulled from local game resources.",
        "home.cta.gear": "Browse gear",
        "home.cta.stages": "Open stages",
        "home.section.jump": "Jump straight to a system",
        "home.section.heroes": "Playable heroes",
        "home.section.research": "Research notes",
        "home.note.generated": "The site can be regenerated from text DB and dump-derived exports with build.py.",
        "home.note.validation": "The remaining unresolved references are limited to a StageInfo special token.",
        "home.stat.items": "items and gear",
        "home.stat.heroes": "playable classes",
        "home.stat.stages": "stage entries",
        "home.stat.languages": "languages",
        "category.gear.title": "Gear",
        "category.gear.description": "Search weapons, armor, and accessories by grade, class, gear type, part, and level.",
        "category.materials.title": "Materials",
        "category.materials.description": "Decoration, engraving, inscription, and other materials with their effect groups.",
        "category.effects.title": "Material Effects",
        "category.effects.description": "Which stat mods can roll from each material group, with tier ranges and target gear groups.",
        "category.stage-boxes.title": "Stage Boxes",
        "category.stage-boxes.description": "Normal, stage boss, and act boss boxes with level bands and drop tables.",
        "category.heroes.title": "Heroes",
        "category.heroes.description": "Six playable heroes with base stats, weapon types, skills, and attribute nodes.",
        "category.monsters.title": "Monsters",
        "category.monsters.description": "Monster rewards, combat stats, and identifiers for stage references.",
        "category.skills.title": "Skills & Passives",
        "category.skills.description": "Active and passive skills with activation rules, range, scaling, and data keys.",
        "category.runes.title": "Runes",
        "category.runes.description": "Rune nodes, max levels, prerequisite links, connections, and icons.",
        "category.pets.title": "Pets",
        "category.pets.description": "Pet unlock requirements and stat bonuses.",
        "category.stages.title": "Stages",
        "category.stages.description": "All 120 stages with difficulty, act, monster lineup, boss, boxes, and first clear rewards.",
        "category.cube.title": "Cube",
        "category.cube.description": "Synthesis, alchemy, crafting, decoration, engraving, inscription, extraction, and offering data.",
        "category.database.title": "All Data",
        "category.database.description": "The normalized 45 InfoData tables and schema reference.",
        "filter.search.placeholder": "Search by name, ID, key, or tag",
        "filter.all": "All",
        "filter.grade": "Grade",
        "filter.type": "Type",
        "filter.class": "Class",
        "filter.gearType": "Gear type",
        "filter.part": "Part",
        "filter.difficulty": "Difficulty",
        "filter.act": "Act",
        "filter.materialType": "Material type",
        "filter.slot": "Slot",
        "filter.category": "Category",
        "filter.reset": "Reset",
        "view.table": "Table",
        "view.cards": "Cards",
        "pager.previous": "Previous",
        "pager.next": "Next",
        "pager.page": "Page",
        "state.loading": "Loading",
        "state.empty": "No data matches the current filters.",
        "state.error": "Failed to load data.",
        "detail.section.overview": "Overview",
        "detail.section.baseStats": "Base stats",
        "detail.section.skills": "Skills",
        "detail.section.attributes": "Attribute nodes",
        "detail.section.gearStats": "Gear stats",
        "detail.section.unique": "Unique effect",
        "detail.section.materialPool": "Material effect pool",
        "detail.section.dropTable": "Drop table",
        "detail.section.monsters": "Monster lineup",
        "detail.section.rewards": "Rewards",
        "detail.section.scaling": "Scaling",
        "detail.section.entries": "Entries",
        "detail.section.raw": "Raw fields",
        "detail.open": "Open",
        "field.id": "ID",
        "field.name": "Name",
        "field.type": "Type",
        "field.grade": "Grade",
        "field.class": "Class",
        "field.gearType": "Gear type",
        "field.part": "Part",
        "field.level": "Level",
        "field.mainWeapon": "Main weapon",
        "field.subWeapon": "Off-hand",
        "field.unlock": "Unlock",
        "field.attackDamage": "Attack damage",
        "field.attackSpeed": "Attack speed",
        "field.castSpeed": "Cast speed",
        "field.criticalChance": "Crit chance",
        "field.criticalDamage": "Crit damage",
        "field.maxHp": "Max HP",
        "field.armor": "Armor",
        "field.moveSpeed": "Move speed",
        "field.cooldown": "Cooldown",
        "field.range": "Range",
        "field.activation": "Activation",
        "field.value": "Value",
        "field.tier": "Tier",
        "field.min": "Min",
        "field.max": "Max",
        "field.weight": "Weight",
        "field.percent": "Share",
        "field.act": "Act",
        "field.stage": "Stage",
        "field.stageLevel": "Stage Lv",
        "field.wave": "Waves",
        "field.boss": "Boss",
        "field.monsters": "Monsters",
        "field.gold": "Gold",
        "field.exp": "EXP",
        "field.count": "Count",
        "field.table": "Table",
        "field.records": "Records",
        "field.status": "Status",
    },
}

JA_TRANSLATION_FIXES = {
    "app.subtitle": "ゲームデータから再生成できる攻略データベース",
    "nav.home": "ホーム",
    "nav.search": "検索",
    "nav.locale": "言語",
    "nav.menu": "メニュー",
    "nav.back": "戻る",
    "nav.database": "データベース",
    "nav.combat": "戦闘",
    "nav.collection": "収集",
    "nav.tools": "ツール",
    "nav.systems": "システム",
    "nav.reference": "リファレンス",
    "home.kicker": "Community database",
    "home.description": "タスクバーで動く小さな放置RPGのヒーロー、装備、スキル、ルーン、ステージ、ドロップをゲームデータから整理した wiki です。",
    "home.cta.gear": "装備を見る",
    "home.cta.stages": "ステージを見る",
    "home.section.jump": "カテゴリへ移動",
    "home.section.heroes": "プレイアブルヒーロー",
    "home.section.research": "調査メモ",
    "home.note.generated": "build.py で text / dump / Mono から一括再生成できます。",
    "home.note.validation": "未解決の参照は検証レポートに残し、ページ側では注意点として扱います。",
    "home.stat.items": "アイテムと装備",
    "home.stat.heroes": "ヒーロークラス",
    "home.stat.stages": "ステージ",
    "home.stat.languages": "対応言語",
    "category.gear.title": "装備",
    "category.gear.description": "武器、防具、アクセサリーをグレード、種別、部位、レベルで検索できます。",
    "category.materials.title": "素材",
    "category.materials.description": "装飾、刻印、刻文などの素材と、付与される効果プールを確認できます。",
    "category.effects.title": "素材効果",
    "category.effects.description": "素材グループごとのステータス補正、Tier 範囲、対象部位を整理しています。",
    "category.stage-boxes.title": "ステージ箱",
    "category.stage-boxes.description": "通常箱、ステージボス箱、Act ボス箱のレベル帯とドロップテーブルです。",
    "category.heroes.title": "ヒーロー",
    "category.heroes.description": "6人のヒーローの基礎ステータス、武器種、スキル、属性ノードをまとめています。",
    "category.monsters.title": "モンスター",
    "category.monsters.description": "モンスターの報酬、戦闘ステータス、ステージ参照用 ID を整理しています。",
    "category.skills.title": "スキル",
    "category.skills.description": "アクティブスキルとパッシブスキルの発動条件、射程、値、参照キーを整理しています。",
    "category.runes.title": "ルーン",
    "category.runes.description": "ルーンノード、最大レベル、前提レベル、接続関係、アイコンを確認できます。",
    "category.pets.title": "ペット",
    "category.pets.description": "ペットの解放条件とステータスボーナスです。",
    "category.stages.title": "ステージ",
    "category.stages.description": "全120ステージの難易度、Act、モンスター構成、ボス、箱、初回クリア報酬を整理しています。",
    "category.cube.title": "キューブ",
    "category.cube.description": "合成、錬金、クラフト、抽出などキューブ系データをまとめています。",
    "category.database.title": "全データ",
    "category.database.description": "正規化した InfoData テーブルとスキーマ参照です。",
    "filter.search.placeholder": "名前、ID、キー、タグで検索",
    "filter.all": "すべて",
    "filter.grade": "グレード",
    "filter.type": "タイプ",
    "filter.class": "クラス",
    "filter.gearType": "装備種",
    "filter.part": "部位",
    "filter.difficulty": "難易度",
    "filter.act": "Act",
    "filter.materialType": "素材種",
    "filter.slot": "スロット",
    "filter.category": "カテゴリ",
    "filter.reset": "リセット",
    "view.table": "表",
    "view.cards": "カード",
    "pager.previous": "前へ",
    "pager.next": "次へ",
    "pager.page": "ページ",
    "state.loading": "読み込み中",
    "state.empty": "条件に一致するデータがありません。",
    "state.error": "データの読み込みに失敗しました。",
    "detail.section.overview": "概要",
    "detail.section.baseStats": "基礎ステータス",
    "detail.section.skills": "スキル",
    "detail.section.attributes": "属性ノード",
    "detail.section.gearStats": "装備性能",
    "detail.section.unique": "ユニーク効果",
    "detail.section.materialPool": "素材効果プール",
    "detail.section.dropTable": "ドロップテーブル",
    "detail.section.sources": "入手元",
    "detail.section.farmStages": "おすすめステージ",
    "detail.section.connections": "接続ノード",
    "detail.section.monsters": "モンスター構成",
    "detail.section.rewards": "報酬",
    "detail.section.scaling": "スケーリング",
    "detail.section.entries": "データ",
    "detail.section.raw": "Raw フィールド",
    "detail.open": "詳細",
    "field.id": "ID",
    "field.name": "名前",
    "field.type": "タイプ",
    "field.grade": "グレード",
    "field.class": "クラス",
    "field.gearType": "装備種",
    "field.part": "部位",
    "field.level": "レベル",
    "field.mainWeapon": "メイン武器",
    "field.subWeapon": "サブ武器",
    "field.unlock": "解放",
    "field.attackDamage": "攻撃力",
    "field.attackSpeed": "攻撃速度",
    "field.castSpeed": "詠唱速度",
    "field.criticalChance": "クリティカル率",
    "field.criticalDamage": "クリティカル威力",
    "field.maxHp": "最大HP",
    "field.armor": "防御力",
    "field.cooldown": "クールダウン",
    "field.moveSpeed": "移動速度",
    "field.activation": "発動",
    "field.value": "値",
    "field.range": "射程",
    "field.tier": "Tier",
    "field.weight": "重み",
    "field.percent": "確率",
    "field.max": "最大",
    "field.stage": "Stage",
    "field.stageLevel": "ステージLv",
    "field.wave": "Wave",
    "field.boss": "ボス",
    "field.monsters": "モンスター",
    "field.gold": "ゴールド",
    "field.exp": "EXP",
    "field.count": "件数",
    "field.table": "テーブル",
    "field.records": "レコード数",
    "field.status": "状態",
    "field.chest": "宝箱",
    "field.source": "入手元",
    "field.drop": "ドロップ",
    "field.spawn": "出現",
    "field.cost": "コスト",
    "field.effect": "効果",
    "tooltip.baseStats": "基本ステータス",
    "tooltip.inherentStats": "固有ステータス",
    "tooltip.slots": "装備スロット",
    "tooltip.weaponEffects": "武器装飾効果",
    "tooltip.armorEffects": "防具装飾効果",
    "tooltip.accessoryEffects": "アクセサリー装飾効果",
    "tooltip.trade": "取引",
    "tooltip.tradeable": "取引可能",
    "tooltip.notTradeable": "取引不可",
    "tooltip.source": "入手",
    "tooltip.emptySlot": "空きスロット",
    "tooltip.requiredLevel": "必要レベル",
    "rune.planner.title": "ルーンツリー",
    "rune.planner.subtitle": "ノードを選択してレベルを調整すると、必要ゴールドと合計ボーナスを確認できます。",
    "rune.selected": "選択中",
    "rune.level": "レベル",
    "rune.cost": "必要コスト",
    "rune.totalCost": "合計コスト",
    "rune.totalBonuses": "合計ボーナス",
    "rune.maxAll": "全て最大",
    "rune.reset": "リセット",
    "rune.connected": "接続",
    "rune.preview": "プレビュー",
    "rune.requiredLevel": "前提レベル",
    "rune.nodeCount": "ノード数",
    "rune.zoom": "ズーム",
    "rune.zoomIn": "拡大",
    "rune.zoomOut": "縮小",
    "rune.resetView": "表示を戻す",
    "rune.dragHint": "ドラッグで移動",
    "rune.category.Chests": "宝箱",
    "rune.category.Combat": "戦闘",
    "rune.category.Cube": "キューブ",
    "rune.category.EXP": "EXP",
    "rune.category.Gold": "ゴールド",
    "rune.category.Hero": "ヒーロー",
    "rune.category.Offline": "オフライン",
    "rune.category.Slots": "枠拡張",
    "rune.category.Other": "その他",
    "stageAtlas.title": "ステージアトラス",
    "stageAtlas.subtitle": "Actマップからステージを選択し、敵構成、出現比率、ボス、箱ドロップを確認できます。",
    "stageAtlas.act": "Act",
    "stageAtlas.selectedStage": "選択ステージ",
    "stageAtlas.openDetail": "詳細を開く",
    "stageAtlas.monsterLineup": "敵構成",
    "stageAtlas.rewards": "報酬",
    "stageAtlas.dropPreview": "箱の中身プレビュー",
    "stageAtlas.spawnShare": "出現比率",
    "stageAtlas.expectedPerWave": "1Wave目安",
    "stageAtlas.wavePlan": "Wave",
    "stageAtlas.normalBox": "通常箱",
    "stageAtlas.bossBox": "ボス箱",
    "stageAtlas.firstClear": "初回クリア",
    "stageAtlas.boss": "ボス",
    "stageAtlas.mapHint": "ステージノードをクリック",
}

EN_TRANSLATION_FIXES = {
    "detail.section.sources": "Sources",
    "detail.section.farmStages": "Recommended stages",
    "detail.section.connections": "Connected nodes",
    "field.chest": "Chest",
    "field.source": "Source",
    "field.drop": "Drop",
    "field.spawn": "Spawn",
    "field.cost": "Cost",
    "field.effect": "Effect",
    "tooltip.baseStats": "Base stats",
    "tooltip.inherentStats": "Inherent stats",
    "tooltip.slots": "Equipment slots",
    "tooltip.weaponEffects": "Weapon decoration effect",
    "tooltip.armorEffects": "Armor decoration effect",
    "tooltip.accessoryEffects": "Accessory decoration effect",
    "tooltip.trade": "Trade",
    "tooltip.tradeable": "Tradeable",
    "tooltip.notTradeable": "Not tradeable",
    "tooltip.source": "Source",
    "tooltip.emptySlot": "Empty slot",
    "tooltip.requiredLevel": "Required level",
    "rune.planner.title": "Rune Tree",
    "rune.planner.subtitle": "Select nodes and adjust levels to calculate required gold and total bonuses.",
    "rune.selected": "Selected",
    "rune.level": "Level",
    "rune.cost": "Required cost",
    "rune.totalCost": "Total cost",
    "rune.totalBonuses": "Total bonuses",
    "rune.maxAll": "Max all",
    "rune.reset": "Reset",
    "rune.connected": "Connected",
    "rune.preview": "Preview",
    "rune.requiredLevel": "Prerequisite level",
    "rune.nodeCount": "Nodes",
    "rune.zoom": "Zoom",
    "rune.zoomIn": "Zoom in",
    "rune.zoomOut": "Zoom out",
    "rune.resetView": "Reset view",
    "rune.dragHint": "Drag to pan",
    "rune.category.Chests": "Chests",
    "rune.category.Combat": "Combat",
    "rune.category.Cube": "Cube",
    "rune.category.EXP": "EXP",
    "rune.category.Gold": "Gold",
    "rune.category.Hero": "Hero",
    "rune.category.Offline": "Offline",
    "rune.category.Slots": "Slots",
    "rune.category.Other": "Other",
    "stageAtlas.title": "Stage Atlas",
    "stageAtlas.subtitle": "Pick a stage from the Act map to inspect monsters, spawn shares, boss data, and chest drops.",
    "stageAtlas.act": "Act",
    "stageAtlas.selectedStage": "Selected stage",
    "stageAtlas.openDetail": "Open details",
    "stageAtlas.monsterLineup": "Monster lineup",
    "stageAtlas.rewards": "Rewards",
    "stageAtlas.dropPreview": "Drop preview",
    "stageAtlas.spawnShare": "Spawn share",
    "stageAtlas.expectedPerWave": "Expected / wave",
    "stageAtlas.wavePlan": "Waves",
    "stageAtlas.normalBox": "Normal box",
    "stageAtlas.bossBox": "Boss box",
    "stageAtlas.firstClear": "First clear",
    "stageAtlas.boss": "Boss",
    "stageAtlas.mapHint": "Click a stage node",
}

TRANSLATIONS["ja"].update(JA_TRANSLATION_FIXES)
TRANSLATIONS["en"].update(EN_TRANSLATION_FIXES)
TRANSLATIONS["ja"].update(
    {
        "category.my-save.title": "マイセーブ",
        "category.my-save.description": "ローカルのセーブファイルをブラウザ内だけで読み込み、所持品、進行度、ルーン、ペット状態をwikiデータと連携します。",
        "category.market.title": "マーケット",
        "category.market.description": "Steamマーケット相場、出品数、流動性、セーブ内アイテムの概算評価を確認します。",
        "save.title": "マイセーブ連携",
        "save.subtitle": "SaveFile_Live.es3を選択すると、この端末内でのみ復号してwiki表示に反映します。ファイルはアップロードされません。",
        "save.pickFile": "セーブを選択",
        "save.loaded": "セーブ読込済み",
        "save.notLoaded": "未読込",
        "save.privacy": "ローカル復号のみ。サーバー送信なし、書き込みなし。",
        "save.version": "バージョン",
        "save.playTime": "プレイ時間",
        "save.currentStage": "現在ステージ",
        "save.maxStage": "最高到達",
        "save.inventory": "インベントリ",
        "save.stash": "倉庫",
        "save.tradeStash": "取引倉庫",
        "save.equipped": "装備中",
        "save.marketValue": "推定相場",
        "save.owned": "所持数",
        "save.runes": "ルーン",
        "save.pets": "ペット",
        "save.heroes": "ヒーロー",
        "save.error": "セーブの読込に失敗しました",
        "market.title": "マーケット相場",
        "market.subtitle": "CloudflareキャッシュAPIを優先し、セーブを読み込むと倉庫内アイテムを概算査定できます。",
        "market.search": "相場検索",
        "market.refresh": "更新",
        "market.lowest": "最安値",
        "market.median": "中央値",
        "market.listings": "出品数",
        "market.volume": "24h販売",
        "market.updated": "更新",
        "market.status": "市場状態",
        "market.valuation": "セーブ内アイテム査定",
        "market.estimate": "概算評価",
        "market.endpoint": "取得元",
        "market.unavailable": "ライブ相場は現在の環境では取得できません。Cloudflare Pages Functions配備後に同一オリジンAPIから取得されます。",
        "relation.sources": "入手元",
        "relation.chestContents": "箱の中身",
        "relation.stageAppearances": "出現ステージ",
        "relation.petTarget": "ペット解放対象",
        "relation.saveOwned": "セーブ所持",
    }
)
TRANSLATIONS["en"].update(
    {
        "category.my-save.title": "My Save",
        "category.my-save.description": "Load a local save file in the browser only and connect inventory, progress, runes, and pets to wiki data.",
        "category.market.title": "Market",
        "category.market.description": "Inspect Steam market prices, listings, liquidity, and estimated value for items in your loaded save.",
        "save.title": "My Save Link",
        "save.subtitle": "Select SaveFile_Live.es3 to decrypt it locally in this browser. The file is never uploaded.",
        "save.pickFile": "Choose save",
        "save.loaded": "Save loaded",
        "save.notLoaded": "Not loaded",
        "save.privacy": "Local decrypt only. No upload and no write-back.",
        "save.version": "Version",
        "save.playTime": "Play time",
        "save.currentStage": "Current stage",
        "save.maxStage": "Best stage",
        "save.inventory": "Inventory",
        "save.stash": "Warehouse",
        "save.tradeStash": "Trade stash",
        "save.equipped": "Equipped",
        "save.marketValue": "Estimated value",
        "save.owned": "Owned",
        "save.runes": "Runes",
        "save.pets": "Pets",
        "save.heroes": "Heroes",
        "save.error": "Failed to read save",
        "market.title": "Market Prices",
        "market.subtitle": "Uses the Cloudflare cached API first; with a loaded save, it estimates warehouse item value.",
        "market.search": "Search market",
        "market.refresh": "Refresh",
        "market.lowest": "Lowest",
        "market.median": "Median",
        "market.listings": "Listings",
        "market.volume": "24h volume",
        "market.updated": "Updated",
        "market.status": "Market status",
        "market.valuation": "Save inventory valuation",
        "market.estimate": "Estimate",
        "market.endpoint": "Source",
        "market.unavailable": "Live market data is not available in this environment. After Cloudflare Pages Functions are deployed, same-origin API requests will be used.",
        "relation.sources": "Sources",
        "relation.chestContents": "Chest contents",
        "relation.stageAppearances": "Stage appearances",
        "relation.petTarget": "Pet unlock target",
        "relation.saveOwned": "Owned in save",
    }
)

TRANSLATIONS["ja"].update(
    {
        "market.buyingAvailable": "閲覧・購入導線は利用可能。出品と新規更新のみ制限中です。",
        "market.cachePolicy": "Cloudflareで短時間キャッシュし、検索・履歴・注文板を同一オリジン経由で取得します。",
        "market.currency": "通貨",
        "market.usd": "USD",
        "market.jpy": "JPY",
        "market.filters": "絞り込み",
        "market.gear": "装備種",
        "market.level": "レベル",
        "market.sort": "並び替え",
        "market.sort.listings": "出品数が多い",
        "market.sort.price": "価格が安い",
        "market.sort.volume": "24h販売が多い",
        "market.sort.level": "レベルが高い",
        "market.tradableOnly": "取引可能のみ",
        "market.dealOnly": "割安候補",
        "market.resetFilters": "条件をリセット",
        "market.viewSteam": "Steamで購入",
        "market.details": "相場詳細",
        "market.close": "閉じる",
        "market.history": "価格推移",
        "market.orderbook": "注文板",
        "market.lowestSell": "最安売り",
        "market.highestBuy": "最高買い",
        "market.sellOrders": "売り注文",
        "market.buyOrders": "買い注文",
        "market.netAfterFee": "手数料後",
        "market.feeNote": "Steam手数料15%想定",
        "market.change": "変動",
        "market.movers": "急騰・急落",
        "market.moversUp": "上昇",
        "market.moversDown": "下落",
        "market.staticFallback": "ライブ取得できない場合は、wiki生成時点の候補を表示します。",
        "market.liveResults": "ライブ結果",
        "market.staticResults": "wiki候補",
        "market.page": "ページ",
        "market.next": "次へ",
        "market.previous": "前へ",
        "market.scope": "査定範囲",
        "market.scope.all": "全所持品",
        "market.scope.inventory": "インベントリ",
        "market.scope.stash": "倉庫",
        "market.scope.tradeStash": "取引倉庫",
        "market.scope.equipped": "装備中",
        "market.priced": "価格取得",
        "market.unpriced": "未取得",
        "market.netEstimate": "手数料後概算",
        "market.valuationLimit": "負荷対策のため一度に上位120種類まで査定します。",
        "market.noHistory": "価格推移データがありません。",
        "market.openMarketSearch": "相場で開く",
    }
)
TRANSLATIONS["en"].update(
    {
        "market.buyingAvailable": "Browsing and purchase links are available; only new listings and fresh updates are limited.",
        "market.cachePolicy": "Cloudflare caches search, history, and order-book calls briefly through the same origin.",
        "market.currency": "Currency",
        "market.usd": "USD",
        "market.jpy": "JPY",
        "market.filters": "Filters",
        "market.gear": "Gear",
        "market.level": "Level",
        "market.sort": "Sort",
        "market.sort.listings": "Most listings",
        "market.sort.price": "Lowest price",
        "market.sort.volume": "Highest 24h volume",
        "market.sort.level": "Highest level",
        "market.tradableOnly": "Tradable only",
        "market.dealOnly": "Deal candidates",
        "market.resetFilters": "Reset filters",
        "market.viewSteam": "Buy on Steam",
        "market.details": "Market details",
        "market.close": "Close",
        "market.history": "Price trend",
        "market.orderbook": "Order book",
        "market.lowestSell": "Lowest sell",
        "market.highestBuy": "Highest buy",
        "market.sellOrders": "Sell orders",
        "market.buyOrders": "Buy orders",
        "market.netAfterFee": "After fee",
        "market.feeNote": "Assumes 15% Steam fee",
        "market.change": "Change",
        "market.movers": "Movers",
        "market.moversUp": "Rising",
        "market.moversDown": "Falling",
        "market.staticFallback": "When live data is unavailable, generated wiki candidates are shown.",
        "market.liveResults": "Live results",
        "market.staticResults": "Wiki candidates",
        "market.page": "Page",
        "market.next": "Next",
        "market.previous": "Previous",
        "market.scope": "Valuation scope",
        "market.scope.all": "All owned",
        "market.scope.inventory": "Inventory",
        "market.scope.stash": "Warehouse",
        "market.scope.tradeStash": "Trade stash",
        "market.scope.equipped": "Equipped",
        "market.priced": "Priced",
        "market.unpriced": "Unpriced",
        "market.netEstimate": "Net estimate",
        "market.valuationLimit": "To protect the API, one valuation pass checks up to 120 item types.",
        "market.noHistory": "No price trend data is available.",
        "market.openMarketSearch": "Open in market",
    }
)

TRANSLATIONS["ja"].update(
    {
        "app.title": "TBH Lab",
        "app.subtitle": "ゲームデータから再生成できる攻略データベース",
        "home.title": "TBH Lab",
        "home.kicker": "TaskbarHero data laboratory",
        "category.farm-planner.title": "Farm Planner",
        "category.farm-planner.description": "アイテム、ペット、敵、ステージを横断して、入手先やおすすめ周回先を探す計画画面です。",
        "category.progress-planner.title": "Progress Planner",
        "category.progress-planner.description": "セーブデータをwiki全体と連携し、次のステージ、ルーン、ペット周回、所持品整理をまとめて判断します。",
        "farm.title": "Farm Planner",
        "farm.subtitle": "狙いたい対象を検索し、箱、ステージ、敵出現、ペット解放条件、マーケット導線をまとめて確認します。",
        "farm.search": "対象検索",
        "farm.placeholder": "アイテム名、ペット名、敵名、ステージ名、ID",
        "farm.targetType": "対象",
        "farm.allTargets": "すべて",
        "farm.items": "アイテム",
        "farm.pets": "ペット",
        "farm.monsters": "敵",
        "farm.stages": "ステージ",
        "farm.results": "候補",
        "farm.selected": "選択中",
        "farm.bestSources": "主な入手先",
        "farm.recommendedStages": "おすすめ周回ステージ",
        "farm.petTargets": "ペット解放対象",
        "farm.stageRewards": "ステージ報酬",
        "farm.openMarket": "相場を見る",
        "farm.openDetail": "詳細ページ",
        "farm.routeCount": "関連ルート",
        "farm.expected": "期待値",
        "farm.noSelection": "左の候補から対象を選択してください。",
        "farm.sourceHint": "出現率や箱の中身は生成済み関連データから推定しています。",
        "plan.title": "Progress Planner",
        "plan.subtitle": "セーブをローカルで読み込み、現在の進行度から次に見るべきステージ、ルーン予算、未解放ペット、所持品候補を整理します。",
        "plan.loadHint": "この画面でもセーブを読み込めます。ファイルはアップロードされません。",
        "plan.overview": "進行サマリー",
        "plan.campaign": "ステージ計画",
        "plan.current": "現在",
        "plan.best": "最高到達",
        "plan.next": "次候補",
        "plan.nextStage": "次のステージ",
        "plan.noNextStage": "次のステージ候補はありません。",
        "plan.openStages": "ステージで開く",
        "plan.runeBudget": "ルーン予算",
        "plan.affordableRunes": "今買えるルーン",
        "plan.affordableCount": "購入可能",
        "plan.noAffordableRunes": "現在のゴールドで購入できる次レベル候補はありません。",
        "plan.petHunts": "未解放ペット周回",
        "plan.inventoryActions": "所持品アクション",
        "plan.staticMode": "セーブ未読込のため、wiki生成データから汎用候補を表示しています。",
        "plan.loadSave": "セーブを読み込む",
        "plan.marketableOwned": "取引候補",
        "plan.openFarm": "Farm Plannerで開く",
        "plan.openSave": "マイセーブで開く",
        "plan.required": "必要数",
        "plan.stageReward": "主な報酬",
        "plan.runeNextCost": "次Lv費用",
        "plan.progress": "進行度",
        "save.currentWave": "現在Wave",
        "save.jumpCurrentStage": "現在位置へ",
        "save.jumpBestStage": "最高到達へ",
        "save.markerCurrent": "今",
        "save.markerBest": "最高",
        "save.markerCleared": "済",
        "save.applyRunes": "セーブ反映",
        "save.runeNodesActive": "有効ノード",
        "save.runeLevels": "ルーンLv",
        "save.remainingRuneCost": "残り必要ゴールド",
        "save.goldAfterMax": "最大化後ゴールド",
        "save.nextGoals": "次の攻略メモ",
        "save.progressLinks": "進行リンク",
        "save.runeProgress": "ルーン進行度",
        "save.spentRuneCost": "使用済みゴールド",
        "save.openRunePlanner": "ルーンツリーで調整",
        "save.petGoals": "未解放ペット目標",
        "save.noPetGoals": "未解放ペット目標はありません。",
        "category.lab-status.title": "Lab Status",
        "category.lab-status.description": "生成済みJSON、データ鮮度、関連データ、Cloudflare Pages公開準備を確認するTBH Labの運用画面です。",
        "lab.title": "TBH Lab Status",
        "lab.subtitle": "公開中のwikiがどの生成データで動いているか、どの連携が有効かを確認します。",
        "lab.generated": "生成日時",
        "lab.generatedLocal": "ローカル時刻",
        "lab.categories": "カテゴリ",
        "lab.entries": "掲載項目",
        "lab.locales": "言語",
        "lab.datasets": "生成データ",
        "lab.relationships": "関連データ",
        "lab.market": "マーケット連携",
        "lab.saveSchema": "セーブ読込スキーマ",
        "lab.cloudflare": "Cloudflare準備",
        "lab.runes": "ルーンツリー",
        "lab.stages": "ステージアトラス",
        "lab.ok": "有効",
        "lab.pending": "確認待ち",
        "lab.filesReady": "生成JSON配置済み",
        "lab.functionsReady": "Pages Functions想定",
        "lab.staticBuildReady": "静的ビルド対応",
        "lab.localOnlySave": "セーブはブラウザ内のみ",
        "lab.sourceFiles": "ソースファイル",
        "lab.openData": "データを開く",
        "lab.lastBuildNote": "Cloudflareではローカル解析を再実行せず、GitHubに含めた generated JSON からビルドします。",
        "lab.relationshipSummary": "アイテム、箱、敵、ペット、ステージ間の参照を結合済みです。",
        "lab.marketSummary": "同一オリジンの /api/market 経由で短時間キャッシュします。",
    }
)
TRANSLATIONS["en"].update(
    {
        "app.title": "TBH Lab",
        "app.subtitle": "Generated TaskbarHero data laboratory",
        "home.title": "TBH Lab",
        "home.kicker": "TaskbarHero data laboratory",
        "category.farm-planner.title": "Farm Planner",
        "category.farm-planner.description": "Search items, pets, monsters, and stages to find sources and recommended farms.",
        "category.progress-planner.title": "Progress Planner",
        "category.progress-planner.description": "Connect a local save to the whole wiki and decide the next stage, rune spending, pet hunts, and inventory actions.",
        "farm.title": "Farm Planner",
        "farm.subtitle": "Search a target and inspect chests, stages, monster appearances, pet unlock routes, and market links in one place.",
        "farm.search": "Target search",
        "farm.placeholder": "Item, pet, monster, stage, or ID",
        "farm.targetType": "Target",
        "farm.allTargets": "All",
        "farm.items": "Items",
        "farm.pets": "Pets",
        "farm.monsters": "Monsters",
        "farm.stages": "Stages",
        "farm.results": "Candidates",
        "farm.selected": "Selected",
        "farm.bestSources": "Best sources",
        "farm.recommendedStages": "Recommended stages",
        "farm.petTargets": "Pet targets",
        "farm.stageRewards": "Stage rewards",
        "farm.openMarket": "Open market",
        "farm.openDetail": "Open detail",
        "farm.routeCount": "Routes",
        "farm.expected": "Expected",
        "farm.noSelection": "Pick a target from the candidate list.",
        "farm.sourceHint": "Rates and routes are estimated from generated relationship data.",
        "plan.title": "Progress Planner",
        "plan.subtitle": "Load a save locally and turn current progress into stage, rune, pet, and inventory priorities.",
        "plan.loadHint": "You can load a save here too. The file is never uploaded.",
        "plan.overview": "Progress summary",
        "plan.campaign": "Stage plan",
        "plan.current": "Current",
        "plan.best": "Best",
        "plan.next": "Next",
        "plan.nextStage": "Next stage",
        "plan.noNextStage": "No next stage candidate is available.",
        "plan.openStages": "Open stages",
        "plan.runeBudget": "Rune budget",
        "plan.affordableRunes": "Affordable runes",
        "plan.affordableCount": "Affordable",
        "plan.noAffordableRunes": "No next-level rune candidate is affordable with current gold.",
        "plan.petHunts": "Locked pet hunts",
        "plan.inventoryActions": "Inventory actions",
        "plan.staticMode": "No save is loaded, so generic candidates from generated wiki data are shown.",
        "plan.loadSave": "Load save",
        "plan.marketableOwned": "Tradable candidates",
        "plan.openFarm": "Open in Farm Planner",
        "plan.openSave": "Open My Save",
        "plan.required": "Required",
        "plan.stageReward": "Main reward",
        "plan.runeNextCost": "Next Lv cost",
        "plan.progress": "Progress",
        "save.currentWave": "Current wave",
        "save.jumpCurrentStage": "Go to current",
        "save.jumpBestStage": "Go to best",
        "save.markerCurrent": "NOW",
        "save.markerBest": "BEST",
        "save.markerCleared": "CLEAR",
        "save.applyRunes": "Apply save",
        "save.runeNodesActive": "Active nodes",
        "save.runeLevels": "Rune levels",
        "save.remainingRuneCost": "Remaining gold",
        "save.goldAfterMax": "Gold after max",
        "save.nextGoals": "Next goals",
        "save.progressLinks": "Progress links",
        "save.runeProgress": "Rune progress",
        "save.spentRuneCost": "Spent gold",
        "save.openRunePlanner": "Tune in rune tree",
        "save.petGoals": "Locked pet goals",
        "save.noPetGoals": "No locked pet goals remain.",
        "category.lab-status.title": "Lab Status",
        "category.lab-status.description": "Inspect generated JSON, data freshness, relationship coverage, and Cloudflare Pages readiness.",
        "lab.title": "TBH Lab Status",
        "lab.subtitle": "Check which generated data powers the public wiki and which integrations are active.",
        "lab.generated": "Generated at",
        "lab.generatedLocal": "Local time",
        "lab.categories": "Categories",
        "lab.entries": "Entries",
        "lab.locales": "Languages",
        "lab.datasets": "Generated data",
        "lab.relationships": "Relationships",
        "lab.market": "Market integration",
        "lab.saveSchema": "Save reader schema",
        "lab.cloudflare": "Cloudflare readiness",
        "lab.runes": "Rune tree",
        "lab.stages": "Stage atlas",
        "lab.ok": "Ready",
        "lab.pending": "Check",
        "lab.filesReady": "Generated JSON committed",
        "lab.functionsReady": "Pages Functions expected",
        "lab.staticBuildReady": "Static build ready",
        "lab.localOnlySave": "Save parsing stays local",
        "lab.sourceFiles": "Source files",
        "lab.openData": "Open data",
        "lab.lastBuildNote": "On Cloudflare, the local extraction pipeline is not rerun; the site builds from committed generated JSON.",
        "lab.relationshipSummary": "Items, chests, monsters, pets, and stages are joined into cross-reference data.",
        "lab.marketSummary": "Market requests go through the same-origin /api/market cache.",
    }
)


def reset_output() -> None:
    if PUBLIC_GENERATED.exists():
        shutil.rmtree(PUBLIC_GENERATED)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    CATEGORIES_DIR.mkdir(parents=True, exist_ok=True)
    DETAILS_DIR.mkdir(parents=True, exist_ok=True)
    LOCALES_DIR.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_data(name: str) -> Any:
    return load_json(WIKI_DATA / f"{name}.json")


def load_table(name: str) -> list[dict[str, Any]]:
    return load_json(TABLES / f"{name}.json")


_MONO_CACHE: dict[str, Any] | None = None


def load_mono() -> dict[str, Any]:
    global _MONO_CACHE
    if _MONO_CACHE is None:
        path = WIKI_DATA / "mono_localization.json"
        _MONO_CACHE = load_json(path) if path.exists() else {}
    return _MONO_CACHE


def slugify(value: Any) -> str:
    text = str(value)
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", text)
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return slug or "entry"


def humanize(value: Any) -> str:
    if value is None:
        return "-"
    text = str(value)
    if "_" in text:
        text = text.split("_", 1)[1] if text.startswith(("RuneName_", "SkillName_", "Passive_", "MonsterName_", "PetName_")) else text
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    text = text.replace("_", " ").replace("-", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text or "-"


def skill_display_name(skill: dict[str, Any], class_name: str | None = None) -> str:
    skill_key = int(skill.get("SkillKey") or 0)
    resolved_class = class_name or CLASS_BY_SKILL_PREFIX.get(skill_key // 10000, "Hero")
    if skill.get("SLOTTYPE") == "BASEATTACK" or not skill.get("SkillNameKey"):
        return f"{resolved_class} Base Attack"
    skill_number = (skill_key % 10000) // 100
    if skill_number > 0:
        return f"{resolved_class} Skill {skill_number}"
    return humanize(skill.get("SkillNameKey"))


def hero_class_text(class_name: str | None) -> dict[str, str]:
    key = HERO_KEY_BY_CLASS.get(class_name or "")
    return mono_text(f"HeroName_{key}", class_name or "Hero") if key else localized(class_name or "Hero")


def skill_title(skill: dict[str, Any], class_name: str | None = None) -> dict[str, str]:
    resolved_class = class_name or CLASS_BY_SKILL_PREFIX.get(int(skill.get("SkillKey") or 0) // 10000, "Hero")
    if skill.get("SLOTTYPE") == "BASEATTACK" or not skill.get("SkillNameKey"):
        hero = hero_class_text(resolved_class)
        return localized(f"{hero['en']} Base Attack", f"{hero['ja']} 通常攻撃")
    return mono_text(skill.get("SkillNameKey"), skill_display_name(skill, resolved_class))


def compact(value: Any) -> str:
    if value is None or value == "":
        return "-"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def localized(en: Any, ja: Any | None = None) -> dict[str, str]:
    en_text = compact(en)
    return {"ja": compact(ja if ja is not None else en_text), "en": en_text}


def localized_value(value: Any, fallback: Any = None) -> dict[str, str]:
    if isinstance(value, dict):
        en = value.get("en") or value.get("en-US") or fallback
        ja = value.get("ja") or value.get("ja-JP") or en or fallback
        return localized(en, ja)
    return localized(value if value not in (None, "") else fallback)


def mono_text(key: Any, fallback: Any = None) -> dict[str, str]:
    if key in (None, ""):
        return localized_value(fallback)
    values = load_mono().get("string_table", {}).get("by_key", {}).get(str(key), {})
    return localized_value(values, fallback if fallback is not None else humanize(key))


def mono_enum(prefix: str, value: Any) -> dict[str, str]:
    if value in (None, ""):
        return localized("-")
    return mono_text(f"{prefix}_{value}", humanize(value))


ENUM_FALLBACKS: dict[str, dict[str, str]] = {
    "MAIN_WEAPON": {"en": "Main Weapon", "ja": "メイン武器"},
    "SUB_WEAPON": {"en": "Off-hand", "ja": "サブ武器"},
    "ACCESSORY": {"en": "Accessory", "ja": "アクセサリー"},
    "ARMOR": {"en": "Armor", "ja": "防具"},
    "WEAPON": {"en": "Weapon", "ja": "武器"},
    "COMMON": {"en": "Common", "ja": "コモン"},
    "BASEATTACK": {"en": "Base Attack", "ja": "通常攻撃"},
    "BASEATTACK_COUNT": {"en": "Base Attack Count", "ja": "通常攻撃回数"},
    "COOLDOWN": {"en": "Cooldown", "ja": "クールダウン"},
    "CONTINUOUS": {"en": "Continuous", "ja": "継続"},
    "SKILL": {"en": "Skill", "ja": "スキル"},
    "Passive": {"en": "Passive", "ja": "パッシブ"},
    "Active": {"en": "Active", "ja": "アクティブ"},
    "FLAT": {"en": "Flat", "ja": "固定値"},
    "ADDITIVE": {"en": "Increased", "ja": "増加"},
    "Physical": {"en": "Physical", "ja": "物理"},
    "Fire": {"en": "Fire", "ja": "火炎"},
    "Cold": {"en": "Cold", "ja": "冷気"},
    "Lightning": {"en": "Lightning", "ja": "雷"},
    "Chaos": {"en": "Chaos", "ja": "混沌"},
    "Melee": {"en": "Melee", "ja": "近接"},
    "Projectile": {"en": "Projectile", "ja": "投射物"},
    "AOE": {"en": "Area", "ja": "範囲"},
    "Summon": {"en": "Summon", "ja": "召喚"},
    "Trap": {"en": "Trap", "ja": "罠"},
    "DLC": {"en": "DLC", "ja": "DLC"},
    "MONSTER": {"en": "Monster", "ja": "モンスター"},
}


def enum_text(value: Any, *prefixes: str) -> dict[str, str]:
    if value in (None, ""):
        return localized("-")
    text = str(value)
    by_key = load_mono().get("string_table", {}).get("by_key", {})
    candidate_keys = [f"{prefix}_{text}" for prefix in prefixes] + [text]
    for key in candidate_keys:
        if key in by_key:
            return mono_text(key, humanize(text))
    if text in ENUM_FALLBACKS:
        return localized_value(ENUM_FALLBACKS[text], humanize(text))
    if "," in text:
        return join_localized([enum_text(part.strip(), *prefixes) for part in text.split(",")], ", ")
    return localized(humanize(text))


def stat_name(stat_type: Any) -> dict[str, str]:
    if stat_type in (None, ""):
        return localized("-")
    stat = str(stat_type)
    for prefix in ("AccountStatName", "StatName", "ShortStatName", "RuneName", "Passive"):
        values = load_mono().get("string_table", {}).get("by_key", {}).get(f"{prefix}_{stat}")
        if values:
            return localized_value(values, humanize(stat))
    return localized(humanize(stat))


def apply_template(template: dict[str, str], *values: Any) -> dict[str, str]:
    result: dict[str, str] = {}
    for locale, text in template.items():
        formatted = text
        for index, value in enumerate(values):
            formatted = formatted.replace("{" + str(index) + "}", compact(value))
        result[locale] = formatted
    return result


def stat_effect_text(stat_type: Any, value: Any, mod_type: Any = None, max_value: Any = None) -> dict[str, str]:
    if stat_type in (None, ""):
        return localized("-")
    stat = str(stat_type)
    mod = str(mod_type) if mod_type not in (None, "") else None
    by_key = load_mono().get("string_table", {}).get("by_key", {})
    keys: list[str] = []
    if mod and max_value not in (None, ""):
        keys.append(f"Stat_{stat}_{mod}_MinMax")
    if mod:
        keys.append(f"Stat_{stat}_{mod}")
    keys.append(f"AccountStat_{stat}")
    for key in keys:
        if key in by_key:
            return apply_template(localized_value(by_key[key], humanize(stat)), value, max_value)
    label = stat_name(stat)
    if max_value not in (None, ""):
        return localized(f"{label['en']} {value}-{max_value}", f"{label['ja']} {value}-{max_value}")
    return localized(f"{label['en']} +{value}", f"{label['ja']} +{value}")


def currency_name(currency_key: Any) -> dict[str, str]:
    if currency_key in (None, ""):
        return localized("-")
    return mono_text(f"CurrencyName_{currency_key}", "Gold" if str(currency_key) == "100001" else currency_key)


def join_localized(parts: list[dict[str, str]], separator: str = " / ") -> dict[str, str]:
    return {
        "en": separator.join(part.get("en", "") for part in parts if part.get("en")),
        "ja": separator.join(part.get("ja", "") for part in parts if part.get("ja")),
    }


def metric(label_key: str, value: Any) -> dict[str, str]:
    return {"labelKey": label_key, "value": compact(value)}


def raw_rows(row: dict[str, Any], skip: set[str] | None = None) -> list[list[str]]:
    ignored = skip or set()
    return [[key, compact(value)] for key, value in row.items() if key not in ignored and value is not None]


def copy_assets() -> dict[str, str]:
    index: dict[str, str] = {}
    for dirname in ["hero", "item", "map", "runes", "skills", "UI"]:
        source = RESOURCE_IMAGE / dirname
        if not source.exists():
            continue
        destination = ASSETS_DIR / "game" / dirname.lower()
        shutil.copytree(source, destination, dirs_exist_ok=True)
        for file in destination.rglob("*"):
            if file.is_file():
                url = "/" + file.relative_to(PUBLIC_GENERATED.parent).as_posix()
                index[file.stem.lower()] = url
                index[file.name.lower()] = url
    return index


def asset(index: dict[str, str], key: Any, fallback: str | None = None) -> str | None:
    if not key:
        return fallback
    text = Path(str(key)).name
    candidates = [text, f"{text}.png"]
    for candidate in candidates:
        found = index.get(candidate.lower())
        if found:
            return found
        found = index.get(Path(candidate).stem.lower())
        if found:
            return found
    return fallback


def category_definition(category_id: str, count: int, icon: str | None, layout: str, nav_group: str) -> dict[str, Any]:
    return {
        "id": category_id,
        "titleKey": f"category.{category_id}.title",
        "descriptionKey": f"category.{category_id}.description",
        "count": count,
        "icon": icon,
        "layout": layout,
        "navGroup": nav_group,
        "listPath": f"/generated/categories/{category_id}.json",
    }


def entry(
    category_id: str,
    entity_id: Any,
    title: dict[str, str],
    subtitle: dict[str, str] | None = None,
    icon: str | None = None,
    rarity: str | None = None,
    tags: list[str] | None = None,
    fields: dict[str, Any] | None = None,
    field_display: dict[str, dict[str, str]] | None = None,
    slug: str | None = None,
    tooltip: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_slug = slug or f"{entity_id}-{slugify(title.get('en') or title.get('ja') or entity_id)}"
    return {
        "categoryId": category_id,
        "entityId": compact(entity_id),
        "slug": resolved_slug,
        "title": title,
        "subtitle": subtitle or localized(""),
        "icon": icon,
        "rarity": rarity,
        "tags": [compact(tag) for tag in tags or [] if tag is not None and compact(tag) != "-"],
        "fields": {key: compact(value) for key, value in (fields or {}).items()},
        "fieldDisplay": field_display or {},
        "detailPath": f"/generated/details/{category_id}/{resolved_slug}.json",
        "tooltip": tooltip,
    }


def write_detail(category_id: str, item: dict[str, Any], detail: dict[str, Any]) -> None:
    payload = {
        "categoryId": category_id,
        "entityId": item["entityId"],
        "slug": item["slug"],
        "title": item["title"],
        "subtitle": item["subtitle"],
        "icon": item["icon"],
        "rarity": item.get("rarity"),
        "tags": item.get("tags", []),
        **detail,
    }
    write_json(DETAILS_DIR / category_id / f"{item['slug']}.json", payload)


def write_category(
    category: dict[str, Any],
    entries: list[dict[str, Any]],
    columns: list[dict[str, str]],
    filters: list[dict[str, Any]] | None = None,
) -> None:
    write_json(
        CATEGORIES_DIR / f"{category['id']}.json",
        {
            "category": category,
            "columns": columns,
            "filters": filters or [],
            "entries": entries,
        },
    )


def facet(entries: list[dict[str, Any]], field: str, label_key: str, limit: int = 40) -> dict[str, Any]:
    values = sorted({entry["fields"].get(field) for entry in entries if entry["fields"].get(field) not in (None, "", "-")})
    if field == "grade":
        order = {grade: index for index, grade in enumerate(GRADE_ORDER)}
        values = sorted(values, key=lambda value: order.get(value, 999))
    return {"id": field, "labelKey": label_key, "options": values[:limit]}


def item_title(item: dict[str, Any]) -> dict[str, str]:
    return localized_value(item.get("localized_name"), humanize(item.get("display_name") or item.get("NameKey") or item.get("ItemKey")))


def item_icon(item: dict[str, Any], assets: dict[str, str]) -> str | None:
    return asset(assets, item.get("IconPath")) or asset(assets, f"Item_{item.get('ItemKey')}")


def tooltip_row(
    label: dict[str, str] | None = None,
    value: dict[str, str] | str | int | float | None = None,
    label_key: str | None = None,
    tone: str | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {"value": localized_value(value)}
    if label_key:
        row["labelKey"] = label_key
    elif label:
        row["label"] = label
    if tone:
        row["tone"] = tone
    return row


def tooltip_section(title_key: str, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    filtered = [row for row in rows if (row.get("value") or {}).get("en") not in ("", "-")]
    if not filtered:
        return None
    return {"titleKey": title_key, "rows": filtered}


def number_text(value: Any) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return compact(value)
    if numeric.is_integer():
        return str(int(numeric))
    return f"{numeric:g}"


def stat_amount(value: Any, percent: bool) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return compact(value)
    if percent and abs(numeric) >= 100:
        numeric /= 100.0
    if numeric.is_integer():
        return str(int(numeric))
    return f"{numeric:.2f}".rstrip("0").rstrip(".")


def stat_range(min_value: Any, max_value: Any, percent: bool) -> str:
    if max_value in (None, "", min_value):
        return stat_amount(min_value, percent)
    return f"{stat_amount(min_value, percent)}-{stat_amount(max_value, percent)}"


def stat_template(stat: Any, mod: Any) -> dict[str, str]:
    if stat in (None, "", "NONE"):
        return localized("-")
    key = f"Stat_{stat}_{mod or 'FLAT'}"
    values = load_mono().get("string_table", {}).get("by_key", {}).get(key)
    if values:
        return localized_value(values)
    return mono_text(f"StatName_{stat}", humanize(stat))


def stat_line(stat: Any, mod: Any, min_value: Any, max_value: Any = None) -> dict[str, str]:
    template = stat_template(stat, mod)
    percent = "%" in template.get("en", "") or "%" in template.get("ja", "") or "Percent" in str(stat)
    amount = stat_range(min_value, max_value, percent)
    result: dict[str, str] = {}
    for locale in ("en", "ja"):
        text = template.get(locale) or template.get("en") or humanize(stat)
        if "{0}" in text:
            result[locale] = text.replace("{0}", amount)
        else:
            sign = "+" if str(amount).strip() and not str(amount).startswith("-") else ""
            result[locale] = f"{text} {sign}{amount}".strip()
    return result


def gear_group_label(group: Any) -> dict[str, str]:
    labels = {
        "WEAPON": localized("Weapon", "武器"),
        "ARMOR": localized("Armor", "防具"),
        "ACCESSORY": localized("Accessory", "アクセサリー"),
    }
    return labels.get(str(group), localized(humanize(group)))


def material_type_label(value: Any) -> dict[str, str]:
    labels = {
        "CRAFTING": localized("Crafting material", "クラフト素材"),
        "DECORATION": localized("Decoration material", "装飾素材"),
        "ENGRAVING": localized("Engraving material", "刻印素材"),
        "INSCRIPTION": localized("Inscription material", "刻文素材"),
        "OFFERING": localized("Offering material", "奉納素材"),
        "SOULSTONE": localized("Soulstone", "ソウルストーン"),
    }
    return labels.get(str(value), localized(humanize(value)))


def item_subtitle(item: dict[str, Any]) -> dict[str, str]:
    parts = [mono_enum("Grade", item.get("GRADE"))]
    if item.get("GEARTYPE"):
        parts.append(mono_enum("GearType", item.get("GEARTYPE")))
    elif (item.get("material") or {}).get("MATERIALTYPE"):
        parts.append(material_type_label((item.get("material") or {}).get("MATERIALTYPE")))
    elif item.get("ITEMTYPE"):
        parts.append(mono_enum("ItemType", item.get("ITEMTYPE")))
    if item.get("PARTS"):
        parts.append(mono_enum("ItemParts", item.get("PARTS")))
    if item.get("Level"):
        parts.append(localized(f"Lv. {item.get('Level')}", f"Lv. {item.get('Level')}"))
    return join_localized(parts)


def item_trade_text(item: dict[str, Any]) -> dict[str, str]:
    if item.get("IsCanExchangeMarketable") is True:
        return {"en": "Tradeable", "ja": "取引可能"}
    return {"en": "Not tradeable", "ja": "取引不可"}


def item_field_display(item: dict[str, Any]) -> dict[str, dict[str, str]]:
    display: dict[str, dict[str, str]] = {}
    if item.get("GRADE"):
        display["grade"] = mono_enum("Grade", item.get("GRADE"))
    if item.get("ITEMTYPE"):
        display["type"] = mono_enum("ItemType", item.get("ITEMTYPE"))
    if item.get("GEARTYPE"):
        display["gearType"] = mono_enum("GearType", item.get("GEARTYPE"))
    elif (item.get("material") or {}).get("MATERIALTYPE"):
        display["gearType"] = material_type_label((item.get("material") or {}).get("MATERIALTYPE"))
    if item.get("PARTS"):
        display["part"] = mono_enum("ItemParts", item.get("PARTS"))
    return display


def item_tooltip(item: dict[str, Any], icon: str | None) -> dict[str, Any]:
    sections: list[dict[str, Any]] = []
    gear = item.get("gear") or {}
    material_groups = item.get("material_stat_group") or []
    rows = [
        tooltip_row(label_key="field.grade", value=mono_enum("Grade", item.get("GRADE")), tone="rarity"),
        tooltip_row(label_key="field.type", value=mono_enum("ItemType", item.get("ITEMTYPE"))),
    ]
    if item.get("Level"):
        rows.append(tooltip_row(label_key="tooltip.requiredLevel", value=f"Lv. {item.get('Level')}"))
    rows.append(tooltip_row(label_key="tooltip.trade", value=item_trade_text(item)))

    if gear:
        base_rows = []
        if gear.get("BaseStat1_Value") not in (None, ""):
            base_rows.append(tooltip_row(label_key="field.attackDamage", value=number_text(gear.get("BaseStat1_Value")), tone="primary"))
        if gear.get("BaseStat2_Value") not in (None, ""):
            base_rows.append(tooltip_row(label_key="field.attackSpeed", value=f"{(float(gear.get('BaseStat2_Value') or 0) / 100):.2f}", tone="primary"))
        base_section = tooltip_section("tooltip.baseStats", base_rows)
        if base_section:
            sections.append(base_section)

        inherent_rows = []
        for index in range(1, 4):
            stat = gear.get(f"InherentStat{index}_STATTYPE")
            if stat and stat != "NONE":
                inherent_rows.append(
                    tooltip_row(
                        label=mono_text(f"StatName_{stat}", humanize(stat)),
                        value=stat_line(stat, gear.get(f"InherentStat{index}_MODTYPE"), gear.get(f"InherentStat{index}_Value")),
                        tone="magic",
                    )
                )
        inherent_section = tooltip_section("tooltip.inherentStats", inherent_rows)
        if inherent_section:
            sections.append(inherent_section)

        slot_rows = [
            tooltip_row(value=localized("Decoration slot", "装飾スロット")),
            tooltip_row(value=localized("Engraving slot", "刻印スロット")),
            tooltip_row(value=localized("Inscription slot", "刻文スロット")),
        ]
        slot_section = tooltip_section("tooltip.slots", slot_rows)
        if slot_section:
            sections.append(slot_section)

    if material_groups:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for group in material_groups:
            grouped[str(group.get("GearGroup") or "OTHER")].append(group)
        section_titles = {
            "WEAPON": "tooltip.weaponEffects",
            "ARMOR": "tooltip.armorEffects",
            "ACCESSORY": "tooltip.accessoryEffects",
        }
        for group_name in ("WEAPON", "ARMOR", "ACCESSORY"):
            rows_for_group = []
            for group in grouped.get(group_name, [])[:6]:
                stat = group.get("stat_mod") or {}
                stat_type = stat.get("STATTYPE") or group.get("StatModKey")
                rows_for_group.append(
                    tooltip_row(
                        label=gear_group_label(group_name),
                        value=stat_line(stat_type, stat.get("MODTYPE"), stat.get("MinValue"), stat.get("MaxValue")),
                        tone="magic",
                    )
                )
            section = tooltip_section(section_titles[group_name], rows_for_group)
            if section:
                sections.append(section)

    description = localized_value(item.get("localized_description"))
    if gear and not item.get("DescriptionKey"):
        description = localized("")

    payload = {
        "title": item_title(item),
        "subtitle": item_subtitle(item),
        "icon": icon,
        "rarity": item.get("GRADE"),
        "rows": rows,
        "sections": sections,
    }
    if description.get("en") not in ("", "-") or description.get("ja") not in ("", "-"):
        payload["description"] = description
    return payload


def stage_title(stage: dict[str, Any]) -> dict[str, str]:
    difficulty = mono_enum("Difficulty", stage.get("STAGEDIFFICULITY"))
    return localized(
        f"{difficulty.get('en')} {stage.get('Act')}-{stage.get('StageNo')}",
        f"{difficulty.get('ja')} {stage.get('Act')}-{stage.get('StageNo')}",
    )


def monster_title(monster: dict[str, Any] | None, fallback: Any = None) -> dict[str, str]:
    monster = monster or {}
    return mono_text(monster.get("MonsterNameStringKey"), fallback or humanize(monster.get("MonsterNameStringKey") or monster.get("MonsterKey")))


def build_stage_chest_index(stages: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    output: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for stage in stages:
        for kind, label in (("monster_drop_item", "Monster box"), ("boss_drop_item", "Boss box")):
            item_key = (stage.get(kind) or {}).get("item_key")
            if item_key is None:
                continue
            output[int(item_key)].append(
                {
                    "stage": stage,
                    "kind": label,
                    "rate": (stage.get(kind) or {}).get("rate"),
                }
            )
    return output


def build_item_source_index(items: list[dict[str, Any]], stages: list[dict[str, Any]], drops_by_key: dict[str, Any]) -> dict[int, list[dict[str, Any]]]:
    items_by_key = {int(item["ItemKey"]): item for item in items if item.get("ItemKey") is not None}
    chests_by_drop: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        if item.get("DropKey") is not None:
            chests_by_drop[str(item.get("DropKey"))].append(item)
    stage_chests = build_stage_chest_index(stages)
    sources: dict[int, list[dict[str, Any]]] = defaultdict(list)

    for drop_key, drop in drops_by_key.items():
        for drop_entry in drop.get("entries", []):
            targets: list[int] = []
            if drop_entry.get("reward_type") == "ITEM" and drop_entry.get("reward_key") is not None:
                targets.append(int(drop_entry["reward_key"]))
            elif drop_entry.get("reward_type") == "ITEMGROUP":
                resolved = drop_entry.get("resolved") or {}
                for preview in resolved.get("items_preview", []):
                    if preview.get("item_key") is not None:
                        targets.append(int(preview["item_key"]))
            if not targets:
                continue

            containers = chests_by_drop.get(str(drop_key), [])
            for target in targets:
                for chest in containers or [None]:
                    stage_hits = stage_chests.get(int(chest["ItemKey"]), []) if chest else []
                    if stage_hits:
                        for hit in stage_hits[:6]:
                            sources[target].append(
                                {
                                    "drop_key": drop_key,
                                    "chest": chest,
                                    "stage": hit.get("stage"),
                                    "stage_rate": hit.get("rate"),
                                    "chance": drop_entry.get("weight_percent"),
                                    "source_type": hit.get("kind"),
                                }
                            )
                    else:
                        sources[target].append(
                            {
                                "drop_key": drop_key,
                                "chest": chest,
                                "stage": None,
                                "stage_rate": None,
                                "chance": drop_entry.get("weight_percent"),
                                "source_type": "Drop table",
                            }
                        )

    for item_key in list(sources):
        deduped = []
        seen = set()
        for source in sources[item_key]:
            chest = source.get("chest") or {}
            stage = source.get("stage") or {}
            marker = (chest.get("ItemKey"), stage.get("StageKey"), source.get("drop_key"), source.get("chance"))
            if marker in seen:
                continue
            seen.add(marker)
            if item_key in items_by_key:
                deduped.append(source)
        deduped.sort(
            key=lambda source: (
                source.get("stage") is None,
                source.get("chest") is None,
                -(source.get("chance") or 0),
            )
        )
        sources[item_key] = deduped[:24]
    return sources


def item_source_rows(sources: list[dict[str, Any]]) -> list[list[Any]]:
    def rate_text(value: Any) -> str:
        if value in (None, ""):
            return "-"
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return compact(value)
        if numeric > 100:
            numeric /= 10
        return f"{numeric:g}%"

    rows: list[list[Any]] = []
    for source in sources[:16]:
        chest = source.get("chest") or {}
        stage = source.get("stage") or {}
        rows.append(
            [
                item_title(chest) if chest else localized(f"DropKey {source.get('drop_key')}", f"DropKey {source.get('drop_key')}"),
                f"{source.get('chance'):.4g}%" if isinstance(source.get("chance"), (int, float)) else source.get("chance"),
                stage_title(stage) if stage else localized("-"),
                rate_text(source.get("stage_rate")),
            ]
        )
    return rows


def item_detail_sections(item: dict[str, Any], drops_by_key: dict[str, Any], sources_by_item: dict[int, list[dict[str, Any]]] | None = None) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    source_rows = item_source_rows((sources_by_item or {}).get(int(item.get("ItemKey") or 0), []))
    if source_rows:
        sections.append(
            {
                "titleKey": "detail.section.sources",
                "type": "table",
                "columns": [
                    {"labelKey": "field.chest"},
                    {"labelKey": "field.percent"},
                    {"labelKey": "field.stage"},
                    {"labelKey": "field.drop"},
                ],
                "rows": source_rows,
            }
        )
    gear = item.get("gear") or {}
    if gear:
        stats = [
            metric("field.attackDamage", gear.get("BaseStat1_Value")),
            metric("field.attackSpeed", gear.get("BaseStat2_Value")),
        ]
        for i in range(1, 4):
            stat = gear.get(f"InherentStat{i}_STATTYPE")
            if stat and stat != "NONE":
                stats.append(metric(f"{stat} / {gear.get(f'InherentStat{i}_MODTYPE')}", gear.get(f"InherentStat{i}_Value")))
        sections.append({"titleKey": "detail.section.gearStats", "type": "stats", "items": stats})
    unique = item.get("unique_mod") or {}
    if unique:
        sections.append(
            {
                "titleKey": "detail.section.unique",
                "type": "table",
                "columns": [{"labelKey": "field.name"}, {"labelKey": "field.type"}, {"labelKey": "field.value"}],
                "rows": raw_rows(unique),
            }
        )
    material_groups = item.get("material_stat_group") or []
    if material_groups:
        rows = []
        for group in material_groups[:80]:
            stat = group.get("stat_mod") or {}
            rows.append(
                [
                    enum_text(group.get("GearGroup"), "GearType", "ItemParts", "Grade"),
                    stat_name(stat.get("STATTYPE") or group.get("StatModKey")),
                    enum_text(stat.get("MODTYPE")),
                    stat_effect_text(stat.get("STATTYPE"), stat.get("MinValue"), stat.get("MODTYPE"), stat.get("MaxValue")),
                    f"T{group.get('MinTier', '-')} - T{group.get('MaxTier', '-')}",
                ]
            )
        sections.append(
            {
                "titleKey": "detail.section.materialPool",
                "type": "table",
                "columns": [
                    {"labelKey": "field.gearType"},
                    {"labelKey": "field.name"},
                    {"labelKey": "field.type"},
                    {"labelKey": "field.value"},
                    {"labelKey": "field.tier"},
                ],
                "rows": rows,
            }
        )
    drop_key = item.get("DropKey")
    drop = drops_by_key.get(str(drop_key)) if drop_key else None
    if drop:
        rows = []
        for drop_entry in drop.get("entries", [])[:80]:
            resolved = drop_entry.get("resolved") or {}
            rows.append(
                [
                    drop_entry.get("reward_type"),
                    resolved.get("name") or resolved.get("group_name") or drop_entry.get("reward_key"),
                    drop_entry.get("weight"),
                    drop_entry.get("weight_percent"),
                ]
            )
        sections.append(
            {
                "titleKey": "detail.section.dropTable",
                "type": "table",
                "columns": [
                    {"labelKey": "field.type"},
                    {"labelKey": "field.name"},
                    {"labelKey": "field.weight"},
                    {"labelKey": "field.percent"},
                ],
                "rows": rows,
            }
        )
    sections.append(
        {
            "titleKey": "detail.section.raw",
            "type": "table",
            "columns": [{"labelKey": "field.name"}, {"labelKey": "field.value"}],
            "rows": raw_rows(item, {"drop_table", "gear", "unique_mod", "material", "material_stat_group", "item_groups"}),
        }
    )
    return sections


def build_items(assets: dict[str, str], drops_by_key: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    items = load_data("items")
    stages = load_data("stages")
    sources_by_item = build_item_source_index(items, stages, drops_by_key)
    gear_entries: list[dict[str, Any]] = []
    material_entries: list[dict[str, Any]] = []
    box_entries: list[dict[str, Any]] = []
    for item in items:
        category_id = {
            "GEAR": "gear",
            "MATERIAL": "materials",
            "STAGEBOX": "stage-boxes",
        }.get(item.get("ITEMTYPE"))
        if not category_id:
            continue
        fields = {
            "grade": item.get("GRADE"),
            "type": item.get("ITEMTYPE"),
            "gearType": item.get("GEARTYPE"),
            "part": item.get("PARTS"),
            "level": item.get("Level"),
            "dropKey": item.get("DropKey"),
            "steam": item.get("IsSteamItem"),
        }
        icon = item_icon(item, assets)
        row = entry(
            category_id,
            item["ItemKey"],
            item_title(item),
            item_subtitle(item),
            icon,
            item.get("GRADE"),
            [item.get("GRADE"), item.get("ITEMTYPE"), item.get("GEARTYPE"), item.get("PARTS")],
            fields,
            item_field_display(item),
            tooltip=item_tooltip(item, icon),
        )
        detail = {
            "heroImage": row["icon"],
            "overview": [
                metric("field.id", item.get("ItemKey")),
                metric("field.grade", item.get("GRADE")),
                metric("field.type", item.get("ITEMTYPE")),
                metric("field.gearType", item.get("GEARTYPE") or item.get("MATERIALTYPE") or "-"),
                metric("field.level", item.get("Level") or "-"),
            ],
            "sections": item_detail_sections(item, drops_by_key, sources_by_item),
            "source": {"table": "ItemInfoData"},
        }
        write_detail(category_id, row, detail)
        if category_id == "gear":
            gear_entries.append(row)
        elif category_id == "materials":
            material_entries.append(row)
        else:
            box_entries.append(row)
    categories = {
        "gear": category_definition("gear", len(gear_entries), asset(assets, "SWORD_300001"), "table", "nav.database"),
        "materials": category_definition("materials", len(material_entries), asset(assets, "Item_110001"), "table", "nav.database"),
        "stage-boxes": category_definition("stage-boxes", len(box_entries), asset(assets, "Item_910011"), "table", "nav.database"),
    }
    return categories, gear_entries, material_entries, box_entries


def build_effects(assets: dict[str, str]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    groups = load_table("StatModGroupInfoData")
    mods = {row["StatModKey"]: row for row in load_table("StatModInfoData")}
    material_groups = {row["StatModGroupKey"] for row in load_table("MaterialInfoData")}
    material_items_by_group: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for item in load_data("items"):
        group_key = ((item.get("material") or {}).get("StatModGroupKey"))
        if group_key:
            material_items_by_group[int(group_key)].append(item)
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in groups:
        if row.get("StatModGroupKey") in material_groups:
            grouped[row["StatModGroupKey"]].append(row)
    entries: list[dict[str, Any]] = []
    for group_key, rows in sorted(grouped.items()):
        stats = [mods.get(row.get("StatModKey"), {}) for row in rows]
        stat_names = sorted({stat.get("STATTYPE") for stat in stats if stat.get("STATTYPE")})
        gear_groups = sorted({row.get("GearGroup") for row in rows if row.get("GearGroup")})
        material_items = material_items_by_group.get(group_key, [])
        primary_material = material_items[0] if material_items else None
        base_title = item_title(primary_material) if primary_material else localized(f"Effect Group {group_key}", f"効果グループ {group_key}")
        title = localized(f"{base_title['en']} Effects", f"{base_title['ja']} 効果")
        localized_stats = [stat_name(stat) for stat in stat_names[:3]]
        subtitle = join_localized(localized_stats, ", ") if localized_stats else localized("Material effect pool", "素材効果プール")
        type_display = join_localized([stat_name(stat) for stat in stat_names[:4]], ", ")
        gear_display = join_localized([enum_text(group, "GearType", "ItemParts", "Grade") for group in gear_groups[:4]], ", ")
        row = entry(
            "effects",
            group_key,
            title,
            subtitle,
            item_icon(primary_material, assets) if primary_material else asset(assets, "Item_113001") or asset(assets, "Item_110001"),
            primary_material.get("GRADE") if primary_material else "ARCANA",
            stat_names + gear_groups,
            {"type": ", ".join(stat_names[:4]), "gearType": ", ".join(gear_groups[:4]), "count": len(rows)},
            {"type": type_display, "gearType": gear_display},
        )
        table_rows = []
        for group_row in rows:
            mod = mods.get(group_row.get("StatModKey"), {})
            table_rows.append(
                [
                    enum_text(group_row.get("GearGroup"), "GearType", "ItemParts", "Grade"),
                    group_row.get("StatModKey"),
                    stat_name(mod.get("STATTYPE")),
                    enum_text(mod.get("MODTYPE")),
                    stat_effect_text(mod.get("STATTYPE"), mod.get("MinValue"), mod.get("MODTYPE"), mod.get("MaxValue")),
                    f"T{group_row.get('MinTier', '-')} - T{group_row.get('MaxTier', '-')}",
                ]
            )
        write_detail(
            "effects",
            row,
            {
                "overview": [
                    metric("field.id", group_key),
                    metric("field.count", len(rows)),
                    {"labelKey": "field.gearType", "value": join_localized([enum_text(group, "GearType", "ItemParts", "Grade") for group in gear_groups], ", ")},
                    {"labelKey": "field.type", "value": join_localized([stat_name(stat) for stat in stat_names[:6]], ", ")},
                ],
                "sections": [
                    {
                        "titleKey": "detail.section.entries",
                        "type": "table",
                        "columns": [
                            {"labelKey": "field.gearType"},
                            {"labelKey": "field.id"},
                            {"labelKey": "field.name"},
                            {"labelKey": "field.type"},
                            {"labelKey": "field.value"},
                            {"labelKey": "field.tier"},
                        ],
                        "rows": table_rows,
                    }
                ],
                "source": {"table": "StatModGroupInfoData"},
            },
        )
        entries.append(row)
    category = category_definition("effects", len(entries), asset(assets, "Item_113001") or asset(assets, "Item_110001"), "table", "nav.database")
    return category, entries


def build_heroes(assets: dict[str, str]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    heroes = load_data("heroes")
    entries: list[dict[str, Any]] = []
    for hero in heroes:
        class_name = hero.get("ClassType") or hero.get("display_name")
        icon = asset(assets, f"Inventory_ChaIllust_{'Abalist' if class_name == 'Hunter' else class_name}_Mid_Anim_0")
        full_art = asset(assets, f"Arrage_ChaAnim_{'Abalist' if class_name == 'Hunter' else class_name}_Large_0", icon)
        row = entry(
            "heroes",
            hero["HeroKey"],
            localized_value(hero.get("localized_name"), class_name),
            localized_value(hero.get("localized_description"), HERO_FLAVOR.get(class_name, localized("Hero"))),
            icon,
            "DIVINE" if hero.get("dlc_required") else "LEGENDARY",
            [class_name, hero.get("MainWeaponGearType"), hero.get("SubWeaponGearType")],
            {
                "class": class_name,
                "mainWeapon": hero.get("MainWeaponGearType"),
                "subWeapon": hero.get("SubWeaponGearType"),
                "maxHp": hero.get("MaxHp"),
                "attackDamage": hero.get("AttackDamage"),
                "armor": hero.get("Armor"),
            },
            {
                "class": localized_value(hero.get("localized_name"), class_name),
                "mainWeapon": enum_text(hero.get("MainWeaponGearType"), "GearType"),
                "subWeapon": enum_text(hero.get("SubWeaponGearType"), "GearType"),
            },
            slug=slugify(class_name),
        )
        base_stats = [
            metric("field.maxHp", hero.get("MaxHp")),
            metric("field.armor", hero.get("Armor")),
            metric("field.attackDamage", hero.get("AttackDamage")),
            metric("field.attackSpeed", hero.get("AttackSpeed")),
            metric("field.castSpeed", f"{hero.get('CastSpeed')}%"),
            metric("field.criticalChance", f"{(hero.get('CriticalChance') or 0) / 10:g}%"),
            metric("field.criticalDamage", f"{(hero.get('CriticalDamage') or 0) / 10:g}%"),
            metric("field.cooldown", f"{hero.get('CooldownReduction')}%"),
            metric("field.moveSpeed", hero.get("MovementSpeed")),
        ]
        skill_rows = []
        for skill in hero.get("skills", []):
            skill_rows.append(
                [
                    skill_title(skill, class_name),
                    enum_text(skill.get("SLOTTYPE")),
                    enum_text(skill.get("ACTIVATIONTYPE")),
                    skill.get("ActivationValue"),
                    skill.get("Range"),
                    enum_text(skill.get("DamageType")),
                    enum_text(skill.get("DamageDeliveryType")),
                ]
            )
        attribute_rows = []
        for attr in hero.get("attributes", []):
            attribute_rows.append(
                [
                    attr.get("AttributeKey"),
                    attr.get("RequiredHeroLevel"),
                    attr.get("MaxLevel"),
                    mono_text((attr.get("passive_skill") or {}).get("SkillNameKey") or (attr.get("skill") or {}).get("SkillNameKey"), "-"),
                    stat_name((attr.get("passive_skill") or {}).get("STATTYPE")) if (attr.get("passive_skill") or {}).get("STATTYPE") else enum_text((attr.get("skill") or {}).get("ACTIVATIONTYPE")),
                    (attr.get("passive_skill") or {}).get("Value") or (attr.get("skill") or {}).get("ActivationValue"),
                ]
            )
        write_detail(
            "heroes",
            row,
            {
                "heroImage": full_art,
                "overview": [
                    metric("field.class", class_name),
                    metric("field.mainWeapon", hero.get("MainWeaponGearType")),
                    metric("field.subWeapon", hero.get("SubWeaponGearType")),
                    metric("field.unlock", "DLC" if hero.get("dlc_required") else hero.get("UnlockCost")),
                ],
                "sections": [
                    {"titleKey": "detail.section.baseStats", "type": "stats", "items": base_stats},
                    {
                        "titleKey": "detail.section.skills",
                        "type": "table",
                        "columns": [
                            {"labelKey": "field.name"},
                            {"labelKey": "filter.slot"},
                            {"labelKey": "field.activation"},
                            {"labelKey": "field.value"},
                            {"labelKey": "field.range"},
                            {"labelKey": "field.type"},
                            {"labelKey": "field.type"},
                        ],
                        "rows": skill_rows,
                    },
                    {
                        "titleKey": "detail.section.attributes",
                        "type": "table",
                        "columns": [
                            {"labelKey": "field.id"},
                            {"labelKey": "field.level"},
                            {"labelKey": "field.max"},
                            {"labelKey": "field.name"},
                            {"labelKey": "field.type"},
                            {"labelKey": "field.value"},
                        ],
                        "rows": attribute_rows,
                    },
                ],
                "source": {"table": "HeroInfoData"},
            },
        )
        entries.append(row)
    category = category_definition("heroes", len(entries), asset(assets, "Inventory_ChaIllust_Knight_Mid_Anim_0"), "cards", "nav.database")
    return category, entries


def build_monsters(assets: dict[str, str], stages: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    stage_count: Counter[str] = Counter()
    for stage in stages:
        for monster in stage.get("monsters_resolved", []):
            if monster.get("base"):
                stage_count[str(monster.get("monster_key"))] += 1
    entries: list[dict[str, Any]] = []
    for monster in load_table("MonsterInfoData"):
        name = humanize(monster.get("MonsterNameStringKey") or f"Monster {monster.get('MonsterKey')}")
        row = entry(
            "monsters",
            monster["MonsterKey"],
            monster_title(monster, name),
            localized(monster.get("MONSTERTYPE")),
            asset(assets, "AdditionalGoldNormalMonster"),
            "RARE" if monster.get("MONSTERTYPE") == "BOSS" else "COMMON",
            [monster.get("MONSTERTYPE")],
            {
                "type": monster.get("MONSTERTYPE"),
                "gold": monster.get("RewardGold"),
                "exp": monster.get("RewardExp"),
                "attackDamage": monster.get("AttackDamage"),
                "maxHp": monster.get("MaxLife"),
                "stages": stage_count[str(monster["MonsterKey"])],
            },
            {
                "type": localized(humanize(monster.get("MONSTERTYPE"))),
            },
        )
        write_detail(
            "monsters",
            row,
            {
                "overview": [
                    metric("field.id", monster.get("MonsterKey")),
                    metric("field.type", monster.get("MONSTERTYPE")),
                    metric("field.gold", monster.get("RewardGold")),
                    metric("field.exp", monster.get("RewardExp")),
                    metric("field.attackDamage", monster.get("AttackDamage")),
                    metric("field.maxHp", monster.get("MaxLife")),
                ],
                "sections": [
                    {
                        "titleKey": "detail.section.raw",
                        "type": "table",
                        "columns": [{"labelKey": "field.name"}, {"labelKey": "field.value"}],
                        "rows": raw_rows(monster),
                    }
                ],
                "source": {"table": "MonsterInfoData"},
            },
        )
        entries.append(row)
    category = category_definition("monsters", len(entries), asset(assets, "AdditionalGoldNormalMonster"), "table", "nav.database")
    return category, entries


def build_skills(assets: dict[str, str]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    entries: list[dict[str, Any]] = []
    for skill in load_table("SkillInfoData"):
        title = skill_display_name(skill)
        slot_text = enum_text(skill.get("SLOTTYPE"))
        activation_text = enum_text(skill.get("ACTIVATIONTYPE"))
        row = entry(
            "skills",
            skill["SkillKey"],
            skill_title(skill),
            join_localized([slot_text, activation_text]),
            asset(assets, Path(str(skill.get("AnimClipPath1") or "")).name),
            "LEGENDARY",
            [skill.get("SLOTTYPE"), skill.get("ACTIVATIONTYPE"), skill.get("DamageType")],
            {
                "category": "Active",
                "type": skill.get("SLOTTYPE"),
                "activation": skill.get("ACTIVATIONTYPE"),
                "range": skill.get("Range"),
                "value": skill.get("Value") or skill.get("ActivationValue"),
            },
            {
                "category": enum_text("Active"),
                "type": slot_text,
                "activation": activation_text,
            },
        )
        write_detail(
            "skills",
            row,
            {
                "overview": [
                    metric("field.id", skill.get("SkillKey")),
                    {"labelKey": "filter.slot", "value": slot_text},
                    {"labelKey": "field.activation", "value": activation_text},
                    metric("field.range", skill.get("Range")),
                    metric("field.value", skill.get("Value") or skill.get("ActivationValue")),
                ],
                "sections": [
                    {
                        "titleKey": "detail.section.raw",
                        "type": "table",
                        "columns": [{"labelKey": "field.name"}, {"labelKey": "field.value"}],
                        "rows": raw_rows(skill),
                    }
                ],
                "source": {"table": "SkillInfoData"},
            },
        )
        entries.append(row)
    for passive in load_table("PassiveSkillInfoData"):
        title = humanize(passive.get("SkillNameKey") or f"Passive {passive.get('PassiveSkillKey')}")
        stat_text = stat_name(passive.get("STATTYPE"))
        mod_text = enum_text(passive.get("MODTYPE"))
        row = entry(
            "skills",
            f"passive-{passive['PassiveSkillKey']}",
            mono_text(passive.get("SkillNameKey"), title),
            stat_effect_text(passive.get("STATTYPE"), passive.get("Value"), passive.get("MODTYPE")),
            asset(assets, "AllHeroAttackDamage"),
            "ARCANA",
            ["Passive", passive.get("STATTYPE"), passive.get("MODTYPE")],
            {
                "category": "Passive",
                "type": passive.get("STATTYPE"),
                "activation": passive.get("MODTYPE"),
                "value": passive.get("Value"),
            },
            {
                "category": enum_text("Passive"),
                "type": stat_text,
                "activation": mod_text,
            },
        )
        write_detail(
            "skills",
            row,
            {
                "overview": [
                    metric("field.id", passive.get("PassiveSkillKey")),
                    {"labelKey": "field.type", "value": stat_text},
                    metric("field.value", passive.get("Value")),
                ],
                "sections": [
                    {
                        "titleKey": "detail.section.raw",
                        "type": "table",
                        "columns": [{"labelKey": "field.name"}, {"labelKey": "field.value"}],
                        "rows": raw_rows(passive),
                    }
                ],
                "source": {"table": "PassiveSkillInfoData"},
            },
        )
        entries.append(row)
    category = category_definition("skills", len(entries), asset(assets, "Skill_30101"), "table", "nav.combat")
    return category, entries


def build_runes(assets: dict[str, str]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    runes = load_table("RuneInfoData")
    level_rows = load_table("RuneLevelInfoData")
    layout_data = load_json(RUNE_LAYOUT_PATH) if RUNE_LAYOUT_PATH.exists() else {"nodes": [], "meta": {}}
    layout_by_key = {str(row["key"]): row for row in layout_data.get("nodes", [])}
    layout_meta = layout_data.get("meta", {})
    levels_by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in level_rows:
        levels_by_key[str(row.get("LevelDataKey") or row.get("LevelKey"))].append(row)
    for rows in levels_by_key.values():
        rows.sort(key=lambda item: int(item.get("Level") or 0))

    def rune_links(value: Any) -> list[str]:
        return [part for part in compact(value).split() if part.isdigit()]

    def rune_cost(row: dict[str, Any]) -> dict[str, str]:
        cost = row.get("CostValue") or 0
        currency = currency_name(row.get("CostItemKey"))
        return localized(f"{cost} {currency['en']}", f"{cost} {currency['ja']}")

    by_key = {str(rune["RuneKey"]): rune for rune in runes}
    graph_edges: list[dict[str, Any]] = []
    for rune in runes:
        source = str(rune["RuneKey"])
        for target in rune_links(rune.get("NextRuneKey")):
            graph_edges.append({"from": source, "to": target, "kind": "connected"})

    layout_keys = {str(key) for key in layout_by_key}
    missing_layout_keys = [str(rune["RuneKey"]) for rune in runes if str(rune["RuneKey"]) not in layout_keys]
    column_width = 72
    row_height = 72
    left = int(layout_meta.get("originOffset") or 40)
    top = int(layout_meta.get("originOffset") or 40)
    positions: dict[str, dict[str, int]] = {}
    for key, layout in layout_by_key.items():
        positions[key] = {"x": int(layout.get("x") or left), "y": int(layout.get("y") or top)}
    for index, key in enumerate(missing_layout_keys):
        positions[key] = {
            "x": left + (index % 8) * column_width,
            "y": top + (index // 8) * row_height,
        }

    entries: list[dict[str, Any]] = []
    graph_nodes: list[dict[str, Any]] = []
    all_cost = 0
    for rune in runes:
        title = humanize(rune.get("NameKey") or f"Rune {rune.get('RuneKey')}")
        icon = asset(assets, rune.get("IconPath"))
        next_nodes = rune_links(rune.get("NextRuneKey"))
        preview_nodes = rune_links(rune.get("PreviewRuneKey"))
        rows = levels_by_key.get(str(rune.get("LevelDataKey")), [])
        stat_types = sorted({level.get("STATTYPE") for level in rows if level.get("STATTYPE")})
        primary_stat = stat_types[0] if stat_types else rune.get("IconPath")
        stat_display = stat_name(primary_stat)
        layout = layout_by_key.get(str(rune["RuneKey"]), {})
        category = layout.get("category") or "Other"
        is_unlock = bool(layout.get("isUnlock"))
        level_payload = [
            {
                "level": level.get("Level"),
                "costItemKey": level.get("CostItemKey"),
                "costItem": currency_name(level.get("CostItemKey")),
                "costValue": level.get("CostValue") or 0,
                "statType": level.get("STATTYPE"),
                "statName": stat_name(level.get("STATTYPE")),
                "value": level.get("Value"),
                "effect": stat_effect_text(level.get("STATTYPE"), level.get("Value")),
            }
            for level in rows
        ]
        all_cost += sum(int(level.get("CostValue") or 0) for level in rows)
        tooltip = {
            "title": mono_text(rune.get("NameKey"), title),
            "subtitle": localized(f"Max Lv {rune.get('MaxLevel')}", f"最大 Lv {rune.get('MaxLevel')}"),
            "icon": icon,
            "rarity": "ARCANA",
            "rows": [
                {"labelKey": "field.level", "value": localized(rune.get("MaxLevel"))},
                {"labelKey": "field.effect", "value": stat_display},
                {"labelKey": "rune.connected", "value": localized(len(next_nodes))},
            ],
            "sections": [
                {
                    "titleKey": "detail.section.scaling",
                    "rows": [
                        {"label": localized(f"Lv {level.get('Level')}", f"Lv {level.get('Level')}"), "value": stat_effect_text(level.get("STATTYPE"), level.get("Value"))}
                        for level in rows[:6]
                    ],
                }
            ],
        }
        row = entry(
            "runes",
            rune["RuneKey"],
            mono_text(rune.get("NameKey"), title),
            localized(f"Max Lv {rune.get('MaxLevel')}", f"最大 Lv {rune.get('MaxLevel')}"),
            icon,
            "ARCANA",
            [rune.get("IconPath"), primary_stat, f"max:{rune.get('MaxLevel')}"],
            {"level": rune.get("MaxLevel"), "type": primary_stat, "count": len(next_nodes), "category": category},
            {"type": stat_display},
            tooltip=tooltip,
        )
        connection_rows = []
        for kind, targets in [("connected", next_nodes), ("preview", preview_nodes)]:
            for target in targets:
                target_rune = by_key.get(target, {})
                connection_rows.append(
                    [
                        {"connected": localized("Connected", "接続"), "preview": localized("Preview", "プレビュー")}[kind],
                        mono_text(target_rune.get("NameKey"), f"Rune {target}"),
                        target_rune.get("PrevNodeRequiredLevel") or "-",
                    ]
                )
        scaling_rows = [
            [
                level.get("Level"),
                stat_effect_text(level.get("STATTYPE"), level.get("Value")),
                rune_cost(level),
            ]
            for level in rows
        ]
        write_detail(
            "runes",
            row,
            {
                "overview": [
                    metric("field.id", rune.get("RuneKey")),
                    metric("field.level", rune.get("MaxLevel")),
                    metric("field.value", rune.get("PrevNodeRequiredLevel") or "-"),
                    {"labelKey": "field.effect", "value": stat_display},
                    metric("field.count", len(next_nodes)),
                ],
                "sections": [
                    {
                        "titleKey": "detail.section.connections",
                        "type": "table",
                        "columns": [{"labelKey": "field.type"}, {"labelKey": "field.name"}, {"labelKey": "rune.requiredLevel"}],
                        "rows": connection_rows,
                    },
                    {
                        "titleKey": "detail.section.scaling",
                        "type": "table",
                        "columns": [{"labelKey": "field.level"}, {"labelKey": "field.effect"}, {"labelKey": "field.cost"}],
                        "rows": scaling_rows,
                    },
                ],
                "source": {"table": "RuneInfoData"},
            },
        )
        entries.append(row)

        position = positions.get(str(rune["RuneKey"]), {"x": left, "y": top})
        graph_nodes.append(
            {
                "id": str(rune["RuneKey"]),
                "runeKey": rune["RuneKey"],
                "title": row["title"],
                "subtitle": row["subtitle"],
                "icon": icon,
                "rarity": row["rarity"],
                "x": position["x"],
                "y": position["y"],
                "maxLevel": rune.get("MaxLevel") or len(rows),
                "requiredLevel": rune.get("PrevNodeRequiredLevel"),
                "next": next_nodes,
                "preview": preview_nodes,
                "statType": primary_stat,
                "statName": stat_display,
                "category": category,
                "categoryKey": f"rune.category.{category}",
                "categoryColor": RUNE_CATEGORY_COLORS.get(category, RUNE_CATEGORY_COLORS["Other"]),
                "isUnlock": is_unlock,
                "totalCost": sum(int(level.get("CostValue") or 0) for level in rows),
                "levels": level_payload,
            }
        )
    node_size = int(layout_meta.get("nodeSize") or 40)
    bounds = {
        "width": int(layout_meta.get("width") or (max((node["x"] for node in graph_nodes), default=0) + node_size + left)),
        "height": int(layout_meta.get("height") or (max((node["y"] for node in graph_nodes), default=0) + node_size + top)),
        "nodeSize": node_size,
    }
    categories = [
        {"id": category, "labelKey": f"rune.category.{category}", "color": RUNE_CATEGORY_COLORS.get(category, RUNE_CATEGORY_COLORS["Other"])}
        for category in (layout_meta.get("categories") or sorted({node["category"] for node in graph_nodes}))
    ]
    write_json(
        PUBLIC_GENERATED / "rune-graph.json",
        {
            "nodes": graph_nodes,
            "edges": graph_edges,
            "bounds": bounds,
            "categories": categories,
            "totals": {"allCost": all_cost, "nodeCount": len(graph_nodes)},
        },
    )
    category = category_definition("runes", len(entries), asset(assets, "AllHeroAttackDamage"), "table", "nav.combat")
    return category, entries


def pet_farm_rows(monster_key: Any, stages: list[dict[str, Any]]) -> list[list[Any]]:
    if monster_key in (None, ""):
        return []
    rows: list[dict[str, Any]] = []
    target = int(monster_key)
    for stage in stages:
        monsters = stage.get("monsters_resolved", [])
        total_weight = sum(int(monster.get("weight") or 0) for monster in monsters)
        for monster in monsters:
            if int(monster.get("monster_key") or -1) != target:
                continue
            weight = int(monster.get("weight") or 0)
            spawn = round(weight * 100 / total_weight, 4) if total_weight else None
            rows.append({"stage": stage, "spawn": spawn, "weight": weight})
    rows.sort(key=lambda item: (-(item.get("spawn") or 0), item["stage"].get("StageLevel") or 0))
    return [
        [
            stage_title(row["stage"]),
            f"{row.get('spawn'):.4g}%" if row.get("spawn") is not None else "-",
            row["stage"].get("StageLevel"),
            row["stage"].get("WaveAmount"),
        ]
        for row in rows[:12]
    ]


def build_pets(assets: dict[str, str], monsters_by_key: dict[str, dict[str, Any]], stages: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    pet_stats = {row["PetStatKey"]: row for row in load_table("PetStatInfoData")}
    entries: list[dict[str, Any]] = []
    for pet in load_table("PetInfoData"):
        title = humanize(pet.get("NameKey") or f"Pet {pet.get('PetKey')}")
        monster = monsters_by_key.get(str(pet.get("Param1"))) or {}
        stat = pet_stats.get(pet.get("StatDataKey")) or {}
        unlock_target = monster_title(monster, pet.get("Param1"))
        farm_rows = pet_farm_rows(pet.get("Param1"), stages)
        row = entry(
            "pets",
            pet["PetKey"],
            mono_text(pet.get("NameKey"), title),
            localized(
                f"{pet.get('UnlockCondition')} {unlock_target.get('en')}",
                f"{pet.get('UnlockCondition')} {unlock_target.get('ja')}",
            ),
            asset(assets, "BG_Pet"),
            "COSMIC" if pet.get("UnlockCondition") == "DLC" else "RARE",
            [pet.get("UnlockCondition")],
            {
                "type": pet.get("UnlockCondition"),
                "count": pet.get("Param2") or "-",
                "gold": stat.get("AdditionalGoldPercent"),
                "exp": stat.get("AdditionalExpPercent"),
            },
            {
                "type": localized(humanize(pet.get("UnlockCondition"))),
            },
        )
        sections = [
            {
                "titleKey": "detail.section.baseStats",
                "type": "table",
                "columns": [{"labelKey": "field.name"}, {"labelKey": "field.value"}],
                "rows": raw_rows(stat),
            }
        ]
        if farm_rows:
            sections.append(
                {
                    "titleKey": "detail.section.farmStages",
                    "type": "table",
                    "columns": [
                        {"labelKey": "field.stage"},
                        {"labelKey": "field.spawn"},
                        {"labelKey": "field.stageLevel"},
                        {"labelKey": "field.wave"},
                    ],
                    "rows": farm_rows,
                }
            )
        write_detail(
            "pets",
            row,
            {
                "overview": [
                    metric("field.id", pet.get("PetKey")),
                    metric("field.type", pet.get("UnlockCondition")),
                    metric("field.count", pet.get("Param2") or "-"),
                    {"labelKey": "field.name", "value": unlock_target},
                ],
                "sections": sections,
                "source": {"table": "PetInfoData"},
            },
        )
        entries.append(row)
    category = category_definition("pets", len(entries), asset(assets, "BG_Pet"), "cards", "nav.collection")
    return category, entries


def stage_rate_text(value: Any) -> str:
    if value in (None, ""):
        return "-"
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return compact(value)
    if numeric > 100:
        numeric /= 10
    return f"{numeric:g}%"


def monster_detail_slug(monster: dict[str, Any], monster_key: Any) -> str:
    title = monster_title(monster, monster_key)
    return f"{monster_key}-{slugify(title.get('en') or title.get('ja') or monster_key)}"


def drop_preview_rows(drop_key: Any, drops_by_key: dict[str, Any], items_by_key: dict[int, dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    if drop_key in (None, ""):
        return []
    drop = drops_by_key.get(str(drop_key)) or {}
    entries = sorted(drop.get("entries", []), key=lambda row: row.get("weight_percent") or 0, reverse=True)
    rows: list[dict[str, Any]] = []
    for row in entries[:limit]:
        resolved = row.get("resolved") or {}
        title = localized(humanize(resolved.get("kind") or row.get("reward_type")))
        sample = localized("")
        icon = None
        rarity = None
        if resolved.get("kind") == "item":
            item = items_by_key.get(int(resolved.get("item_key") or row.get("reward_key") or 0))
            if item:
                title = item_title(item)
                icon = item_icon(item, {})
                rarity = item.get("GRADE")
            else:
                title = localized_value(resolved.get("name"), row.get("reward_key"))
        elif resolved.get("kind") == "item_group":
            group_name = resolved.get("group_name") or f"Item group {resolved.get('item_group_key')}"
            title = localized_value(group_name)
            preview_names = [compact(item.get("name")) for item in resolved.get("items_preview", []) if item.get("name")]
            if preview_names:
                sample = localized(", ".join(preview_names[:3]))
        rows.append(
            {
                "title": title,
                "sample": sample,
                "icon": icon,
                "rarity": rarity,
                "weight": row.get("weight"),
                "weightPercent": row.get("weight_percent"),
                "rewardType": row.get("reward_type"),
                "rewardKey": row.get("reward_key"),
            }
        )
    return rows


def stage_reward_payload(
    label_key: str,
    item_key: Any,
    rate: Any,
    boxes_by_key: dict[str, dict[str, Any]],
    items_by_key: dict[int, dict[str, Any]],
    drops_by_key: dict[str, Any],
    assets: dict[str, str],
    first_clear_drop_key: Any = None,
) -> dict[str, Any] | None:
    if item_key in (None, "") and first_clear_drop_key in (None, ""):
        return None
    box_entry = boxes_by_key.get(str(item_key)) if item_key not in (None, "") else None
    item = items_by_key.get(int(item_key)) if item_key not in (None, "") else None
    drop_key = first_clear_drop_key or (box_entry or {}).get("fields", {}).get("dropKey") or (item or {}).get("DropKey")
    title = (box_entry or {}).get("title") or (item_title(item) if item else localized(f"DropKey {drop_key}", f"DropKey {drop_key}"))
    return {
        "labelKey": label_key,
        "itemKey": item_key,
        "dropKey": drop_key,
        "title": title,
        "icon": (box_entry or {}).get("icon") or item_icon(item or {}, assets),
        "rarity": (box_entry or {}).get("rarity") or (item or {}).get("GRADE"),
        "rate": stage_rate_text(rate),
        "detailHref": f"#/detail/stage-boxes/{box_entry['slug']}" if box_entry else None,
        "preview": drop_preview_rows(drop_key, drops_by_key, items_by_key),
    }


def build_stage_atlas(stages: list[dict[str, Any]], entries: list[dict[str, Any]], boxes: list[dict[str, Any]], drops_by_key: dict[str, Any], assets: dict[str, str]) -> dict[str, Any]:
    entries_by_key = {entry["entityId"]: entry for entry in entries}
    boxes_by_key = {box["entityId"]: box for box in boxes}
    items_by_key = {int(item["ItemKey"]): item for item in load_data("items") if item.get("ItemKey") is not None}
    acts: list[dict[str, Any]] = []
    for act in sorted({stage.get("Act") for stage in stages if stage.get("Act") is not None}):
        act_stages = []
        for stage in stages:
            if stage.get("Act") != act:
                continue
            entry_row = entries_by_key.get(str(stage.get("StageKey"))) or {}
            monster_weight_total = sum(Number for Number in [int(ref.get("weight") or 0) for ref in stage.get("monsters_resolved", [])]) or 1
            monsters = []
            for monster_ref in stage.get("monsters_resolved", []):
                monster = monster_ref.get("base") or {}
                weight = int(monster_ref.get("weight") or 0)
                share = round(weight / monster_weight_total * 100, 4)
                expected = round((stage.get("WaveMonsterAmount") or 0) * share / 100, 3)
                monster_key = monster_ref.get("monster_key")
                monsters.append(
                    {
                        "key": monster_key,
                        "title": monster_title(monster, monster_ref.get("display_name") or monster_key),
                        "href": f"#/detail/monsters/{monster_detail_slug(monster, monster_key)}",
                        "weight": weight,
                        "spawnShare": share,
                        "expectedPerWave": expected,
                        "gold": monster.get("RewardGold"),
                        "exp": monster.get("RewardExp"),
                        "attackDamage": monster.get("AttackDamage"),
                        "attackSpeed": monster.get("AttackSpeed"),
                        "maxHp": monster.get("MaxLife"),
                        "moveSpeed": monster.get("MovementSpeed"),
                    }
                )
            boss_base = ((stage.get("boss_resolved") or {}).get("base") or {})
            boss_key = (stage.get("boss_resolved") or {}).get("monster_key") or stage.get("BossMonsterKey")
            rewards = [
                stage_reward_payload(
                    "stageAtlas.normalBox",
                    stage.get("MonsterDropItemKey"),
                    stage.get("MonsterDropItemRate"),
                    boxes_by_key,
                    items_by_key,
                    drops_by_key,
                    assets,
                ),
                stage_reward_payload(
                    "stageAtlas.bossBox",
                    stage.get("BossDropItemKey"),
                    stage.get("BossDropItemRate"),
                    boxes_by_key,
                    items_by_key,
                    drops_by_key,
                    assets,
                ),
                stage_reward_payload(
                    "stageAtlas.firstClear",
                    None,
                    None,
                    boxes_by_key,
                    items_by_key,
                    drops_by_key,
                    assets,
                    stage.get("FirstClearDropKey"),
                ),
            ]
            act_stages.append(
                {
                    "id": compact(stage.get("StageKey")),
                    "slug": entry_row.get("slug"),
                    "detailHref": f"#/detail/stages/{entry_row.get('slug')}" if entry_row.get("slug") else None,
                    "title": entry_row.get("title") or stage_title(stage),
                    "subtitle": entry_row.get("subtitle") or localized(""),
                    "difficulty": stage.get("STAGEDIFFICULITY"),
                    "difficultyLabel": mono_enum("Difficulty", stage.get("STAGEDIFFICULITY")),
                    "difficultyColor": STAGE_DIFFICULTY_COLORS.get(stage.get("STAGEDIFFICULITY"), "#d3a13d"),
                    "stageType": stage.get("STAGETYPE"),
                    "act": stage.get("Act"),
                    "stageNo": stage.get("StageNo"),
                    "stageLevel": stage.get("StageLevel"),
                    "waveAmount": stage.get("WaveAmount"),
                    "waveMonsterAmount": stage.get("WaveMonsterAmount"),
                    "position": STAGE_NODE_POSITIONS.get(stage.get("Act"), {}).get(stage.get("StageNo"), {"x": 50, "y": 50}),
                    "monsters": monsters,
                    "boss": {
                        "key": boss_key,
                        "title": monster_title(boss_base, (stage.get("boss_resolved") or {}).get("display_name") or boss_key),
                        "href": f"#/detail/monsters/{monster_detail_slug(boss_base, boss_key)}" if boss_key else None,
                        "attackDamage": boss_base.get("AttackDamage"),
                        "attackDamageScaled": round((boss_base.get("AttackDamage") or 0) * (stage.get("BossDamageMultiplier") or 1000) / 1000, 2),
                        "maxHp": boss_base.get("MaxLife"),
                        "maxHpScaled": round((boss_base.get("MaxLife") or 0) * (stage.get("BossHpMultiplier") or 1000) / 1000, 2),
                        "gold": boss_base.get("RewardGold"),
                        "exp": boss_base.get("RewardExp"),
                    },
                    "rewards": [reward for reward in rewards if reward],
                }
            )
        acts.append(
            {
                "act": act,
                "label": localized(f"Act {act}", f"Act {act}"),
                "background": asset(assets, f"Act{act}_Bg"),
                "stages": sorted(
                    act_stages,
                    key=lambda stage: (
                        STAGE_DIFFICULTY_ORDER.index(stage.get("difficulty") or "NORMAL")
                        if stage.get("difficulty") in STAGE_DIFFICULTY_ORDER
                        else 999,
                        stage.get("stageNo") or 0,
                    ),
                ),
            }
        )
    return {
        "acts": acts,
        "difficulties": [
            {"id": difficulty, "label": mono_enum("Difficulty", difficulty), "color": STAGE_DIFFICULTY_COLORS[difficulty]}
            for difficulty in STAGE_DIFFICULTY_ORDER
        ],
        "generatedFrom": ["StageInfoData", "MonsterInfoData", "ItemInfoData", "DropInfoData"],
    }


def build_stages(assets: dict[str, str], drops_by_key: dict[str, Any], boxes: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    stages = sorted(load_data("stages"), key=lambda s: (STAGE_DIFFICULTY_ORDER.index(s.get("STAGEDIFFICULITY", "NORMAL")), s.get("Act", 0), s.get("StageNo", 0)))
    entries: list[dict[str, Any]] = []
    for stage in stages:
        stage_name = stage.get("display_name") or f"Act {stage.get('Act')}-{stage.get('StageNo')}"
        difficulty = stage.get("STAGEDIFFICULITY")
        difficulty_name = mono_enum("Difficulty", difficulty)
        boss_base = ((stage.get("boss_resolved") or {}).get("base") or {})
        boss_name = monster_title(boss_base, (stage.get("boss_resolved") or {}).get("display_name"))
        boss = boss_name.get("en")
        icon = asset(assets, f"Act{stage.get('Act')}_Bg")
        title = localized(
            f"{stage.get('Act')}-{stage.get('StageNo')} {stage_name}",
            f"{stage.get('Act')}-{stage.get('StageNo')} {difficulty_name.get('ja')}",
        )
        row = entry(
            "stages",
            stage["StageKey"],
            title,
            localized(
                f"{difficulty_name.get('en')} / Lv {stage.get('StageLevel')} / Boss {boss}",
                f"{difficulty_name.get('ja')} / Lv {stage.get('StageLevel')} / Boss {boss}",
            ),
            icon,
            None,
            [difficulty, stage.get("STAGETYPE"), f"Act {stage.get('Act')}"],
            {
                "difficulty": difficulty,
                "act": stage.get("Act"),
                "stage": stage.get("StageNo"),
                "level": stage.get("StageLevel"),
                "wave": stage.get("WaveAmount"),
                "boss": boss,
            },
            {
                "difficulty": difficulty_name,
                "boss": boss_name,
            },
        )
        monster_rows = []
        for monster_ref in stage.get("monsters_resolved", []):
            monster = monster_ref.get("base") or {}
            monster_rows.append(
                [
                    monster_ref.get("monster_key"),
                    monster_title(monster, monster_ref.get("monster_key")),
                    monster_ref.get("weight"),
                    monster.get("RewardGold"),
                    monster.get("RewardExp"),
                ]
            )
        reward_rows = [
            ["Monster box", (stage.get("monster_drop_item") or {}).get("display_name") or stage.get("MonsterDropItemKey"), stage.get("MonsterDropItemRate")],
            ["Boss box", (stage.get("boss_drop_item") or {}).get("display_name") or stage.get("BossDropItemKey"), stage.get("BossDropItemRate")],
            ["First clear", stage.get("FirstClearDropKey"), "-"],
        ]
        write_detail(
            "stages",
            row,
            {
                "heroImage": icon,
                "overview": [
                    metric("field.id", stage.get("StageKey")),
                    metric("filter.difficulty", difficulty),
                    metric("field.act", stage.get("Act")),
                    metric("field.stage", stage.get("StageNo")),
                    metric("field.stageLevel", stage.get("StageLevel")),
                    metric("field.wave", stage.get("WaveAmount")),
                    metric("field.boss", boss),
                ],
                "sections": [
                    {
                        "titleKey": "detail.section.monsters",
                        "type": "table",
                        "columns": [
                            {"labelKey": "field.id"},
                            {"labelKey": "field.name"},
                            {"labelKey": "field.weight"},
                            {"labelKey": "field.gold"},
                            {"labelKey": "field.exp"},
                        ],
                        "rows": monster_rows,
                    },
                    {
                        "titleKey": "detail.section.rewards",
                        "type": "table",
                        "columns": [{"labelKey": "field.type"}, {"labelKey": "field.name"}, {"labelKey": "field.value"}],
                        "rows": reward_rows,
                    },
                    {
                        "titleKey": "detail.section.scaling",
                        "type": "table",
                        "columns": [{"labelKey": "field.name"}, {"labelKey": "field.value"}],
                        "rows": raw_rows(stage.get("stage_level_scaling") or {}),
                    },
                ],
                "source": {"table": "StageInfoData"},
            },
        )
        entries.append(row)
    write_json(PUBLIC_GENERATED / "stage-atlas.json", build_stage_atlas(stages, entries, boxes, drops_by_key, assets))
    category = category_definition("stages", len(entries), asset(assets, "Act1_Bg"), "cards", "nav.systems")
    return category, entries, stages


def build_cube(assets: dict[str, str]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    recipes = load_data("recipes")
    table_map = {
        "synthesis": "SynthesisRecipeInfoData",
        "crafting": "CraftingRecipeInfoData",
        "cube": "CubeRecipeInfoData",
        "cube_sub": "CubeSubRecipeInfoData",
        "extraction": "ExtractionCostInfoData",
        "synthesis_drops": "SynthesisDropInfoData",
    }
    labels = {
        "synthesis": "Synthesis",
        "crafting": "Crafting",
        "cube": "Cube Overview",
        "cube_sub": "Cube Sub Recipes",
        "extraction": "Extraction",
        "synthesis_drops": "Synthesis Drops",
    }
    entries: list[dict[str, Any]] = []
    for key, value in recipes.items():
        if not isinstance(value, list):
            continue
        row = entry(
            "cube",
            key,
            localized(labels.get(key, humanize(key))),
            localized(f"{len(value)} records"),
            asset(assets, "Icon_Cube_Synthesis") or asset(assets, "MenuButton_Cube_Active"),
            "BEYOND",
            [key],
            {"type": humanize(key), "count": len(value), "table": table_map.get(key, key)},
            slug=slugify(key),
        )
        rows = []
        for recipe in value[:120]:
            if isinstance(recipe, dict):
                rows.extend(raw_rows(recipe))
        write_detail(
            "cube",
            row,
            {
                "overview": [metric("field.count", len(value)), metric("field.table", table_map.get(key, key))],
                "sections": [
                    {
                        "titleKey": "detail.section.entries",
                        "type": "table",
                        "columns": [{"labelKey": "field.name"}, {"labelKey": "field.value"}],
                        "rows": rows[:160],
                    }
                ],
                "source": {"table": table_map.get(key, key)},
            },
        )
        entries.append(row)
    category = category_definition("cube", len(entries), asset(assets, "MenuButton_Cube_Active"), "cards", "nav.systems")
    return category, entries


def build_database(assets: dict[str, str]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    entries: list[dict[str, Any]] = []
    for path in sorted(TABLES.glob("*.json")):
        data = load_json(path)
        name = path.stem
        row = entry(
            "database",
            name,
            localized(name),
            localized(f"{len(data)} records"),
            asset(assets, "Icon_Setting") or asset(assets, "MenuButton_Stat_Active"),
            "COMMON",
            ["InfoData", name],
            {"table": name, "records": len(data), "count": len(data)},
            slug=slugify(name),
        )
        preview_rows = []
        for record in data[:12]:
            if isinstance(record, dict):
                preview_rows.extend(raw_rows(record))
        write_detail(
            "database",
            row,
            {
                "overview": [metric("field.table", name), metric("field.records", len(data))],
                "sections": [
                    {
                        "titleKey": "detail.section.entries",
                        "type": "table",
                        "columns": [{"labelKey": "field.name"}, {"labelKey": "field.value"}],
                        "rows": preview_rows[:200],
                    }
                ],
                "source": {"table": name},
            },
        )
        entries.append(row)
    category = category_definition("database", len(entries), asset(assets, "Icon_Setting") or asset(assets, "MenuButton_Stat_Active"), "table", "nav.reference")
    return category, entries


def entry_ref(item: dict[str, Any] | None, category_id: str | None = None) -> dict[str, Any] | None:
    if not item:
        return None
    resolved_category = category_id or item.get("categoryId")
    slug = item.get("slug")
    return {
        "categoryId": resolved_category,
        "entityId": item.get("entityId"),
        "slug": slug,
        "href": f"#/detail/{resolved_category}/{slug}" if resolved_category and slug else None,
        "title": item.get("title"),
        "rarity": item.get("rarity"),
    }


def stage_entry_ref(stage: dict[str, Any], stage_entries_by_key: dict[str, dict[str, Any]]) -> dict[str, Any]:
    row = stage_entries_by_key.get(str(stage.get("StageKey")))
    base = entry_ref(row, "stages") or {}
    base.update(
        {
            "stageKey": stage.get("StageKey"),
            "difficulty": stage.get("STAGEDIFFICULITY"),
            "act": stage.get("Act"),
            "stageNo": stage.get("StageNo"),
            "stageLevel": stage.get("StageLevel"),
            "waveAmount": stage.get("WaveAmount"),
            "waveMonsterAmount": stage.get("WaveMonsterAmount"),
            "title": base.get("title") or stage_title(stage),
        }
    )
    return base


def relationship_drop_contents(
    drop_key: Any,
    drops_by_key: dict[str, Any],
    item_entries_by_key: dict[str, dict[str, Any]],
    limit: int = 24,
) -> list[dict[str, Any]]:
    drop = drops_by_key.get(str(drop_key)) if drop_key not in (None, "") else None
    if not drop:
        return []
    rows: list[dict[str, Any]] = []
    for drop_entry in sorted(drop.get("entries", []), key=lambda row: row.get("weight_percent") or 0, reverse=True)[:limit]:
        resolved = drop_entry.get("resolved") or {}
        preview_items = []
        if resolved.get("kind") == "item":
            preview = item_entries_by_key.get(str(resolved.get("item_key") or drop_entry.get("reward_key")))
            if preview:
                preview_items.append(entry_ref(preview))
        elif resolved.get("kind") == "item_group":
            for preview in resolved.get("items_preview", [])[:4]:
                item_row = item_entries_by_key.get(str(preview.get("item_key")))
                preview_items.append(entry_ref(item_row) or {"entityId": compact(preview.get("item_key")), "title": localized_value(preview.get("name"))})
        rows.append(
            {
                "rewardType": drop_entry.get("reward_type"),
                "rewardKey": drop_entry.get("reward_key"),
                "weight": drop_entry.get("weight"),
                "weightPercent": drop_entry.get("weight_percent"),
                "groupName": localized_value(resolved.get("group_name"), resolved.get("group_name") or drop_entry.get("reward_key")),
                "items": [item for item in preview_items if item],
            }
        )
    return rows


def build_relationships(entry_map: dict[str, list[dict[str, Any]]], stage_rows: list[dict[str, Any]], drops_by_key: dict[str, Any]) -> dict[str, Any]:
    all_item_entries = entry_map.get("gear", []) + entry_map.get("materials", []) + entry_map.get("stage-boxes", [])
    item_entries_by_key = {entry["entityId"]: entry for entry in all_item_entries}
    box_entries_by_key = {entry["entityId"]: entry for entry in entry_map.get("stage-boxes", [])}
    stage_entries_by_key = {entry["entityId"]: entry for entry in entry_map.get("stages", [])}
    monster_entries_by_key = {entry["entityId"]: entry for entry in entry_map.get("monsters", [])}
    pet_entries_by_key = {entry["entityId"]: entry for entry in entry_map.get("pets", [])}
    items = load_data("items")
    items_by_key = {str(item.get("ItemKey")): item for item in items}
    sources_by_item = build_item_source_index(items, stage_rows, drops_by_key)

    item_sources: dict[str, Any] = {}
    for item_key, sources in sources_by_item.items():
        rows = []
        for source in sources[:5]:
            chest = source.get("chest") or {}
            stage = source.get("stage") or {}
            rows.append(
                {
                    "dropKey": source.get("drop_key"),
                    "sourceType": source.get("source_type"),
                    "chance": source.get("chance"),
                    "stageRate": source.get("stage_rate"),
                    "chest": entry_ref(box_entries_by_key.get(str(chest.get("ItemKey")))),
                    "stage": stage_entry_ref(stage, stage_entries_by_key) if stage else None,
                }
            )
        item_sources[str(item_key)] = {"item": entry_ref(item_entries_by_key.get(str(item_key))), "sources": rows}

    chest_sources: dict[str, list[dict[str, Any]]] = defaultdict(list)
    stage_rewards: dict[str, Any] = {}
    for stage in stage_rows:
        rewards = []
        for field, rate, label in (
            ("MonsterDropItemKey", "MonsterDropItemRate", "stageAtlas.normalBox"),
            ("BossDropItemKey", "BossDropItemRate", "stageAtlas.bossBox"),
        ):
            item_key = stage.get(field)
            if item_key in (None, ""):
                continue
            source = {
                "kind": label,
                "rate": stage.get(rate),
                "stage": stage_entry_ref(stage, stage_entries_by_key),
            }
            chest_sources[str(item_key)].append(source)
            rewards.append({"kind": label, "rate": stage.get(rate), "item": entry_ref(box_entries_by_key.get(str(item_key)))})
        if stage.get("FirstClearDropKey") not in (None, ""):
            rewards.append({"kind": "stageAtlas.firstClear", "dropKey": stage.get("FirstClearDropKey")})
        stage_rewards[str(stage.get("StageKey"))] = {
            "stage": stage_entry_ref(stage, stage_entries_by_key),
            "rewards": rewards,
        }

    chests: dict[str, Any] = {}
    for chest_key, chest_entry in box_entries_by_key.items():
        item = items_by_key.get(str(chest_key)) or {}
        chests[chest_key] = {
            "chest": entry_ref(chest_entry),
            "dropKey": item.get("DropKey") or chest_entry.get("fields", {}).get("dropKey"),
            "contents": relationship_drop_contents(item.get("DropKey") or chest_entry.get("fields", {}).get("dropKey"), drops_by_key, item_entries_by_key),
            "sources": chest_sources.get(chest_key, [])[:12],
        }

    monsters: dict[str, Any] = defaultdict(lambda: {"monster": None, "stages": [], "petTargets": []})
    for stage in stage_rows:
        total_weight = sum(int(monster.get("weight") or 0) for monster in stage.get("monsters_resolved", [])) or 1
        stage_ref = stage_entry_ref(stage, stage_entries_by_key)
        for monster_ref in stage.get("monsters_resolved", []):
            key = str(monster_ref.get("monster_key"))
            weight = int(monster_ref.get("weight") or 0)
            monsters[key]["monster"] = entry_ref(monster_entries_by_key.get(key))
            monsters[key]["stages"].append(
                {
                    "stage": stage_ref,
                    "weight": weight,
                    "spawnShare": round(weight * 100 / total_weight, 4),
                    "expectedPerWave": round((stage.get("WaveMonsterAmount") or 0) * weight / total_weight, 3),
                    "boss": False,
                }
            )
        boss_key = stage.get("BossMonsterKey")
        if boss_key not in (None, ""):
            key = str(boss_key)
            monsters[key]["monster"] = entry_ref(monster_entries_by_key.get(key))
            monsters[key]["stages"].append({"stage": stage_ref, "weight": None, "spawnShare": None, "expectedPerWave": 1, "boss": True})

    pets: dict[str, Any] = {}
    for pet in load_table("PetInfoData"):
        pet_key = str(pet.get("PetKey"))
        monster_key = str(pet.get("Param1")) if pet.get("UnlockCondition") == "KillMonster" else None
        farm = []
        if monster_key and monster_key in monsters:
            farm = sorted(
                [row for row in monsters[monster_key]["stages"] if not row.get("boss")],
                key=lambda row: (-(row.get("spawnShare") or 0), row.get("stage", {}).get("stageLevel") or 0),
            )[:16]
            monsters[monster_key]["petTargets"].append({"pet": entry_ref(pet_entries_by_key.get(pet_key)), "required": pet.get("Param2")})
        pets[pet_key] = {
            "pet": entry_ref(pet_entries_by_key.get(pet_key)),
            "unlockCondition": pet.get("UnlockCondition"),
            "targetMonsterKey": monster_key,
            "targetMonster": entry_ref(monster_entries_by_key.get(monster_key or "")),
            "required": pet.get("Param2"),
            "recommendedStages": farm,
        }

    return {
        "generatedFrom": ["ItemInfoData", "DropInfoData", "StageInfoData", "MonsterInfoData", "PetInfoData"],
        "items": item_sources,
        "chests": chests,
        "monsters": dict(monsters),
        "pets": pets,
        "stages": stage_rewards,
    }


def market_grade_name(grade: Any) -> str:
    return {
        "COMMON": "Common",
        "UNCOMMON": "Uncommon",
        "RARE": "Rare",
        "LEGENDARY": "Legendary",
        "IMMORTAL": "Immortal",
        "ARCANA": "Arcana",
        "BEYOND": "Beyond",
        "CELESTIAL": "Celestial",
        "DIVINE": "Divine",
        "COSMIC": "Cosmic",
    }.get(str(grade), humanize(grade))


def market_query_candidates(item: dict[str, Any]) -> list[str]:
    names = [
        (item.get("localized_name") or {}).get("en"),
        (item.get("mono_fields") or {}).get("name"),
        item.get("display_name"),
    ]
    base_names = []
    seen = set()
    for name in names:
        if not name:
            continue
        clean = compact(name).strip()
        if clean and clean not in seen:
            seen.add(clean)
            base_names.append(clean)
    grade = item.get("GRADE")
    candidates: list[str] = []
    for name in base_names:
        if grade:
            grade_text = market_grade_name(grade)
            candidates.append(f"{name} ({grade_text})")
            if grade != "COMMON":
                candidates.append(f"{name} ({grade_text}) A")
                candidates.append(f"{name} ({grade_text}) B")
        candidates.append(name)
    deduped: list[str] = []
    for candidate in candidates:
        if candidate not in deduped:
            deduped.append(candidate)
    return deduped[:8]


def build_market_manifest(entry_map: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    item_entries_by_key = {entry["entityId"]: entry for entry in (entry_map.get("gear", []) + entry_map.get("materials", []) + entry_map.get("stage-boxes", []))}
    market_items = []
    for item in load_data("items"):
        if not item.get("IsSteamItem"):
            continue
        item_key = str(item.get("ItemKey"))
        entry_row = item_entries_by_key.get(item_key)
        market_items.append(
            {
                "itemKey": item.get("ItemKey"),
                "categoryId": entry_row.get("categoryId") if entry_row else None,
                "slug": entry_row.get("slug") if entry_row else None,
                "href": f"#/detail/{entry_row.get('categoryId')}/{entry_row.get('slug')}" if entry_row else None,
                "title": item_title(item),
                "icon": entry_row.get("icon") if entry_row else None,
                "rarity": item.get("GRADE"),
                "itemType": item.get("ITEMTYPE"),
                "gearType": item.get("GEARTYPE") or (item.get("material") or {}).get("MATERIALTYPE"),
                "part": item.get("PARTS"),
                "level": item.get("Level"),
                "marketable": item.get("IsCanExchangeMarketable") is True,
                "queries": market_query_candidates(item),
            }
        )
    return {
        "generatedFrom": ["ItemInfoData", "Mono ItemTable", "tbh-market.com API shape"],
        "api": {
            "steamAppId": "3678970",
            "sameOriginBase": "/api/market",
            "upstreamReference": "https://tbh-market.com/api",
            "itemPath": "/item/{hash_name}",
            "itemsPath": "/items",
            "statsPath": "/stats",
            "filtersPath": "/filters",
            "ratePath": "/rate",
            "moversPath": "/movers",
            "orderbookPath": "/orderbook/{hash_name}",
            "steamListingPath": "https://steamcommunity.com/market/listings/3678970/{hash_name}",
            "cacheTtlSeconds": {"item": 300, "items": 300, "stats": 300, "filters": 3600, "rate": 1800, "movers": 600, "orderbook": 60},
        },
        "items": market_items,
    }


def build_save_schema() -> dict[str, Any]:
    return {
        "privacy": {
            "mode": "browser-local-only",
            "upload": False,
            "writeBack": False,
            "notes": [
                "The user selects an ES3 file with the File API.",
                "The wiki decrypts and parses it in the browser process.",
                "Only derived in-memory state is used for joins.",
            ],
        },
        "crypto": {
            "format": "Easy Save 3",
            "algorithm": "AES-128-CBC",
            "iv": "first 16 bytes",
            "keyDerivation": "PBKDF2-HMAC-SHA1",
            "iterations": 100,
            "keyLengthBytes": 16,
            "password": "emuMqG3bLYJ938ZDCfieWJ",
            "postProcess": "PKCS7 unpad, then gzip decompress when payload starts with 1f8b",
        },
        "joins": {
            "inventory": "inventorySaveDatas[].ItemUniqueId -> itemSaveDatas[].UniqueId -> ItemKey -> market_manifest/items and wiki detail",
            "stash": "stashSaveDatas[].ItemUniqueId -> itemSaveDatas[].UniqueId -> ItemKey",
            "tradingStash": "tradingStashSaveDatas[].ItemUniqueId -> itemSaveDatas[].UniqueId -> ItemKey",
            "equipped": "heroSaveDatas[].equippedItemIds[] -> itemSaveDatas[].UniqueId -> ItemKey",
            "runes": "RuneSaveData[].RuneKey -> rune-graph.json nodes",
            "pets": "PetSaveData[].PetKey -> relationships.json pets",
            "stage": "commonSaveData.currentStageKey / maxCompletedStage -> difficulty + act + stage",
        },
        "knownCollections": [
            "commonSaveData",
            "settingSaveData",
            "currenySaveDatas",
            "heroSaveDatas",
            "RuneSaveData",
            "PetSaveData",
            "itemSaveDatas",
            "inventorySaveDatas",
            "stashSaveDatas",
            "tradingStashSaveDatas",
            "aggregateSaveDatas",
        ],
    }


def build_manifest(categories: dict[str, dict[str, Any]], entry_map: dict[str, list[dict[str, Any]]], assets: dict[str, str]) -> dict[str, Any]:
    validation = load_data("validation_report")
    item_count = len(load_data("items"))
    home = {
        "heroArt": asset(assets, "Act1_Bg"),
        "rosterArt": asset(assets, "Arrage_ChaAnim_Knight_Large_0"),
        "stats": [
            {"labelKey": "home.stat.items", "value": item_count},
            {"labelKey": "home.stat.heroes", "value": len(entry_map["heroes"])},
            {"labelKey": "home.stat.stages", "value": len(entry_map["stages"])},
            {"labelKey": "home.stat.languages", "value": 2},
        ],
        "notes": [
            {"labelKey": "home.note.generated"},
            {"labelKey": "home.note.validation", "value": validation.get("missing_total")},
        ],
    }
    nav_groups = [
        {"id": "nav.tools", "items": ["my-save", "market", "farm-planner", "progress-planner", "lab-status"]},
        {"id": "nav.database", "items": ["gear", "materials", "effects", "stage-boxes", "heroes", "monsters"]},
        {"id": "nav.combat", "items": ["skills", "runes"]},
        {"id": "nav.collection", "items": ["pets"]},
        {"id": "nav.systems", "items": ["stages", "cube"]},
        {"id": "nav.reference", "items": ["database"]},
    ]
    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "locales": ["ja", "en"],
        "version": "local-export",
        "categories": [categories[key] for key in ORDERED_CATEGORY_IDS if key in categories],
        "navGroups": nav_groups,
        "home": home,
        "featured": [
            {"categoryId": "gear", "slug": entry_map["gear"][0]["slug"]},
            {"categoryId": "heroes", "slug": entry_map["heroes"][0]["slug"]},
            {"categoryId": "stages", "slug": entry_map["stages"][0]["slug"]},
            {"categoryId": "runes", "slug": entry_map["runes"][0]["slug"]},
        ],
    }


def main() -> None:
    reset_output()
    assets = copy_assets()
    drops = load_data("drops")
    drops_by_key = {str(key): value for key, value in drops.items()}

    categories: dict[str, dict[str, Any]] = {}
    entry_map: dict[str, list[dict[str, Any]]] = {}

    categories["my-save"] = category_definition("my-save", 1, asset(assets, "MenuButton_Inventory_Active") or asset(assets, "Icon_Setting"), "cards", "nav.tools")
    categories["market"] = category_definition("market", len(load_data("items")), asset(assets, "Icon_TradingStash") or asset(assets, "Item_100001"), "cards", "nav.tools")
    planner_count = len(load_data("items")) + len(load_table("PetInfoData")) + len(load_table("MonsterInfoData")) + len(load_table("StageInfoData"))
    categories["farm-planner"] = category_definition("farm-planner", planner_count, asset(assets, "MenuButton_Portal_Active") or asset(assets, "Icon_Search") or asset(assets, "Item_100001"), "cards", "nav.tools")
    categories["progress-planner"] = category_definition("progress-planner", len(load_table("StageInfoData")) + len(load_table("RuneInfoData")) + len(load_table("PetInfoData")), asset(assets, "MenuButton_Stat_Active") or asset(assets, "Icon_Setting"), "cards", "nav.tools")
    categories["lab-status"] = category_definition("lab-status", 6, asset(assets, "Icon_Setting") or asset(assets, "MenuButton_Stat_Active"), "cards", "nav.tools")

    item_categories, gear, materials, boxes = build_items(assets, drops_by_key)
    categories.update(item_categories)
    entry_map["gear"] = gear
    entry_map["materials"] = materials
    entry_map["stage-boxes"] = boxes

    stages_category, stages_entries, stage_rows = build_stages(assets, drops_by_key, boxes)
    categories["stages"] = stages_category
    entry_map["stages"] = stages_entries

    heroes_category, heroes = build_heroes(assets)
    categories["heroes"] = heroes_category
    entry_map["heroes"] = heroes

    effects_category, effects = build_effects(assets)
    categories["effects"] = effects_category
    entry_map["effects"] = effects

    monsters_table = {str(row["MonsterKey"]): row for row in load_table("MonsterInfoData")}
    monsters_category, monsters = build_monsters(assets, stage_rows)
    categories["monsters"] = monsters_category
    entry_map["monsters"] = monsters

    skills_category, skills = build_skills(assets)
    categories["skills"] = skills_category
    entry_map["skills"] = skills

    runes_category, runes = build_runes(assets)
    categories["runes"] = runes_category
    entry_map["runes"] = runes

    pets_category, pets = build_pets(assets, monsters_table, stage_rows)
    categories["pets"] = pets_category
    entry_map["pets"] = pets

    cube_category, cube = build_cube(assets)
    categories["cube"] = cube_category
    entry_map["cube"] = cube

    database_category, database = build_database(assets)
    categories["database"] = database_category
    entry_map["database"] = database

    column_sets = {
        "gear": [
            {"key": "grade", "labelKey": "field.grade"},
            {"key": "gearType", "labelKey": "field.gearType"},
            {"key": "part", "labelKey": "field.part"},
            {"key": "level", "labelKey": "field.level"},
        ],
        "materials": [
            {"key": "grade", "labelKey": "field.grade"},
            {"key": "type", "labelKey": "field.type"},
            {"key": "dropKey", "labelKey": "field.id"},
        ],
        "effects": [
            {"key": "type", "labelKey": "field.type"},
            {"key": "gearType", "labelKey": "field.gearType"},
            {"key": "count", "labelKey": "field.count"},
        ],
        "stage-boxes": [
            {"key": "grade", "labelKey": "field.grade"},
            {"key": "level", "labelKey": "field.level"},
            {"key": "dropKey", "labelKey": "field.id"},
        ],
        "heroes": [
            {"key": "class", "labelKey": "field.class"},
            {"key": "mainWeapon", "labelKey": "field.mainWeapon"},
            {"key": "subWeapon", "labelKey": "field.subWeapon"},
            {"key": "maxHp", "labelKey": "field.maxHp"},
        ],
        "monsters": [
            {"key": "type", "labelKey": "field.type"},
            {"key": "gold", "labelKey": "field.gold"},
            {"key": "exp", "labelKey": "field.exp"},
            {"key": "maxHp", "labelKey": "field.maxHp"},
        ],
        "skills": [
            {"key": "category", "labelKey": "filter.category"},
            {"key": "type", "labelKey": "field.type"},
            {"key": "activation", "labelKey": "field.activation"},
            {"key": "range", "labelKey": "field.range"},
        ],
        "runes": [
            {"key": "level", "labelKey": "field.level"},
            {"key": "type", "labelKey": "field.type"},
            {"key": "count", "labelKey": "field.count"},
        ],
        "pets": [
            {"key": "type", "labelKey": "field.type"},
            {"key": "count", "labelKey": "field.count"},
            {"key": "gold", "labelKey": "field.gold"},
            {"key": "exp", "labelKey": "field.exp"},
        ],
        "stages": [
            {"key": "difficulty", "labelKey": "filter.difficulty"},
            {"key": "act", "labelKey": "field.act"},
            {"key": "stage", "labelKey": "field.stage"},
            {"key": "level", "labelKey": "field.stageLevel"},
            {"key": "boss", "labelKey": "field.boss"},
        ],
        "cube": [
            {"key": "type", "labelKey": "field.type"},
            {"key": "count", "labelKey": "field.count"},
            {"key": "table", "labelKey": "field.table"},
        ],
        "database": [
            {"key": "table", "labelKey": "field.table"},
            {"key": "records", "labelKey": "field.records"},
        ],
    }

    filter_sets = {
        "gear": [
            facet(gear, "grade", "filter.grade"),
            facet(gear, "gearType", "filter.gearType"),
            facet(gear, "part", "filter.part"),
        ],
        "materials": [facet(materials, "grade", "filter.grade"), facet(materials, "type", "filter.type")],
        "stage-boxes": [facet(boxes, "grade", "filter.grade")],
        "effects": [facet(effects, "gearType", "filter.gearType"), facet(effects, "type", "filter.type")],
        "heroes": [facet(heroes, "mainWeapon", "field.mainWeapon")],
        "monsters": [facet(monsters, "type", "filter.type")],
        "skills": [facet(skills, "category", "filter.category"), facet(skills, "activation", "field.activation")],
        "runes": [facet(runes, "type", "filter.type")],
        "pets": [facet(pets, "type", "filter.type")],
        "stages": [facet(stages_entries, "difficulty", "filter.difficulty"), facet(stages_entries, "act", "filter.act")],
        "cube": [facet(cube, "type", "filter.type")],
        "database": [],
    }

    for category_id, entries in entry_map.items():
        write_category(categories[category_id], entries, column_sets.get(category_id, []), filter_sets.get(category_id, []))

    write_json(PUBLIC_GENERATED / "relationships.json", build_relationships(entry_map, stage_rows, drops_by_key))
    write_json(PUBLIC_GENERATED / "market-manifest.json", build_market_manifest(entry_map))
    write_json(PUBLIC_GENERATED / "save-schema.json", build_save_schema())

    for locale, values in TRANSLATIONS.items():
        write_json(LOCALES_DIR / f"{locale}.json", values)

    write_json(PUBLIC_GENERATED / "site-manifest.json", build_manifest(categories, entry_map, assets))
    print(f"Generated site payload in {PUBLIC_GENERATED}")


if __name__ == "__main__":
    main()
