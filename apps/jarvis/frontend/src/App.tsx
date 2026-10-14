import { useEffect, useRef, useState } from 'react';
import type { Run, Approval, Project } from './contracts';
import { Client, type Mode, modes, modeNames } from './api';
import { Action, Details, Empty, LoadState, useLoad } from './ui';
import { Approvals, Chat, Missions } from './runs';
import { Memory } from './memory';
import { Tutor } from './tutor';
import { Engineer } from './engineer';
import { Campaigns, Cockpit } from './gm';
const pathMode = (p: string): Mode | undefined =>
  p.startsWith('/engineer')
    ? 'ENGINEER'
    : p === '/tutor'
      ? 'TUTOR'
      : p.startsWith('/gm')
        ? 'GAME_MASTER'
        : undefined;
const links = [
  ['/', 'Command Center'],
  ['/chat', 'Conversation'],
  ['/missions', 'Missions'],
  ['/projects', 'Projects'],
  ['/memory', 'Memory'],
  ['/approvals', 'Approvals'],
  ['/engineer', 'Engineer'],
  ['/engineer/graph', 'Code intelligence'],
  ['/tutor', 'Tutor'],
  ['/gm', 'Campaigns'],
  ['/settings', 'Settings'],
];
export function App() {
  const [client, setClient] = useState<Client>();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const activeClient = useRef<Client | undefined>(undefined);
  const logout = () => {
    activeClient.current?.close();
    activeClient.current = undefined;
    setClient(undefined);
  };
  useEffect(() => {
    const hide = () => logout();
    window.addEventListener('pagehide', hide);
    return () => window.removeEventListener('pagehide', hide);
  }, []);
  return client ? (
    <Workspace client={client} logout={logout} />
  ) : (
    <main className="login">
      <div className="brand">J / JARVIS</div>
      <p className="eyebrow">YOUR PERSONAL OPERATING LAYER</p>
      <h1>
        Make room for
        <br />
        focused work.
      </h1>
      <p>
        Connect to your Command Center. Your token stays in memory for this tab and is cleared when
        you leave or sign out.
      </p>
      <form
        aria-label="Sign in"
        onSubmit={async (e) => {
          e.preventDefault();
          if (busy) return;
          const f = e.currentTarget;
          const input = f.elements.namedItem('token') as HTMLInputElement;
          const candidate = new Client(input.value, () => {
            logout();
            setError('Authentication expired. Sign in again.');
          });
          activeClient.current = candidate;
          input.value = '';
          setBusy(true);
          setError('');
          try {
            await candidate.request('/api/settings');
            setClient(candidate);
          } catch {
            candidate.close();
            setError('Unable to sign in. Check your token and backend connection.');
          } finally {
            setBusy(false);
          }
        }}
      >
        <label>
          API token
          <input
            name="token"
            type="password"
            required
            minLength={32}
            maxLength={512}
            autoComplete="off"
            spellCheck={false}
          />
        </label>
        <button disabled={busy}>{busy ? 'Connecting…' : 'Connect to JARVIS'}</button>
        {error && <p role="alert">{error}</p>}
      </form>
      <p className="muted">
        Offline? The shell is available, but authentication and private data require the backend.
      </p>
    </main>
  );
}
function Workspace({ client, logout }: { client: Client; logout: () => void }) {
  const [path, setPath] = useState(window.location.pathname);
  const [mode, setMode] = useState<Mode>(pathMode(window.location.pathname) ?? 'CHIEF_OF_STAFF');
  const [online, setOnline] = useState(navigator.onLine);
  const go = (p: string) => {
    window.history.pushState(null, '', p);
    setPath(p);
    if (p.startsWith('/engineer')) setMode('ENGINEER');
    if (p === '/tutor') setMode('TUTOR');
    if (p.startsWith('/gm')) setMode('GAME_MASTER');
  };
  useEffect(() => {
    const pop = () => {
      const p = window.location.pathname;
      setPath(p);
      const m = pathMode(p);
      if (m) setMode(m);
    };
    const connected = () => setOnline(navigator.onLine);
    window.addEventListener('popstate', pop);
    window.addEventListener('online', connected);
    window.addEventListener('offline', connected);
    return () => {
      window.removeEventListener('popstate', pop);
      window.removeEventListener('online', connected);
      window.removeEventListener('offline', connected);
    };
  }, []);
  useEffect(() => {
    document.getElementById('page-title')?.focus();
  }, [path]);
  const title =
    links.find(([p]) => p === path)?.[1] ??
    (path.startsWith('/gm/') ? 'Campaign cockpit' : 'Page unavailable');
  const gm = /^\/gm\/([a-fA-F0-9-]{36})(\/session)?$/.exec(path);
  return (
    <>
      <a className="skip" href="#main">
        Skip to content
      </a>
      <aside>
        <div className="brand">J / JARVIS</div>
        <p className="muted">COMMAND CENTER</p>
        <nav aria-label="Primary navigation">
          {links.map(([p, label]) => (
            <a
              key={p}
              href={p}
              aria-current={path === p ? 'page' : undefined}
              onClick={(e) => {
                if (!e.ctrlKey && !e.metaKey && !e.shiftKey) {
                  e.preventDefault();
                  go(p);
                }
              }}
            >
              {label}
            </a>
          ))}
        </nav>
        <button onClick={logout}>Sign out</button>
        <p className="muted">
          Private by design.
          <br />
          Authority stays on the server.
        </p>
      </aside>
      <main id="main" className="workspace">
        <header>
          <div>
            <p className="eyebrow">FOCUS / BUILD / LEARN / PLAY</p>
            <h1 id="page-title" tabIndex={-1}>
              {title}
            </h1>
          </div>
          <label>
            Active mode
            <select
              value={mode}
              onChange={(e) => {
                setMode(e.target.value as Mode);
                const p = {
                  CHIEF_OF_STAFF: '/',
                  ENGINEER: '/engineer',
                  TUTOR: '/tutor',
                  GAME_MASTER: '/gm',
                }[e.target.value as Mode];
                go(p);
              }}
            >
              {modes.map((m) => (
                <option key={m} value={m}>
                  {modeNames[m]}
                </option>
              ))}
            </select>
          </label>
        </header>
        {!online && (
          <div role="status" className="notice">
            Offline · private data and actions need a connection. Reconnect, then refresh the
            current surface.
          </div>
        )}
        <div key={path + mode} className="surface">
          {path === '/' && <Center client={client} mode={mode} go={go} />}
          {path === '/chat' && <Chat client={client} mode={mode} />}
          {path === '/missions' && <Missions client={client} mode={mode} />}
          {path === '/approvals' && <Approvals client={client} />}
          {path === '/memory' && <Memory client={client} mode={mode} />}
          {path === '/tutor' && <Tutor client={client} />}
          {path === '/projects' && <Projects client={client} go={go} />}
          {path === '/engineer' && <Engineer client={client} />}
          {path === '/engineer/graph' && <Engineer client={client} graphOnly />}
          {path === '/gm' && <Campaigns client={client} go={go} />}
          {gm && <Cockpit client={client} id={gm[1]} live={!!gm[2]} go={go} />}
          {path === '/settings' && <Settings client={client} />}
          {!links.some(([p]) => p === path) && !gm && (
            <Empty>Page unavailable. Use the navigation to return to your workspace.</Empty>
          )}
        </div>
      </main>
    </>
  );
}
function Center({ client, mode, go }: { client: Client; mode: Mode; go: (p: string) => void }) {
  const q = useLoad<Run[]>(client, '/api/runs');
  const approvals = useLoad<Approval[]>(client, '/api/approvals');
  const active =
    q.data?.filter(
      (r) => r.mode === mode && !['COMPLETED', 'FAILED', 'CANCELLED'].includes(r.state),
    ) ?? [];
  return (
    <>
      <section className="hero">
        <p className="eyebrow">A CLEAR VIEW OF WHAT COMES NEXT</p>
        <h2>Your work, in focus.</h2>
        <p>
          Ask a question, inspect a source, or pick up a mission. You decide when a protected action
          proceeds.
        </p>
        <button onClick={() => go('/chat')}>Start a conversation →</button>
      </section>
      <div className="cards">
        <section className="panel">
          <h3>Active missions</h3>
          <strong className="metric">{q.loading ? '…' : active.length}</strong>
          <p>{modeNames[mode]}</p>
          <button onClick={() => go('/missions')}>Review missions</button>
        </section>
        <section className="panel">
          <h3>Needs your decision</h3>
          <strong className="metric">
            {approvals.loading
              ? '…'
              : (approvals.data?.filter((a) => a.status === 'PENDING').length ?? 0)}
          </strong>
          <p>Exact, one-use approvals</p>
          <button onClick={() => go('/approvals')}>Review approvals</button>
        </section>
        <section className="panel">
          <h3>Grounded in sources</h3>
          <p>Inspect memory provenance and Graphify evidence before you act.</p>
          <button onClick={() => go('/memory')}>Open memory</button>
        </section>
      </div>
      <LoadState {...q} retry={q.refresh} />
      <LoadState {...approvals} retry={approvals.refresh} />
      <Chat client={client} mode={mode} />
    </>
  );
}
function Projects({ client, go }: { client: Client; go: (p: string) => void }) {
  const q = useLoad<Project[]>(client, '/api/projects');
  return (
    <>
      <h2>Registered code projects</h2>
      <LoadState {...q} retry={q.refresh} />
      {q.data?.map((p) => (
        <section className="panel" key={p.id}>
          <h3>{p.id}</h3>
          <p>{p.kind}</p>
          <button onClick={() => go('/engineer')}>Open Engineer</button>
        </section>
      ))}
      <Empty>
        Chief of Staff goals, checkpoints and watchers are planned. Current project registrations
        are managed on the server.
      </Empty>
    </>
  );
}
function Settings({ client }: { client: Client }) {
  const q = useLoad(client, '/api/settings');
  const tools = useLoad(client, '/api/tools');
  const usage = useLoad(client, '/api/usage');
  return (
    <>
      <h2>Models and privacy</h2>
      <LoadState {...q} retry={q.refresh} />
      {q.data && <Details label="Server model and memory configuration" value={q.data} />}
      <LoadState {...tools} retry={tools.refresh} />
      {tools.data && <Details label="Available tool contracts" value={tools.data} />}
      <LoadState {...usage} retry={usage.refresh} />
      {usage.data && <Details label="Provider admission estimates and usage" value={usage.data} />}
      <p>
        Settings are controlled by the operator. Tokens and private API responses are not saved to
        persistent browser storage. Only public static application assets are cached.
      </p>
      <p>
        Microphone starts off. Optional voice is configured by the operator; integrations remain
        pending.
      </p>
      <Action
        label="Refresh server settings"
        run={() => client.request('/api/settings')}
        onDone={q.refresh}
      />
    </>
  );
}
