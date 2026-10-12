import { useState } from 'react';
import { Client, segment } from './api';
import { Chat } from './runs';
import { Action, Details, Empty, Field, LoadState, Select, Text, field, useLoad } from './ui';
export function Campaigns({ client, go }: { client: Client; go: (p: string) => void }) {
  const q = useLoad<any[]>(client, '/api/campaigns');
  return (
    <>
      <h2>Campaigns</h2>
      <p>
        Campaign role comes from server membership. Prose and transcripts cannot change canonical
        state.
      </p>
      <LoadState {...q} retry={q.refresh} />
      <div className="cards">
        {q.data?.map((c) => (
          <button className="card" key={c.id} onClick={() => go('/gm/' + c.id)}>
            <span className="badge">{c.membership_role}</span>
            <strong>{c.name}</strong>
            <span>{c.game_system}</span>
          </button>
        ))}
      </div>
      {q.data?.length === 0 && <Empty>No campaigns visible to this identity.</Empty>}
      <section className="panel">
        <h3>New campaign</h3>
        <Action
          label="Create campaign"
          run={(f) => client.request('/api/campaigns', { name: field(f, 'name') })}
          onDone={(r) => go('/gm/' + r.id)}
        >
          <Field name="name" label="Campaign name" />
        </Action>
      </section>
    </>
  );
}
export function Cockpit({
  client,
  id,
  live = false,
  go,
}: {
  client: Client;
  id: string;
  live?: boolean;
  go: (p: string) => void;
}) {
  const [session, setSession] = useState('');
  const sessions = useLoad<any[]>(client, '/api/campaigns/' + segment(id) + '/sessions');
  return (
    <>
      <h2>{live ? 'Live session' : 'Campaign cockpit'}</h2>
      <p>Only authorized scene data is loaded. Microphone off; transcript input is text.</p>
      <div className="actions">
        <button onClick={() => go('/gm')}>All campaigns</button>
        <button onClick={() => go('/gm/' + id + (live ? '' : '/session'))}>
          {live ? 'Campaign cockpit' : 'Live session'}
        </button>
      </div>
      <LoadState {...sessions} retry={sessions.refresh} />
      <label>
        Saved sessions
        <select value={session} onChange={(e) => setSession(e.target.value)}>
          <option value="">Campaign overview</option>
          {sessions.data?.map((s) => (
            <option key={s.id} value={s.id}>
              {s.title}
            </option>
          ))}
        </select>
      </label>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          setSession(field(new FormData(e.currentTarget), 'session'));
        }}
      >
        <Field name="session" label="Session ID (optional)" max={36} required={false} />
        <button>Open session</button>
      </form>
      <Scene
        key={id + session + live}
        client={client}
        id={id}
        session={session}
        setSession={setSession}
        live={live}
      />
    </>
  );
}
function Scene({
  client,
  id,
  session,
  setSession,
  live,
}: {
  client: Client;
  id: string;
  session: string;
  setSession: (s: string) => void;
  live: boolean;
}) {
  const base = '/api/campaigns/' + segment(id);
  const q = useLoad<any>(
    client,
    base + '/scene' + (session ? '?session_id=' + segment(session) : ''),
  );
  const [roll, setRoll] = useState<any>();
  const [proposal, setProposal] = useState<any>();
  const [version, setVersion] = useState(0);
  const refresh = () => {
    setRoll(undefined);
    setProposal(undefined);
    setVersion((v) => v + 1);
    q.refresh();
  };
  const gm = q.data?.campaign.membership_role === 'GM';
  return (
    <>
      <LoadState {...q} retry={refresh} />
      {q.data && (
        <div key={version}>
          <div className="section-title">
            <h3>{q.data.campaign.name}</h3>
            <span className="badge">Server role: {q.data.campaign.membership_role}</span>
            <button onClick={refresh}>Refresh scene</button>
          </div>
          {q.data.session && <p>Session: {q.data.session.title}</p>}
          <div className="cards">
            {q.data.entries.map((entry: any) => (
              <article className="panel" key={entry.id}>
                <span className="badge">{entry.visibility}</span>
                <h3>{entry.name}</h3>
                <Text value={entry.content} />
                <Details label="Canonical entry provenance" value={entry} />
              </article>
            ))}
          </div>
          {q.data.entries.length === 0 && <Empty>No visible entries in this scene.</Empty>}
          <p className="muted">
            {q.data.omitted_for_budget} entries or transcript lines omitted for budget.
          </p>
          <Details label="Rules evidence" value={q.data.rules} />
          {gm && (
            <details>
              <summary>GM campaign controls</summary>
              <Action
                label="Add canonical entry"
                run={(f) =>
                  client.request(base + '/entries', {
                    kind: field(f, 'kind'),
                    name: field(f, 'name'),
                    content: field(f, 'content'),
                    visibility: field(f, 'visibility'),
                    ...(field(f, 'player') ? { player_actor_id: field(f, 'player') } : {}),
                  })
                }
                onDone={refresh}
              >
                <Select
                  name="kind"
                  label="Entry kind"
                  values={['NPC', 'PC', 'LOCATION', 'LORE', 'FACTION', 'ITEM', 'HOOK', 'STATE']}
                />
                <Field name="name" label="Entry name" />
                <Field name="content" label="Entry content" type="textarea" max={8000} />
                <Select
                  name="visibility"
                  label="Entry visibility"
                  values={['PARTY', 'PUBLIC', 'GM_SECRET', 'PLAYER_PRIVATE', 'INFERRED', 'RUMOR']}
                />
                <Field
                  name="player"
                  label="Controlling player actor ID (PC/private)"
                  max={36}
                  required={false}
                />
              </Action>
              <Action
                label="Create session"
                run={(f) => client.request(base + '/sessions', { title: field(f, 'title') })}
                onDone={(r) => setSession(r.id)}
              >
                <Field name="title" label="Session title" />
              </Action>
              <Action
                label="Add campaign member"
                run={(f) =>
                  client.request(base + '/members', {
                    actor_id: field(f, 'actor'),
                    role: field(f, 'role'),
                    display_name: field(f, 'display'),
                  })
                }
                onDone={refresh}
              >
                <Field name="actor" label="Member actor UUID" max={36} />
                <Select name="role" label="Membership role" values={['PLAYER', 'GM']} />
                <Field name="display" label="Member display name" max={120} />
              </Action>
            </details>
          )}
          <section className="panel">
            <h3>Roll authority</h3>
            <p>
              PC rolls default to the human controller. NPC rolls use the auditable dice service.
            </p>
            <Action
              label="Request roll"
              run={(f) =>
                client.request(base + '/dice', {
                  campaign_id: id,
                  ...(session ? { session_id: session } : {}),
                  request_id: crypto.randomUUID(),
                  subject_entry_id: field(f, 'subject'),
                  expression: field(f, 'expression'),
                  purpose: field(f, 'purpose'),
                })
              }
              onDone={setRoll}
            >
              <label>
                Roll subject
                <select name="subject" required>
                  {q.data.entries
                    .filter((e: any) => ['PC', 'NPC'].includes(e.kind))
                    .map((e: any) => (
                      <option key={e.id} value={e.id}>
                        {e.name}
                      </option>
                    ))}
                </select>
              </label>
              <Field name="expression" label="Dice expression" value="1d20" max={32} />
              <Field name="purpose" label="Roll purpose" value="check" />
            </Action>
            {roll && (
              <>
                <Text value={roll} />
                {roll.status === 'AWAITING_HUMAN' && (
                  <Action
                    label="Report human roll"
                    run={(f) =>
                      client.request(base + '/rolls/' + segment(roll.id) + '/report', {
                        total: Number(field(f, 'total')),
                      })
                    }
                    onDone={setRoll}
                  >
                    <Field name="total" label="Your rolled total" type="number" />
                  </Action>
                )}
              </>
            )}
            <details>
              <summary>Delegate one PC roll</summary>
              <p>
                Only the controller can delegate. This authorization expires and is consumed once.
              </p>
              <Action
                label="Delegate one roll"
                run={(f) =>
                  client.request(base + '/delegations', {
                    subject_entry_id: field(f, 'subject'),
                    nonce: crypto.randomUUID(),
                    ttl_seconds: 300,
                  })
                }
                onDone={setRoll}
              >
                <Field name="subject" label="Controlled PC entry ID" max={36} />
              </Action>
            </details>
          </section>
          {gm && (
            <CampaignProposals
              client={client}
              id={id}
              base={base}
              session={session}
              proposal={proposal}
              setProposal={setProposal}
              refresh={refresh}
            />
          )}
          {live && session && (
            <section className="panel">
              <h3>Session transcript · non-canonical</h3>
              {q.data.transcript.map((t: any) => (
                <article key={t.id}>
                  <strong>
                    {t.speaker} · {t.visibility}
                  </strong>
                  <Text value={t.content} />
                </article>
              ))}
              <Action
                label="Add transcript line"
                run={(f) =>
                  client.request(base + '/sessions/' + segment(session) + '/transcript', {
                    speaker: field(f, 'speaker'),
                    content: field(f, 'content'),
                    visibility: field(f, 'visibility'),
                    ...(field(f, 'player') ? { player_actor_id: field(f, 'player') } : {}),
                  })
                }
                onDone={refresh}
              >
                <Field name="speaker" label="Speaker" max={120} />
                <Field name="content" label="Transcript text" type="textarea" max={4000} />
                <Select
                  name="visibility"
                  label="Transcript visibility"
                  values={
                    gm
                      ? ['PARTY', 'PUBLIC', 'GM_SECRET', 'PLAYER_PRIVATE']
                      : ['PARTY', 'PUBLIC', 'PLAYER_PRIVATE']
                  }
                />
                <Field
                  name="player"
                  label="Private transcript owner UUID"
                  required={false}
                  max={36}
                />
              </Action>
            </section>
          )}
          <Chat
            client={client}
            mode="GAME_MASTER"
            scope={{ campaign_id: id, ...(session ? { session_id: session } : {}) }}
          />
        </div>
      )}
    </>
  );
}
function CampaignProposals({
  client,
  id,
  base,
  session,
  proposal,
  setProposal,
  refresh,
}: {
  client: Client;
  id: string;
  base: string;
  session: string;
  proposal: any;
  setProposal: (p: any) => void;
  refresh: () => void;
}) {
  const q = useLoad<any[]>(client, base + '/events');
  return (
    <section className="panel">
      <h3>Canonical event proposals</h3>
      <p>
        Inspect exact changes, then decide as GM. Pending proposals do not alter canonical state.
      </p>
      <LoadState {...q} retry={q.refresh} />
      <Action
        label="Propose campaign event"
        run={(f) =>
          client.request(base + '/events/propose', {
            campaign_id: id,
            ...(session ? { session_id: session } : {}),
            summary: field(f, 'summary'),
            changes: JSON.parse(field(f, 'changes')),
          })
        }
        onDone={(r) => {
          setProposal(r);
          q.refresh();
        }}
      >
        <Field name="summary" label="Event summary" max={500} />
        <Field name="changes" label="Structured changes JSON" type="textarea" max={32000} />
      </Action>
      {(proposal ? [proposal] : (q.data ?? [])).map((p) => (
        <section key={p.id}>
          <Text value={p} />
          {p.status === 'PENDING' && (
            <div className="actions">
              <Action
                label="Approve canonical event"
                run={() =>
                  client.request(base + '/events/' + segment(p.id) + '/decide', { approve: true })
                }
                onDone={refresh}
              />
              <Action
                label="Reject canonical event"
                run={() =>
                  client.request(base + '/events/' + segment(p.id) + '/decide', { approve: false })
                }
                onDone={refresh}
              />
            </div>
          )}
        </section>
      ))}
    </section>
  );
}
