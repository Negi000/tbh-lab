# TBH Lab

TBH Lab is a generated TaskbarHero wiki and tooling lab. It turns local text, dump, Mono, and image resources into static JSON, then ships a Vite/React frontend with Cloudflare Pages Functions for market data.

GitHub: https://github.com/Negi000/tbh-lab

## Repository Layout

- `site/` - Cloudflare Pages project root. Build this directory on Cloudflare.
- `site/src/` - React UI, wiki pages, save reader, market UI, and lab status surfaces.
- `site/functions/` - Cloudflare Pages Functions, including `/api/market`.
- `site/public/generated/` - generated wiki payload that should be committed for public builds.
- `tools/` - local extraction and payload generation scripts.
- `build.py` - full local rebuild from local resources, then frontend build.
- `docs/` - architecture and deployment notes.

## Local Development

```powershell
cd E:\THB_Lab\site
npm ci
npm run dev
```

Full regeneration requires the local resource folders that are intentionally not pushed:

```powershell
cd E:\THB_Lab
python build.py
```

## Cloudflare Pages

Connect the GitHub repository `Negi000/tbh-lab` and use `site` as the Cloudflare Pages project root.

- Build command: `npm ci && npm run build`
- Build output directory: `dist`
- Functions directory: `functions`
- Wrangler config: `site/wrangler.toml`

Do not run `python build.py` in Cloudflare. The public build uses the committed `site/public/generated` payload.

Local Wrangler deployment requires Cloudflare authentication first:

```powershell
cd E:\THB_Lab\site
npx wrangler login
npx wrangler whoami
```

## Privacy

The My Save feature decrypts selected save files in the browser only. It does not upload saves and does not write back to disk.
