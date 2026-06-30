import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type FormEvent,
} from "react";
import { DropLabWorkbench, FarmPlannerWorkbench, LabStatusWorkbench, MarketWorkbench, ProgressPlannerWorkbench, SaveWorkbench } from "./toolPages";
import type { SaveSnapshot } from "./saveReader";
import { MagitechDashboard } from "./components/MagitechDashboard";
import { MagitechCatalog } from "./components/MagitechCatalog";
import { BlueprintDetail } from "./components/BlueprintDetail";





type RuneLevel = {
  level: number;
  costItemKey: number;
  costItem: Localized;
  costValue: number;
  statType: string;
  statName: Localized;
  value: number;
  effect: Localized;
};

type RuneNode = {
  id: string;
  runeKey: number;
  title: Localized;
  subtitle: Localized;
  icon: string | null;
  rarity: string | null;
  x: number;
  y: number;
  maxLevel: number;
  requiredLevel: number | null;
  next: string[];
  preview: string[];
  statType: string;
  statName: Localized;
  category: string;
  categoryKey: string;
  categoryColor: string;
  isUnlock: boolean;
  totalCost: number;
  levels: RuneLevel[];
};

type RuneGraph = {
  nodes: RuneNode[];
  edges: Array<{ from: string; to: string; kind: "connected" | "preview" }>;
  bounds: { width: number; height: number; nodeSize: number };
  categories: Array<{ id: string; labelKey: string; color: string }>;
  totals: { allCost: number; nodeCount: number };
};

type StageAtlasMonster = {
  key: number | null;
  title: Localized;
  href: string | null;
  weight: number;
  spawnShare: number;
  expectedPerWave: number;
  gold: number | null;
  exp: number | null;
  attackDamage: number | null;
  attackSpeed: number | null;
  maxHp: number | null;
  moveSpeed: number | null;
};

type StageAtlasBoss = {
  key: number | null;
  title: Localized;
  href: string | null;
  attackDamage: number | null;
  attackDamageScaled: number;
  maxHp: number | null;
  maxHpScaled: number;
  gold: number | null;
  exp: number | null;
};

type StageAtlasRewardPreview = {
  title: Localized;
  sample: Localized;
  icon: string | null;
  rarity: string | null;
  weight: number;
  weightPercent: number;
  rewardType: string;
  rewardKey: number;
};

type StageAtlasReward = {
  labelKey: string;
  itemKey: number | null;
  dropKey: string | number | null;
  title: Localized;
  icon: string | null;
  rarity: string | null;
  rate: string;
  detailHref: string | null;
  preview: StageAtlasRewardPreview[];
};

type StageAtlasStage = {
  id: string;
  slug: string | null;
  detailHref: string | null;
  title: Localized;
  subtitle: Localized;
  difficulty: string;
  difficultyLabel: Localized;
  difficultyColor: string;
  stageType: string;
  act: number;
  stageNo: number;
  stageLevel: number;
  waveAmount: number;
  waveMonsterAmount: number;
  position: { x: number; y: number };
  monsters: StageAtlasMonster[];
  boss: StageAtlasBoss;
  rewards: StageAtlasReward[];
};

type StageAtlasPayload = {
  acts: Array<{ act: number; label: Localized; background: string | null; stages: StageAtlasStage[] }>;
  difficulties: Array<{ id: string; label: Localized; color: string }>;
  generatedFrom: string[];
};

import { 
  SITE_ORIGIN, 
  SUPPORTED_LOCALES,
  normalizeLocale,
  localizedText,
  href,
  useJson,
  formatValue,
  useRoute,
  useLocale,
  seoUrl,
  formatNumber,
  fallbackDictionary
} from "./lib/utils";
import type { 
  LocaleCode, 
  Localized, 
  CategorySummary, 
  Manifest, 
  DetailSection, 
  Route 
} from "./lib/utils";

function App() {
  const route = useRoute();
  const { locale, setLocale } = useLocale();
  const manifestState = useJson<Manifest>("/generated/site-manifest.json");
  const dictionaryState = useJson<Record<string, string>>(`/generated/locales/${locale}.json`);
  const [globalQuery, setGlobalQuery] = useState("");
  const [saveSnapshot, setSaveSnapshot] = useState<SaveSnapshot | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const handle = requestAnimationFrame(() => {
      setMenuOpen(false);
    });
    return () => cancelAnimationFrame(handle);
  }, [route]);

  const manifest = manifestState.data;
  const dictionary = dictionaryState.data;
  const t = (key: string) => dictionary?.[key] ?? fallbackDictionary(locale)[key] ?? key;
  const text = (value: Localized | undefined) => localizedText(value, locale);

  const categoryMap = useMemo(() => {
    const map = new Map<string, CategorySummary>();
    manifest?.categories.forEach((category) => map.set(category.id, category));
    return map;
  }, [manifest]);

  const activeCategory = route.kind !== "home" ? categoryMap.get(route.categoryId) ?? null : null;
  const loading = manifestState.loading || dictionaryState.loading;
  const error = manifestState.error || dictionaryState.error;
  const localeOptions = manifest?.locales?.length
    ? manifest.locales.map((code) => ({ code, label: manifest.localeLabels?.[code] ?? SUPPORTED_LOCALES.find((option) => option.code === code)?.label ?? code }))
    : SUPPORTED_LOCALES;

  function submitSearch(event: FormEvent) {
    event.preventDefault();
    const query = globalQuery.trim();
    if (query) {
      window.location.hash = href({ kind: "category", categoryId: "gear", query });
    }
  }

  return (
    <div className={`app ${menuOpen ? "menu-open" : ""}`}>
      <div className="background-map" />
      <header className="topbar scan-line">
        <button
          type="button"
          className="menu-toggle"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label={t("nav.menu")}
          aria-expanded={menuOpen}
        >
          <span className="burger-line"></span>
          <span className="burger-line"></span>
          <span className="burger-line"></span>
        </button>
        <a className="brand magitech-brand" href={href({ kind: "home" })}>
          <span className="magitech-badge">▲</span>
          <div>
            <strong style={{ fontFamily: "var(--font-display)", letterSpacing: "1px" }}>TBH LAB</strong>
            <small style={{ fontFamily: "var(--font-mono)", fontSize: "9px", opacity: 0.7, color: "var(--brass)" }}>DATA ANALYSIS SYSTEM</small>
          </div>
        </a>

        {/* Save Scan Status Indicator */}
        <div className="save-scan-status">
          <span className={`status-dot ${saveSnapshot ? "online" : "offline"}`}></span>
          <span className="status-text">
            {saveSnapshot ? "SCANNER // ONLINE" : "SCANNER // OFFLINE"}
          </span>
        </div>

        <form className="top-search" onSubmit={submitSearch}>
          <input
            value={globalQuery}
            onChange={(event) => setGlobalQuery(event.target.value)}
            placeholder={t("filter.search.placeholder")}
            aria-label={t("nav.search")}
          />
          <button type="submit" style={{ fontFamily: "var(--font-display)" }}>SCAN</button>
        </form>
        <label className="language-control">
          <span style={{ fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px" }}>LOCALE</span>
          <select value={locale} onChange={(event) => setLocale(event.target.value as LocaleCode)}>
            {localeOptions.map((option) => (
              <option value={option.code} key={option.code}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </header>

      <div className="shell">
        <SeoManager route={route} manifest={manifest} activeCategory={activeCategory} locale={locale} t={t} />
        {manifest ? (
          <>
            <div className={`sidebar-overlay ${menuOpen ? "open" : ""}`} onClick={() => setMenuOpen(false)} />
            <Sidebar
              manifest={manifest}
              activeCategoryId={route.kind === "home" ? null : route.categoryId}
              t={t}
              categoryMap={categoryMap}
              menuOpen={menuOpen}
              setMenuOpen={setMenuOpen}
            />
          </>
        ) : null}

        <main className="content">
          {loading ? (
            <StatePanel label={t("state.loading")} />
          ) : error || !manifest ? (
            <StatePanel label={t("state.error")} detail={error ?? "manifest"} />
          ) : route.kind === "home" ? (
            <MagitechDashboard manifest={manifest} t={t} text={text} locale={locale} saveSnapshot={saveSnapshot} onSaveLoaded={setSaveSnapshot} />
          ) : route.kind === "category" && activeCategory?.id === "my-save" ? (
            <SaveWorkbench t={t} text={text} locale={locale} saveSnapshot={saveSnapshot} onSaveLoaded={setSaveSnapshot} />
          ) : route.kind === "category" && activeCategory?.id === "market" ? (
            <MarketWorkbench key={route.query ?? ""} t={t} text={text} locale={locale} saveSnapshot={saveSnapshot} initialQuery={route.query} />
          ) : route.kind === "category" && activeCategory?.id === "farm-planner" ? (
            <FarmPlannerWorkbench t={t} text={text} locale={locale} />
          ) : route.kind === "category" && activeCategory?.id === "drop-lab" ? (
            <DropLabWorkbench t={t} text={text} locale={locale} saveSnapshot={saveSnapshot} />
          ) : route.kind === "category" && activeCategory?.id === "progress-planner" ? (
            <ProgressPlannerWorkbench t={t} text={text} locale={locale} saveSnapshot={saveSnapshot} onSaveLoaded={setSaveSnapshot} />
          ) : route.kind === "category" && activeCategory?.id === "lab-status" ? (
            <LabStatusWorkbench t={t} text={text} locale={locale} />
          ) : route.kind === "category" && activeCategory ? (
            <MagitechCatalog category={activeCategory} t={t} text={text} locale={locale} initialQuery={route.query} saveSnapshot={saveSnapshot} />
          ) : route.kind === "detail" && activeCategory ? (
            <BlueprintDetail category={activeCategory} slug={route.slug} t={t} text={text} locale={locale} saveSnapshot={saveSnapshot} />
          ) : (
            <StatePanel label={t("state.error")} detail="route" />
          )}
        </main>
      </div>
    </div>
  );
}

function upsertMeta(selector: string, create: () => HTMLMetaElement, content: string) {
  let element = document.head.querySelector<HTMLMetaElement>(selector);
  if (!element) {
    element = create();
    document.head.appendChild(element);
  }
  element.setAttribute("content", content);
}

function upsertLink(selector: string, create: () => HTMLLinkElement, hrefValue: string) {
  let element = document.head.querySelector<HTMLLinkElement>(selector);
  if (!element) {
    element = create();
    document.head.appendChild(element);
  }
  element.setAttribute("href", hrefValue);
}

function setNamedMeta(name: string, content: string) {
  upsertMeta(
    `meta[name="${name}"]`,
    () => {
      const element = document.createElement("meta");
      element.setAttribute("name", name);
      return element;
    },
    content,
  );
}

function setPropertyMeta(property: string, content: string) {
  upsertMeta(
    `meta[property="${property}"]`,
    () => {
      const element = document.createElement("meta");
      element.setAttribute("property", property);
      return element;
    },
    content,
  );
}

function applyDocumentSeo({
  title,
  description,
  route,
  locale,
  locales,
  siteUrl,
  jsonLdData,
}: {
  title: string;
  description: string;
  route: Route;
  locale: LocaleCode;
  locales: LocaleCode[];
  siteUrl: string;
  jsonLdData?: Record<string, unknown>;
}) {
  const canonical = seoUrl(route, locale, siteUrl);
  document.title = title;
  document.documentElement.lang = normalizeLocale(locale);
  setNamedMeta("description", description);
  setNamedMeta("twitter:card", "summary_large_image");
  setNamedMeta("twitter:title", title);
  setNamedMeta("twitter:description", description);
  setPropertyMeta("og:site_name", "TBH Lab");
  setPropertyMeta("og:type", route.kind === "home" ? "website" : "article");
  setPropertyMeta("og:title", title);
  setPropertyMeta("og:description", description);
  setPropertyMeta("og:url", canonical);
  upsertLink(
    'link[rel="canonical"]',
    () => {
      const element = document.createElement("link");
      element.setAttribute("rel", "canonical");
      return element;
    },
    canonical,
  );

  document.head.querySelectorAll('link[rel="alternate"][data-tbh-hreflang="true"]').forEach((element) => element.remove());
  locales.forEach((alternateLocale) => {
    const element = document.createElement("link");
    element.setAttribute("rel", "alternate");
    element.setAttribute("hreflang", alternateLocale);
    element.setAttribute("href", seoUrl(route, alternateLocale, siteUrl));
    element.setAttribute("data-tbh-hreflang", "true");
    document.head.appendChild(element);
  });
  const defaultAlternate = document.createElement("link");
  defaultAlternate.setAttribute("rel", "alternate");
  defaultAlternate.setAttribute("hreflang", "x-default");
  defaultAlternate.setAttribute("href", seoUrl(route, "en-US", siteUrl));
  defaultAlternate.setAttribute("data-tbh-hreflang", "true");
  document.head.appendChild(defaultAlternate);

  let jsonLd = document.head.querySelector<HTMLScriptElement>("#tbh-jsonld");
  if (!jsonLd) {
    jsonLd = document.createElement("script");
    jsonLd.type = "application/ld+json";
    jsonLd.id = "tbh-jsonld";
    document.head.appendChild(jsonLd);
  }
  const defaultJsonLd = {
    "@context": "https://schema.org",
    "@type": route.kind === "home" ? "WebSite" : "WebPage",
    name: title,
    description,
    url: canonical,
    inLanguage: normalizeLocale(locale),
    isPartOf: {
      "@type": "WebSite",
      name: "TBH Lab",
      url: siteUrl,
    },
  };
  jsonLd.textContent = JSON.stringify(jsonLdData ? { ...defaultJsonLd, ...jsonLdData } : defaultJsonLd);
}

function SeoManager({
  route,
  manifest,
  activeCategory,
  locale,
  t,
}: {
  route: Route;
  manifest: Manifest | null;
  activeCategory: CategorySummary | null;
  locale: LocaleCode;
  t: (key: string) => string;
}) {
  useEffect(() => {
    const suffix = t("seo.titleSuffix");
    const titleRoot = route.kind === "home" ? t("home.title") : activeCategory ? t(activeCategory.titleKey) : t("app.title");
    const detailTail = route.kind === "detail" ? ` #${route.slug.replace(/-/g, " ")}` : "";
    const title = route.kind === "home" ? `${titleRoot} | ${suffix}` : `${titleRoot}${detailTail} | TBH Lab`;
    const description = route.kind === "home" ? t("seo.defaultDescription") : activeCategory ? t(activeCategory.descriptionKey) : t("seo.defaultDescription");

    // Dynamic Rich JSON-LD Data for Homepage & Category lists
    let jsonLdData: Record<string, unknown> | undefined;
    if (route.kind === "home") {
      jsonLdData = {
        "@type": "WebSite",
        potentialAction: {
          "@type": "SearchAction",
          target: `${manifest?.seo?.siteUrl ?? SITE_ORIGIN}/?q={search_term_string}`,
          "query-input": "required name=search_term_string"
        }
      };
    } else if (route.kind === "category" && activeCategory) {
      jsonLdData = {
        "@type": "CollectionPage",
        about: {
          "@type": "Thing",
          name: t(activeCategory.titleKey),
          description: t(activeCategory.descriptionKey)
        }
      };
    }

    applyDocumentSeo({
      title,
      description,
      route,
      locale,
      locales: manifest?.locales?.length ? manifest.locales : SUPPORTED_LOCALES.map((option) => option.code),
      siteUrl: manifest?.seo?.siteUrl ?? SITE_ORIGIN,
      jsonLdData,
    });
  }, [activeCategory, locale, manifest, route, t]);
  return null;
}

function Sidebar({
  manifest,
  activeCategoryId,
  t,
  categoryMap,
  menuOpen,
  setMenuOpen,
}: {
  manifest: Manifest;
  activeCategoryId: string | null;
  t: (key: string) => string;
  categoryMap: Map<string, CategorySummary>;
  menuOpen: boolean;
  setMenuOpen: (open: boolean) => void;
}) {
  return (
    <aside className={`sidebar ${menuOpen ? "open" : ""}`} style={{ borderColor: "rgba(212, 165, 57, 0.15)" }}>
      <div className="sidebar-title" style={{ background: "linear-gradient(145deg, rgba(20, 16, 12, 0.95), rgba(8, 6, 4, 0.98))", border: "1px solid rgba(212, 165, 57, 0.25)" }}>
        <span className="status-dot online" style={{ background: "var(--brass)", boxShadow: "0 0 10px rgba(212, 165, 57, 0.8)", animation: "none" }} />
        <div>
          <strong style={{ fontFamily: "var(--font-display)", color: "#fff", fontSize: "11px", letterSpacing: "1px" }}>LAB CONTROL</strong>
          <small style={{ fontFamily: "var(--font-mono)", fontSize: "9px", color: "var(--muted)", opacity: 0.8 }}>SYSTEM NAVIGATION</small>
        </div>
        <button
          type="button"
          className="menu-close-btn"
          onClick={() => setMenuOpen(false)}
          aria-label="Close menu"
        >
          &times;
        </button>
      </div>
      {manifest.navGroups.map((group) => (
        <section className="nav-group" key={group.id}>
          <h2 style={{ fontFamily: "var(--font-display)", fontSize: "9px", color: "var(--brass-soft)", letterSpacing: "1px", marginBottom: "8px", opacity: 0.8 }}>
            // {t(group.id)}
          </h2>
          {group.items.map((id) => {
            const category = categoryMap.get(id);
            if (!category) {
              return null;
            }
            return (
              <a
                className={`nav-link ${activeCategoryId === id ? "active" : ""}`}
                href={href({ kind: "category", categoryId: id })}
                key={id}
                style={{ padding: "8px 10px" }}
              >
                <Icon src={category.icon} />
                <span style={{ fontSize: "13px", fontWeight: activeCategoryId === id ? 700 : 400 }}>{t(category.titleKey)}</span>
                <span className="tech-badge" style={{ fontSize: "9px", padding: "1px 5px" }}>{formatNumber(category.count)}</span>
              </a>
            );
          })}
        </section>
      ))}
    </aside>
  );
}

export function StageAtlasWorkbench({
  t,
  text,
  locale,
  saveSnapshot,
}: {
  t: (key: string) => string;
  text: (value: Localized | undefined) => string;
  locale: LocaleCode;
  saveSnapshot: SaveSnapshot | null;
}) {
  const { data, loading, error } = useJson<StageAtlasPayload>("/generated/stage-atlas.json");
  const initialStageRoute = saveSnapshot?.currentStage;
  const [act, setAct] = useState(() => initialStageRoute?.act || 1);
  const [difficulty, setDifficulty] = useState<string>(() => initialStageRoute?.difficulty || "NORMAL");
  const [selectedId, setSelectedId] = useState<string | null>(() => (initialStageRoute ? String(initialStageRoute.stageKey) : null));
  const saveStageKeys = useMemo(
    () => ({
      current: saveSnapshot?.currentStage?.stageKey ?? null,
      best: saveSnapshot?.maxCompletedStage?.stageKey ?? null,
    }),
    [saveSnapshot],
  );

  if (loading) {
    return <StatePanel label={t("state.loading")} />;
  }
  if (error || !data) {
    return <StatePanel label={t("state.error")} detail={error ?? "stage-atlas"} />;
  }

  const activeAct = data.acts.find((item) => item.act === act) ?? data.acts[0];
  const activeDifficulty = data.difficulties.find((item) => item.id === difficulty) ?? data.difficulties[0];
  const stages = (activeAct?.stages ?? [])
    .filter((stage) => stage.difficulty === activeDifficulty?.id)
    .sort((a, b) => a.stageNo - b.stageNo);
  const selected = stages.find((stage) => stage.id === selectedId) ?? stages[0] ?? null;
  const totalMonsterWeight = selected?.monsters.reduce((sum, monster) => sum + (Number(monster.weight) || 0), 0) ?? 0;
  const percent = (value: number | null | undefined) => `${formatNumber(Math.round((Number(value) || 0) * 10) / 10, locale)}%`;
  const jumpToSaveStage = (route: SaveSnapshot["currentStage"]) => {
    if (!route) {
      return;
    }
    setAct(route.act || 1);
    if (route.difficulty) {
      setDifficulty(route.difficulty);
    }
    setSelectedId(String(route.stageKey));
  };
  const stageKeyNumber = (stage: StageAtlasStage | null | undefined) => Number(stage?.id ?? 0);
  const isSaveCleared = (stage: StageAtlasStage) => !!saveStageKeys.best && stageKeyNumber(stage) <= saveStageKeys.best;
  const selectedKey = stageKeyNumber(selected);

  return (
    <section className="panel section stage-atlas">
      <div className="stage-atlas-heading">
        <div>
          <h2>{t("stageAtlas.title")}</h2>
          <p>{t("stageAtlas.subtitle")}</p>
        </div>
        <div className="stage-atlas-source">
          {data.generatedFrom.map((source) => (
            <span key={source}>{source}</span>
          ))}
        </div>
      </div>

      <div className="stage-atlas-controls">
        <div className="stage-atlas-tabs" aria-label={t("stageAtlas.act")}>
          {data.acts.map((item) => (
            <button
              type="button"
              className={activeAct?.act === item.act ? "active" : ""}
              key={item.act}
              onClick={() => {
                setAct(item.act);
                setSelectedId(null);
              }}
            >
              {text(item.label)}
            </button>
          ))}
        </div>
        <div className="stage-atlas-tabs difficulty-tabs" aria-label={t("filter.difficulty")}>
          {data.difficulties.map((item) => (
            <button
              type="button"
              className={activeDifficulty?.id === item.id ? "active" : ""}
              key={item.id}
              onClick={() => {
                setDifficulty(item.id);
                setSelectedId(null);
              }}
              style={{ "--stage-color": item.color } as CSSProperties}
            >
              {text(item.label)}
            </button>
          ))}
        </div>
        <div className="stage-save-jump">
          <span>{t("stageAtlas.mapHint")}</span>
          {saveSnapshot?.currentStage ? (
            <button type="button" onClick={() => jumpToSaveStage(saveSnapshot.currentStage)}>
              {t("save.jumpCurrentStage")}
            </button>
          ) : null}
          {saveSnapshot?.maxCompletedStage ? (
            <button type="button" onClick={() => jumpToSaveStage(saveSnapshot.maxCompletedStage)}>
              {t("save.jumpBestStage")}
            </button>
          ) : null}
        </div>
      </div>

      {saveSnapshot ? (
        <div className="stage-save-strip">
          <Metric label={t("save.currentStage")} value={text(saveSnapshot.currentStage?.label) || "-"} />
          <Metric label={t("save.maxStage")} value={text(saveSnapshot.maxCompletedStage?.label) || "-"} />
          <Metric label={t("save.currentWave")} value={formatValue(saveSnapshot.currentStageWave, locale)} />
        </div>
      ) : null}

      <div className="stage-atlas-layout">
        <div className="stage-map-frame">
          <div
            className="stage-map"
            style={{
              backgroundImage: activeAct?.background ? `linear-gradient(180deg, rgba(8, 8, 7, 0.3), rgba(8, 8, 7, 0.68)), url(${activeAct.background})` : undefined,
            }}
          >
            <svg className="stage-map-path" viewBox="0 0 100 100" preserveAspectRatio="none">
              {stages.slice(0, -1).map((stage, index) => {
                const next = stages[index + 1];
                return (
                  <line
                    key={`${stage.id}:${next.id}`}
                    x1={stage.position.x}
                    y1={stage.position.y}
                    x2={next.position.x}
                    y2={next.position.y}
                  />
                );
              })}
            </svg>
            {stages.map((stage) => (
              <button
                type="button"
                className={`stage-node ${selected?.id === stage.id ? "selected" : ""} ${saveStageKeys.current === stageKeyNumber(stage) ? "current" : ""} ${saveStageKeys.best === stageKeyNumber(stage) ? "best" : ""} ${isSaveCleared(stage) ? "cleared" : ""}`}
                key={stage.id}
                onClick={() => setSelectedId(stage.id)}
                title={text(stage.title)}
                style={
                  {
                    left: `${stage.position.x}%`,
                    top: `${stage.position.y}%`,
                    "--stage-color": stage.difficultyColor,
                  } as CSSProperties
                }
              >
                <strong>{stage.stageNo}</strong>
                <span>{formatNumber(stage.stageLevel, locale)}</span>
                {saveStageKeys.current === stageKeyNumber(stage) ? (
                  <em>{t("save.markerCurrent")}</em>
                ) : saveStageKeys.best === stageKeyNumber(stage) ? (
                  <em>{t("save.markerBest")}</em>
                ) : isSaveCleared(stage) ? (
                  <em>{t("save.markerCleared")}</em>
                ) : null}
              </button>
            ))}
          </div>
        </div>

        <aside className="stage-inspector">
          {selected ? (
            <>
              <div className="stage-selected-card">
                <small>{t("stageAtlas.selectedStage")}</small>
                <h3>{text(selected.title)}</h3>
                <p>{text(selected.difficultyLabel)} / {t("field.stageLevel")} {formatNumber(selected.stageLevel, locale)}</p>
                {saveSnapshot ? (
                  <div className="stage-save-badges">
                    {saveStageKeys.current === selectedKey ? <span>{t("save.markerCurrent")}</span> : null}
                    {saveStageKeys.best === selectedKey ? <span>{t("save.markerBest")}</span> : null}
                    {selected && isSaveCleared(selected) ? <span>{t("save.markerCleared")}</span> : null}
                  </div>
                ) : null}
                {selected.detailHref ? <a className="game-button" href={selected.detailHref}>{t("stageAtlas.openDetail")}</a> : null}
              </div>

              <div className="stat-grid stage-metrics">
                <Metric label={t("stageAtlas.wavePlan")} value={`${formatNumber(selected.waveAmount, locale)} / ${formatNumber(selected.waveMonsterAmount, locale)}`} />
                <Metric label={t("field.monsters")} value={formatNumber(selected.monsters.length, locale)} />
                <Metric label={t("field.weight")} value={formatNumber(totalMonsterWeight, locale)} />
              </div>

              <div className="stage-boss-card">
                <small>{t("stageAtlas.boss")}</small>
                {selected.boss.href ? <a href={selected.boss.href}>{text(selected.boss.title)}</a> : <strong>{text(selected.boss.title)}</strong>}
                <div>
                  <span>{t("field.attackDamage")} {formatValue(selected.boss.attackDamageScaled, locale)}</span>
                  <span>{t("field.maxHp")} {formatValue(selected.boss.maxHpScaled, locale)}</span>
                </div>
              </div>

              <div className="stage-panel-list">
                <h3>{t("stageAtlas.monsterLineup")}</h3>
                {selected.monsters.map((monster) => (
                  <a className="stage-monster-row" href={monster.href ?? "#"} key={monster.key ?? text(monster.title)}>
                    <span>
                      <strong>{text(monster.title)}</strong>
                      <small>{t("stageAtlas.spawnShare")} {percent(monster.spawnShare)}</small>
                    </span>
                    <span>{t("stageAtlas.expectedPerWave")} {formatNumber(monster.expectedPerWave, locale)}</span>
                    <div className="stage-monster-tooltip">
                      <strong>{text(monster.title)}</strong>
                      <span>{t("field.attackDamage")} {formatValue(monster.attackDamage, locale)}</span>
                      <span>{t("field.attackSpeed")} {formatValue(monster.attackSpeed, locale)}</span>
                      <span>{t("field.maxHp")} {formatValue(monster.maxHp, locale)}</span>
                      <span>{t("field.gold")} {formatValue(monster.gold, locale)} / {t("field.exp")} {formatValue(monster.exp, locale)}</span>
                    </div>
                  </a>
                ))}
              </div>

              <div className="stage-panel-list reward-list">
                <h3>{t("stageAtlas.rewards")}</h3>
                {selected.rewards.map((reward) => (
                  <div className="stage-reward" key={`${reward.labelKey}:${reward.itemKey ?? reward.dropKey}`}>
                    <div className="stage-reward-head">
                      <Icon src={reward.icon} rarity={reward.rarity} />
                      <span>
                        <small>{t(reward.labelKey)} / {reward.rate}</small>
                        {reward.detailHref ? <a href={reward.detailHref}>{text(reward.title)}</a> : <strong>{text(reward.title)}</strong>}
                      </span>
                    </div>
                    {reward.preview.length ? (
                      <div className="stage-drop-preview">
                        <small>{t("stageAtlas.dropPreview")}</small>
                        {reward.preview.slice(0, 4).map((drop) => (
                          <div key={`${drop.rewardType}:${drop.rewardKey}`}>
                            <span>{text(drop.title)}</span>
                            <strong>{percent(drop.weightPercent)}</strong>
                            {text(drop.sample) !== "-" ? <small>{text(drop.sample)}</small> : null}
                          </div>
                        ))}
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="empty">{t("state.empty")}</p>
          )}
        </aside>
      </div>
    </section>
  );
}

export function RuneWorkbench({
  t,
  text,
  locale,
  saveSnapshot,
}: {
  t: (key: string) => string;
  text: (value: Localized | undefined) => string;
  locale: LocaleCode;
  saveSnapshot: SaveSnapshot | null;
}) {
  const { data, loading, error } = useJson<RuneGraph>("/generated/rune-graph.json");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [manualLevels, setManualLevels] = useState<Record<string, number>>({});
  const [levelSource, setLevelSource] = useState<"save" | "manual">("save");
  const [zoom, setZoom] = useState(0.31);
  const [pan, setPan] = useState({ x: 26, y: -4 });
  const [mutedCategories, setMutedCategories] = useState<Record<string, boolean>>({});
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const dragRef = useRef<{ pointerId: number; startX: number; startY: number; originX: number; originY: number } | null>(null);

  const nodeMap = useMemo(() => {
    const map = new Map<string, RuneNode>();
    data?.nodes.forEach((node) => map.set(node.id, node));
    return map;
  }, [data]);

  const saveLevels = useMemo(() => {
    if (!data || !saveSnapshot) {
      return {};
    }
    return Object.fromEntries(
      data.nodes
        .map((node) => {
          const level = Math.max(0, Math.min(node.maxLevel, Number(saveSnapshot.runeLevels[String(node.runeKey)]) || 0));
          return [node.id, level] as const;
        })
        .filter(([, level]) => level > 0),
    );
  }, [data, saveSnapshot]);
  const levels = saveSnapshot && levelSource === "save" ? saveLevels : manualLevels;

  const resolvedSelectedId = selectedId && nodeMap.has(selectedId) ? selectedId : data?.nodes[0]?.id ?? null;
  const selected = resolvedSelectedId ? nodeMap.get(resolvedSelectedId) ?? null : null;
  const selectedLevel = selected ? levels[selected.id] ?? 0 : 0;

  const totals = useMemo(() => {
    const bonusMap = new Map<string, { name: Localized; value: number }>();
    let cost = 0;
    data?.nodes.forEach((node) => {
      const level = levels[node.id] ?? 0;
      node.levels
        .filter((row) => Number(row.level) <= level)
        .forEach((row) => {
          cost += Number(row.costValue) || 0;
          const current = bonusMap.get(row.statType) ?? { name: row.statName, value: 0 };
          current.value += Number(row.value) || 0;
          bonusMap.set(row.statType, current);
        });
    });
    return { cost, bonuses: Array.from(bonusMap.values()).sort((a, b) => text(a.name).localeCompare(text(b.name))) };
  }, [data, levels, text]);

  const runeProgress = useMemo(() => {
    if (!data) {
      return null;
    }
    let activeNodes = 0;
    let currentLevels = 0;
    let maxLevels = 0;
    let remainingCost = 0;
    data.nodes.forEach((node) => {
      const level = Math.max(0, Math.min(node.maxLevel, levels[node.id] ?? 0));
      if (level > 0) {
        activeNodes += 1;
      }
      currentLevels += level;
      maxLevels += node.maxLevel;
      remainingCost += node.levels
        .filter((row) => Number(row.level) > level)
        .reduce((sum, row) => sum + (Number(row.costValue) || 0), 0);
    });
    return { activeNodes, currentLevels, maxLevels, remainingCost };
  }, [data, levels]);

  if (loading) {
    return <StatePanel label={t("state.loading")} />;
  }
  if (error || !data) {
    return <StatePanel label={t("state.error")} detail={error ?? "rune-graph"} />;
  }

  const nodeSize = data.bounds.nodeSize || 40;
  const resetView = () => {
    setZoom(0.31);
    setPan({ x: 26, y: -4 });
  };
  const changeZoom = (delta: number) => {
    setZoom((current) => Math.max(0.25, Math.min(1.25, Number((current + delta).toFixed(2)))));
  };
  const setNodeLevel = (node: RuneNode, level: number) => {
    setLevelSource("manual");
    setManualLevels((current) => ({ ...current, [node.id]: Math.max(0, Math.min(node.maxLevel, level)) }));
  };
  const applySaveLevels = () => {
    if (saveSnapshot) {
      setLevelSource("save");
    }
  };
  const toggleCategory = (category: string) => {
    setMutedCategories((current) => ({ ...current, [category]: !current[category] }));
  };
  const endDrag = () => {
    dragRef.current = null;
  };
  const selectedCost = selected
    ? selected.levels
        .filter((row) => Number(row.level) <= selectedLevel)
        .reduce((sum, row) => sum + (Number(row.costValue) || 0), 0)
    : 0;
  const hovered = hoveredId ? nodeMap.get(hoveredId) ?? null : null;
  const hoveredLevel = hovered ? levels[hovered.id] ?? 0 : 0;
  const hoveredEffectLevel = hovered ? Math.max(0, Math.min(hoveredLevel || 1, hovered.levels.length) - 1) : 0;
  const hoveredEffect = hovered ? hovered.levels[hoveredEffectLevel]?.effect ?? hovered.subtitle : undefined;
  const hoveredFlip = hovered ? hovered.x > data.bounds.width * 0.66 : false;

  return (
    <section className="panel section rune-workbench">
      <div className="rune-board-toolbar">
        <div className="rune-zoom-group" aria-label={t("rune.zoom")}>
          <span>{t("rune.zoom")}</span>
          <button type="button" onClick={() => changeZoom(-0.08)} aria-label={t("rune.zoomOut")}>
            -
          </button>
          <strong>{Math.round(zoom * 100)}%</strong>
          <button type="button" onClick={() => changeZoom(0.08)} aria-label={t("rune.zoomIn")}>
            +
          </button>
          <button type="button" onClick={resetView}>
            {t("rune.resetView")}
          </button>
        </div>
        <div className="rune-category-filter">
          {data.categories.map((category) => {
            const muted = mutedCategories[category.id];
            return (
              <button
                type="button"
                className={`rune-category-chip ${muted ? "muted" : ""}`}
                key={category.id}
                onClick={() => toggleCategory(category.id)}
                style={{ "--category-color": category.color } as CSSProperties}
                aria-pressed={!muted}
              >
                <span />
                {t(category.labelKey)}
              </button>
            );
          })}
        </div>
        <span className="rune-drag-hint">{t("rune.dragHint")}</span>
        <div className="rune-actions rune-toolbar-actions">
          <button type="button" className="game-button" disabled={!saveSnapshot} onClick={applySaveLevels}>
            {t("save.applyRunes")}
          </button>
          <button
            type="button"
            className="game-button"
            onClick={() => {
              setLevelSource("manual");
              setManualLevels(Object.fromEntries(data.nodes.map((node) => [node.id, node.maxLevel])));
            }}
          >
            {t("rune.maxAll")}
          </button>
          <button
            type="button"
            className="game-button"
            onClick={() => {
              setLevelSource("manual");
              setManualLevels({});
            }}
          >
            {t("rune.reset")}
          </button>
        </div>
      </div>

      {saveSnapshot && runeProgress ? (
        <div className="rune-save-strip">
          <Metric label={t("save.loaded")} value={saveSnapshot.fileName} />
          <Metric label={t("save.runeNodesActive")} value={`${formatNumber(runeProgress.activeNodes, locale)} / ${formatNumber(data.totals.nodeCount, locale)}`} />
          <Metric label={t("save.runeLevels")} value={`${formatNumber(runeProgress.currentLevels, locale)} / ${formatNumber(runeProgress.maxLevels, locale)}`} />
          <Metric label={t("save.remainingRuneCost")} value={formatNumber(runeProgress.remainingCost, locale)} />
          <Metric label={t("save.goldAfterMax")} value={formatNumber(saveSnapshot.gold - runeProgress.remainingCost, locale)} />
        </div>
      ) : null}

      <div className="rune-layout">
        <div className="rune-board-shell">
          <div
            className="rune-board"
            onPointerDown={(event) => {
              if (event.button !== 0 || (event.target as HTMLElement).closest("button")) {
                return;
              }
              event.currentTarget.setPointerCapture(event.pointerId);
              dragRef.current = {
                pointerId: event.pointerId,
                startX: event.clientX,
                startY: event.clientY,
                originX: pan.x,
                originY: pan.y,
              };
            }}
            onPointerMove={(event) => {
              const drag = dragRef.current;
              if (!drag || drag.pointerId !== event.pointerId) {
                return;
              }
              setPan({
                x: drag.originX + event.clientX - drag.startX,
                y: drag.originY + event.clientY - drag.startY,
              });
            }}
            onPointerUp={endDrag}
            onPointerCancel={endDrag}
            onPointerLeave={endDrag}
          >
            <div
              className="rune-map"
              style={{
                width: data.bounds.width,
                height: data.bounds.height,
                transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
              }}
            >
              <svg className="rune-map-lines" viewBox={`0 0 ${data.bounds.width} ${data.bounds.height}`}>
                {data.edges.map((edge, index) => {
                  const from = nodeMap.get(edge.from);
                  const to = nodeMap.get(edge.to);
                  if (!from || !to) {
                    return null;
                  }
                  const muted = mutedCategories[from.category] || mutedCategories[to.category];
                  return (
                    <line
                      className={`rune-map-edge ${edge.kind} ${muted ? "muted" : ""}`}
                      key={`${edge.from}:${edge.to}:${index}`}
                      x1={from.x + nodeSize / 2}
                      y1={from.y + nodeSize / 2}
                      x2={to.x + nodeSize / 2}
                      y2={to.y + nodeSize / 2}
                      style={{ "--edge-color": from.categoryColor } as CSSProperties}
                    />
                  );
                })}
              </svg>
              {data.nodes.map((node) => {
                const level = levels[node.id] ?? 0;
                const active = level > 0;
                const selectedNode = resolvedSelectedId === node.id;
                const muted = mutedCategories[node.category];
                return (
                  <button
                    type="button"
                    className={`rune-map-node ${active ? "active" : ""} ${selectedNode ? "selected" : ""} ${muted ? "muted" : ""} ${node.isUnlock ? "unlock" : ""}`}
                    key={node.id}
                    onClick={() => {
                      setSelectedId(node.id);
                      setHoveredId(node.id);
                    }}
                    onPointerEnter={() => setHoveredId(node.id)}
                    onPointerMove={() => setHoveredId(node.id)}
                    onPointerLeave={() => setHoveredId((current) => (current === node.id ? null : current))}
                    onMouseEnter={() => setHoveredId(node.id)}
                    onMouseLeave={() => setHoveredId((current) => (current === node.id ? null : current))}
                    onFocus={() => setHoveredId(node.id)}
                    onBlur={() => setHoveredId((current) => (current === node.id ? null : current))}
                    onPointerDown={(event) => event.stopPropagation()}
                    style={
                      {
                        left: node.x,
                        top: node.y,
                        width: nodeSize,
                        height: nodeSize,
                        "--category-color": node.categoryColor,
                      } as CSSProperties
                    }
                    title={text(node.title)}
                  >
                    {node.icon ? <img src={node.icon} alt="" draggable={false} loading="lazy" /> : <span />}
                    <span className="rune-node-rank">
                      {level}/{node.maxLevel}
                    </span>
                  </button>
                );
              })}
            </div>
            {hovered ? (
              <div
                className={`rune-hover-card ${hoveredFlip ? "flip" : ""}`}
                style={
                  {
                    left: pan.x + (hovered.x + (hoveredFlip ? -12 : nodeSize + 12)) * zoom,
                    top: pan.y + (hovered.y - 8) * zoom,
                    "--category-color": hovered.categoryColor,
                  } as CSSProperties
                }
              >
                <strong>{text(hovered.title)}</strong>
                <span>{formatValue(hoveredEffect, locale)}</span>
                <small>
                  {t(hovered.categoryKey)} / {t("rune.level")} {formatNumber(hoveredLevel, locale)}/{formatNumber(hovered.maxLevel, locale)}
                </small>
              </div>
            ) : null}
          </div>
        </div>

        <aside className="rune-side rune-detail-panel">
          {selected ? (
            <>
              <div className="rune-selected">
                <Icon src={selected.icon} large rarity={selected.rarity} />
                <div>
                  <small>{t("rune.selected")}</small>
                  <h3>{text(selected.title)}</h3>
                  <p>{t(selected.categoryKey)} / {text(selected.statName)}</p>
                </div>
              </div>
              <div className="rune-levels">
                {Array.from({ length: selected.maxLevel + 1 }, (_, level) => (
                  <button
                    className={selectedLevel === level ? "chip active" : "chip"}
                    onClick={() => setNodeLevel(selected, level)}
                    key={level}
                  >
                    {level === 0 ? "0" : `${t("rune.level")} ${formatNumber(level, locale)}`}
                  </button>
                ))}
              </div>
              <div className="stat-grid rune-metrics">
                <Metric label={t("rune.cost")} value={formatNumber(selectedCost, locale)} />
                <Metric label={t("rune.requiredLevel")} value={formatValue(selected.requiredLevel, locale)} />
                <Metric label={t("rune.totalCost")} value={formatNumber(selected.totalCost, locale)} />
              </div>
              <div className="rune-effect-list">
                {selected.levels.map((level) => (
                  <div className={Number(level.level) <= selectedLevel ? "active" : ""} key={`${selected.id}:${level.level}`}>
                    <span>{t("rune.level")} {formatNumber(level.level, locale)}</span>
                    <strong>{formatValue(level.effect, locale)}</strong>
                    <small>{formatNumber(level.costValue, locale)} {text(level.costItem)}</small>
                  </div>
                ))}
              </div>
            </>
          ) : null}

          <div className="rune-total">
            <div className="stat-grid rune-metrics">
              <Metric label={t("rune.totalCost")} value={formatNumber(totals.cost, locale)} />
              <Metric label={t("rune.maxAll")} value={formatNumber(data.totals.allCost, locale)} />
              <Metric label={t("rune.nodeCount")} value={formatNumber(data.totals.nodeCount, locale)} />
              {runeProgress ? <Metric label={t("save.remainingRuneCost")} value={formatNumber(runeProgress.remainingCost, locale)} /> : null}
            </div>
            <h3>{t("rune.totalBonuses")}</h3>
            {totals.bonuses.length ? (
              <div className="rune-bonus-list">
                {totals.bonuses.slice(0, 18).map((bonus) => (
                  <div key={text(bonus.name)}>
                    <span>{text(bonus.name)}</span>
                    <strong>+{formatNumber(bonus.value, locale)}</strong>
                  </div>
                ))}
              </div>
            ) : (
              <p className="empty">{t("state.empty")}</p>
            )}
          </div>
        </aside>
      </div>
    </section>
  );
}





export function AdUnit() {
  useEffect(() => {
    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      ((window as any).adsbygoogle = (window as any).adsbygoogle || []).push({});
    } catch {
      // ignore
    }
  }, []);
  return (
    <div className="ad-wrapper">
      <ins
        className="adsbygoogle"
        style={{ display: "block" }}
        data-ad-client="ca-pub-1835873052239386"
        data-ad-slot="default"
        data-ad-format="auto"
        data-full-width-responsive="true"
      />
    </div>
  );
}

export function MagitechFooter({ t }: { t: (key: string) => string }) {
  return (
    <footer className="magitech-footer">
      <div className="magitech-footer-links">
        <a href="https://ko-fi.com/X8X11KVU5K" target="_blank" rel="noreferrer">
          {t("support.kofi").toUpperCase()}
        </a>
        <a href="https://ofuse.me/o?uid=116462" target="_blank" rel="noreferrer">
          {t("support.ofuse").toUpperCase()}
        </a>
      </div>
      <div className="magitech-footer-text">
        TBH LAB // CORE ENGINE STATUS: NOMINAL // AD NOTICE ACTIVE
      </div>
    </footer>
  );
}


export function DetailSectionView({
  section,
  t,
  locale,
}: {
  section: DetailSection;
  t: (key: string) => string;
  locale: LocaleCode;
}) {
  if (section.type === "stats") {
    return (
      <div className="stat-grid">
        {section.items.map((item, index) => (
          <Metric key={`${item.labelKey}:${index}`} label={t(item.labelKey)} value={formatValue(item.value, locale)} />
        ))}
      </div>
    );
  }
  if (section.type === "cards") {
    return (
      <div className="entry-grid">
        {section.items.map((item, index) => (
          <article className="entry-card" key={index}>
            <div>
              <h3>{formatValue(item.title, locale)}</h3>
              <p>{localizedText(item.subtitle, locale)}</p>
            </div>
          </article>
        ))}
      </div>
    );
  }
  return (
    <div className="table-wrap">
      <table className="data-table compact">
        <thead>
          <tr>
            {section.columns.map((column, index) => (
              <th key={`${column.labelKey}:${index}`}>{t(column.labelKey)}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {section.rows.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {row.map((cell, cellIndex) => (
                <td key={`${rowIndex}:${cellIndex}`}>{formatValue(cell, locale)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Pager({
  page,
  pageCount,
  setPage,
  t,
  locale,
  bottom,
}: {
  page: number;
  pageCount: number;
  setPage: (value: number | ((current: number) => number)) => void;
  t: (key: string) => string;
  locale: LocaleCode;
  bottom?: boolean;
}) {
  return (
    <div className={`pager ${bottom ? "bottom" : ""}`}>
      <button disabled={page <= 1} onClick={() => setPage((current) => Math.max(1, current - 1))}>
        {t("pager.previous")}
      </button>
      <span>
        {t("pager.page")} {formatNumber(page, locale)} / {formatNumber(pageCount, locale)}
      </span>
      <button disabled={page >= pageCount} onClick={() => setPage((current) => Math.min(pageCount, current + 1))}>
        {t("pager.next")}
      </button>
    </div>
  );
}

export function Icon({
  src,
  large,
  hero,
  rarity,
}: {
  src?: string | null;
  large?: boolean;
  hero?: boolean;
  rarity?: string | null;
}) {
  return (
    <span className={`icon ${large ? "large" : ""} ${hero ? "hero" : ""} rarity-${rarity ?? "NONE"}`}>
      {src ? <img src={src} alt="" loading="lazy" /> : <span />}
    </span>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <small>{label}</small>
      <strong>{value}</strong>
    </div>
  );
}

export function StatePanel({ label, detail }: { label: string; detail?: string }) {
  return (
    <section className="panel state-panel">
      <div className="loading-rune" />
      <h1>{label}</h1>
      {detail ? <p>{detail}</p> : null}
    </section>
  );
}
export default App;
