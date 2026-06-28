import { useEffect, useMemo, useState, type CSSProperties, type ChangeEvent, type FormEvent, type ReactNode } from "react";
import { readTaskbarHeroSave, type LocaleCode, type Localized, type SaveOwnedItem, type SaveSnapshot } from "./saveReader";

type Translator = (key: string) => string;
type TextResolver = (value: Localized | undefined) => string;

type RefData = {
  categoryId?: string | null;
  entityId?: string | null;
  slug?: string | null;
  href?: string | null;
  title?: Localized;
  rarity?: string | null;
};

type RelationshipPayload = {
  items: Record<string, { item?: RefData | null; sources: RelationSource[]; recipes?: any[] }>;
  chests: Record<string, { chest?: RefData | null; dropKey?: string | number | null; contents: ChestContent[]; sources: RelationSource[] }>;
  monsters: Record<string, { monster?: RefData | null; stages: MonsterStage[]; petTargets: Array<{ pet?: RefData | null; required?: number | null }> }>;
  pets: Record<string, { pet?: RefData | null; targetMonster?: RefData | null; required?: number | null; recommendedStages: MonsterStage[] }>;
  stages: Record<string, { stage?: RefData | null; rewards: Array<{ kind: string; rate?: number | string | null; item?: RefData | null; dropKey?: number | string | null }> }>;
};

type RelationSource = {
  dropKey?: string | number | null;
  sourceType?: string | null;
  chance?: number | string | null;
  stageRate?: number | string | null;
  chest?: RefData | null;
  stage?: (RefData & { difficulty?: string; act?: number; stageNo?: number; stageLevel?: number }) | null;
};

type MonsterStage = {
  stage?: (RefData & { stageLevel?: number; waveAmount?: number }) | null;
  spawnShare?: number | null;
  expectedPerWave?: number | null;
  boss?: boolean;
};

type ChestContent = {
  rewardType: string;
  rewardKey: number | string;
  weightPercent: number;
  groupName: Localized;
  items: RefData[];
};

type MarketManifestItem = {
  itemKey: number;
  categoryId: string | null;
  slug: string | null;
  href: string | null;
  title: Localized;
  icon: string | null;
  rarity: string | null;
  itemType: string | null;
  gearType: string | null;
  part: string | null;
  level: number | null;
  marketable: boolean;
  queries: string[];
};

type MarketManifest = {
  api: { sameOriginBase: string; upstreamReference: string; steamAppId?: string };
  items: MarketManifestItem[];
};

type RuneGraphLite = {
  nodes: Array<{
    id?: string;
    runeKey: number;
    title?: Localized;
    icon?: string | null;
    rarity?: string | null;
    categoryKey?: string;
    categoryColor?: string;
    maxLevel: number;
    levels: Array<{ level: number; costValue: number; effect?: Localized; statName?: Localized; value?: number }>;
  }>;
  totals: { allCost: number; nodeCount: number };
};

type LabManifest = {
  generatedAt: string;
  locales: string[];
  version: string;
  categories: Array<{ id: string; titleKey: string; descriptionKey: string; count: number; listPath: string }>;
  navGroups: Array<{ id: string; items: string[] }>;
};

type SaveSchemaPayload = {
  encryption?: Record<string, string | number>;
  joins?: Record<string, string>;
  knownCollections?: string[];
};

type StageAtlasLite = {
  acts: Array<{ act: number; label?: Localized; stages: PlanStage[] }>;
  difficulties: Array<{ id: string }>;
  generatedFrom: string[];
};

type PlanStage = {
  id: string;
  detailHref?: string | null;
  title: Localized;
  difficulty?: string;
  difficultyLabel?: Localized;
  difficultyColor?: string;
  act?: number;
  stageNo?: number;
  stageLevel?: number;
  waveAmount?: number;
  rewards?: Array<{
    labelKey?: string;
    title?: Localized;
    icon?: string | null;
    rarity?: string | null;
    detailHref?: string | null;
    rate?: string | number | null;
  }>;
};

type MarketItem = {
  hash_name: string;
  name: string;
  name_ja?: string;
  type?: string;
  gear?: string;
  level?: number;
  name_color?: string;
  icon_url?: string;
  sell_price?: number | null;
  median_price?: number | null;
  sell_listings?: number | null;
  volume?: number | null;
  updated_at?: number | null;
  old_price?: number | null;
  chg?: number | null;
  descriptions?: string | null;
  steam_history?: string | null;
};

type MarketItemsResponse = {
  items?: MarketItem[];
  total?: number;
  page?: number;
  pageSize?: number;
};

type MarketStats = {
  items?: number;
  lastRunAt?: number;
  status?: string;
  market?: { state?: string; since?: string; ja?: string; en?: string };
};

type MarketFilterResponse = {
  gears?: Array<{ gear: string; n: number }>;
  levels?: number[];
};

type MarketMoversResponse = {
  up?: MarketItem[];
  down?: MarketItem[];
  window?: number;
};

type MarketHistoryPoint = {
  sell_price?: number | null;
  sell_listings?: number | null;
  recorded_at: number;
};

type MarketItemResponse = {
  item?: MarketItem | null;
  history?: MarketHistoryPoint[];
};

type MarketOrderBook = {
  ok?: boolean;
  cur?: string;
  lowSell?: number | null;
  highBuy?: number | null;
  sellCount?: number;
  buyCount?: number;
  sell?: Array<{ price: number | null; qty: number }>;
  buy?: Array<{ price: number | null; qty: number }>;
};

type MarketCurrency = "usd" | "jpy";
type ValuationScope = "all" | "inventory" | "stash" | "tradingStash" | "equipped";

type ValuationRow = {
  owned: SaveOwnedItem;
  manifest: MarketManifestItem;
  market: MarketItem | null;
};

type PlannerKind = "item" | "pet" | "monster" | "stage";

type PlannerRow = {
  key: string;
  kind: PlannerKind;
  ref: RefData | null | undefined;
  title: string;
  subtitle: string;
  score: number;
  haystack: string;
};

type DropLabKind = "chest" | "item";

type DropLabRow = {
  key: string;
  id: string;
  kind: DropLabKind;
  ref: RefData | null | undefined;
  title: string;
  subtitle: string;
  score: number;
  haystack: string;
};

const STEAM_APP_ID = "3678970";
const MARKET_PAGE_SIZE = 48;
const VALUATION_LIMIT = 120;
const STEAM_FEE_RATE = 1.15;
const marketQuoteCache = new Map<string, Promise<MarketItem | null>>();

function localeBase(locale: LocaleCode) {
  return locale.split("-", 1)[0];
}

function isJapaneseLocale(locale: LocaleCode) {
  return localeBase(locale) === "ja";
}

function intlLocale(locale: LocaleCode) {
  return locale || "en-US";
}

function useJson<T>(path: string | null) {
  const [state, setState] = useState<{ path: string | null; data: T | null; error: string | null }>({ path: null, data: null, error: null });
  useEffect(() => {
    if (!path) {
      return;
    }
    let cancelled = false;
    fetch(path)
      .then((response) => {
        if (!response.ok) {
          throw new Error(path);
        }
        return response.json() as Promise<T>;
      })
      .then((data) => {
        if (!cancelled) {
          setState({ path, data, error: null });
        }
      })
      .catch((error: Error) => {
        if (!cancelled) {
          setState({ path, data: null, error: error.message });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [path]);
  if (!path) {
    return { data: null, error: null, loading: false };
  }
  if (state.path !== path) {
    return { data: null, error: null, loading: true };
  }
  return { data: state.data, error: state.error, loading: false };
}

function localText(value: Localized | undefined, locale: LocaleCode) {
  const base = localeBase(locale);
  return value?.[locale] ?? value?.[base] ?? value?.["en-US"] ?? value?.en ?? value?.["ja-JP"] ?? value?.ja ?? "";
}

function numberText(value: string | number | null | undefined, locale: LocaleCode) {
  const number = Number(value);
  if (Number.isFinite(number)) {
    return new Intl.NumberFormat(intlLocale(locale)).format(number);
  }
  return value === null || value === undefined || value === "" ? "-" : String(value);
}

function percentText(value: string | number | null | undefined, locale: LocaleCode) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "-";
  }
  const rate = number > 100 ? number / 10 : number;
  return `${new Intl.NumberFormat(intlLocale(locale), { maximumFractionDigits: 3 }).format(rate)}%`;
}

function displayValue(value: string | number | Localized | null | undefined, locale: LocaleCode) {
  if (value && typeof value === "object") {
    return localText(value, locale) || "-";
  }
  return numberText(value, locale);
}

function hoursText(seconds: number, locale: LocaleCode) {
  return `${numberText(Math.round((seconds / 3600) * 10) / 10, locale)}h`;
}

function priceText(cents: number | null | undefined, locale: LocaleCode, currency: MarketCurrency = "usd", rate?: number | null) {
  if (!Number.isFinite(Number(cents))) {
    return "-";
  }
  const usd = Number(cents) / 100;
  if (currency === "jpy" && rate) {
    return new Intl.NumberFormat("ja-JP", { style: "currency", currency: "JPY", maximumFractionDigits: 0 }).format(usd * rate);
  }
  return new Intl.NumberFormat(intlLocale(locale), { style: "currency", currency: "USD" }).format(usd);
}

function dateText(seconds: number | null | undefined, locale: LocaleCode) {
  if (!seconds) {
    return "-";
  }
  return new Intl.DateTimeFormat(intlLocale(locale), { dateStyle: "short", timeStyle: "short" }).format(new Date(seconds * 1000));
}

function cleanNotice(value: string) {
  return value.replace(/^⚠️?\s*/u, "");
}

function refLink(ref: RefData | null | undefined, text: TextResolver) {
  if (!ref) {
    return <span className="muted">-</span>;
  }
  const label = text(ref.title);
  return ref.href ? (
    <a className="inline-link" href={ref.href}>
      {label || ref.entityId}
    </a>
  ) : (
    <span>{label || ref.entityId}</span>
  );
}

function marketBase() {
  const env = import.meta.env.VITE_TBH_MARKET_ENDPOINT as string | undefined;
  return (env || "/api/market").replace(/\/$/, "");
}

async function fetchMarketJson<T>(path: string): Promise<T> {
  const response = await fetch(`${marketBase()}/${path.replace(/^\//, "")}`, { headers: { accept: "application/json" } });
  const contentType = response.headers.get("content-type") ?? "";
  if (!response.ok || !contentType.includes("json")) {
    throw new Error(`market:${response.status}`);
  }
  return response.json() as Promise<T>;
}

function marketImage(iconUrl: string | null | undefined) {
  return iconUrl ? `https://community.fastly.steamstatic.com/economy/image/${iconUrl}/64fx64f` : "";
}

function steamMarketUrl(hashName: string) {
  return `https://steamcommunity.com/market/listings/${STEAM_APP_ID}/${encodeURIComponent(hashName)}`;
}

function marketName(item: MarketItem, locale: LocaleCode) {
  return isJapaneseLocale(locale) && item.name_ja ? item.name_ja : item.name;
}

function marketColor(item: MarketItem) {
  return item.name_color ? `#${item.name_color}` : "#d3a13d";
}

function changeText(value: number | null | undefined, locale: LocaleCode) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "-";
  }
  return `${number >= 0 ? "+" : ""}${new Intl.NumberFormat(intlLocale(locale), { maximumFractionDigits: 1 }).format(number * 100)}%`;
}

function dealPercent(item: MarketItem) {
  const lowest = Number(item.sell_price);
  const median = Number(item.median_price);
  if (!Number.isFinite(lowest) || !Number.isFinite(median) || lowest <= 0 || median <= 0 || lowest >= median) {
    return null;
  }
  return Math.round((1 - lowest / median) * 100);
}

function marketStatusText(stats: MarketStats | null, t: Translator, locale: LocaleCode) {
  if (stats?.market?.state === "suspended") {
    return t("market.buyingAvailable");
  }
  if (stats?.market) {
    return cleanNotice(localText({ ja: stats.market.ja, en: stats.market.en }, locale));
  }
  return t("market.cachePolicy");
}

function valuationScopeCount(owned: SaveOwnedItem, scope: ValuationScope) {
  if (scope === "all") {
    return owned.quantity;
  }
  return owned.sources[scope] ?? 0;
}

function valuationRowsForScope(saveSnapshot: SaveSnapshot, manifestByItem: Map<string, MarketManifestItem>, scope: ValuationScope) {
  return saveSnapshot.ownedItems
    .map((owned) => ({ owned, manifest: manifestByItem.get(String(owned.itemKey)), scopedQuantity: valuationScopeCount(owned, scope) }))
    .filter((row): row is { owned: SaveOwnedItem; manifest: MarketManifestItem; scopedQuantity: number } => !!row.manifest && row.scopedQuantity > 0)
    .sort((a, b) => b.scopedQuantity - a.scopedQuantity)
    .slice(0, VALUATION_LIMIT);
}

async function cachedMarketQuote(query: string) {
  const normalized = query.trim().toLowerCase();
  if (!normalized) {
    return null;
  }
  const cached = marketQuoteCache.get(normalized);
  if (cached) {
    return cached;
  }
  const promise = fetchMarketJson<MarketItemsResponse>(`items?${new URLSearchParams({ q: query, pageSize: "6" }).toString()}`)
    .then((data) => data.items?.[0] ?? null)
    .catch(() => null);
  marketQuoteCache.set(normalized, promise);
  return promise;
}

async function mapInBatches<T, U>(rows: T[], size: number, mapper: (row: T) => Promise<U>) {
  const results: U[] = [];
  for (let index = 0; index < rows.length; index += size) {
    results.push(...(await Promise.all(rows.slice(index, index + size).map(mapper))));
  }
  return results;
}

function ownedLookup(saveSnapshot: SaveSnapshot | null) {
  return new Map((saveSnapshot?.ownedItems ?? []).map((item) => [String(item.itemKey), item]));
}

function marketManifestLookup(manifest: MarketManifest | null | undefined) {
  return new Map((manifest?.items ?? []).map((item) => [String(item.itemKey), item]));
}

function flattenPlanStages(stageAtlas: StageAtlasLite | null | undefined) {
  return (stageAtlas?.acts ?? [])
    .flatMap((act) => act.stages ?? [])
    .filter((stage): stage is PlanStage => !!stage?.id)
    .sort((a, b) => Number(a.id) - Number(b.id));
}

function stageByKey(stageAtlas: StageAtlasLite | null | undefined) {
  return new Map(flattenPlanStages(stageAtlas).map((stage) => [String(stage.id), stage]));
}

function findNextStage(saveSnapshot: SaveSnapshot | null, stageAtlas: StageAtlasLite | null | undefined) {
  const stages = flattenPlanStages(stageAtlas);
  const bestKey = Number(saveSnapshot?.maxCompletedStage?.stageKey || saveSnapshot?.currentStage?.stageKey || 0);
  if (!bestKey) {
    return stages[0] ?? null;
  }
  return stages.find((stage) => Number(stage.id) > bestKey) ?? null;
}

function isoDateText(value: string | null | undefined, locale: LocaleCode) {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat(intlLocale(locale), { dateStyle: "medium", timeStyle: "short" }).format(date);
}

function plannerKindLabel(kind: PlannerKind, t: Translator) {
  const keys: Record<PlannerKind, string> = {
    item: "farm.items",
    pet: "farm.pets",
    monster: "farm.monsters",
    stage: "farm.stages",
  };
  return t(keys[kind]);
}

function dropLabKindLabel(kind: DropLabKind, t: Translator) {
  return kind === "chest" ? t("drop.chests") : t("drop.items");
}

export function DropLabWorkbench({
  t,
  text,
  locale,
  saveSnapshot,
}: {
  t: Translator;
  text: TextResolver;
  locale: LocaleCode;
  saveSnapshot: SaveSnapshot | null;
}) {
  const relationshipsState = useJson<RelationshipPayload>("/generated/relationships.json");
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<DropLabKind | "all">("all");
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const owned = useMemo(() => ownedLookup(saveSnapshot), [saveSnapshot]);
  const rows = useMemo(() => {
    const relationships = relationshipsState.data;
    if (!relationships) {
      return [];
    }
    const makeHaystack = (parts: Array<string | number | null | undefined>) => parts.filter(Boolean).join(" ").toLowerCase();
    const chestRows: DropLabRow[] = Object.entries(relationships.chests).map(([id, relation]) => {
      const title = text(relation.chest?.title) || id;
      const samples = relation.contents.flatMap((content) => [text(content.groupName), ...content.items.slice(0, 4).map((item) => text(item.title))]);
      return {
        key: `chest:${id}`,
        id,
        kind: "chest",
        ref: relation.chest,
        title,
        subtitle: `${t("drop.dropKey")} ${relation.dropKey ?? "-"} / ${t("drop.contents")} ${numberText(relation.contents.length, locale)}`,
        score: relation.contents.length + relation.sources.length,
        haystack: makeHaystack([id, title, relation.dropKey, relation.chest?.slug, relation.chest?.rarity, ...samples]),
      };
    });
    const itemRows: DropLabRow[] = Object.entries(relationships.items)
      .filter(([, relation]) => relation.sources.length > 0)
      .map(([id, relation]) => {
        const title = text(relation.item?.title) || id;
        const chests = relation.sources.slice(0, 6).map((source) => text(source.chest?.title));
        const stages = relation.sources.slice(0, 6).map((source) => text(source.stage?.title));
        return {
          key: `item:${id}`,
          id,
          kind: "item",
          ref: relation.item,
          title,
          subtitle: `${t("drop.bestSources")} ${numberText(relation.sources.length, locale)}`,
          score: relation.sources.length,
          haystack: makeHaystack([id, title, relation.item?.slug, relation.item?.rarity, ...chests, ...stages]),
        };
      });
    return [...chestRows, ...itemRows].sort((a, b) => b.score - a.score || a.title.localeCompare(b.title));
  }, [locale, relationshipsState.data, t, text]);
  const visibleRows = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return rows
      .filter((row) => (mode === "all" || row.kind === mode) && (!needle || row.haystack.includes(needle)))
      .slice(0, 100);
  }, [mode, query, rows]);
  const selected = visibleRows.find((row) => row.key === selectedKey) ?? visibleRows[0] ?? null;
  const relationships = relationshipsState.data;

  function submitSearch(event: FormEvent) {
    event.preventDefault();
    setSelectedKey(null);
  }

  return (
    <div className="page-stack tool-page drop-page">
      <section className="page-header panel drop-hero-panel">
        <div>
          <a className="back-link" href="#/">{t("nav.back")}</a>
          <h1>{t("drop.title")}</h1>
          <p>{t("drop.subtitle")}</p>
          <small>{t("drop.rateHint")}</small>
        </div>
        <form className="drop-search-card" onSubmit={submitSearch}>
          <label>
            <span>{t("drop.search")}</span>
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={t("drop.placeholder")} />
          </label>
          <label>
            <span>{t("drop.viewMode")}</span>
            <select value={mode} onChange={(event) => setMode(event.target.value as DropLabKind | "all")}>
              <option value="all">{t("drop.all")}</option>
              <option value="chest">{t("drop.chests")}</option>
              <option value="item">{t("drop.items")}</option>
            </select>
          </label>
        </form>
      </section>

      {relationshipsState.loading ? (
        <section className="panel state-panel compact-state"><h2>{t("state.loading")}</h2></section>
      ) : relationshipsState.error || !relationships ? (
        <section className="panel state-panel compact-state"><h2>{t("state.error")}</h2><p>{relationshipsState.error}</p></section>
      ) : (
        <section className="panel section drop-workbench">
          <div className="section-heading">
            <h2>{t("drop.results")} {numberText(visibleRows.length, locale)}</h2>
            <span>{t("farm.routeCount")} {numberText(rows.length, locale)}</span>
          </div>
          <div className="drop-layout">
            <div className="drop-result-list">
              {visibleRows.length ? (
                visibleRows.map((row) => (
                  <button type="button" className={selected?.key === row.key ? "active" : ""} key={row.key} onClick={() => setSelectedKey(row.key)}>
                    <span>{dropLabKindLabel(row.kind, t)}</span>
                    <strong>{row.title}</strong>
                    <small>{row.subtitle}</small>
                  </button>
                ))
              ) : (
                <p className="empty">{t("state.empty")}</p>
              )}
            </div>
            <aside className="drop-detail-panel">
              {selected ? (
                <>
                  <div className="drop-selected-card">
                    <small>{dropLabKindLabel(selected.kind, t)} / #{selected.id}</small>
                    <h2>{selected.title}</h2>
                    <p>{selected.subtitle}</p>
                    <div className="market-card-actions inline">
                      {selected.ref?.href ? <a href={selected.ref.href}>{selected.kind === "chest" ? t("drop.openChest") : t("drop.openItem")}</a> : null}
                    </div>
                  </div>
                  <DropLabDetails selected={selected} relationships={relationships} owned={owned} t={t} text={text} locale={locale} />
                </>
              ) : (
                <p className="empty">{t("drop.noSelection")}</p>
              )}
            </aside>
          </div>
        </section>
      )}
    </div>
  );
}

function DropLabDetails({
  selected,
  relationships,
  owned,
  t,
  text,
  locale,
}: {
  selected: DropLabRow;
  relationships: RelationshipPayload;
  owned: Map<string, SaveOwnedItem>;
  t: Translator;
  text: TextResolver;
  locale: LocaleCode;
}) {
  if (selected.kind === "chest") {
    const relation = relationships.chests[selected.id];
    return (
      <>
        <RelationList title={t("drop.sources")}>
          {(relation?.sources ?? []).slice(0, 16).map((source, index) => (
            <li key={index}>
              {refLink(source.stage, text)}
              <span>{percentText(source.stageRate, locale)}</span>
              <strong>{t(source.sourceType ?? "")}</strong>
            </li>
          ))}
        </RelationList>
        <div className="drop-content-list">
          <h3>{t("drop.contents")}</h3>
          {(relation?.contents ?? []).slice(0, 20).map((content) => (
            <article className="drop-content-row" key={`${content.rewardType}:${content.rewardKey}`}>
              <div>
                <strong>{text(content.groupName) || content.rewardKey}</strong>
                <span>{content.rewardType} / {percentText(content.weightPercent, locale)}</span>
              </div>
              <div className="drop-item-chip-list">
                {content.items.slice(0, 10).map((item) => (
                  <a href={item.href ?? "#"} className={`mini-rarity-chip rarity-${item.rarity ?? "NONE"}`} key={`${content.rewardKey}:${item.entityId}`}>
                    {text(item.title) || item.entityId}
                  </a>
                ))}
              </div>
            </article>
          ))}
        </div>
      </>
    );
  }
  const relation = relationships.items[selected.id];
  const ownedRow = owned.get(selected.id);
  return (
    <>
      {ownedRow ? (
        <RelationCard
          title={t("drop.ownedHint")}
          rows={[
            [t("save.owned"), numberText(ownedRow.quantity, locale)],
            [t("save.stash"), numberText(ownedRow.sources.stash, locale)],
            [t("save.equipped"), numberText(ownedRow.sources.equipped, locale)],
          ]}
        />
      ) : null}
      <RelationList title={t("drop.bestSources")}>
        {(relation?.sources ?? []).slice(0, 20).map((source, index) => (
          <li key={index}>
            {refLink(source.chest, text)}
            <span>{percentText(source.chance, locale)}</span>
            {refLink(source.stage, text)}
          </li>
        ))}
      </RelationList>
    </>
  );
}

export function FarmPlannerWorkbench({
  t,
  text,
  locale,
}: {
  t: Translator;
  text: TextResolver;
  locale: LocaleCode;
}) {
  const relationshipsState = useJson<RelationshipPayload>("/generated/relationships.json");
  const marketManifestState = useJson<MarketManifest>("/generated/market-manifest.json");
  const [query, setQuery] = useState("");
  const [kindFilter, setKindFilter] = useState<PlannerKind | "all">("all");
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const manifestByItem = useMemo(() => marketManifestLookup(marketManifestState.data), [marketManifestState.data]);
  const rows = useMemo(() => {
    const relationships = relationshipsState.data;
    if (!relationships) {
      return [];
    }
    const makeHaystack = (parts: Array<string | number | null | undefined>) => parts.filter(Boolean).join(" ").toLowerCase();
    const itemRows: PlannerRow[] = Object.entries(relationships.items).map(([key, relation]) => {
      const title = text(relation.item?.title) || key;
      const chestNames = relation.sources.slice(0, 5).map((source) => text(source.chest?.title));
      return {
        key: `item:${key}`,
        kind: "item",
        ref: relation.item,
        title,
        subtitle: `${t("relation.sources")} ${numberText(relation.sources.length, locale)}`,
        score: relation.sources.length,
        haystack: makeHaystack([key, title, relation.item?.slug, relation.item?.rarity, ...chestNames]),
      };
    });
    const petRows: PlannerRow[] = Object.entries(relationships.pets).map(([key, relation]) => {
      const title = text(relation.pet?.title) || key;
      const target = text(relation.targetMonster?.title);
      return {
        key: `pet:${key}`,
        kind: "pet",
        ref: relation.pet,
        title,
        subtitle: `${target || t("relation.petTarget")} / ${numberText(relation.required, locale)}`,
        score: relation.recommendedStages.length,
        haystack: makeHaystack([key, title, target, relation.pet?.slug, relation.targetMonster?.entityId]),
      };
    });
    const monsterRows: PlannerRow[] = Object.entries(relationships.monsters).map(([key, relation]) => {
      const title = text(relation.monster?.title) || key;
      return {
        key: `monster:${key}`,
        kind: "monster",
        ref: relation.monster,
        title,
        subtitle: `${t("relation.stageAppearances")} ${numberText(relation.stages.length, locale)}`,
        score: relation.stages.length + relation.petTargets.length,
        haystack: makeHaystack([key, title, relation.monster?.slug, ...relation.stages.slice(0, 5).map((stage) => text(stage.stage?.title))]),
      };
    });
    const stageRows: PlannerRow[] = Object.entries(relationships.stages).map(([key, relation]) => {
      const title = text(relation.stage?.title) || key;
      return {
        key: `stage:${key}`,
        kind: "stage",
        ref: relation.stage,
        title,
        subtitle: `${t("stageAtlas.rewards")} ${numberText(relation.rewards.length, locale)}`,
        score: relation.rewards.length,
        haystack: makeHaystack([key, title, relation.stage?.slug, ...relation.rewards.slice(0, 5).map((reward) => text(reward.item?.title))]),
      };
    });
    return [...itemRows, ...petRows, ...monsterRows, ...stageRows].sort((a, b) => b.score - a.score || a.title.localeCompare(b.title));
  }, [locale, relationshipsState.data, t, text]);
  const visibleRows = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return rows
      .filter((row) => (kindFilter === "all" || row.kind === kindFilter) && (!needle || row.haystack.includes(needle)))
      .slice(0, 80);
  }, [kindFilter, query, rows]);
  const selected = visibleRows.find((row) => row.key === selectedKey) ?? visibleRows[0] ?? null;
  const selectedId = selected?.key.split(":")[1] ?? "";
  const relationships = relationshipsState.data;
  const selectedMarket = selected?.kind === "item" ? manifestByItem.get(selectedId) : undefined;

  function submitSearch(event: FormEvent) {
    event.preventDefault();
    setSelectedKey(null);
  }

  return (
    <div className="page-stack tool-page farm-page">
      <section className="page-header panel farm-hero-panel">
        <div>
          <a className="back-link" href="#/">{t("nav.back")}</a>
          <h1>{t("farm.title")}</h1>
          <p>{t("farm.subtitle")}</p>
          <small>{t("farm.sourceHint")}</small>
        </div>
        <form className="farm-search-card" onSubmit={submitSearch}>
          <label>
            <span>{t("farm.search")}</span>
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={t("farm.placeholder")} />
          </label>
          <label>
            <span>{t("farm.targetType")}</span>
            <select value={kindFilter} onChange={(event) => setKindFilter(event.target.value as PlannerKind | "all")}>
              <option value="all">{t("farm.allTargets")}</option>
              <option value="item">{t("farm.items")}</option>
              <option value="pet">{t("farm.pets")}</option>
              <option value="monster">{t("farm.monsters")}</option>
              <option value="stage">{t("farm.stages")}</option>
            </select>
          </label>
        </form>
      </section>

      {relationshipsState.loading ? (
        <section className="panel state-panel compact-state"><h2>{t("state.loading")}</h2></section>
      ) : relationshipsState.error || !relationships ? (
        <section className="panel state-panel compact-state"><h2>{t("state.error")}</h2><p>{relationshipsState.error}</p></section>
      ) : (
        <section className="panel section farm-workbench">
          <div className="section-heading">
            <h2>{t("farm.results")} {numberText(visibleRows.length, locale)}</h2>
            <span>{t("farm.routeCount")} {numberText(rows.length, locale)}</span>
          </div>
          <div className="farm-layout">
            <div className="farm-result-list">
              {visibleRows.length ? (
                visibleRows.map((row) => (
                  <button
                    type="button"
                    className={selected?.key === row.key ? "active" : ""}
                    key={row.key}
                    onClick={() => setSelectedKey(row.key)}
                  >
                    <span>{plannerKindLabel(row.kind, t)}</span>
                    <strong>{row.title}</strong>
                    <small>{row.subtitle}</small>
                  </button>
                ))
              ) : (
                <p className="empty">{t("state.empty")}</p>
              )}
            </div>

            <aside className="farm-detail-panel">
              {selected ? (
                <>
                  <div className="farm-selected-card">
                    <small>{t("farm.selected")} / {plannerKindLabel(selected.kind, t)}</small>
                    <h2>{selected.title}</h2>
                    <p>{selected.subtitle}</p>
                    <div className="market-card-actions inline">
                      {selected.ref?.href ? <a href={selected.ref.href}>{t("farm.openDetail")}</a> : null}
                      {selectedMarket ? <a href={`#/category/market?q=${encodeURIComponent(selectedMarket.queries[0] ?? selected.title)}`}>{t("farm.openMarket")}</a> : null}
                    </div>
                  </div>
                  <FarmPlannerDetails
                    selected={selected}
                    selectedId={selectedId}
                    relationships={relationships}
                    t={t}
                    text={text}
                    locale={locale}
                  />
                </>
              ) : (
                <p className="empty">{t("farm.noSelection")}</p>
              )}
            </aside>
          </div>
        </section>
      )}
    </div>
  );
}

function FarmPlannerDetails({
  selected,
  selectedId,
  relationships,
  t,
  text,
  locale,
}: {
  selected: PlannerRow;
  selectedId: string;
  relationships: RelationshipPayload;
  t: Translator;
  text: TextResolver;
  locale: LocaleCode;
}) {
  if (selected.kind === "item") {
    const relation = relationships.items[selectedId];
    return (
      <RelationList title={t("farm.bestSources")}>
        {(relation?.sources ?? []).slice(0, 14).map((source, index) => (
          <li key={index}>
            {refLink(source.chest, text)}
            <span>{percentText(source.chance, locale)}</span>
            {refLink(source.stage, text)}
          </li>
        ))}
      </RelationList>
    );
  }
  if (selected.kind === "pet") {
    const relation = relationships.pets[selectedId];
    return (
      <>
        <RelationCard title={t("relation.petTarget")} rows={[[text(relation?.targetMonster?.title) || "-", numberText(relation?.required, locale)]]} />
        <RelationList title={t("farm.recommendedStages")}>
          {(relation?.recommendedStages ?? []).slice(0, 14).map((stage, index) => (
            <li key={index}>
              {refLink(stage.stage, text)}
              <span>{percentText(stage.spawnShare, locale)}</span>
              <strong>{t("farm.expected")} {numberText(stage.expectedPerWave, locale)}</strong>
            </li>
          ))}
        </RelationList>
      </>
    );
  }
  if (selected.kind === "monster") {
    const relation = relationships.monsters[selectedId];
    return (
      <>
        <RelationList title={t("relation.stageAppearances")}>
          {(relation?.stages ?? []).slice(0, 16).map((stage, index) => (
            <li key={index}>
              {refLink(stage.stage, text)}
              <span>{stage.boss ? t("stageAtlas.boss") : percentText(stage.spawnShare, locale)}</span>
              <strong>{t("farm.expected")} {numberText(stage.expectedPerWave, locale)}</strong>
            </li>
          ))}
        </RelationList>
        {relation?.petTargets.length ? (
          <RelationList title={t("farm.petTargets")}>
            {relation.petTargets.map((target, index) => (
              <li key={index}>
                {refLink(target.pet, text)}
                <span>{numberText(target.required, locale)}</span>
              </li>
            ))}
          </RelationList>
        ) : null}
      </>
    );
  }
  const relation = relationships.stages[selectedId];
  return (
    <RelationList title={t("farm.stageRewards")}>
      {(relation?.rewards ?? []).slice(0, 16).map((reward, index) => (
        <li key={index}>
          {reward.item ? refLink(reward.item, text) : <span>{reward.dropKey}</span>}
          <span>{reward.rate ? percentText(reward.rate, locale) : t(reward.kind)}</span>
        </li>
      ))}
    </RelationList>
  );
}

export function ProgressPlannerWorkbench({
  t,
  text,
  locale,
  saveSnapshot,
  onSaveLoaded,
}: {
  t: Translator;
  text: TextResolver;
  locale: LocaleCode;
  saveSnapshot: SaveSnapshot | null;
  onSaveLoaded: (snapshot: SaveSnapshot) => void;
}) {
  const relationshipsState = useJson<RelationshipPayload>("/generated/relationships.json");
  const marketManifestState = useJson<MarketManifest>("/generated/market-manifest.json");
  const runeGraphState = useJson<RuneGraphLite>("/generated/rune-graph.json");
  const stageAtlasState = useJson<StageAtlasLite>("/generated/stage-atlas.json");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const manifestByItem = useMemo(() => marketManifestLookup(marketManifestState.data), [marketManifestState.data]);
  const stagesByKey = useMemo(() => stageByKey(stageAtlasState.data), [stageAtlasState.data]);
  const allStages = useMemo(() => flattenPlanStages(stageAtlasState.data), [stageAtlasState.data]);
  const currentStage = saveSnapshot?.currentStage ? stagesByKey.get(String(saveSnapshot.currentStage.stageKey)) ?? null : null;
  const bestStage = saveSnapshot?.maxCompletedStage ? stagesByKey.get(String(saveSnapshot.maxCompletedStage.stageKey)) ?? null : null;
  const nextStage = useMemo(() => findNextStage(saveSnapshot, stageAtlasState.data), [saveSnapshot, stageAtlasState.data]);
  const stageProgress = useMemo(() => {
    const bestKey = Number(saveSnapshot?.maxCompletedStage?.stageKey ?? 0);
    const reached = bestKey ? allStages.filter((stage) => Number(stage.id) <= bestKey).length : 0;
    return { reached, total: allStages.length, percent: allStages.length ? Math.round((reached / allStages.length) * 100) : 0 };
  }, [allStages, saveSnapshot]);
  const runePlan = useMemo(() => {
    const graph = runeGraphState.data;
    if (!graph) {
      return null;
    }
    let activeNodes = 0;
    let currentLevels = 0;
    let maxLevels = 0;
    let spentCost = 0;
    let remainingCost = 0;
    const allCandidates = graph.nodes
      .map((node) => {
        const currentLevel = Math.max(0, Math.min(node.maxLevel, Number(saveSnapshot?.runeLevels[String(node.runeKey)]) || 0));
        if (currentLevel > 0) {
          activeNodes += 1;
        }
        currentLevels += currentLevel;
        maxLevels += node.maxLevel;
        node.levels.forEach((level) => {
          const cost = Number(level.costValue) || 0;
          if (Number(level.level) <= currentLevel) {
            spentCost += cost;
          } else {
            remainingCost += cost;
          }
        });
        const next = node.levels.find((level) => Number(level.level) > currentLevel);
        return next
          ? {
              node,
              currentLevel,
              nextLevel: Number(next.level),
              cost: Number(next.costValue) || 0,
              effect: next.effect,
              affordable: saveSnapshot ? Number(next.costValue) <= saveSnapshot.gold : true,
            }
          : null;
      })
      .filter((row): row is NonNullable<typeof row> => !!row)
      .sort((a, b) => Number(b.affordable) - Number(a.affordable) || a.cost - b.cost);
    return {
      activeNodes,
      currentLevels,
      maxLevels,
      spentCost,
      remainingCost,
      candidates: allCandidates.slice(0, 14),
      affordableCount: allCandidates.filter((candidate) => candidate.affordable).length,
    };
  }, [runeGraphState.data, saveSnapshot]);
  const petGoals = useMemo(() => {
    const relationships = relationshipsState.data;
    if (!relationships) {
      return [];
    }
    const unlocked = new Set((saveSnapshot?.pets ?? []).filter((pet) => pet.unlocked).map((pet) => String(pet.petKey)));
    return Object.entries(relationships.pets)
      .map(([key, relation]) => ({ key, relation }))
      .filter(({ key }) => !saveSnapshot || !unlocked.has(key))
      .sort((a, b) => (Number(b.relation.recommendedStages[0]?.expectedPerWave) || 0) - (Number(a.relation.recommendedStages[0]?.expectedPerWave) || 0))
      .slice(0, 8);
  }, [relationshipsState.data, saveSnapshot]);
  const inventoryRows = useMemo(() => {
    if (saveSnapshot) {
      return saveSnapshot.ownedItems
        .map((owned) => ({ owned, manifest: manifestByItem.get(String(owned.itemKey)) }))
        .filter((row): row is { owned: SaveOwnedItem; manifest: MarketManifestItem } => !!row.manifest && row.manifest.marketable)
        .sort((a, b) => b.owned.quantity - a.owned.quantity)
        .slice(0, 12);
    }
    return (marketManifestState.data?.items ?? [])
      .filter((item) => item.marketable)
      .sort((a, b) => (Number(b.level) || 0) - (Number(a.level) || 0))
      .slice(0, 12)
      .map((manifest) => ({ owned: null, manifest }));
  }, [manifestByItem, marketManifestState.data, saveSnapshot]);
  const unlockedPets = saveSnapshot?.pets.filter((pet) => pet.unlocked).length ?? 0;
  const totalPets = saveSnapshot?.pets.length || Object.keys(relationshipsState.data?.pets ?? {}).length;

  async function handleFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      onSaveLoaded(await readTaskbarHeroSave(file));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : t("save.error"));
    } finally {
      setBusy(false);
      event.target.value = "";
    }
  }

  return (
    <div className="page-stack tool-page progress-page">
      <section className="page-header panel progress-hero-panel">
        <div>
          <a className="back-link" href="#/">{t("nav.back")}</a>
          <h1>{t("plan.title")}</h1>
          <p>{t("plan.subtitle")}</p>
          <small>{t("plan.loadHint")}</small>
        </div>
        <div className="progress-load-card">
          <label className="file-button">
            <input type="file" accept=".es3,.bak,application/octet-stream" onChange={handleFile} />
            <span>{busy ? t("state.loading") : t("plan.loadSave")}</span>
          </label>
          <a className="inline-link" href="#/category/my-save">{t("plan.openSave")}</a>
        </div>
      </section>

      {error ? <section className="panel state-panel compact-state"><h2>{t("save.error")}</h2><p>{error}</p></section> : null}
      {!saveSnapshot ? <section className="panel progress-static-note"><p>{t("plan.staticMode")}</p></section> : null}

      <section className="panel section progress-overview-panel">
        <div className="section-heading">
          <h2>{t("plan.overview")}</h2>
          <span>{saveSnapshot ? saveSnapshot.fileName : t("save.notLoaded")}</span>
        </div>
        <div className="stat-grid save-stat-grid">
          <SaveMetric label={t("field.gold")} value={saveSnapshot ? numberText(saveSnapshot.gold, locale) : "-"} />
          <SaveMetric label={t("plan.progress")} value={`${numberText(stageProgress.reached, locale)} / ${numberText(stageProgress.total, locale)} (${numberText(stageProgress.percent, locale)}%)`} />
          <SaveMetric label={t("save.pets")} value={`${numberText(unlockedPets, locale)} / ${numberText(totalPets, locale)}`} />
          <SaveMetric label={t("save.runeLevels")} value={runePlan ? `${numberText(runePlan.currentLevels, locale)} / ${numberText(runePlan.maxLevels, locale)}` : "-"} />
        </div>
      </section>

      <section className="progress-grid">
        <article className="panel section progress-card progress-stage-card">
          <div className="section-heading">
            <h2>{t("plan.campaign")}</h2>
            <a href="#/category/stages">{t("plan.openStages")}</a>
          </div>
          <div className="progress-stage-stack">
            <ProgressStageRow label={t("plan.current")} route={saveSnapshot?.currentStage} stage={currentStage} text={text} locale={locale} />
            <ProgressStageRow label={t("plan.best")} route={saveSnapshot?.maxCompletedStage} stage={bestStage} text={text} locale={locale} />
            <ProgressStageRow label={t("plan.nextStage")} route={null} stage={nextStage} text={text} locale={locale} fallback={t("plan.noNextStage")} />
          </div>
        </article>

        <article className="panel section progress-card">
          <div className="section-heading">
            <h2>{t("plan.runeBudget")}</h2>
            <a href="#/category/runes">{t("save.openRunePlanner")}</a>
          </div>
          <div className="progress-mini-metrics">
            <SaveMetric label={t("save.spentRuneCost")} value={numberText(runePlan?.spentCost, locale)} />
            <SaveMetric label={t("save.remainingRuneCost")} value={numberText(runePlan?.remainingCost, locale)} />
            <SaveMetric label={t("plan.affordableCount")} value={numberText(runePlan?.affordableCount, locale)} />
          </div>
          <div className="progress-rune-list">
            {(runePlan?.candidates ?? []).length ? (
              runePlan?.candidates.map((candidate) => (
                <a className={`progress-rune-row ${candidate.affordable ? "affordable" : ""}`} href="#/category/runes" key={candidate.node.runeKey}>
                  {candidate.node.icon ? <img src={candidate.node.icon} alt="" /> : <span className="progress-icon-placeholder" />}
                  <span>
                    <strong>{text(candidate.node.title) || `#${candidate.node.runeKey}`}</strong>
                    <small>{numberText(candidate.currentLevel, locale)} to {numberText(candidate.nextLevel, locale)} / {displayValue(candidate.effect, locale)}</small>
                  </span>
                  <em>{numberText(candidate.cost, locale)}</em>
                </a>
              ))
            ) : (
              <p className="empty">{t("plan.noAffordableRunes")}</p>
            )}
          </div>
        </article>

        <article className="panel section progress-card">
          <div className="section-heading">
            <h2>{t("plan.petHunts")}</h2>
            <a href="#/category/farm-planner">{t("plan.openFarm")}</a>
          </div>
          <div className="progress-pet-list">
            {petGoals.length ? (
              petGoals.map(({ key, relation }) => {
                const stage = relation.recommendedStages[0];
                return (
                  <div className="progress-pet-row" key={key}>
                    <div>
                      <strong>{refLink(relation.pet, text)}</strong>
                      <small>{t("relation.petTarget")}: {refLink(relation.targetMonster, text)} / {t("plan.required")} {numberText(relation.required, locale)}</small>
                    </div>
                    {stage ? (
                      <a href={stage.stage?.href ?? "#/category/stages"}>
                        <span>{text(stage.stage?.title)}</span>
                        <em>{percentText(stage.spawnShare, locale)} / {numberText(stage.expectedPerWave, locale)}</em>
                      </a>
                    ) : null}
                  </div>
                );
              })
            ) : (
              <p className="empty">{t("save.noPetGoals")}</p>
            )}
          </div>
        </article>

        <article className="panel section progress-card">
          <div className="section-heading">
            <h2>{t("plan.inventoryActions")}</h2>
            <a href="#/category/market">{t("market.valuation")}</a>
          </div>
          <div className="progress-inventory-list">
            {inventoryRows.map(({ owned, manifest }) => (
              <a className="progress-inventory-row" href={manifest.href ?? "#/category/gear"} key={manifest.itemKey}>
                {manifest.icon ? <img src={manifest.icon} alt="" /> : <span className="progress-icon-placeholder" />}
                <span>
                  <strong>{text(manifest.title)}</strong>
                  <small>{manifest.gearType ?? manifest.itemType ?? "-"} / {manifest.rarity ?? "-"}</small>
                </span>
                <em>{owned ? numberText(owned.quantity, locale) : numberText(manifest.level, locale)}</em>
              </a>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
}

function ProgressStageRow({
  label,
  route,
  stage,
  text,
  locale,
  fallback = "-",
}: {
  label: string;
  route: SaveSnapshot["currentStage"] | null | undefined;
  stage: PlanStage | null | undefined;
  text: TextResolver;
  locale: LocaleCode;
  fallback?: string;
}) {
  const title = text(stage?.title) || text(route?.label) || fallback;
  const reward = stage?.rewards?.[0];
  const href = stage?.detailHref ?? "#/category/stages";
  return (
    <a className="progress-stage-row" href={href}>
      <span>
        <small>{label}</small>
        <strong>{title}</strong>
        <em>
          {text(stage?.difficultyLabel ?? route?.difficultyLabel) || route?.difficulty || "-"} / Lv {numberText(stage?.stageLevel, locale)}
        </em>
      </span>
      <span>
        <small>{reward ? text(reward.title) : "-"}</small>
        <strong>{reward?.rate ? percentText(reward.rate, locale) : numberText(stage?.waveAmount, locale)}</strong>
      </span>
    </a>
  );
}

export function LabStatusWorkbench({
  t,
  text,
  locale,
}: {
  t: Translator;
  text: TextResolver;
  locale: LocaleCode;
}) {
  const manifestState = useJson<LabManifest>("/generated/site-manifest.json");
  const relationshipsState = useJson<RelationshipPayload>("/generated/relationships.json");
  const marketManifestState = useJson<MarketManifest>("/generated/market-manifest.json");
  const saveSchemaState = useJson<SaveSchemaPayload>("/generated/save-schema.json");
  const runeGraphState = useJson<RuneGraphLite>("/generated/rune-graph.json");
  const stageAtlasState = useJson<StageAtlasLite>("/generated/stage-atlas.json");
  const [marketStats, setMarketStats] = useState<MarketStats | null>(null);
  const [marketError, setMarketError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchMarketJson<MarketStats>("stats")
      .then((stats) => {
        if (!cancelled) {
          setMarketStats(stats);
          setMarketError(null);
        }
      })
      .catch((error: Error) => {
        if (!cancelled) {
          setMarketError(error.message);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const manifest = manifestState.data;
  const relationships = relationshipsState.data;
  const marketManifest = marketManifestState.data;
  const saveSchema = saveSchemaState.data;
  const runeGraph = runeGraphState.data;
  const stageAtlas = stageAtlasState.data;
  const totalEntries = manifest?.categories.reduce((sum, category) => sum + (Number(category.count) || 0), 0) ?? 0;
  const relationshipCount = relationships
    ? Object.keys(relationships.items).length +
      Object.keys(relationships.chests).length +
      Object.keys(relationships.monsters).length +
      Object.keys(relationships.pets).length +
      Object.keys(relationships.stages).length
    : 0;
  const stageCount = stageAtlas?.acts.reduce((sum, act) => sum + act.stages.length, 0) ?? 0;
  const marketableCount = marketManifest?.items.filter((item) => item.marketable).length ?? 0;
  const generatedLinks = [
    ["site-manifest.json", "/generated/site-manifest.json"],
    ["relationships.json", "/generated/relationships.json"],
    ["market-manifest.json", "/generated/market-manifest.json"],
    ["save-schema.json", "/generated/save-schema.json"],
    ["rune-graph.json", "/generated/rune-graph.json"],
    ["stage-atlas.json", "/generated/stage-atlas.json"],
  ];

  return (
    <div className="page-stack tool-page lab-page">
      <section className="page-header panel lab-hero-panel">
        <div>
          <a className="back-link" href="#/">{t("nav.back")}</a>
          <h1>{t("lab.title")}</h1>
          <p>{t("lab.subtitle")}</p>
          <small>{t("lab.lastBuildNote")}</small>
        </div>
        <div className="lab-status-sigil">
          <strong>TBH</strong>
          <span>LAB</span>
        </div>
      </section>

      <section className="panel section lab-summary-panel">
        <div className="stat-grid save-stat-grid">
          <SaveMetric label={t("lab.generated")} value={isoDateText(manifest?.generatedAt, locale)} />
          <SaveMetric label={t("lab.categories")} value={numberText(manifest?.categories.length, locale)} />
          <SaveMetric label={t("lab.entries")} value={numberText(totalEntries, locale)} />
          <SaveMetric label={t("lab.locales")} value={(manifest?.locales ?? []).join(" / ") || "-"} />
        </div>
      </section>

      <section className="panel section lab-board-panel">
        <div className="section-heading">
          <h2>{t("lab.datasets")}</h2>
          <span>{manifestState.loading || relationshipsState.loading ? t("state.loading") : t("lab.ok")}</span>
        </div>
        <div className="lab-card-grid">
          <LabStatusCard
            title={t("lab.relationships")}
            status={relationships ? t("lab.ok") : t("lab.pending")}
            value={numberText(relationshipCount, locale)}
            body={t("lab.relationshipSummary")}
          />
          <LabStatusCard
            title={t("lab.market")}
            status={marketStats || marketManifest ? t("lab.ok") : t("lab.pending")}
            value={`${numberText(marketableCount, locale)} / ${numberText(marketManifest?.items.length, locale)}`}
            body={marketStats ? marketStatusText(marketStats, t, locale) : marketError || t("lab.marketSummary")}
          />
          <LabStatusCard
            title={t("lab.saveSchema")}
            status={saveSchema ? t("lab.ok") : t("lab.pending")}
            value={numberText(saveSchema?.knownCollections?.length, locale)}
            body={t("lab.localOnlySave")}
          />
          <LabStatusCard
            title={t("lab.runes")}
            status={runeGraph ? t("lab.ok") : t("lab.pending")}
            value={`${numberText(runeGraph?.totals.nodeCount, locale)} / ${numberText(runeGraph?.totals.allCost, locale)}`}
            body={`${t("rune.nodeCount")} / ${t("rune.maxAll")}`}
          />
          <LabStatusCard
            title={t("lab.stages")}
            status={stageAtlas ? t("lab.ok") : t("lab.pending")}
            value={`${numberText(stageCount, locale)} / ${numberText(stageAtlas?.difficulties.length, locale)}`}
            body={(stageAtlas?.generatedFrom ?? []).join(" / ") || t("stageAtlas.title")}
          />
          <LabStatusCard
            title={t("lab.cloudflare")}
            status={manifest && marketManifest ? t("lab.ok") : t("lab.pending")}
            value={t("lab.staticBuildReady")}
            body={`${t("lab.filesReady")} / ${t("lab.functionsReady")}`}
          />
        </div>
      </section>

      <section className="panel section lab-source-panel">
        <div className="section-heading">
          <h2>{t("lab.sourceFiles")}</h2>
        </div>
        <div className="lab-source-grid">
          {generatedLinks.map(([label, href]) => (
            <a href={href} target="_blank" rel="noreferrer" key={href}>
              <span>{label}</span>
              <strong>{t("lab.openData")}</strong>
            </a>
          ))}
        </div>
      </section>

      {manifest ? (
        <section className="panel section lab-category-panel">
          <div className="section-heading">
            <h2>{t("lab.categories")}</h2>
          </div>
          <div className="lab-category-list">
            {manifest.categories.map((category) => (
              <a href={`#/category/${category.id}`} key={category.id}>
                <span>{t(category.titleKey)}</span>
                <strong>{numberText(category.count, locale)}</strong>
                <small>{text({ ja: t(category.descriptionKey), en: t(category.descriptionKey) })}</small>
              </a>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}

function LabStatusCard({
  title,
  status,
  value,
  body,
}: {
  title: string;
  status: string;
  value: string;
  body: string;
}) {
  return (
    <article className="lab-card">
      <div>
        <h3>{title}</h3>
        <span>{status}</span>
      </div>
      <strong>{value}</strong>
      <p>{body}</p>
    </article>
  );
}

export function SaveWorkbench({
  t,
  text,
  locale,
  saveSnapshot,
  onSaveLoaded,
}: {
  t: Translator;
  text: TextResolver;
  locale: LocaleCode;
  saveSnapshot: SaveSnapshot | null;
  onSaveLoaded: (snapshot: SaveSnapshot) => void;
}) {
  const manifestState = useJson<MarketManifest>("/generated/market-manifest.json");
  const relationshipsState = useJson<RelationshipPayload>("/generated/relationships.json");
  const runeGraphState = useJson<RuneGraphLite>("/generated/rune-graph.json");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const manifestByItem = useMemo(() => marketManifestLookup(manifestState.data), [manifestState.data]);
  const currentStageRef = saveSnapshot?.currentStage
    ? relationshipsState.data?.stages?.[String(saveSnapshot.currentStage.stageKey)]?.stage ?? null
    : null;
  const bestStageRef = saveSnapshot?.maxCompletedStage
    ? relationshipsState.data?.stages?.[String(saveSnapshot.maxCompletedStage.stageKey)]?.stage ?? null
    : null;
  const petGoalRows = useMemo(() => {
    if (!relationshipsState.data || !saveSnapshot) {
      return [];
    }
    const unlocked = new Set(saveSnapshot.pets.filter((pet) => pet.unlocked).map((pet) => String(pet.petKey)));
    return Object.entries(relationshipsState.data.pets)
      .map(([key, relation]) => ({ key, relation }))
      .filter(({ key }) => !unlocked.has(key))
      .sort((a, b) => (Number(b.relation.recommendedStages[0]?.expectedPerWave) || 0) - (Number(a.relation.recommendedStages[0]?.expectedPerWave) || 0))
      .slice(0, 6);
  }, [relationshipsState.data, saveSnapshot]);
  const runeSummary = useMemo(() => {
    if (!runeGraphState.data || !saveSnapshot) {
      return null;
    }
    let activeNodes = 0;
    let currentLevels = 0;
    let maxLevels = 0;
    let spentCost = 0;
    let remainingCost = 0;
    runeGraphState.data.nodes.forEach((node) => {
      const level = Math.max(0, Math.min(node.maxLevel, Number(saveSnapshot.runeLevels[String(node.runeKey)]) || 0));
      if (level > 0) {
        activeNodes += 1;
      }
      currentLevels += level;
      maxLevels += node.maxLevel;
      node.levels.forEach((row) => {
        const cost = Number(row.costValue) || 0;
        if (Number(row.level) <= level) {
          spentCost += cost;
        } else {
          remainingCost += cost;
        }
      });
    });
    return {
      activeNodes,
      currentLevels,
      maxLevels,
      spentCost,
      remainingCost,
      nodeCount: runeGraphState.data.totals.nodeCount,
    };
  }, [runeGraphState.data, saveSnapshot]);
  const ownedPreview = (saveSnapshot?.ownedItems ?? [])
    .map((owned) => ({ owned, manifest: manifestByItem.get(String(owned.itemKey)) }))
    .filter((row): row is { owned: SaveOwnedItem; manifest: MarketManifestItem } => !!row.manifest)
    .slice(0, 18);

  async function handleFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      onSaveLoaded(await readTaskbarHeroSave(file));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : t("save.error"));
    } finally {
      setBusy(false);
      event.target.value = "";
    }
  }

  return (
    <div className="page-stack tool-page">
      <section className="page-header panel save-hero-panel">
        <div>
          <a className="back-link" href="#/">{t("nav.back")}</a>
          <h1>{t("save.title")}</h1>
          <p>{t("save.subtitle")}</p>
          <small>{t("save.privacy")}</small>
        </div>
        <label className="file-button">
          <input type="file" accept=".es3,.bak,application/octet-stream" onChange={handleFile} />
          <span>{busy ? t("state.loading") : t("save.pickFile")}</span>
        </label>
      </section>

      {error ? <section className="panel state-panel compact-state"><h2>{t("save.error")}</h2><p>{error}</p></section> : null}

      {saveSnapshot ? (
        <>
          <section className="panel section">
            <div className="section-heading">
              <h2>{t("save.loaded")}</h2>
              <span>{saveSnapshot.fileName}</span>
            </div>
            <div className="stat-grid save-stat-grid">
              <SaveMetric label={t("save.version")} value={saveSnapshot.version || "-"} />
              <SaveMetric label={t("save.playTime")} value={hoursText(saveSnapshot.playTimeSeconds, locale)} />
              <SaveMetric label={t("field.gold")} value={numberText(saveSnapshot.gold, locale)} />
              <SaveMetric label={t("field.count")} value={numberText(saveSnapshot.totalClears, locale)} />
              <SaveMetric label={t("save.currentStage")} value={text(saveSnapshot.currentStage?.label)} />
              <SaveMetric label={t("save.maxStage")} value={text(saveSnapshot.maxCompletedStage?.label)} />
              <SaveMetric label={t("save.heroes")} value={saveSnapshot.arrangedHeroKeys.join(" / ") || "-"} />
              <SaveMetric label={t("save.pets")} value={`${saveSnapshot.pets.filter((pet) => pet.unlocked).length} / ${saveSnapshot.pets.length}`} />
            </div>
          </section>

          <section className="panel section save-goals-panel">
            <div className="section-heading">
              <h2>{t("save.nextGoals")}</h2>
              <a href="#/category/stages">{t("stageAtlas.title")}</a>
            </div>
            <div className="save-goal-grid">
              <article className="save-goal-card">
                <h3>{t("save.progressLinks")}</h3>
                <div className="save-link-list">
                  {currentStageRef ? (
                    <a href={currentStageRef.href ?? "#/category/stages"}>
                      <span>{t("save.currentStage")}</span>
                      <strong>{text(currentStageRef.title)}</strong>
                    </a>
                  ) : (
                    <span>{t("save.currentStage")} / {text(saveSnapshot.currentStage?.label) || "-"}</span>
                  )}
                  {bestStageRef ? (
                    <a href={bestStageRef.href ?? "#/category/stages"}>
                      <span>{t("save.maxStage")}</span>
                      <strong>{text(bestStageRef.title)}</strong>
                    </a>
                  ) : (
                    <span>{t("save.maxStage")} / {text(saveSnapshot.maxCompletedStage?.label) || "-"}</span>
                  )}
                </div>
              </article>

              <article className="save-goal-card">
                <h3>{t("save.runeProgress")}</h3>
                {runeSummary ? (
                  <div className="save-mini-metrics">
                    <SaveMetric label={t("save.runeNodesActive")} value={`${numberText(runeSummary.activeNodes, locale)} / ${numberText(runeSummary.nodeCount, locale)}`} />
                    <SaveMetric label={t("save.runeLevels")} value={`${numberText(runeSummary.currentLevels, locale)} / ${numberText(runeSummary.maxLevels, locale)}`} />
                    <SaveMetric label={t("save.spentRuneCost")} value={numberText(runeSummary.spentCost, locale)} />
                    <SaveMetric label={t("save.remainingRuneCost")} value={numberText(runeSummary.remainingCost, locale)} />
                  </div>
                ) : (
                  <p className="empty">{t("state.loading")}</p>
                )}
                <a className="inline-link" href="#/category/runes">{t("save.openRunePlanner")}</a>
              </article>

              <article className="save-goal-card save-pet-goals">
                <h3>{t("save.petGoals")}</h3>
                {petGoalRows.length ? (
                  petGoalRows.map(({ key, relation }) => (
                    <div className="save-pet-goal" key={key}>
                      <div className="save-pet-head">
                        {refLink(relation.pet, text)}
                        <span>{numberText(relation.required, locale)}</span>
                      </div>
                      <small>{t("relation.petTarget")}: {refLink(relation.targetMonster, text)}</small>
                      <div className="save-stage-links">
                        {relation.recommendedStages.slice(0, 3).map((stage, index) =>
                          stage.stage?.href ? (
                            <a href={stage.stage.href} key={`${key}:${stage.stage.entityId ?? index}`}>
                              <span>{localText(stage.stage.title, locale)}</span>
                              <strong>{percentText(stage.spawnShare, locale)} / {numberText(stage.expectedPerWave, locale)}</strong>
                            </a>
                          ) : null,
                        )}
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="empty">{t("save.noPetGoals")}</p>
                )}
              </article>
            </div>
          </section>

          <section className="panel section">
            <div className="section-heading">
              <h2>{t("save.inventory")}</h2>
              <a href="#/category/market">{t("market.valuation")}</a>
            </div>
            <div className="save-slot-strip">
              <SaveMetric label={t("save.inventory")} value={numberText(saveSnapshot.occupiedSlots.inventory, locale)} />
              <SaveMetric label={t("save.stash")} value={numberText(saveSnapshot.occupiedSlots.stash, locale)} />
              <SaveMetric label={t("save.tradeStash")} value={numberText(saveSnapshot.occupiedSlots.tradingStash, locale)} />
              <SaveMetric label={t("save.equipped")} value={numberText(saveSnapshot.occupiedSlots.equipped, locale)} />
              <SaveMetric label={t("save.runes")} value={numberText(Object.keys(saveSnapshot.runeLevels).length, locale)} />
            </div>
            <div className="table-wrap">
              <table className="data-table compact">
                <thead>
                  <tr>
                    <th>{t("field.name")}</th>
                    <th>{t("save.owned")}</th>
                    <th>{t("field.grade")}</th>
                    <th>{t("field.type")}</th>
                    <th>{t("market.search")}</th>
                  </tr>
                </thead>
                <tbody>
                  {ownedPreview.map(({ owned, manifest }) => (
                    <tr key={owned.itemKey}>
                      <td>
                        <a className="table-name" href={manifest.href ?? "#/category/gear"}>
                          <span className={`mini-rarity rarity-${manifest.rarity ?? "NONE"}`} />
                          <span>
                            <strong>{text(manifest.title)}</strong>
                            <small>#{manifest.itemKey}</small>
                          </span>
                        </a>
                      </td>
                      <td>{numberText(owned.quantity, locale)}</td>
                      <td>{manifest.rarity ?? "-"}</td>
                      <td>{manifest.gearType ?? manifest.itemType ?? "-"}</td>
                      <td>{manifest.queries[0] ?? "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      ) : (
        <section className="panel state-panel compact-state">
          <h2>{t("save.notLoaded")}</h2>
          <p>{t("save.privacy")}</p>
        </section>
      )}
    </div>
  );
}

function SaveMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <small>{label}</small>
      <strong>{value}</strong>
    </div>
  );
}

export function MarketWorkbench({
  t,
  text,
  locale,
  saveSnapshot,
  initialQuery,
}: {
  t: Translator;
  text: TextResolver;
  locale: LocaleCode;
  saveSnapshot: SaveSnapshot | null;
  initialQuery?: string;
}) {
  const manifestState = useJson<MarketManifest>("/generated/market-manifest.json");
  const [query, setQuery] = useState(initialQuery ?? "Long Sword");
  const [gear, setGear] = useState("");
  const [level, setLevel] = useState("");
  const [sort, setSort] = useState("listings_desc");
  const [currency, setCurrency] = useState<MarketCurrency>(() => (isJapaneseLocale(locale) ? "jpy" : "usd"));
  const [tradableOnly, setTradableOnly] = useState(false);
  const [dealOnly, setDealOnly] = useState(false);
  const [page, setPage] = useState(1);
  const [selectedHash, setSelectedHash] = useState<string | null>(null);
  const [results, setResults] = useState<MarketItem[]>([]);
  const [total, setTotal] = useState(0);
  const [stats, setStats] = useState<MarketStats | null>(null);
  const [filtersData, setFiltersData] = useState<MarketFilterResponse | null>(null);
  const [movers, setMovers] = useState<MarketMoversResponse | null>(null);
  const [rate, setRate] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [liveError, setLiveError] = useState<string | null>(null);
  const [valuationRows, setValuationRows] = useState<ValuationRow[]>([]);
  const [valuationScope, setValuationScope] = useState<ValuationScope>("all");
  const [valuationLoading, setValuationLoading] = useState(false);
  const manifestByItem = useMemo(() => marketManifestLookup(manifestState.data), [manifestState.data]);
  const staticMatches = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!manifestState.data) {
      return [];
    }
    return manifestState.data.items
      .filter((item) => {
        const searchMatch = !needle || [text(item.title), item.rarity, item.gearType, item.itemType, ...item.queries].join(" ").toLowerCase().includes(needle);
        const gearMatch = !gear || item.gearType === gear || item.itemType === gear;
        const levelMatch = !level || Number(item.level) === Number(level);
        const tradableMatch = !tradableOnly || item.marketable;
        return searchMatch && gearMatch && levelMatch && tradableMatch;
      })
      .slice(0, 18);
  }, [gear, level, manifestState.data, query, text, tradableOnly]);

  useEffect(() => {
    fetchMarketJson<MarketStats>("stats").then(setStats).catch(() => undefined);
    fetchMarketJson<MarketFilterResponse>("filters").then(setFiltersData).catch(() => undefined);
    fetchMarketJson<{ usdjpy?: number | null }>("rate").then((data) => setRate(data.usdjpy ?? null)).catch(() => undefined);
    fetchMarketJson<MarketMoversResponse>("movers?n=6").then(setMovers).catch(() => undefined);
  }, []);

  useEffect(() => {
    let cancelled = false;
    const params = new URLSearchParams({ sort, page: String(page), pageSize: String(MARKET_PAGE_SIZE) });
    if (query.trim()) {
      params.set("q", query.trim());
    }
    if (gear) {
      params.set("gear", gear);
    }
    if (level) {
      params.set("level", level);
    }
    if (tradableOnly) {
      params.set("tradableOnly", "1");
    }
    if (dealOnly) {
      params.set("deal", "1");
    }
    const timer = window.setTimeout(() => {
      setLoading(true);
      setLiveError(null);
      fetchMarketJson<MarketItemsResponse>(`items?${params.toString()}`)
        .then((data) => {
          if (!cancelled) {
            setResults(data.items ?? []);
            setTotal(data.total ?? 0);
          }
        })
        .catch(() => {
          if (!cancelled) {
            setResults([]);
            setTotal(0);
            setLiveError(t("market.unavailable"));
          }
        })
        .finally(() => {
          if (!cancelled) {
            setLoading(false);
          }
        });
    }, 250);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [dealOnly, gear, level, page, query, sort, t, tradableOnly]);

  function runSearch(event?: FormEvent) {
    event?.preventDefault();
    setPage(1);
  }

  function resetFilters() {
    setQuery("");
    setGear("");
    setLevel("");
    setSort("listings_desc");
    setTradableOnly(false);
    setDealOnly(false);
    setPage(1);
  }

  async function updateValuation() {
    if (!saveSnapshot || !manifestState.data) {
      return;
    }
    setValuationLoading(true);
    setLiveError(null);
    const ownedRows = valuationRowsForScope(saveSnapshot, manifestByItem, valuationScope);
    try {
      const rows = await mapInBatches(ownedRows, 4, async (row) => {
        const search = row.manifest.queries[0] || text(row.manifest.title);
        if (!search) {
          return { owned: row.owned, manifest: row.manifest, market: null };
        }
        return { owned: row.owned, manifest: row.manifest, market: await cachedMarketQuote(search) };
      });
      setValuationRows(rows.sort((a, b) => (Number(b.market?.sell_price) || 0) * b.owned.quantity - (Number(a.market?.sell_price) || 0) * a.owned.quantity));
    } catch {
      setLiveError(t("market.unavailable"));
      setValuationRows(ownedRows.map((row) => ({ owned: row.owned, manifest: row.manifest, market: null })));
    } finally {
      setValuationLoading(false);
    }
  }

  const valuationTotal = valuationRows.reduce((sum, row) => sum + (Number(row.market?.sell_price) || 0) * row.owned.quantity, 0);
  const valuationPriced = valuationRows.filter((row) => row.market?.sell_price).length;
  const valuationNetTotal = Math.round(valuationTotal / STEAM_FEE_RATE);
  const pageCount = Math.max(1, Math.ceil(total / MARKET_PAGE_SIZE));

  return (
    <div className="page-stack tool-page">
      <section className="page-header panel market-hero-panel">
        <div>
          <a className="back-link" href="#/">{t("nav.back")}</a>
          <h1>{t("market.title")}</h1>
          <p>{t("market.subtitle")}</p>
          <small>{t("market.endpoint")}: {marketBase()}</small>
        </div>
        <div className="overview">
          <SaveMetric label={t("market.status")} value={stats?.market?.state ?? stats?.status ?? "-"} />
          <SaveMetric label={t("home.stat.items")} value={numberText(stats?.items ?? manifestState.data?.items.length, locale)} />
          <SaveMetric label={t("market.updated")} value={dateText(stats?.lastRunAt, locale)} />
          <SaveMetric label={t("market.currency")} value={currency === "jpy" ? t("market.jpy") : t("market.usd")} />
        </div>
      </section>

      <section className="panel market-alert">
        <strong>{stats?.market?.state ?? "ready"}</strong>
        <span>{marketStatusText(stats, t, locale)}</span>
      </section>

      {movers && ((movers.up?.length ?? 0) > 0 || (movers.down?.length ?? 0) > 0) ? (
        <MarketMovers movers={movers} t={t} locale={locale} currency={currency} rate={rate} onSelect={setSelectedHash} />
      ) : null}

      {stats?.market && stats.market.state !== "suspended" ? (
        <section className="panel market-alert">
          <strong>{stats.market.state}</strong>
          <span>{cleanNotice(localText({ ja: stats.market.ja, en: stats.market.en }, locale))}</span>
        </section>
      ) : null}

      <section className="panel section">
        <form className="market-search" onSubmit={runSearch}>
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={t("market.search")} />
          <button type="submit">{loading ? t("state.loading") : t("market.search")}</button>
        </form>
        <div className="market-filter-bar">
          <label>
            <span>{t("market.gear")}</span>
            <select value={gear} onChange={(event) => { setGear(event.target.value); setPage(1); }}>
              <option value="">{t("filter.all")}</option>
              {(filtersData?.gears ?? []).map((option) => (
                <option value={option.gear} key={option.gear}>
                  {option.gear} ({numberText(option.n, locale)})
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>{t("market.level")}</span>
            <select value={level} onChange={(event) => { setLevel(event.target.value); setPage(1); }}>
              <option value="">{t("filter.all")}</option>
              {(filtersData?.levels ?? []).map((option) => (
                <option value={option} key={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>{t("market.sort")}</span>
            <select value={sort} onChange={(event) => { setSort(event.target.value); setPage(1); }}>
              <option value="listings_desc">{t("market.sort.listings")}</option>
              <option value="price_asc">{t("market.sort.price")}</option>
              <option value="volume_desc">{t("market.sort.volume")}</option>
              <option value="level_desc">{t("market.sort.level")}</option>
            </select>
          </label>
          <label>
            <span>{t("market.currency")}</span>
            <select value={currency} onChange={(event) => setCurrency(event.target.value as MarketCurrency)}>
              <option value="jpy">{t("market.jpy")}</option>
              <option value="usd">{t("market.usd")}</option>
            </select>
          </label>
          <button type="button" className={tradableOnly ? "chip active" : "chip"} onClick={() => { setTradableOnly((value) => !value); setPage(1); }}>
            {t("market.tradableOnly")}
          </button>
          <button type="button" className={dealOnly ? "chip active" : "chip"} onClick={() => { setDealOnly((value) => !value); setPage(1); }}>
            {t("market.dealOnly")}
          </button>
          <button type="button" className="chip" onClick={resetFilters}>
            {t("market.resetFilters")}
          </button>
        </div>
        {liveError ? <p className="empty">{liveError}</p> : null}
        <MarketResults
          results={results}
          staticMatches={staticMatches}
          total={total}
          t={t}
          text={text}
          locale={locale}
          currency={currency}
          rate={rate}
          onSelect={setSelectedHash}
        />
        {total > MARKET_PAGE_SIZE ? (
          <div className="pager bottom">
            <button disabled={page <= 1} onClick={() => setPage((current) => Math.max(1, current - 1))}>
              {t("market.previous")}
            </button>
            <span>
              {t("market.page")} {numberText(page, locale)} / {numberText(pageCount, locale)}
            </span>
            <button disabled={page >= pageCount} onClick={() => setPage((current) => Math.min(pageCount, current + 1))}>
              {t("market.next")}
            </button>
          </div>
        ) : null}
      </section>

      {selectedHash ? (
        <MarketItemPanel key={selectedHash} hashName={selectedHash} t={t} locale={locale} currency={currency} rate={rate} onClose={() => setSelectedHash(null)} />
      ) : null}

      <section className="panel section">
        <div className="section-heading">
          <h2>{t("market.valuation")}</h2>
          <button className="game-button" type="button" disabled={!saveSnapshot || valuationLoading} onClick={updateValuation}>
            {valuationLoading ? t("state.loading") : t("market.refresh")}
          </button>
        </div>
        <div className="market-filter-bar compact">
          <label>
            <span>{t("market.scope")}</span>
            <select value={valuationScope} onChange={(event) => setValuationScope(event.target.value as ValuationScope)}>
              <option value="all">{t("market.scope.all")}</option>
              <option value="inventory">{t("market.scope.inventory")}</option>
              <option value="stash">{t("market.scope.stash")}</option>
              <option value="tradingStash">{t("market.scope.tradeStash")}</option>
              <option value="equipped">{t("market.scope.equipped")}</option>
            </select>
          </label>
          <span className="market-note">{t("market.valuationLimit")}</span>
        </div>
        <div className="save-slot-strip">
          <SaveMetric label={t("save.loaded")} value={saveSnapshot ? t("save.loaded") : t("save.notLoaded")} />
          <SaveMetric label={t("save.owned")} value={numberText(saveSnapshot?.ownedItems.length ?? 0, locale)} />
          <SaveMetric label={t("market.priced")} value={`${numberText(valuationPriced, locale)} / ${numberText(valuationRows.length, locale)}`} />
          <SaveMetric label={t("market.estimate")} value={priceText(valuationTotal, locale, currency, rate)} />
          <SaveMetric label={t("market.netEstimate")} value={priceText(valuationNetTotal, locale, currency, rate)} />
        </div>
        <ValuationTable rows={valuationRows} t={t} text={text} locale={locale} currency={currency} rate={rate} />
      </section>
    </div>
  );
}

function MarketResults({
  results,
  staticMatches,
  total,
  t,
  text,
  locale,
  currency,
  rate,
  onSelect,
}: {
  results: MarketItem[];
  staticMatches: MarketManifestItem[];
  total: number;
  t: Translator;
  text: TextResolver;
  locale: LocaleCode;
  currency: MarketCurrency;
  rate: number | null;
  onSelect: (hashName: string) => void;
}) {
  if (results.length > 0) {
    return (
      <>
        <div className="section-heading subtle-heading"><h2>{t("market.liveResults")} / {numberText(total, locale)}</h2></div>
        <div className="market-grid">
          {results.map((item) => (
            <article className="market-card live" key={item.hash_name} style={{ "--market-color": marketColor(item) } as CSSProperties}>
              {item.icon_url ? <img src={marketImage(item.icon_url)} alt="" /> : <span className="market-icon-placeholder" />}
              <div>
                <h3>{marketName(item, locale)}</h3>
                <p>{item.type ?? item.gear ?? "-"}</p>
                <dl>
                  <dt>{t("market.lowest")}</dt><dd>{priceText(item.sell_price, locale, currency, rate)}</dd>
                  <dt>{t("market.median")}</dt><dd>{priceText(item.median_price, locale, currency, rate)}</dd>
                  <dt>{t("market.listings")}</dt><dd>{numberText(item.sell_listings, locale)}</dd>
                  <dt>{t("market.volume")}</dt><dd>{numberText(item.volume, locale)}</dd>
                </dl>
                <div className="market-card-actions">
                  {dealPercent(item) !== null ? <span>-{dealPercent(item)}%</span> : null}
                  {item.chg !== undefined && item.chg !== null ? <span className={Number(item.chg) >= 0 ? "up" : "down"}>{changeText(item.chg, locale)}</span> : null}
                  <button type="button" onClick={() => onSelect(item.hash_name)}>{t("market.details")}</button>
                  <a href={steamMarketUrl(item.hash_name)} target="_blank" rel="noreferrer">{t("market.viewSteam")}</a>
                </div>
              </div>
            </article>
          ))}
        </div>
      </>
    );
  }
  return (
    <>
      <div className="section-heading subtle-heading"><h2>{t("market.staticResults")}</h2><span>{t("market.staticFallback")}</span></div>
      <div className="market-grid">
        {staticMatches.map((item) => (
          <a className="market-card static" href={item.href ?? "#/category/gear"} key={item.itemKey}>
            {item.icon ? <img src={item.icon} alt="" /> : <span className="market-icon-placeholder" />}
            <div>
              <h3>{text(item.title)}</h3>
              <p>{item.queries[0] ?? item.gearType ?? item.itemType}</p>
              <dl>
                <dt>{t("field.grade")}</dt><dd>{item.rarity ?? "-"}</dd>
                <dt>{t("field.level")}</dt><dd>{numberText(item.level, "en")}</dd>
              </dl>
            </div>
          </a>
        ))}
      </div>
    </>
  );
}

function MarketMovers({
  movers,
  t,
  locale,
  currency,
  rate,
  onSelect,
}: {
  movers: MarketMoversResponse;
  t: Translator;
  locale: LocaleCode;
  currency: MarketCurrency;
  rate: number | null;
  onSelect: (hashName: string) => void;
}) {
  const groups = [
    { id: "up", title: t("market.moversUp"), rows: movers.up ?? [] },
    { id: "down", title: t("market.moversDown"), rows: movers.down ?? [] },
  ];
  return (
    <section className="panel market-movers">
      <div className="section-heading">
        <h2>{t("market.movers")}</h2>
        <span>{numberText(movers.window ?? 24, locale)}h</span>
      </div>
      <div className="market-mover-grid">
        {groups.map((group) => (
          <div key={group.id}>
            <h3>{group.title}</h3>
            {group.rows.length ? (
              group.rows.slice(0, 6).map((item) => (
                <button type="button" className="market-mover-row" onClick={() => onSelect(item.hash_name)} key={item.hash_name}>
                  {item.icon_url ? <img src={marketImage(item.icon_url)} alt="" /> : <span className="market-icon-placeholder" />}
                  <span>{marketName(item, locale)}</span>
                  <strong>{priceText(item.sell_price, locale, currency, rate)}</strong>
                  <em className={Number(item.chg) >= 0 ? "up" : "down"}>{changeText(item.chg, locale)}</em>
                </button>
              ))
            ) : (
              <p className="empty">{t("state.empty")}</p>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}

function MarketItemPanel({
  hashName,
  t,
  locale,
  currency,
  rate,
  onClose,
}: {
  hashName: string;
  t: Translator;
  locale: LocaleCode;
  currency: MarketCurrency;
  rate: number | null;
  onClose: () => void;
}) {
  const [detail, setDetail] = useState<MarketItemResponse | null>(null);
  const [orderbook, setOrderbook] = useState<MarketOrderBook | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetchMarketJson<MarketItemResponse>(`item/${encodeURIComponent(hashName)}`)
      .then((data) => {
        if (!cancelled) {
          setDetail(data);
        }
      })
      .catch(() => undefined)
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });
    fetchMarketJson<MarketOrderBook>(`orderbook/${encodeURIComponent(hashName)}`)
      .then((data) => {
        if (!cancelled && data.ok) {
          setOrderbook(data);
        }
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [hashName]);

  const item = detail?.item ?? null;
  const history = detail?.history ?? [];
  return (
    <section className="panel section market-detail-panel">
      <div className="section-heading">
        <h2>{t("market.details")}</h2>
        <button type="button" className="game-button" onClick={onClose}>{t("market.close")}</button>
      </div>
      {loading ? (
        <p className="empty">{t("state.loading")}</p>
      ) : item ? (
        <div className="market-detail-grid">
          <div className="market-detail-head" style={{ "--market-color": marketColor(item) } as CSSProperties}>
            {item.icon_url ? <img src={marketImage(item.icon_url)} alt="" /> : <span className="market-icon-placeholder" />}
            <div>
              <h3>{marketName(item, locale)}</h3>
              <p>{item.type ?? item.gear ?? "-"}</p>
              <div className="market-card-actions inline">
                <a href={steamMarketUrl(item.hash_name)} target="_blank" rel="noreferrer">{t("market.viewSteam")}</a>
              </div>
            </div>
          </div>
          <div className="stat-grid save-stat-grid">
            <SaveMetric label={t("market.lowest")} value={priceText(item.sell_price, locale, currency, rate)} />
            <SaveMetric label={t("market.median")} value={priceText(item.median_price, locale, currency, rate)} />
            <SaveMetric label={t("market.netAfterFee")} value={priceText(Math.round((Number(item.sell_price) || 0) / STEAM_FEE_RATE), locale, currency, rate)} />
            <SaveMetric label={t("market.listings")} value={numberText(item.sell_listings, locale)} />
            <SaveMetric label={t("market.volume")} value={numberText(item.volume, locale)} />
            <SaveMetric label={t("market.updated")} value={dateText(item.updated_at, locale)} />
          </div>
          <div className="market-chart">
            <div className="section-heading subtle-heading">
              <h3>{t("market.history")}</h3>
            </div>
            <PriceSparkline history={history} locale={locale} currency={currency} rate={rate} />
          </div>
          {orderbook ? <OrderBookView orderbook={orderbook} t={t} locale={locale} currency={currency} rate={rate} /> : null}
        </div>
      ) : (
        <p className="empty">{t("market.unavailable")}</p>
      )}
    </section>
  );
}

function PriceSparkline({
  history,
  locale,
  currency,
  rate,
}: {
  history: MarketHistoryPoint[];
  locale: LocaleCode;
  currency: MarketCurrency;
  rate: number | null;
}) {
  const points = history.filter((point) => Number(point.sell_price) > 0).slice(-80);
  if (points.length < 2) {
    return <p className="empty">-</p>;
  }
  const values = points.map((point) => Number(point.sell_price));
  const min = Math.min(...values);
  const max = Math.max(...values);
  const width = 640;
  const height = 180;
  const span = Math.max(1, max - min);
  const polyline = points
    .map((point, index) => {
      const x = (index / Math.max(1, points.length - 1)) * width;
      const y = height - ((Number(point.sell_price) - min) / span) * (height - 24) - 12;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  const first = values[0];
  const last = values[values.length - 1];
  return (
    <div className="sparkline-box">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="price trend">
        <line x1="0" y1={height - 12} x2={width} y2={height - 12} />
        <polyline points={polyline} />
      </svg>
      <div>
        <span>{priceText(first, locale, currency, rate)}</span>
        <strong>{priceText(last, locale, currency, rate)}</strong>
      </div>
    </div>
  );
}

function OrderBookView({
  orderbook,
  t,
  locale,
  currency,
  rate,
}: {
  orderbook: MarketOrderBook;
  t: Translator;
  locale: LocaleCode;
  currency: MarketCurrency;
  rate: number | null;
}) {
  return (
    <div className="market-orderbook">
      <div className="section-heading subtle-heading">
        <h3>{t("market.orderbook")}</h3>
      </div>
      <div className="save-slot-strip">
        <SaveMetric label={t("market.lowestSell")} value={priceText(orderbook.lowSell, locale, currency, rate)} />
        <SaveMetric label={t("market.highestBuy")} value={priceText(orderbook.highBuy, locale, currency, rate)} />
      </div>
      <div className="orderbook-grid">
        <OrderSide title={t("market.sellOrders")} rows={orderbook.sell ?? []} locale={locale} currency={currency} rate={rate} />
        <OrderSide title={t("market.buyOrders")} rows={orderbook.buy ?? []} locale={locale} currency={currency} rate={rate} />
      </div>
    </div>
  );
}

function OrderSide({
  title,
  rows,
  locale,
  currency,
  rate,
}: {
  title: string;
  rows: Array<{ price: number | null; qty: number }>;
  locale: LocaleCode;
  currency: MarketCurrency;
  rate: number | null;
}) {
  return (
    <div>
      <h4>{title}</h4>
      {rows.slice(0, 8).map((row, index) => (
        <p key={index}>
          <span>{priceText(row.price, locale, currency, rate)}</span>
          <strong>{numberText(row.qty, locale)}</strong>
        </p>
      ))}
    </div>
  );
}

function MarketQuoteRelationCard({
  manifest,
  t,
  text,
  locale,
}: {
  manifest: MarketManifestItem;
  t: Translator;
  text: TextResolver;
  locale: LocaleCode;
}) {
  const [quote, setQuote] = useState<MarketItem | null>(null);
  const [rate, setRate] = useState<number | null>(null);
  const currency: MarketCurrency = isJapaneseLocale(locale) ? "jpy" : "usd";

  useEffect(() => {
    let cancelled = false;
    const query = manifest.queries[0] || text(manifest.title);
    cachedMarketQuote(query).then((item) => {
      if (!cancelled) {
        setQuote(item);
      }
    });
    fetchMarketJson<{ usdjpy?: number | null }>("rate")
      .then((data) => {
        if (!cancelled) {
          setRate(data.usdjpy ?? null);
        }
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [manifest, text]);

  if (!quote) {
    return <RelationCard title={t("category.market.title")} rows={manifest.queries.slice(0, 3).map((query, index) => [index === 0 ? t("market.search") : "", query])} />;
  }

  return (
    <article className="relation-card market-quote-card" style={{ "--market-color": marketColor(quote) } as CSSProperties}>
      <h3>{t("category.market.title")}</h3>
      <p>
        <span>{t("market.lowest")}</span>
        <strong>{priceText(quote.sell_price, locale, currency, rate)}</strong>
      </p>
      <p>
        <span>{t("market.listings")}</span>
        <strong>{numberText(quote.sell_listings, locale)}</strong>
      </p>
      <p>
        <span>{t("market.updated")}</span>
        <strong>{dateText(quote.updated_at, locale)}</strong>
      </p>
      <div className="market-card-actions inline">
        <a href={`#/category/market?q=${encodeURIComponent(manifest.queries[0] ?? text(manifest.title))}`}>{t("market.openMarketSearch")}</a>
        <a href={steamMarketUrl(quote.hash_name)} target="_blank" rel="noreferrer">{t("market.viewSteam")}</a>
      </div>
    </article>
  );
}

function ValuationTable({
  rows,
  t,
  text,
  locale,
  currency,
  rate,
}: {
  rows: ValuationRow[];
  t: Translator;
  text: TextResolver;
  locale: LocaleCode;
  currency: MarketCurrency;
  rate: number | null;
}) {
  if (rows.length === 0) {
    return <p className="empty">{t("market.unavailable")}</p>;
  }
  return (
    <div className="table-wrap">
      <table className="data-table compact">
        <thead>
          <tr>
            <th>{t("field.name")}</th>
            <th>{t("save.owned")}</th>
            <th>{t("market.lowest")}</th>
            <th>{t("market.estimate")}</th>
            <th>{t("market.netAfterFee")}</th>
            <th>{t("market.listings")}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.owned.itemKey}>
              <td>{row.manifest.href ? <a className="inline-link" href={row.manifest.href}>{text(row.manifest.title)}</a> : text(row.manifest.title)}</td>
              <td>{numberText(row.owned.quantity, locale)}</td>
              <td>{priceText(row.market?.sell_price, locale, currency, rate)}</td>
              <td>{priceText((Number(row.market?.sell_price) || 0) * row.owned.quantity, locale, currency, rate)}</td>
              <td>{priceText(Math.round(((Number(row.market?.sell_price) || 0) * row.owned.quantity) / STEAM_FEE_RATE), locale, currency, rate)}</td>
              <td>{numberText(row.market?.sell_listings, locale)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function DetailAugmentPanel({
  categoryId,
  entityId,
  t,
  text,
  locale,
  saveSnapshot,
}: {
  categoryId: string;
  entityId: string;
  t: Translator;
  text: TextResolver;
  locale: LocaleCode;
  saveSnapshot: SaveSnapshot | null;
}) {
  const relationships = useJson<RelationshipPayload>("/generated/relationships.json");
  const marketManifest = useJson<MarketManifest>("/generated/market-manifest.json");
  const owned = ownedLookup(saveSnapshot).get(entityId);
  if (relationships.loading || marketManifest.loading) {
    return null;
  }
  const market = marketManifest.data?.items.find((item) => String(item.itemKey) === entityId);
  const isItemCategory = ["gear", "materials", "stage-boxes"].includes(categoryId);
  const itemRelation = isItemCategory ? relationships.data?.items?.[entityId] : undefined;
  const chestRelation = relationships.data?.chests?.[entityId];
  const monsterRelation = relationships.data?.monsters?.[entityId];
  const petRelation = relationships.data?.pets?.[entityId];
  const stageRelation = relationships.data?.stages?.[entityId];
  if (!itemRelation && !chestRelation && !monsterRelation && !petRelation && !stageRelation && !owned && !market) {
    return null;
  }
  return (
    <section className="panel section relation-panel">
      <div className="section-heading">
        <h2>{t("nav.tools")}</h2>
        {market ? <a href={`#/category/market?q=${encodeURIComponent(market.queries[0] ?? text(market.title))}`}>{t("category.market.title")}</a> : null}
      </div>
      <div className="relation-grid">
        {owned ? <RelationCard title={t("relation.saveOwned")} rows={[[t("save.owned"), numberText(owned.quantity, locale)], [t("save.stash"), numberText(owned.sources.stash, locale)], [t("save.equipped"), numberText(owned.sources.equipped, locale)]]} /> : null}
        {market ? <MarketQuoteRelationCard manifest={market} t={t} text={text} locale={locale} /> : null}
        {itemRelation ? (
          <RelationList title={t("relation.sources")}>
            {itemRelation.sources.slice(0, 5).map((source, index) => (
              <li key={index}>
                {refLink(source.chest, text)} <span>{percentText(source.chance, locale)}</span> {refLink(source.stage, text)}
              </li>
            ))}
          </RelationList>
        ) : null}
        {itemRelation?.recipes && itemRelation.recipes.length > 0 ? (
          <RelationList title={locale.startsWith("ja") ? "使用先レシピ" : "Used in Recipes"}>
            {itemRelation.recipes.slice(0, 8).map((recipe, index) => (
              <li key={index}>
                <a className="inline-link" href={`#/category/cube`}>
                  {recipe.recipeType === "Crafting"
                    ? (locale.startsWith("ja") ? `クラフト [ティア ${recipe.tier}]` : `Craft [Tier ${recipe.tier}]`)
                    : (locale.startsWith("ja") ? `サブレシピ [ティア ${recipe.tier}]` : `Sub Recipe [Tier ${recipe.tier}]`)
                  }
                </a>
                <span>{recipe.craftingType || recipe.synthesisType || ""}</span>
                <strong style={{ opacity: 0.5 }}>#{recipe.recipeKey}</strong>
              </li>
            ))}
          </RelationList>
        ) : null}
        {chestRelation ? (
          <RelationList title={t("relation.chestContents")}>
            {chestRelation.contents.slice(0, 6).map((content) => (
              <li key={`${content.rewardType}:${content.rewardKey}`}>
                <span>{localText(content.groupName, locale)}</span>
                <strong>{percentText(content.weightPercent, locale)}</strong>
              </li>
            ))}
          </RelationList>
        ) : null}
        {monsterRelation ? (
          <RelationList title={t("relation.stageAppearances")}>
            {monsterRelation.stages.slice(0, 6).map((stage, index) => (
              <li key={index}>
                {refLink(stage.stage, text)}
                <span>{stage.boss ? t("stageAtlas.boss") : percentText(stage.spawnShare, locale)}</span>
              </li>
            ))}
          </RelationList>
        ) : null}
        {petRelation ? (
          <RelationList title={t("relation.petTarget")}>
            <li>{refLink(petRelation.targetMonster, text)} <span>{numberText(petRelation.required, locale)}</span></li>
            {petRelation.recommendedStages.slice(0, 4).map((stage, index) => (
              <li key={index}>{refLink(stage.stage, text)} <span>{percentText(stage.spawnShare, locale)}</span></li>
            ))}
          </RelationList>
        ) : null}
        {stageRelation ? (
          <RelationList title={t("stageAtlas.rewards")}>
            {stageRelation.rewards.map((reward, index) => (
              <li key={index}>{reward.item ? refLink(reward.item, text) : reward.dropKey} <span>{reward.rate ? percentText(reward.rate, locale) : t(reward.kind)}</span></li>
            ))}
          </RelationList>
        ) : null}
      </div>
    </section>
  );
}

function RelationCard({ title, rows }: { title: string; rows: string[][] }) {
  return (
    <article className="relation-card">
      <h3>{title}</h3>
      {rows.map(([label, value], index) => (
        <p key={`${label}:${index}`}>
          <span>{label}</span>
          <strong>{value}</strong>
        </p>
      ))}
    </article>
  );
}

function RelationList({ title, children }: { title: string; children: ReactNode }) {
  return (
    <article className="relation-card">
      <h3>{title}</h3>
      <ul>{children}</ul>
    </article>
  );
}
