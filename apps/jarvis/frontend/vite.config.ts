import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import { createHash } from 'node:crypto';
export default defineConfig({
  plugins: [
    react(),
    {
      name: 'static-only-worker',
      generateBundle(_, bundle) {
        const assets = [
          '/',
          '/icon.svg',
          '/manifest.webmanifest',
          ...Object.keys(bundle)
            .filter((x) => /\.(js|css)$/.test(x))
            .map((x) => '/' + x),
        ];
        const version = createHash('sha256')
          .update(JSON.stringify(assets))
          .digest('hex')
          .slice(0, 16);
        this.emitFile({
          type: 'asset',
          fileName: 'sw.js',
          source: String.raw`
const CACHE = 'jarvis-static-${version}';
const ASSETS = ${JSON.stringify(assets)};
const ROUTES = /^\/(?:chat|missions|projects|memory|approvals|engineer(?:\/graph)?|tutor|gm(?:\/[a-fA-F0-9-]{36}(?:\/session)?)?|settings)?$/;
self.addEventListener('install', e => e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS))));
self.addEventListener('activate', e => e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k.startsWith('jarvis-static-') && k !== CACHE).map(k => caches.delete(k))))));
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (u.origin !== self.location.origin || e.request.method !== 'GET' || e.request.headers.has('Authorization') || u.search || u.pathname.startsWith('/api/') || u.pathname === '/health') return;
  if (e.request.mode === 'navigate' && ROUTES.test(u.pathname)) {
    e.respondWith(fetch(e.request).catch(() => caches.open(CACHE).then(c => c.match('/')))); return;
  }
  if (ASSETS.includes(u.pathname)) e.respondWith(caches.open(CACHE).then(c => c.match(u.pathname)).then(r => r || fetch(e.request)));
});`,
        });
      },
    },
  ],
  build: { outDir: '../src/jarvis/web', emptyOutDir: true, sourcemap: false },
  server: { proxy: { '/api': 'http://127.0.0.1:8000', '/health': 'http://127.0.0.1:8000' } },
  test: {
    environment: 'jsdom',
    setupFiles: ['tests/setup.ts'],
    include: ['tests/*.test.ts', 'tests/*.test.tsx'],
  },
});
