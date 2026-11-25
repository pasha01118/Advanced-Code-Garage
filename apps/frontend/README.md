# Frontend — Advanced Code Garage

Next.js 16 App Router + React 19 + TypeScript + Tailwind CSS dashboard, deployed on Vercel.

## Local development

Run from the repository root (pnpm 12.6.0 workspace):

```bash
corepack enable && corepack prepare pnpm@12.6.0 --activate
pnpm install
# apps/frontend/.env.local:
#   NEXT_PUBLIC_SUPABASE_URL=...
#   NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=...
#   NEXT_PUBLIC_API_URL=http://localhost:8000   # omit on Vercel (vercel.json rewrites /api)
pnpm --filter frontend dev
```

Useful checks: `pnpm lint`, `pnpm exec tsc --noEmit`, `pnpm build` (from `apps/frontend`).

## Backend API and live streams

`vercel.json` rewrites `/api/:path*` to the Render-hosted FastAPI backend; there is intentionally no
second rewrite in `next.config.ts`. Both live streams (terminal logs and the admin Sentinel feed) use
authenticated SSE consumed by a fetch-based client — not WebSockets or WebRTC.

## Contract

`pnpm gen:api` regenerates `../../packages/contract/generated/api.ts` from
`../../packages/contract/openapi.json`. CI checks both the committed spec against the live FastAPI
schema and the generated TypeScript against the spec.

See the [Next.js documentation](https://nextjs.org/docs) for framework details.
