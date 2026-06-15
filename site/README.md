# TBH Lab Site

This is the Cloudflare Pages project for TBH Lab.

## Commands

```bash
npm ci
npm run dev
npm run lint
npm run build
npm run preview
```

## Cloudflare Pages

- Project root: `site`
- Build command: `npm ci && npm run build`
- Output: `dist`
- Functions: `functions`

The site build expects `public/generated` to already exist. Regenerate that payload locally from the repository root with `python build.py`.
