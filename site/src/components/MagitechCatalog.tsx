import { useState, useDeferredValue, useMemo } from "react";
import { Icon, Pager, StatePanel, AdUnit, MagitechFooter, StageAtlasWorkbench, RuneWorkbench } from "../App";
import { 
  href, 
  useJson, 
  categoryListPath, 
  formatNumber
} from "../lib/utils";
import type { 
  CategorySummary, 
  Entry, 
  LocaleCode, 
  Localized, 
} from "../lib/utils";
import type { SaveSnapshot, SaveOwnedItem } from "../saveReader";

interface MagitechCatalogProps {
  category: CategorySummary;
  t: (key: string) => string;
  text: (value: Localized | undefined) => string;
  locale: LocaleCode;
  initialQuery?: string;
  saveSnapshot: SaveSnapshot | null;
}

type CategoryPayload = {
  category: CategorySummary;
  columns: Array<{ key: string; labelKey: string }>;
  filters: Array<{ id: string; labelKey: string; options: string[] }>;
  entries: Entry[];
};

export function MagitechCatalog({
  category,
  t,
  text,
  locale,
  initialQuery,
  saveSnapshot,
}: MagitechCatalogProps) {
  const { data, loading, error } = useJson<CategoryPayload>(categoryListPath(category, locale));
  const [query, setQuery] = useState(initialQuery ?? "");
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [page, setPage] = useState(1);
  const [selectedEntryId, setSelectedEntryId] = useState<string | null>(null);
  
  // Mobile Tab State: "filters" | "list" | "preview"
  const [mobileTab, setMobileTab] = useState<"filters" | "list" | "preview">("list");

  const deferredQuery = useDeferredValue(query);
  const PAGE_SIZE = 32; // Optimized page size for console layout

  const filteredEntries = useMemo(() => {
    if (!data) {
      return [];
    }
    const needle = deferredQuery.trim().toLowerCase();
    return data.entries.filter((entry) => {
      const filterMatch = Object.entries(filters).every(
        ([field, value]) => !value || entry.fields[field] === value
      );
      if (!filterMatch) {
        return false;
      }
      if (!needle) {
        return true;
      }
      const haystack = [
        entry.entityId,
        ...Object.values(entry.title),
        ...Object.values(entry.subtitle),
        ...entry.tags,
        ...Object.values(entry.fields),
        ...Object.values(entry.fieldDisplay ?? {}).flatMap((value) => Object.values(value)),
      ]
        .join(" ")
        .toLowerCase();
      return haystack.includes(needle);
    });
  }, [data, deferredQuery, filters]);

  // Handle visible list and auto-selection
  const pageCount = useMemo(() => Math.max(1, Math.ceil(filteredEntries.length / PAGE_SIZE)), [filteredEntries]);
  const currentPage = useMemo(() => Math.min(page, pageCount), [page, pageCount]);
  const visibleEntries = useMemo(() => {
    return filteredEntries.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);
  }, [filteredEntries, currentPage]);

  const selectedEntry = useMemo(() => {
    if (visibleEntries.length === 0) return null;
    const matched = visibleEntries.find(e => e.entityId === selectedEntryId);
    return matched || visibleEntries[0];
  }, [visibleEntries, selectedEntryId]);

  if (loading) {
    return <StatePanel label={t("state.loading")} />;
  }
  if (error || !data) {
    return <StatePanel label={t("state.error")} detail={error ?? category.id} />;
  }

  const filterLabel = (filterId: string, option: string) => {
    const matched = data.entries.find(
      (entry) => entry.fields[filterId] === option && entry.fieldDisplay?.[filterId]
    );
    return text(matched?.fieldDisplay?.[filterId]) || option;
  };

  const isRuneCategory = category.id === "runes";
  const isStageCategory = category.id === "stages";

  // Check if save data has item owned
  const getOwnedCount = (entry: Entry) => {
    if (!saveSnapshot) return null;
    // Map item names or IDs to saveSnapshot structure
    const owned = saveSnapshot.ownedItems.find(
      (item: SaveOwnedItem) => String(item.itemKey) === entry.entityId
    );
    return owned ? owned.quantity : 0;
  };

  // Custom styling for specific fields
  const renderField = (key: string, value: string, entry: Entry) => {
    const fieldDisp = entry.fieldDisplay?.[key];
    const displayVal = fieldDisp ? text(fieldDisp) : value;
    if (key === "rarity" || key === "quality") {
      return <span className={`badge rarity-${value.toUpperCase()}`}>{displayVal}</span>;
    }
    return <span>{displayVal}</span>;
  };

  return (
    <div className="catalog-console animated fade-in">
      {/* Console Top Header */}
      <div className="lab-header console-glow" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
        <div>
          <a className="back-link" href={href({ kind: "home" })} style={{ fontFamily: "var(--font-display)", fontSize: "11px", color: "var(--brass-soft)" }}>
            // {t("nav.back").toUpperCase()}
          </a>
          <h1 style={{ fontSize: "24px", marginTop: "4px", fontFamily: "var(--font-display)" }}>
            {t(category.titleKey).toUpperCase()} DATA BANK
          </h1>
          <p className="terminal-prompt">// SCANNING DATA ARCHIVES: SUCCESSFUL</p>
        </div>
        
        <div className="header-status-badge">
          <Icon src={category.icon} />
          <div style={{ textAlign: "right" }}>
            <div className="status-label">Records Loaded</div>
            <strong className="status-value">{formatNumber(category.count, locale)}</strong>
          </div>
        </div>
      </div>

      {/* Special Workbenches (Stages or Runes) */}
      {isRuneCategory && (
        <RuneWorkbench t={t} text={text} locale={locale} saveSnapshot={saveSnapshot} />
      )}
      {isStageCategory && (
        <StageAtlasWorkbench t={t} text={text} locale={locale} saveSnapshot={saveSnapshot} />
      )}

      {/* Mobile Tab Selectors */}
      <div className="mobile-tab-bar">
        <button 
          className={mobileTab === "filters" ? "active" : ""} 
          onClick={() => setMobileTab("filters")}
        >
          FILTERS
        </button>
        <button 
          className={mobileTab === "list" ? "active" : ""} 
          onClick={() => setMobileTab("list")}
        >
          RECORDS ({filteredEntries.length})
        </button>
        <button 
          className={mobileTab === "preview" ? "active" : ""} 
          onClick={() => setMobileTab("preview")}
          disabled={!selectedEntry}
        >
          PREVIEW
        </button>
      </div>

      {/* 3-Column Core Console Workspace */}
      <div className="console-workspace">
        
        {/* Column 1: Filters (Left panel) */}
        <aside className={`console-column col-filters ${mobileTab === "filters" ? "mobile-active" : ""}`}>
          <div className="column-header">
            <span className="terminal-tag">// SEARCH PARAMETERS</span>
          </div>
          
          <div className="filter-scroll-area">
            <div className="search-box-wrapper">
              <input
                value={query}
                onChange={(event) => {
                  setQuery(event.target.value);
                }}
                placeholder={t("filter.search.placeholder")}
                className="console-search-input"
              />
              {query && <button className="clear-search-btn" onClick={() => setQuery("")}>×</button>}
            </div>

            {data.filters.map((filter) => (
              <div className="filter-group-panel" key={filter.id}>
                <h4>{t(filter.labelKey).toUpperCase()}</h4>
                <div className="filter-chips-grid">
                  <button
                    className={!filters[filter.id] ? "chip active" : "chip"}
                    onClick={() => {
                      setFilters((current) => ({ ...current, [filter.id]: "" }));
                    }}
                  >
                    {t("filter.all")}
                  </button>
                  {filter.options.map((option) => (
                    <button
                      className={filters[filter.id] === option ? "chip active" : "chip"}
                      onClick={() => {
                        setFilters((current) => ({ ...current, [filter.id]: option }));
                      }}
                      key={`${filter.id}:${option}`}
                    >
                      {filterLabel(filter.id, option)}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </aside>

        {/* Column 2: Scan Results List (Center panel) */}
        <main className={`console-column col-list ${mobileTab === "list" ? "mobile-active" : ""}`}>
          <div className="column-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span className="terminal-tag">
              // SCAN RESULTS ({formatNumber(filteredEntries.length, locale)} MATCHES)
            </span>
            <Pager page={currentPage} pageCount={pageCount} setPage={setPage} t={t} locale={locale} />
          </div>

          <div className="record-scroll-list">
            {visibleEntries.length === 0 ? (
              <div className="console-empty-state">
                <div className="blink-warning">⚠️</div>
                <p>NO COMPATIBLE RECORDS DETECTED IN ARCHIVE</p>
                <small>Try widening your search queries or resetting filters</small>
              </div>
            ) : (
              visibleEntries.map((entry) => {
                const isSelected = selectedEntry?.entityId === entry.entityId;
                const ownedQty = getOwnedCount(entry);
                return (
                  <article 
                    className={`console-item-card rarity-${entry.rarity ?? "NONE"} ${isSelected ? "selected-hologram" : ""}`}
                    key={entry.slug}
                    onClick={() => {
                      setSelectedEntryId(entry.entityId);
                      setMobileTab("preview"); // Auto focus preview on mobile select
                    }}
                  >
                    <div className="card-badge-line"></div>
                    <div className="card-media-box">
                      <Icon src={entry.icon} rarity={entry.rarity} />
                    </div>
                    <div className="card-details">
                      <div className="card-title-row">
                        <h3>{text(entry.title)}</h3>
                        {ownedQty !== null && ownedQty > 0 && (
                          <span className="owned-inventory-tag">x{ownedQty} OWNED</span>
                        )}
                      </div>
                      <p className="card-subtitle">{text(entry.subtitle) || entry.entityId}</p>
                      
                      {/* Secondary parameters */}
                      <div className="card-brief-params">
                        {Object.entries(entry.fields).slice(0, 3).map(([key, value]) => (
                          <span className="brief-param-node" key={key}>
                            <span className="param-label">{t(`field.${key}`)}:</span>{" "}
                            <span className="param-val">{value}</span>
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="card-laser-glow"></div>
                  </article>
                );
              })
            )}
          </div>
        </main>

        {/* Column 3: Quick Preview (Right panel) */}
        <aside className={`console-column col-preview ${mobileTab === "preview" ? "mobile-active" : ""}`}>
          <div className="column-header">
            <span className="terminal-tag">// DETAILED SPECTRAL ANALYSIS</span>
          </div>

          <div className="preview-scroll-area">
            {selectedEntry ? (
              <div className="hologram-preview-panel">
                
                {/* Visual Header Display */}
                <div className="hologram-display">
                  <div className="hologram-projection">
                    <Icon src={selectedEntry.icon} large rarity={selectedEntry.rarity} />
                    <div className="hologram-ring"></div>
                  </div>
                  <h2 className="preview-title">{text(selectedEntry.title)}</h2>
                  <p className="preview-subtitle">{text(selectedEntry.subtitle)}</p>
                  <span className={`badge rarity-${selectedEntry.rarity ?? "NONE"}`}>
                    {(selectedEntry.rarity ?? "COMMON").toUpperCase()}
                  </span>
                </div>

                {/* Database Metrics Grid */}
                <div className="preview-details-grid">
                  <div className="preview-section-title">// PARAMETERS</div>
                  {Object.entries(selectedEntry.fields).map(([key, value]) => (
                    <div className="preview-data-row" key={key}>
                      <span className="preview-data-label">{t(`field.${key}`)}</span>
                      <span className="preview-data-value">
                        {renderField(key, value, selectedEntry)}
                      </span>
                    </div>
                  ))}
                  
                  {/* Save data association */}
                  {saveSnapshot && (
                    <div className="preview-data-row inventory-status-row">
                      <span className="preview-data-label">Scanned Inventory</span>
                      <span className="preview-data-value highlight-val">
                        {getOwnedCount(selectedEntry) !== null 
                          ? `${getOwnedCount(selectedEntry)} units owned` 
                          : "0 units owned"
                        }
                      </span>
                    </div>
                  )}
                </div>

                {/* Actions Panel */}
                <div className="preview-actions">
                  <a 
                    href={href({ kind: "detail", categoryId: selectedEntry.categoryId, slug: selectedEntry.slug })}
                    className="game-button primary action-btn"
                  >
                    OPEN SCHEMATIC ANALYZER ⚙️
                  </a>
                  {mobileTab === "preview" && (
                    <button 
                      className="game-button mobile-back-list-btn"
                      onClick={() => setMobileTab("list")}
                    >
                      RETURN TO RECORDS LIST
                    </button>
                  )}
                </div>

              </div>
            ) : (
              <div className="console-empty-state" style={{ height: "100%", justifyContent: "center" }}>
                <div className="radar-scanner">
                  <div className="radar-line"></div>
                </div>
                <p>SELECT A RECORD TO INITIALIZE DEEP ANALYZER</p>
              </div>
            )}
          </div>
        </aside>

      </div>
      <AdUnit />
      <MagitechFooter t={t} />
    </div>
  );
}
