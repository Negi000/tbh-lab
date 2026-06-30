import React, { useState, useEffect } from "react";
import { readTaskbarHeroSave } from "../saveReader";
import type { SaveSnapshot, SaveOwnedItem } from "../saveReader";
import { Icon, AdUnit, MagitechFooter } from "../App";
import { href, useJson, formatNumber } from "../lib/utils";
import type { Manifest, LocaleCode, Localized } from "../lib/utils";
import type { MarketManifest, MarketManifestItem } from "../toolPages";

interface MagitechDashboardProps {
  manifest: Manifest;
  t: (key: string) => string;
  text: (value: Localized | undefined) => string;
  locale: LocaleCode;
  saveSnapshot: SaveSnapshot | null;
  onSaveLoaded: (snapshot: SaveSnapshot | null) => void;
}

export function MagitechDashboard({
  manifest,
  t,
  text,
  locale,
  saveSnapshot,
  onSaveLoaded,
}: MagitechDashboardProps) {
  const [dragActive, setDragActive] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Asset Valuation States
  const [assetValueJpy, setAssetValueJpy] = useState<number | null>(null);
  const [assetValueUsd, setAssetValueUsd] = useState<number | null>(null);
  const [valLoading, setValLoading] = useState(false);

  const marketManifestState = useJson<MarketManifest>("/generated/market-manifest.json");

  // File loading handlers
  const handleFile = async (file: File) => {
    setBusy(true);
    setError(null);
    try {
      const snapshot = await readTaskbarHeroSave(file);
      onSaveLoaded(snapshot);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : t("save.error"));
    } finally {
      setBusy(false);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await handleFile(e.target.files[0]);
    }
  };

  // Asset Valuation calculation
  useEffect(() => {
    if (!saveSnapshot || !marketManifestState.data) {
      return;
    }

    const calculateAssetValue = async () => {
      setValLoading(true);
      try {
        const manifestData = marketManifestState.data;
        if (!manifestData) return;

        const rateEndpoint = import.meta.env.VITE_TBH_MARKET_ENDPOINT || "/api/market";
        let rate = 160.0; // Default fallback
        try {
          const rateRes = await fetch(`${rateEndpoint.replace(/\/$/, "")}/rate`);
          const rateData = await rateRes.json();
          if (rateData && typeof rateData.usdjpy === "number") {
            rate = rateData.usdjpy;
          }
        } catch {
          // ignore
        }

        const manifestByItem = new Map<number, MarketManifestItem>();
        manifestData.items.forEach((item: MarketManifestItem) => {
          manifestByItem.set(item.itemKey, item);
        });

        const targetItems = saveSnapshot.ownedItems
          .map((owned) => ({ owned, manifest: manifestByItem.get(owned.itemKey) }))
          .filter((row): row is { owned: SaveOwnedItem; manifest: MarketManifestItem } => !!row.manifest && row.manifest.marketable)
          .slice(0, 15);

        let totalUsd = 0;

        // Fetch quotes in parallel
        await Promise.all(
          targetItems.map(async ({ owned, manifest: itemManifest }) => {
            const queryName = itemManifest.queries[0] || text(itemManifest.title);
            if (!queryName) return;
            try {
              const res = await fetch(`${rateEndpoint.replace(/\/$/, "")}/items?q=${encodeURIComponent(queryName)}`);
              const data = await res.json();
              if (data && data.items && data.items[0]) {
                const quote = data.items[0];
                const sellPrice = Number(quote.sell_price) || 0;
                totalUsd += sellPrice * owned.quantity;
              }
            } catch {
              // ignore
            }
          })
        );

        setAssetValueUsd(totalUsd);
        setAssetValueJpy(Math.round(totalUsd * rate));
      } catch {
        // ignore
      } finally {
        setValLoading(false);
      }
    };

    calculateAssetValue();
  }, [saveSnapshot, marketManifestState.data, text]);

  const jumpCategories = manifest.categories.filter((c) => c.navGroup === "nav.database" || c.navGroup === "nav.combat").slice(0, 8);

  return (
    <div className="lab-dashboard animated fade-in">
      {/* Title block */}
      <div className="lab-header console-glow">
        <h1 style={{ fontSize: "28px", margin: 0, fontFamily: "var(--font-display)", letterSpacing: "1px" }}>
          MAGITECH CONTROL CENTRE
        </h1>
        <p className="terminal-prompt">// DECIPHERING AND ANALYZING TASKBARHERO DATA METRICS</p>
      </div>

      {/* Main console row */}
      {!saveSnapshot ? (
        <section 
          className={`lab-dropzone ${dragActive ? "drag-active" : ""} scan-line`}
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={() => document.getElementById("dashboard-file-input")?.click()}
        >
          <input 
            type="file" 
            id="dashboard-file-input" 
            accept=".es3,.bak,application/octet-stream"
            onChange={handleFileChange}
            style={{ display: "none" }}
          />
          <div className="radar-scanner">
            <div className="radar-line"></div>
          </div>
          <div className="lab-dropzone-icon">▲</div>
          <h2>{busy ? "DECRYPTING SAVE DATA..." : "DRAG & DROP SAVE FILE TO SCAN"}</h2>
          <p className="description-text">
            {busy 
              ? "Reading encrypted ES3 file contents and parsing JSON payload..." 
              : "Click or drop your TaskbarHero save file (.es3) here to initiate laboratory scan"
            }
          </p>
          {error && <p className="terminal-error">[ERROR] {error}</p>}
        </section>
      ) : (
        <div className="lab-panel-grid">
          {/* Left panel: Player analysis snapshot */}
          <article className="magitech-panel lab-subpanel scan-line hover-glow">
            <div className="panel-header-bar">
              <span className="accent-dot"></span>
              <h3>// SCAN ANALYSIS RESULT</h3>
            </div>
            
            <div className="lab-stat-row">
              <div className="lab-metric">
                <small>Player Status</small>
                <strong className="status-online">ACTIVE // ONLINE</strong>
              </div>
              <div className="lab-metric">
                <small>Game Version</small>
                <strong>{saveSnapshot.version || "Unknown"}</strong>
              </div>
            </div>
            
            <div className="lab-stat-row">
              <div className="lab-metric">
                <small>Gold Reserves</small>
                <strong className="gold-text">{formatNumber(saveSnapshot.gold, locale)} G</strong>
              </div>
              <div className="lab-metric">
                <small>Operational Clears</small>
                <strong>{formatNumber(saveSnapshot.totalClears, locale)}</strong>
              </div>
            </div>
            
            <div className="lab-stat-row">
              <div className="lab-metric">
                <small>Active Zone</small>
                <strong style={{ fontSize: "12px", color: "var(--brass-soft)" }}>
                  {saveSnapshot.currentStage ? text(saveSnapshot.currentStage.label) : "Unknown"}
                </strong>
              </div>
              <div className="lab-metric">
                <small>Deployment Roster</small>
                <strong>{saveSnapshot.arrangedHeroKeys.length} Heroes</strong>
              </div>
            </div>
            
            <button 
              type="button" 
              className="game-button danger-button" 
              style={{ width: "100%", marginTop: "14px" }}
              onClick={() => {
                onSaveLoaded(null);
                setAssetValueUsd(null);
                setAssetValueJpy(null);
              }}
            >
              PURGE LOADED SNAPSHOT
            </button>
          </article>

          {/* Right panel: Live Asset valuation */}
          <article className="magitech-panel lab-subpanel scan-line blueprint-grid hover-glow">
            <div className="panel-header-bar">
              <span className="accent-dot"></span>
              <h3>// STEAM MARKET VALUATION</h3>
            </div>
            
            <div className="value-meter-console">
              <div className="value-amount">
                {valLoading ? (
                  <span className="loading-flicker">CALCULATING VALUATION...</span>
                ) : assetValueJpy !== null ? (
                  `¥${formatNumber(assetValueJpy, locale)}`
                ) : (
                  "¥0"
                )}
              </div>
              <div className="value-currency">
                {valLoading ? "" : assetValueUsd !== null ? `~ $${assetValueUsd.toFixed(2)} USD` : "$0.00 USD"}
              </div>
              
              {/* Visual Meter Bar */}
              <div className="console-meter-container">
                <div 
                  className={`console-meter-bar ${valLoading ? "animating" : ""}`}
                  style={{ width: valLoading ? "30%" : assetValueUsd && assetValueUsd > 0 ? `${Math.min(100, Math.max(15, assetValueUsd * 20))}%` : "5%" }}
                ></div>
              </div>
            </div>
            
            <p className="terminal-note">
              * Calculated based on the top marketable items detected in your scanned inventory and stash, using real-time price statistics from the Steam Community Market.
            </p>
            <a 
              href="#/category/market" 
              className="game-button primary" 
              style={{ width: "100%", marginTop: "16px", display: "flex", justifyContent: "center", alignItems: "center" }}
            >
              OPEN MARKET SCANNER
            </a>
          </article>
        </div>
      )}

      {/* Database Quick Scan area */}
      <section className="magitech-panel lab-subpanel hover-glow" style={{ marginTop: "10px" }}>
        <div className="panel-header-bar">
          <span className="accent-dot"></span>
          <h3>// ARCHIVE DATA SCAN (DATABASE)</h3>
        </div>
        <div className="quick-scan-grid">
          {jumpCategories.map((category) => (
            <a className="quick-scan-card" href={href({ kind: "category", categoryId: category.id })} key={category.id}>
              <div className="icon-frame">
                <Icon src={category.icon} />
              </div>
              <div className="card-info">
                <h4>{t(category.titleKey)}</h4>
                <p className="scan-count">{formatNumber(category.count, locale)} records</p>
              </div>
              <div className="card-arrow">➔</div>
            </a>
          ))}
        </div>
      </section>
      <AdUnit />
      <MagitechFooter t={t} />
    </div>
  );
}
