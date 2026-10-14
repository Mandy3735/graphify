import { useEffect, useState } from 'react';
import type { Run, Approval, ArtifactSummary } from './contracts';
import { Client, type Mode, modeNames, segment, terminal } from './api';
import { Action, Details, Empty, Field, LoadState, Text, field, useLoad } from './ui';
import { VoicePanel } from './VoicePanel';
export function RunView({ client, id }: { client: Client; id: string }) {
  const [run, setRun] = useState<Run>();
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let live = true;
    let timer: ReturnType<typeof setTimeout>;
    setRun(undefined);
    setError('');
    const poll = async () => {
      try {
        const r = await client.request<Run>('/api/runs/' + segment(id));
        if (!live) return;
        setRun(r);
        setError('');
        if (!terminal(r.state))
          timer = setTimeout(poll, r.state === 'WAITING_FOR_APPROVAL' ? 2500 : 700);
      } catch {
        if (live) setError('Run connection interrupted. Reconnect to inspect the durable state.');
      }
    };
    void poll();
    return () => {
      live = false;
      clearTimeout(timer);
    };
  }, [client, id, retry]);
  return (
    <section className="panel" aria-label="Current mission">
      <div className="section-title">
        <h2>Current mission</h2>
        <span role="status" className="badge">
          {run?.state ?? 'Connecting'}
        </span>
      </div>
      {error && (
        <div role="alert">
          {error} <button onClick={() => setRetry((x) => x + 1)}>Reconnect</button>
        </div>
      )}
      {run && (
        <>
          <p>{run.objective}</p>
          <p className="muted">
            {modeNames[run.mode as Mode]} · {run.id}
          </p>
          {!terminal(run.state) && (
            <Action
              label="Cancel run"
              run={() => client.request('/api/runs/' + segment(id) + '/cancel', {})}
              onDone={() => setRetry((x) => x + 1)}
            />
          )}
          {run.state === 'WAITING_FOR_APPROVAL' && (
            <p>Waiting for your decision. Open Approvals to review the exact operation.</p>
          )}
          {run.error && <Text value={run.error} />} {run.result && <Text value={run.result} />}
          <h3>Mission steps</h3>
          <ol>
            {run.steps?.map((s, i) => (
              <li key={i}>
                <strong>{s.state}</strong> — {s.summary}
              </li>
            ))}
          </ol>
          <ModelUsage metadata={run.metadata} />
          <Details label="Model, usage, fallback and source evidence" value={run.metadata} />
          {run.pending_tool && <Details label="Pending tool operation" value={run.pending_tool} />}
          <p className="muted">
            {run.tool_count} tool calls · Updated {new Date(run.updated_at).toLocaleString()}
          </p>
          {run.mode === 'ENGINEER' && <Artifacts client={client} id={id} />}
        </>
      )}
    </section>
  );
}
function Artifacts({ client, id }: { client: Client; id: string }) {
  const q = useLoad<ArtifactSummary[]>(client, '/api/engineer/artifacts?run_id=' + segment(id));
  const [artifact, setArtifact] = useState<string>();
  return (
    <>
      <h3>Engineer artifacts</h3>
      <LoadState {...q} retry={q.refresh} />
      {q.data?.map((a) => (
        <button key={a.artifact_id} onClick={() => setArtifact(a.artifact_id)}>
          Inspect {a.artifact_id}
        </button>
      ))}
      {artifact && <Artifact client={client} id={artifact} />}
    </>
  );
}
function Artifact({ client, id }: { client: Client; id: string }) {
  const q = useLoad(client, '/api/engineer/artifacts/' + segment(id));
  return (
    <>
      <LoadState {...q} retry={q.refresh} />
      {q.data && <Details label="Patch, tests and impact" value={q.data} />}
    </>
  );
}
export function Chat({
  client,
  mode,
  scope = {},
}: {
  client: Client;
  mode: Mode;
  scope?: Record<string, string>;
}) {
  const [id, setId] = useState('');
  return (
    <>
      <section className="panel">
        <h2>Conversation</h2>
        <p className="muted">{modeNames[mode]} · Text is available. Microphone starts off.</p>
        <Action
          label="Send message"
          run={(f) =>
            client.request('/api/chat', {
              message: field(f, 'message'),
              mode,
              ...scope,
              allow_fallback: f.has('fallback'),
            })
          }
          onDone={(r) => setId(r.run_id)}
        >
          <Field name="message" label="Message" type="textarea" max={12000} />
          <label className="check">
            <input type="checkbox" name="fallback" />
            Allow the configured fallback model for this request
          </label>
        </Action>
        <VoicePanel client={client} mode={mode} scope={scope} runId={id} onRun={setId} />
      </section>
      {id && <RunView key={id} client={client} id={id} />}
    </>
  );
}
export function Missions({ client, mode }: { client: Client; mode: Mode }) {
  const q = useLoad<Run[]>(client, '/api/runs');
  const [id, setId] = useState('');
  const rows = q.data?.filter((r) => r.mode === mode);
  return (
    <>
      <div className="section-title">
        <h2>Mission history</h2>
        <button onClick={q.refresh}>Refresh missions</button>
      </div>
      <LoadState {...q} retry={q.refresh} />
      {rows?.length === 0 && (
        <Empty>No missions in this mode yet. Start a conversation to create one.</Empty>
      )}
      <div className="cards">
        {rows?.map((r) => (
          <button className="card" key={r.id} onClick={() => setId(r.id)}>
            <span className="badge">{r.state}</span>
            <strong>{r.objective}</strong>
            <span>{new Date(r.created_at).toLocaleString()}</span>
          </button>
        ))}
      </div>
      {id && <RunView key={id} client={client} id={id} />}
    </>
  );
}
export function Approvals({ client }: { client: Client }) {
  const q = useLoad<Approval[]>(client, '/api/approvals');
  return (
    <>
      <h2>Approvals</h2>
      <p>
        Review the full bound operation before deciding. Approval is exact, expires, and can be used
        once.
      </p>
      <button onClick={q.refresh}>Refresh approvals</button>
      <LoadState {...q} retry={q.refresh} />
      {q.data?.length === 0 && <Empty>No approval requests.</Empty>}
      {q.data?.map((a) => (
        <section className="panel" key={a.id}>
          <h3>{a.status}</h3>
          <p>
            Run {a.run_id} · Expires {new Date(a.expires_at).toLocaleString()}
          </p>
          <Text value={a.operation} />
          <Details label="Operation fingerprint" value={a.operation_hash} />
          {a.status === 'PENDING' && new Date(a.expires_at) > new Date() && (
            <div className="actions">
              <Action
                label="Approve exact operation"
                run={() => client.request('/api/approvals/' + segment(a.id) + '/approve', {})}
                onDone={q.refresh}
              />
              <Action
                label="Reject operation"
                run={() => client.request('/api/approvals/' + segment(a.id) + '/reject', {})}
                onDone={q.refresh}
              />
            </div>
          )}
        </section>
      ))}
    </>
  );
}

function ModelUsage({ metadata = {} }: { metadata: Record<string, unknown> }) {
  const calls = (Array.isArray(metadata.model_calls) ? metadata.model_calls : []) as {
    model: string;
    fallback_from: string | null;
    usage: { input_tokens: number; output_tokens: number };
    estimated_cost: number | null;
  }[];
  return (
    <section aria-label="Model usage">
      <h3>Model and usage</h3>
      <p>Selected model: {String(metadata.selected_model ?? 'No model call')}</p>
      {calls.map((c, i) => (
        <p key={i}>
          {c.model}
          {c.fallback_from ? ` · Fallback from ${c.fallback_from}` : ''} · {c.usage.input_tokens}{' '}
          input / {c.usage.output_tokens} output tokens · Estimated cost:{' '}
          {c.estimated_cost === null
            ? 'unknown (pricing not configured)'
            : c.estimated_cost.toFixed(6)}
        </p>
      ))}
    </section>
  );
}
