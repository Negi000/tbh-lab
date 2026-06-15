# Cloudflare Pages Deployment

TBH Lab is arranged so the public repository can build without private local game resources.

## Pages Settings

- Project root: `site`
- Build command: `npm ci && npm run build`
- Build output directory: `dist`
- Functions directory: `functions`

The generated wiki payload in `site/public/generated` must be committed. Cloudflare should only run the Vite build.

## Wrangler

`site/wrangler.toml` declares the Pages project and output directory. Cloudflare Pages uses `pages_build_output_dir` for Pages projects.

## What Not To Commit

- `リソース/`
- `output/`
- `site/node_modules/`
- `site/dist/`
- `site/.wrangler/`
- local `.es3` save files

## Update Flow

1. Refresh local game resources if needed.
2. Run `python build.py` locally.
3. Review `site/public/generated`.
4. Commit source and generated JSON.
5. Push to GitHub. Cloudflare Pages builds from `site`.
