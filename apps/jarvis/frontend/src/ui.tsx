import { useEffect, useRef, useState, type ReactNode } from 'react';
import { ApiError, Client } from './api';
export function Text({ value }: { value: unknown }) {
  const text = typeof value === 'string' ? value : (JSON.stringify(value, null, 2) ?? '');
  return (
    <pre className="untrusted">
      {text.slice(0, 32000)}
      {text.length > 32000 ? '\n[Display truncated]' : ''}
    </pre>
  );
}
export function Details({ label, value }: { label: string; value: unknown }) {
  return (
    <details>
      <summary>{label}</summary>
      <Text value={value} />
    </details>
  );
}
export function Empty({ children }: { children: ReactNode }) {
  return <p className="empty">{children}</p>;
}
export function useLoad<T>(client: Client, path: string) {
  const [data, setData] = useState<T>();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [version, reload] = useState(0);
  useEffect(() => {
    let live = true;
    setData(undefined);
    setError('');
    setLoading(true);
    client
      .request<T>(path)
      .then((x) => {
        if (live) setData(x);
      })
      .catch((e) => {
        if (live)
          setError(
            e instanceof ApiError ? e.message : 'Connection interrupted. Retry to reconnect.',
          );
      })
      .finally(() => {
        if (live) setLoading(false);
      });
    return () => {
      live = false;
    };
  }, [client, path, version]);
  return { data, error, loading, refresh: () => reload((v) => v + 1) };
}
export function LoadState({
  loading,
  error,
  retry,
}: {
  loading: boolean;
  error: string;
  retry: () => void;
}) {
  return (
    <>
      {loading && <p role="status">Loading…</p>}
      {error && (
        <div role="alert">
          <p>{error}</p>
          <button onClick={retry}>Retry connection</button>
        </div>
      )}
    </>
  );
}
export function Action({
  label,
  children,
  run,
  onDone,
}: {
  label: string;
  children?: ReactNode;
  run: (f: FormData) => Promise<unknown>;
  onDone?: (result: any) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [done, setDone] = useState(false);
  const live = useRef(true);
  useEffect(() => {
    live.current = true;
    return () => {
      live.current = false;
    };
  }, []);
  return (
    <form
      aria-label={label}
      onSubmit={async (e) => {
        e.preventDefault();
        if (busy) return;
        const form = e.currentTarget;
        const data = new FormData(form);
        setBusy(true);
        setError('');
        setDone(false);
        try {
          const r = await run(data);
          if (live.current) {
            form.reset();
            setDone(true);
            onDone?.(r);
          }
        } catch (e) {
          if (live.current)
            setError(
              e instanceof ApiError
                ? e.message
                : 'Action interrupted. Refresh to inspect current state before retrying.',
            );
        } finally {
          if (live.current) setBusy(false);
        }
      }}
    >
      <fieldset disabled={busy}>
        {children}
        <button type="submit">{busy ? 'Working…' : label}</button>
      </fieldset>
      {error && <p role="alert">{error}</p>}
      {done && <p role="status">Saved.</p>}
    </form>
  );
}
export function Field({
  name,
  label,
  value = '',
  type = 'text',
  max = 200,
  required = true,
}: {
  name: string;
  label: string;
  value?: string;
  type?: string;
  max?: number;
  required?: boolean;
}) {
  return (
    <label>
      {label}
      {type === 'textarea' ? (
        <textarea name={name} defaultValue={value} maxLength={max} required={required} rows={3} />
      ) : (
        <input name={name} type={type} defaultValue={value} maxLength={max} required={required} />
      )}
    </label>
  );
}
export function Select({ name, label, values }: { name: string; label: string; values: string[] }) {
  return (
    <label>
      {label}
      <select name={name}>
        {values.map((v) => (
          <option key={v}>{v}</option>
        ))}
      </select>
    </label>
  );
}
export const field = (f: FormData, key: string) => String(f.get(key) ?? '').trim();
