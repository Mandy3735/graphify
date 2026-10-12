import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { Text, useLoad } from '../src/ui';
import { Client, ApiError } from '../src/api';
import { App } from '../src/App';
import { RunView, Approvals } from '../src/runs';
import { Memory } from '../src/memory';
function fakeClient(handler: (path: string, body?: unknown) => unknown) {
  const c = new Client('a'.repeat(32));
  vi.spyOn(c, 'request').mockImplementation(async (p, b) => handler(p, b));
  return c;
}
describe('browser trust boundary', () => {
  it('renders script, HTML and executable links literally and bounds content', () => {
    const { container } = render(
      <Text
        value={
          '<script>alert(1)</script><a href="javascript:alert(1)">click</a>' + 'x'.repeat(40000)
        }
      />,
    );
    expect(container.querySelector('script,a,iframe')).toBeNull();
    expect(container.textContent).toContain('<script>');
    expect(container.textContent).toContain('[Display truncated]');
    expect(container.textContent!.length).toBeLessThan(32100);
  });
  it('aborts requests and removes credential after close', async () => {
    const fetcher = vi
      .spyOn(globalThis, 'fetch')
      .mockImplementation(
        (_, o) =>
          new Promise((_, reject) =>
            o?.signal?.addEventListener('abort', () => reject(new Error('aborted'))),
          ),
      );
    const c = new Client('private-token');
    const p = c.request('/api/runs').catch((e) => e.message);
    c.close();
    expect(await p).toBe('aborted');
    await expect(c.request('/api/runs')).rejects.toThrow();
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
  it('rejects unauthorized responses without rendering server details', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response('GM_SECRET_TOKEN', { status: 403 }),
    );
    const c = new Client('test');
    await expect(c.request('/api/campaigns')).rejects.toThrow('Access denied');
  });
  it('expires identity on 401 and refuses cross-origin or redirected requests', async () => {
    const expired = vi.fn();
    const fetcher = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(new Response('', { status: 401 }));
    const c = new Client('test', expired);
    await expect(c.request('/api/settings')).rejects.toThrow('Authentication expired');
    expect(expired).toHaveBeenCalled();
    expect(fetcher.mock.calls[0][1]).toMatchObject({
      cache: 'no-store',
      credentials: 'omit',
      redirect: 'error',
    });
    await expect(new Client('test').request('https://evil/api')).rejects.toThrow();
  });
  it('rejects oversized streamed data before parsing', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('x'.repeat(2_000_001)));
    await expect(new Client('test').request('/api/runs')).rejects.toThrow('display budget');
  });
  it('discards stale results when scope changes', async () => {
    let finish!: (x: any) => void;
    const c = fakeClient((p) => (p.endsWith('old') ? new Promise((r) => (finish = r)) : 'new'));
    function Scoped({ path }: { path: string }) {
      const q = useLoad<string>(c, path);
      return <p>{q.data}</p>;
    }
    const { rerender } = render(<Scoped path="/api/old" />);
    rerender(<Scoped path="/api/new" />);
    await screen.findByText('new');
    finish('GM_SECRET_OLD');
    await waitFor(() => expect(screen.queryByText('GM_SECRET_OLD')).toBeNull());
  });
  it('keeps tokens out of persistent storage and clears the password field', async () => {
    const fetcher = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(new Response('', { status: 401 }));
    const storage = vi.spyOn(Storage.prototype, 'setItem');
    render(<App />);
    await userEvent.type(screen.getByLabelText('API token'), 'private-token-'.repeat(3));
    await userEvent.click(screen.getByRole('button', { name: 'Connect to JARVIS' }));
    await screen.findByRole('alert');
    expect(screen.getByLabelText('API token')).toHaveValue('');
    expect(storage).not.toHaveBeenCalled();
    expect(fetcher.mock.calls[0][0]).toBe('/api/settings');
  });
});
describe('workflow components', () => {
  it('shows durable completion, result and concise steps', async () => {
    const c = fakeClient(() => ({
      id: 'run',
      mode: 'TUTOR',
      state: 'COMPLETED',
      objective: 'Learn',
      result: 'Answer',
      steps: [{ state: 'VERIFYING', summary: 'Validated result' }],
      metadata: { model: 'fake' },
      tool_count: 0,
      updated_at: new Date().toISOString(),
    }));
    render(<RunView client={c} id="run" />);
    await screen.findByText('Answer');
    expect(screen.getByText(/Validated result/)).toBeVisible();
    expect(screen.queryByRole('button', { name: 'Cancel run' })).toBeNull();
  });
  it('reconnects after run polling fails', async () => {
    let failed = true;
    const c = fakeClient(() => {
      if (failed) throw new ApiError(503);
      return { state: 'COMPLETED', mode: 'TUTOR', result: 'Recovered' };
    });
    render(<RunView client={c} id="run" />);
    await screen.findByRole('button', { name: 'Reconnect' });
    failed = false;
    await userEvent.click(screen.getByRole('button', { name: 'Reconnect' }));
    await screen.findByText('Recovered');
  });
  it('submits the exact approval endpoint with no rewritten operation', async () => {
    const c = fakeClient((p) =>
      p === '/api/approvals'
        ? [
            {
              id: 'approval',
              run_id: 'run',
              status: 'PENDING',
              operation: { name: 'external.write', arguments: { text: '<script>unsafe</script>' } },
              expires_at: new Date(Date.now() + 60000).toISOString(),
            },
          ]
        : { run_id: 'run' },
    );
    render(<Approvals client={c} />);
    await screen.findByRole('button', { name: 'Approve exact operation' });
    await userEvent.click(screen.getByRole('button', { name: 'Approve exact operation' }));
    await waitFor(() =>
      expect(c.request).toHaveBeenCalledWith('/api/approvals/approval/approve', {}),
    );
  });
  it('exposes memory provenance and respects server edit eligibility', async () => {
    const c = fakeClient((p) =>
      p.startsWith('/api/memories?')
        ? {
            items: [
              {
                id: 'm',
                content: 'A note',
                memory_class: 'CANONICAL',
                revision: 1,
                visibility: 'PRIVATE',
                editable: false,
                deletable: false,
                sources: [{ locator: 'document' }],
              },
            ],
          }
        : [],
    );
    render(<Memory client={c} mode="TUTOR" />);
    await screen.findByText('A note');
    expect(screen.getByText('Provenance and retrieval reasons')).toBeVisible();
    expect(screen.queryByRole('button', { name: 'Correct memory' })).toBeNull();
  });
});

it('cancel action is human initiated and refreshes the durable run', async () => {
  let cancelled = false;
  const c = fakeClient((path) => {
    if (path.endsWith('/cancel')) {
      cancelled = true;
      return {};
    }
    return {
      state: cancelled ? 'CANCELLED' : 'WAITING_FOR_APPROVAL',
      mode: 'TUTOR',
      objective: 'Wait',
      steps: [],
      tool_count: 0,
      updated_at: new Date().toISOString(),
    };
  });
  render(<RunView client={c} id="run" />);
  await userEvent.click(await screen.findByRole('button', { name: 'Cancel run' }));
  await screen.findByText('CANCELLED');
  expect(c.request).toHaveBeenCalledWith('/api/runs/run/cancel', {});
});

it('a closed client ignores a late unauthorized response from an old identity', async () => {
  let resolve!: (r: Response) => void;
  const expired = vi.fn();
  vi.spyOn(globalThis, 'fetch').mockImplementation(
    () =>
      new Promise((r) => {
        resolve = r;
      }),
  );
  const c = new Client('old-identity', expired);
  const pending = c.request('/api/settings');
  c.close();
  resolve(new Response('', { status: 401 }));
  await expect(pending).rejects.toThrow('cancelled');
  expect(expired).not.toHaveBeenCalled();
});

it('queries a registered Engineer graph and renders extracted source evidence', async () => {
  const { Engineer } = await import('../src/engineer');
  const c = fakeClient((path) => {
    if (path === '/api/projects') return [{ id: 'fixture', kind: 'REGISTERED_CODE_PROJECT' }];
    if (path === '/api/engineer/status') return { available: false };
    if (path.endsWith('/graph/query')) return { run_id: 'graph-run' };
    if (path === '/api/runs/graph-run')
      return {
        id: 'graph-run',
        mode: 'ENGINEER',
        state: 'COMPLETED',
        objective: 'Query graph',
        result: 'source.py:12 · EXTRACTED · calls helper',
        metadata: { graph_evidence: ['source.py:12'] },
        steps: [],
        tool_count: 1,
        updated_at: new Date().toISOString(),
      };
    return [];
  });
  render(<Engineer client={c} graphOnly />);
  await userEvent.selectOptions(await screen.findByLabelText('Code project'), 'fixture');
  await userEvent.type(screen.getByLabelText('Code question'), 'How is helper called?');
  await userEvent.click(screen.getByRole('button', { name: 'Query graph' }));
  await screen.findByText('source.py:12 · EXTRACTED · calls helper');
  expect(c.request).toHaveBeenCalledWith('/api/code/projects/fixture/graph/query', {
    question: 'How is helper called?',
    budget: 1200,
  });
});
