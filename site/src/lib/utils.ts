import { useState, useEffect } from "react";

// === TypeScript Types ===
export type LocaleCode = string;
export type Localized = Partial<Record<string, string>>;

export type CategorySummary = {
  id: string;
  titleKey: string;
  descriptionKey: string;
  count: number;
  icon: string | null;
  layout: "table" | "cards";
  navGroup: string;
  listPath: string;
};

export type NavGroup = {
  id: string;
  items: string[];
};

export type Manifest = {
  generatedAt: string;
  locales: LocaleCode[];
  localeLabels?: Record<string, string>;
  defaultLocale?: LocaleCode;
  seo?: {
    siteUrl?: string;
    defaultLocale?: LocaleCode;
    alternateStrategy?: string;
  };
  version: string;
  categories: CategorySummary[];
  navGroups: NavGroup[];
  home: {
    heroArt: string | null;
    rosterArt: string | null;
    stats: Array<{ labelKey: string; value: string | number }>;
    notes: Array<{ labelKey: string; value?: string | number }>;
  };
  featured: Array<{ categoryId: string; slug: string }>;
};

export type Entry = {
  categoryId: string;
  entityId: string;
  slug: string;
  title: Localized;
  subtitle: Localized;
  icon: string | null;
  rarity: string | null;
  tags: string[];
  fields: Record<string, string>;
  fieldDisplay?: Record<string, Localized>;
  detailPath: string;
  tooltip?: TooltipData | null;
};

export type TooltipRow = {
  label?: Localized;
  labelKey?: string;
  value: Localized;
  tone?: string;
};

export type TooltipSection = {
  titleKey: string;
  rows: TooltipRow[];
};

export type TooltipData = {
  title: Localized;
  subtitle: Localized;
  description?: Localized;
  icon: string | null;
  rarity: string | null;
  rows: TooltipRow[];
  sections: TooltipSection[];
};

export type CellValue = string | number | null | Localized;

export type DetailSection =
  | {
      titleKey: string;
      type: "stats";
      items: Array<{ labelKey: string; value: string }>;
    }
  | {
      titleKey: string;
      type: "table";
      columns: Array<{ labelKey: string }>;
      rows: Array<Array<CellValue>>;
    }
  | {
      titleKey: string;
      type: "cards";
      items: Array<{ title: Localized; subtitle?: Localized; meta?: Array<{ labelKey: string; value: string }> }>;
    };

export type DetailPayload = {
  categoryId: string;
  entityId: string;
  slug: string;
  title: Localized;
  subtitle: Localized;
  icon: string | null;
  heroImage?: string | null;
  rarity: string | null;
  tags: string[];
  overview: Array<{ labelKey: string; value: CellValue }>;
  sections: DetailSection[];
  source?: { table?: string };
};

export type Route =
  | { kind: "home" }
  | { kind: "category"; categoryId: string; query?: string }
  | { kind: "detail"; categoryId: string; slug: string };

// === Constants ===
export const PAGE_SIZE = 48;
export const LOCALE_KEY = "thb-wiki-locale";
export const DEFAULT_LOCALE = "ja-JP";
export const SITE_ORIGIN = "https://tbh.negi-lab.com";
export const SUPPORTED_LOCALES: Array<{ code: LocaleCode; label: string }> = [
  { code: "de-DE", label: "Deutsch" },
  { code: "en-US", label: "English" },
  { code: "es-ES", label: "Español" },
  { code: "fr-FR", label: "Français" },
  { code: "id-ID", label: "Bahasa Indonesia" },
  { code: "ja-JP", label: "日本語" },
  { code: "ko-KR", label: "한국어" },
  { code: "pl-PL", label: "Polski" },
  { code: "pt-BR", label: "Português (Brasil)" },
  { code: "ru-RU", label: "Русский" },
  { code: "th-TH", label: "ไทย" },
  { code: "tr-TR", label: "Türkçe" },
  { code: "vi-VN", label: "Tiếng Việt" },
  { code: "zh-CN", label: "简体中文" },
  { code: "zh-TW", label: "繁體中文" },
];

// === Helper Functions ===
export function normalizeLocale(value: string | null | undefined): LocaleCode {
  if (!value) {
    return DEFAULT_LOCALE;
  }
  const matched = SUPPORTED_LOCALES.find(
    (option) => option.code.toLowerCase() === value.toLowerCase() || option.code.split("-")[0] === value.toLowerCase()
  );
  return matched ? matched.code : DEFAULT_LOCALE;
}

export function intlLocale(locale: LocaleCode) {
  if (locale === "zh-CN") {
    return "zh-Hans-CN";
  }
  if (locale === "zh-TW") {
    return "zh-Hant-TW";
  }
  return locale;
}

export function localizedText(value: Localized | undefined, locale: LocaleCode) {
  if (!value) {
    return "";
  }
  return value[locale] || value[DEFAULT_LOCALE] || Object.values(value)[0] || "";
}

export function href(route: Route): string {
  if (route.kind === "category") {
    const query = route.query ? `?q=${encodeURIComponent(route.query)}` : "";
    return `#/category/${route.categoryId}${query}`;
  }
  if (route.kind === "detail") {
    return `#/detail/${route.categoryId}/${encodeURIComponent(route.slug)}`;
  }
  return "#/";
}

export function categoryListPath(category: CategorySummary, locale: LocaleCode) {
  return category.listPath.replace("{locale}", normalizeLocale(locale));
}

export function useJson<T>(path: string | null) {
  const [state, setState] = useState<{
    path: string | null;
    data: T | null;
    error: string | null;
  }>({ path: null, data: null, error: null });

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
      .then((result) => {
        if (!cancelled) {
          setState({ path, data: result, error: null });
        }
      })
      .catch((err: Error) => {
        if (!cancelled) {
          setState({ path, data: null, error: err.message });
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

export function formatNumber(value: string | number, locale: LocaleCode = "en") {
  const number = Number(value);
  if (Number.isFinite(number)) {
    return new Intl.NumberFormat(intlLocale(locale)).format(number);
  }
  return String(value);
}

export function formatValue(value: CellValue | undefined, locale: LocaleCode) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  if (typeof value === "object") {
    return localizedText(value, locale) || "-";
  }
  if (typeof value === "number") {
    return formatNumber(value, locale);
  }
  return value;
}

export function useRoute() {
  const [route, setRoute] = useState<Route>(parseRoute);
  useEffect(() => {
    const onHashChange = () => setRoute(parseRoute());
    const onPopState = () => setRoute(parseRoute());
    window.addEventListener("hashchange", onHashChange);
    window.addEventListener("popstate", onPopState);
    return () => {
      window.removeEventListener("hashchange", onHashChange);
      window.removeEventListener("popstate", onPopState);
    };
  }, []);
  return route;
}

export function parseRoute(): Route {
  const hash = window.location.hash;
  if (hash.startsWith("#/category/")) {
    const parts = hash.slice("#/category/".length).split("?");
    const categoryId = parts[0];
    const queryParams = new URLSearchParams(parts[1] ?? "");
    const query = queryParams.get("q") ?? undefined;
    return { kind: "category", categoryId, query };
  }
  if (hash.startsWith("#/detail/")) {
    const parts = hash.slice("#/detail/".length).split("/");
    const categoryId = parts[0];
    const slug = decodeURIComponent(parts[1] ?? "");
    return { kind: "detail", categoryId, slug };
  }
  return { kind: "home" };
}

export function useLocale() {
  const [locale, setLocale] = useState<LocaleCode>(() => {
    const requested = new URLSearchParams(window.location.search).get("lang");
    if (requested) {
      return normalizeLocale(requested);
    }
    const saved = window.localStorage.getItem(LOCALE_KEY);
    return normalizeLocale(saved);
  });
  useEffect(() => {
    window.localStorage.setItem(LOCALE_KEY, locale);
    document.documentElement.lang = normalizeLocale(locale);
  }, [locale]);
  return { locale, setLocale };
}

export function routePath(route: Route): string {
  if (route.kind === "category") {
    const query = route.query ? `?q=${encodeURIComponent(route.query)}` : "";
    return `/category/${route.categoryId}${query}`;
  }
  if (route.kind === "detail") {
    return `/detail/${route.categoryId}/${encodeURIComponent(route.slug)}`;
  }
  return "/";
}

export function seoUrl(route: Route, locale: LocaleCode, origin = SITE_ORIGIN): string {
  const url = new URL(origin);
  url.searchParams.set("lang", normalizeLocale(locale));
  const path = routePath(route);
  if (path !== "/") {
    url.searchParams.set("route", path);
  }
  return url.toString();
}

const FALLBACK_TEXT: Record<string, Record<string, string>> = {
  ja: {
    "app.title": "TBH Lab",
    "nav.home": "ホーム",
    "nav.search": "検索",
    "state.loading": "読み込み中",
    "state.error": "読み込み失敗",
  },
  en: {
    "app.title": "TBH Lab",
    "nav.home": "Home",
    "nav.search": "Search",
    "state.loading": "Loading",
    "state.error": "Failed to load",
  },
};

function localeBase(locale: LocaleCode) {
  return locale.split("-")[0];
}

function isJapaneseLocale(locale: LocaleCode) {
  return localeBase(locale) === "ja";
}

export function fallbackDictionary(locale: LocaleCode) {
  return isJapaneseLocale(locale) ? FALLBACK_TEXT.ja : FALLBACK_TEXT.en;
}
