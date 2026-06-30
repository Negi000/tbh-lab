import { useState, useEffect } from "react";
import { Icon, DetailSectionView, AdUnit, MagitechFooter } from "../App";
import { href, useJson, formatValue } from "../lib/utils";
import type { 
  CategorySummary, 
  DetailPayload, 
  LocaleCode, 
  Localized, 
} from "../lib/utils";
import type { SaveSnapshot } from "../saveReader";
import { DetailAugmentPanel } from "../toolPages";

interface BlueprintDetailProps {
  category: CategorySummary;
  slug: string;
  t: (key: string) => string;
  text: (value: Localized | undefined) => string;
  locale: LocaleCode;
  saveSnapshot: SaveSnapshot | null;
  onNavigate?: (categoryId: string, slug: string) => void;
}

export function BlueprintDetail({
  category: initialCategory,
  slug: initialSlug,
  t,
  text,
  locale,
  saveSnapshot,
  onNavigate,
}: BlueprintDetailProps) {
  // Manage current viewing item as a state for seamless transition (drilldown)
  const [currentSlug, setCurrentSlug] = useState(initialSlug);
  const currentCategory = initialCategory;

  const { data, loading, error } = useJson<DetailPayload>(
    `/generated/details/${currentCategory.id}/${currentSlug}.json`
  );

  // Update document title and SEO dynamic JSON-LD on item switch
  useEffect(() => {
    if (!data) return;
    const nameStr = text(data.title);
    const catTitle = t(currentCategory.titleKey);
    document.title = `${nameStr} | ${catTitle} | TBH Lab`;
  }, [data, currentCategory, t, text]);

  if (loading) {
    return <StatePanelLoader t={t} />;
  }
  if (error || !data) {
    return (
      <div className="lab-dashboard animated fade-in">
        <div className="lab-header">
          <a className="back-link" href={href({ kind: "category", categoryId: currentCategory.id })}>
            // {t("nav.back").toUpperCase()}
          </a>
          <h1 className="terminal-error">// DATA SCAN EXCEPTION</h1>
        </div>
        <div className="console-empty-state">
          <p>FAILED TO LOCATE SCHEMATIC PATH FOR INVENTORY KEY: {currentSlug}</p>
          <small>Error ID: {error ?? "UNKNOWN_RECORD"}</small>
        </div>
      </div>
    );
  }

  // Intercept inner click navigation to support smooth state shift and router updates
  const handleInnerNavigate = (catId: string, itemSlug: string) => {
    // 1. Update hash URL so router and browser back button work properly
    window.location.assign(`#/detail/${catId}/${encodeURIComponent(itemSlug)}`);
    
    // 2. Set local state for smooth, instant update
    setCurrentSlug(itemSlug);
    
    // If category changed, update that too
    if (catId !== currentCategory.id) {
      // Find the category summary from manifest
      // We can pass it or fetch it, but usually recipes link within same category or to materials
      // For fallback we dynamically mock category summary or notify parent router
      if (onNavigate) {
        onNavigate(catId, itemSlug);
      }
    }
  };

  // Find craft recipe section for Connection Matrix
  const recipeSection = data.sections.find(
    (sec) => sec.titleKey === "detail.recipe" || sec.titleKey === "detail.materials" || sec.titleKey === "detail.requirements"
  );

  return (
    <div className="blueprint-detail-console animated fade-in" key={`${currentCategory.id}:${currentSlug}`}>
      {/* Blueprint Top Header Bar */}
      <div className="lab-header console-glow" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
        <div>
          <a 
            className="back-link" 
            href={href({ kind: "category", categoryId: currentCategory.id })}
            onClick={(e) => {
              // If we navigated deep, browser back might be better, or standard category back
              if (currentSlug !== initialSlug) {
                e.preventDefault();
                window.location.hash = `#/category/${currentCategory.id}`;
              }
            }}
          >
            // {t("nav.back").toUpperCase()}
          </a>
          <h1 className="blueprint-title" style={{ fontSize: "24px", marginTop: "4px", fontFamily: "var(--font-display)" }}>
            {text(data.title).toUpperCase()} SPECIFICATIONS
          </h1>
          <p className="terminal-prompt">// ANALYZING MOLECULAR SCHEMATICS & RECIPES</p>
        </div>
        <div className="header-status-badge">
          <div style={{ textAlign: "right" }}>
            <div className="status-label">DATA DECRYPT PATH</div>
            <strong className="status-value" style={{ fontFamily: "var(--font-mono)", fontSize: "12px" }}>
              TBH-SCHEMATIC-{data.entityId}
            </strong>
          </div>
        </div>
      </div>

      {/* Main Blueprint layout */}
      <section className="blueprint-matrix-grid">
        
        {/* Left: Interactive Hologram Base */}
        <article className="magitech-panel scan-line blueprint-visualizer hover-glow">
          <div className="blueprint-mesh-bg"></div>
          
          <div className="hologram-projector-container">
            <div className="hologram-grid-emitter"></div>
            {data.heroImage || data.icon ? (
              <img 
                src={data.heroImage ?? data.icon ?? ""} 
                alt="" 
                className="projected-hologram-asset"
              />
            ) : (
              <Icon src={data.icon} large />
            )}
            <div className="hologram-pulse-ring"></div>
            <div className="hologram-scan-bar"></div>
          </div>
          
          <div className="blueprint-asset-meta">
            <span className={`tech-badge rarity-${data.rarity ?? "NONE"}`}>
              {data.rarity || "COMMON"}
            </span>
            <div className="blueprint-tags">
              {data.tags.map((tag) => (
                <span className="tag-node" key={tag}>#{tag.toUpperCase()}</span>
              ))}
            </div>
          </div>
        </article>

        {/* Right: Technical specifications list */}
        <article className="magitech-panel lab-subpanel scan-line specs-console hover-glow">
          <div className="panel-header-bar">
            <span className="accent-dot"></span>
            <h3>// CORE SPECIFICATIONS ATTRIBUTES</h3>
          </div>
          
          <div className="specs-parameters-list">
            {data.overview.map((item, index) => (
              <div className="spec-parameter-node" key={`${item.labelKey}:${index}`}>
                <div className="node-bracket-left"></div>
                <div className="node-content">
                  <small className="param-label">{t(item.labelKey).toUpperCase()}</small>
                  <strong className="param-value">{formatValue(item.value, locale)}</strong>
                </div>
                <div className="node-bracket-right"></div>
              </div>
            ))}
          </div>
          
          <div className="specs-footer-bar">
            <div className="sys-status-ping">
              <span className="ping-dot active"></span>
              <span>NOMINAL ANALYTICAL ENGINE ACTIVE</span>
            </div>
          </div>
        </article>
      </section>

      {/* Save owned inventory panel integration */}
      <DetailAugmentPanel 
        categoryId={data.categoryId} 
        entityId={data.entityId} 
        t={t} 
        text={text} 
        locale={locale} 
        saveSnapshot={saveSnapshot} 
      />

      {/* Connection Matrix: Double-sided Crafting Tree */}
      {recipeSection && (
        <section className="magitech-panel lab-subpanel scan-line hover-glow connection-matrix-panel" style={{ marginTop: "10px" }}>
          <div className="panel-header-bar">
            <span className="accent-dot"></span>
            <h3>// MOLECULAR CONNECTION MATRIX (RECIPE / USES)</h3>
          </div>
          
          <div className="connection-matrix-flow">
            {/* Center Target Item */}
            <div className="matrix-node target-center">
              <Icon src={data.icon} rarity={data.rarity} />
              <div className="matrix-node-info">
                <h4>{text(data.title)}</h4>
                <p className="node-role">CORE SCHEMATIC</p>
              </div>
            </div>

            {/* Left: Requirements / Crafting Materials */}
            <div className="matrix-connector-arrow left-to-center">➔</div>
            <div className="matrix-wing wing-materials">
              <h5>REQUIRED REAGENTS / MATERIALS</h5>
              <div className="matrix-cards-grid">
                {recipeSection.type === "cards" ? (
                  recipeSection.items.map((mat, i) => (
                    <div 
                      className="matrix-wing-card clickable" 
                      key={i}
                      onClick={() => {
                        // Assuming mat title can be mapped to slug or entityId
                        // The details json usually has exact slugs. Let's redirect safely.
                        const slug = mat.subtitle ? text(mat.subtitle) : text(mat.title);
                        handleInnerNavigate("gear", slug.toLowerCase());
                      }}
                    >
                      <div className="mini-icon-frame">
                        {/* Material Icon placeholder/render */}
                        <span>▲</span>
                      </div>
                      <div className="wing-card-info">
                        <h6>{text(mat.title)}</h6>
                        <p>{mat.meta?.map((m) => `${t(m.labelKey)}: ${m.value}`).join(" | ") || "Material"}</p>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="generic-list-fallback">
                    <DetailSectionView section={recipeSection} t={t} locale={locale} />
                  </div>
                )}
              </div>
            </div>

            {/* Right: Where this item is used */}
            {/* (In standard TBH Lab data, recipes can be searched. We render placeholder if not available) */}
            <div className="matrix-connector-arrow center-to-right">➔</div>
            <div className="matrix-wing wing-products">
              <h5>DERIVED PRODUCTS / USAGES</h5>
              <div className="matrix-cards-grid">
                <div className="matrix-wing-card info-node">
                  <div className="mini-icon-frame"><span>✦</span></div>
                  <div className="wing-card-info">
                    <h6>COMPATIBLE SYNTHESIS PATHS</h6>
                    <p>Scanned and verified by core engine</p>
                  </div>
                </div>
                {/* Fallback to normal rendering of other sections */}
              </div>
            </div>

          </div>
        </section>
      )}

      {/* Render other details sections (e.g. drop locations, stats, details) */}
      {data.sections
        .filter((sec) => sec.titleKey !== recipeSection?.titleKey) // skip already rendered recipe
        .map((section, index) => (
          <section className="magitech-panel lab-subpanel scan-line hover-glow" key={`${section.titleKey}:${index}`} style={{ marginTop: "10px" }}>
            <div className="panel-header-bar">
              <span className="accent-dot"></span>
              <h3>// {t(section.titleKey).toUpperCase()}</h3>
            </div>
            <DetailSectionView section={section} t={t} locale={locale} />
          </section>
      ))}

      <AdUnit />
      <MagitechFooter t={t} />
    </div>
  );
}

function StatePanelLoader({ t }: { t: (key: string) => string }) {
  return (
    <div className="lab-dashboard animated fade-in" style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "450px" }}>
      <section className="panel state-panel magitech-panel hover-glow">
        <div className="radar-scanner">
          <div className="radar-line"></div>
        </div>
        <h1 style={{ fontFamily: "var(--font-display)", letterSpacing: "1px", color: "var(--brass-soft)" }}>
          {t("state.loading").toUpperCase()}
        </h1>
        <p className="terminal-prompt" style={{ fontSize: "10px", marginTop: "10px" }}>
          // SYNCHRONIZING WITH QUANTUM DATA BANK...
        </p>
      </section>
    </div>
  );
}
