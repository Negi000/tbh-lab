# TBH Lab Product Architecture

## Goal

Build the wiki as a connected database, not isolated category lists. Every page should answer the next practical question:

- Item: what it is, where it drops, which chests contain it, stage odds, market value, and whether the player's save owns it.
- Chest: contents, exact odds, stage sources, and useful level ranges.
- Stage/map: visual map navigation, monsters, waves, chest drops, first-clear rewards, and farm usefulness.
- Monster: stats, stage appearances, pet unlock relevance, and drop links.
- Pet: unlock requirement, current save unlock state, and best stages to farm the target monster.
- Rune: in-game-like tree, per-level effect, total active bonuses, and gold cost planning.
- Save: local-only file reader that enriches all pages without upload.
- Market: cached market snapshots, price history, liquidity, and save inventory valuation.

## Source Layers

1. Static game data
   - `リソース/text`: InfoData tables.
   - `リソース/dump`: enum and schema hints.
   - `リソース/Mono`: StringTable and ItemTable localizations, plus asset metadata.
   - `リソース/image`: icons, maps, heroes, skills, runes.

2. User-local save data
   - User selects an `.es3` file in the browser.
   - The site decrypts in the browser only.
   - No upload, no server persistence, no write-back.
   - Save reader reference: `E:\Auto_TBH\TBH_Manager\tbh_rebuild\save_reader.py`.

3. Market data
   - Public market API data should be fetched through a Cloudflare cached endpoint.
   - Client pages should read cached snapshots, not hammer upstream APIs.
   - Volatile endpoints need short TTL; historical snapshots can be longer-lived.

## Localization Rules

All display text from game data should resolve in this order:

1. `ItemInfoData.NameKey` or other table key through Mono `ItemTable` / `StringTable`.
2. Direct `ItemKey` lookup only when the row's own key is the translation key.
3. Category-specific fallback generated from localized enum pieces.
4. Raw key only in developer/raw table sections, never as the primary page name.

The site payload keeps:

- Raw values for filtering and linking.
- `Localized` display values for table cells, filter buttons, titles, subtitles, and tooltips.

## Save Data Model

Observed `PlayerSaveData` keys:

- `commonSaveData`: version, current stage, max stage, arranged heroes, play time.
- `currenySaveDatas`: gold and currency amounts.
- `heroSaveDatas`: hero level, equipped item unique IDs, equipped skills, unlocked attributes.
- `PetSaveData`: pet unlock/view state.
- `RuneSaveData`: rune levels.
- `itemSaveDatas`: unique item records; `ItemKey` links to wiki item data, `UniqueId` links to slots.
- `inventorySaveDatas`: inventory slots with `ItemUniqueId`.
- `stashSaveDatas`: warehouse slots with `ItemUniqueId`.
- `tradingStashSaveDatas`: trade stash slots with `ItemUniqueId`.
- `aggregateSaveDatas`: kill counts, clear counts, and other aggregate counters.

Client-side joins:

- `slot.ItemUniqueId -> itemSaveDatas.UniqueId -> ItemKey -> wiki item`.
- Equipped items use `heroSaveDatas[].equippedItemIds -> itemSaveDatas.UniqueId`.
- Pet progress uses `PetSaveData` and aggregate kill counters where available.
- Rune planner uses `RuneSaveData` as current active levels.

## Market Architecture For Cloudflare

Recommended route:

- `GET /api/market/items?query=...`: cached item listings, TTL 5-15 minutes.
- `GET /api/market/item/:hashName/history`: cached price history, TTL 30-60 minutes.
- `GET /api/market/stats`: cached status summary, TTL 5-15 minutes.
- `GET /api/market/snapshot`: optional daily or hourly R2 snapshot for heavy pages.

Caching policy:

- Use Cloudflare Cache API for normal responses.
- Use KV only for small metadata and last-success fallback.
- Use R2 only for historical snapshots or larger compressed market dumps.
- Add stale-if-error behavior so the wiki still works if the market API is unavailable.
- Client pages should debounce search and avoid polling unless the user explicitly refreshes.

Save valuation:

1. Parse save locally.
2. Join owned items by `ItemKey` and, where possible, Steam hash/name.
3. Pull cached market snapshot.
4. Show conservative valuation:
   - lowest sell price
   - median sale price
   - listing count
   - 24h volume/liquidity
   - stale timestamp and market status
5. Never transmit the user's save inventory to the server.

## Interaction Plan

### Items

- Primary card/table name localized from `NameKey`.
- Hover tooltip uses game-like panel.
- Detail sections:
  - sources by chest/stage/drop odds
  - base stats and inherent stats
  - material effect pools
  - market panel
  - save ownership and slots if a save is loaded

### Pets

- Detail page shows unlock target and required count.
- Farm table ranks stages by target monster spawn weight.
- Save-loaded state shows unlocked/locked and estimated remaining kills if aggregate data is available.

### Stage Map

- Use actual map art as a clickable stage grid.
- Selecting a stage opens a side panel:
  - monsters and spawn weights
  - boss
  - waves
  - chest drop item and chance
  - first-clear reward
  - hover monster stats

### Runes

- Generate a rune graph from `RuneInfoData.NextRuneKey` / `PreviewRuneKey`.
- Render a pan/zoom canvas or SVG layer with real rune icons.
- Clicking a rune shows:
  - current level
  - max level
  - per-level value and gold cost
  - connected runes
- Planner modes:
  - no save: manual active levels
  - save loaded: initialize from `RuneSaveData`
  - show total active stat bonuses and gold needed to max selected/all reachable nodes

## Build Outputs To Add

- `relationships.json`: reverse indexes for item sources, chest contents, monster stages, pet targets, stage rewards.
- `rune_graph.json`: nodes, edges, levels, costs, icons, localized names.
- `market_manifest.json`: stable mapping from wiki item names/keys to market hash names.
- `save_schema.json`: documented client-side schema for local save parsing.
