import { useState } from 'react';
import { Client, type Mode, segment } from './api';
import { Action, Details, Empty, Field, LoadState, Select, Text, field, useLoad } from './ui';
export function Memory({ client, mode }: { client: Client; mode: Mode }) {
  const [namespace, setNamespace] = useState('personal');
  const [draft, setDraft] = useState('personal');
  return (
    <>
      <h2>Memory inspector</h2>
      <p>
        Personal memory is owner-scoped. Sources are assertions to inspect; they do not grant
        permissions.
      </p>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          setNamespace(draft);
        }}
      >
        <label>
          Namespace
          <input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            pattern="(personal|(?:project|campaign|session):[a-zA-Z0-9_-]{1,80})"
            maxLength={90}
            required
          />
        </label>
        <button>Open namespace</button>
      </form>
      <MemoryScope key={mode + namespace} client={client} mode={mode} namespace={namespace} />
    </>
  );
}
function MemoryScope({
  client,
  mode,
  namespace,
}: {
  client: Client;
  mode: Mode;
  namespace: string;
}) {
  const params = '?mode=' + mode + '&namespace=' + segment(namespace);
  const q = useLoad<any>(client, '/api/memories' + params);
  const proposals = useLoad<any[]>(client, '/api/memory-proposals' + params);
  const [found, setFound] = useState<any[]>();
  const [exported, setExported] = useState<any>();
  const refresh = () => {
    setFound(undefined);
    setExported(undefined);
    q.refresh();
    proposals.refresh();
  };
  return (
    <>
      <section className="panel">
        <h3>Find a memory</h3>
        <Action
          label="Search memory"
          run={(f) =>
            client.request('/api/memories/search', {
              question: field(f, 'question'),
              namespace,
              mode,
            })
          }
          onDone={(r) => setFound(r.items)}
        >
          <Field name="question" label="Search question" max={2000} />
        </Action>
      </section>
      <LoadState {...q} retry={q.refresh} />
      {(found ?? q.data?.items)?.length === 0 && <Empty>No visible memories in this scope.</Empty>}
      {(found ?? q.data?.items)?.map((m: any) => (
        <MemoryItem key={m.id} client={client} m={m} params={params} refresh={refresh} />
      ))}
      {q.data?.next_cursor && (
        <Action
          label="Load next memory page"
          run={() =>
            client.request('/api/memories' + params + '&after=' + segment(q.data.next_cursor))
          }
          onDone={(r) => setFound(r.items)}
        />
      )}
      <section className="panel">
        <h3>Add a sourced note</h3>
        <Action
          label="Save memory"
          run={(f) =>
            client.request('/api/memories?mode=' + mode, {
              content: field(f, 'content'),
              namespace,
              memory_class: field(f, 'class'),
              visibility: 'PRIVATE',
              sources: [{ kind: 'USER_NOTE', locator: field(f, 'source') }],
            })
          }
          onDone={refresh}
        >
          <Field name="content" label="Memory content" type="textarea" max={4000} />
          <Select
            name="class"
            label="Memory class"
            values={['SEMANTIC', 'PREFERENCE', 'EPISODIC']}
          />
          <Field name="source" label="Source locator" max={300} />
        </Action>
      </section>
      <h3>Model proposals</h3>
      <LoadState {...proposals} retry={proposals.refresh} />
      {proposals.data?.length === 0 && <Empty>No pending memory proposals.</Empty>}
      {proposals.data?.map((p) => (
        <section className="panel" key={p.id}>
          <Text value={p} />
          {p.status === 'PENDING' && (
            <div className="actions">
              <Action
                label="Accept memory proposal"
                run={() =>
                  client.request('/api/memory-proposals/' + segment(p.id) + '/accept' + params, {})
                }
                onDone={refresh}
              />
              <Action
                label="Reject memory proposal"
                run={() =>
                  client.request('/api/memory-proposals/' + segment(p.id) + '/reject' + params, {})
                }
                onDone={refresh}
              />
            </div>
          )}
        </section>
      ))}
      <Action
        label="Inspect scoped export"
        run={() => client.request('/api/memories/export' + params)}
        onDone={setExported}
      />
      {exported && <Details label="Export page (not saved to browser storage)" value={exported} />}
    </>
  );
}
function MemoryItem({
  client,
  m,
  params,
  refresh,
}: {
  client: Client;
  m: any;
  params: string;
  refresh: () => void;
}) {
  const [edit, setEdit] = useState(false);
  const [remove, setRemove] = useState(false);
  return (
    <section className="panel">
      <div className="section-title">
        <h3>
          {m.memory_class} · revision {m.revision}
        </h3>
        <span className="badge">{m.visibility}</span>
      </div>
      <Text value={m.content} />
      <Details
        label="Provenance and retrieval reasons"
        value={{
          sources: m.sources,
          retrieval: m.retrieval,
          namespace: m.namespace,
          mode: m.mode,
          expires_at: m.expires_at,
          structured_data: m.structured_data,
        }}
      />
      <div className="actions">
        {m.editable && <button onClick={() => setEdit(!edit)}>Correct memory</button>}
        {m.deletable && <button onClick={() => setRemove(!remove)}>Delete memory…</button>}
      </div>
      {edit && (
        <Action
          label="Save correction"
          run={(f) =>
            client.request(
              '/api/memories/' + segment(m.id) + params,
              {
                expected_revision: m.revision,
                content: field(f, 'content'),
                structured_data: m.structured_data,
                sources: [{ kind: 'USER_NOTE', locator: field(f, 'source') }],
              },
              'PATCH',
            )
          }
          onDone={refresh}
        >
          <Field
            name="content"
            label="Corrected content"
            type="textarea"
            value={m.content}
            max={4000}
          />
          <Field name="source" label="Correction source" max={300} />
        </Action>
      )}
      {remove && (
        <>
          <p>
            Delete this memory and its eligible correction lineage? Conversation retention is
            separate.
          </p>
          <Action
            label="Confirm memory deletion"
            run={() =>
              client.request('/api/memories/' + segment(m.id) + params, undefined, 'DELETE')
            }
            onDone={refresh}
          />
        </>
      )}
    </section>
  );
}
