import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { runInNewContext } from 'node:vm';
import { describe, expect, it, vi } from 'vitest';
// Test the production worker emitted by the build, rather than duplicating its policy.
const worker = readFileSync(resolve('../src/jarvis/web/sw.js'), 'utf8');
function harness() {
  const handlers: Record<string, (e: any) => void> = {};
  runInNewContext(worker, {
    URL,
    self: {
      location: { origin: 'http://localhost' },
      addEventListener: (k: string, h: (e: any) => void) => (handlers[k] = h),
    },
    fetch: vi.fn(() => Promise.resolve(new Response('asset'))),
    caches: {
      open: () => Promise.resolve({ match: () => Promise.resolve(new Response('asset')) }),
    },
    Response,
    Promise,
  });
  return handlers;
}
describe('production service worker allowlist', () => {
  it.each([
    '/api/runs',
    '/api/campaigns/secret/scene',
    '/api/memories',
    '/health',
    '/docs',
    '/untrusted.svg',
    '/?token=secret',
    'https://evil.test/',
  ])('does not intercept private or unknown requests: %s', (url) => {
    const handlers = harness();
    const respondWith = vi.fn();
    handlers.fetch({ request: new Request(new URL(url, 'http://localhost')), respondWith });
    expect(respondWith).not.toHaveBeenCalled();
  });
  it('does not intercept authenticated shell requests or any write', () => {
    const h = harness();
    for (const req of [
      new Request('http://localhost/', { headers: { Authorization: 'Bearer private' } }),
      new Request('http://localhost/', { method: 'POST' }),
    ]) {
      const respondWith = vi.fn();
      h.fetch({ request: req, respondWith });
      expect(respondWith).not.toHaveBeenCalled();
    }
  });
  it('has valid syntax and intercepts only listed public assets', () => {
    const respondWith = vi.fn();
    harness().fetch({ request: new Request('http://localhost/icon.svg'), respondWith });
    expect(respondWith).toHaveBeenCalledTimes(1);
    expect(worker).not.toContain('localStorage');
    expect(worker).not.toContain('console.');
  });
});
