import { useState } from 'react';
import type { Project } from './contracts';
import { Client, segment } from './api';
import { Chat, RunView } from './runs';
import { Action, Details, Empty, Field, LoadState, Select, field, useLoad } from './ui';
export function Engineer({ client, graphOnly = false }: { client: Client; graphOnly?: boolean }) {
  const projects = useLoad<Project[]>(client, '/api/projects');
  const status = useLoad<any>(client, '/api/engineer/status');
  const [project, setProject] = useState('');
  const [run, setRun] = useState('');
  const start = (r: any) => setRun(r.run_id);
  return (
    <>
      <h2>{graphOnly ? 'Code intelligence' : 'Engineer workspace'}</h2>
      <p>
        Registered roots are operator-controlled. Graph evidence retains source locations and
        confidence; inferred relationships remain labeled.
      </p>
      <LoadState {...projects} retry={projects.refresh} />
      <LoadState {...status} retry={status.refresh} />
      {status.data && (
        <p className="badge">
          Sandbox{' '}
          {status.data.available
            ? 'verified and available'
            : 'unavailable — text and graph remain available'}
        </p>
      )}
      {projects.data?.length === 0 && (
        <Empty>No code projects registered. Configure project roots on the server.</Empty>
      )}
      <label>
        Code project
        <select
          value={project}
          onChange={(e) => {
            setProject(e.target.value);
            setRun('');
          }}
        >
          <option value="">Select a registered project</option>
          {projects.data?.map((p) => (
            <option key={p.id} value={p.id}>
              {p.id}
            </option>
          ))}
        </select>
      </label>
      {project && (
        <section className="panel" key={project}>
          <h3>Graphify evidence</h3>
          <Action
            label="Query graph"
            run={(f) =>
              client.request('/api/code/projects/' + segment(project) + '/graph/query', {
                question: field(f, 'question'),
                budget: 1200,
              })
            }
            onDone={start}
          >
            <Field name="question" label="Code question" max={2000} />
          </Action>
          <div className="actions">
            <Action
              label="Check graph health"
              run={() => client.request('/api/code/projects/' + segment(project) + '/graph')}
              onDone={start}
            />
            <Action
              label="Update graph"
              run={() =>
                client.request('/api/code/projects/' + segment(project) + '/graph/update', {})
              }
              onDone={start}
            />
          </div>
          <Action
            label="Find graph path"
            run={(f) =>
              client.request('/api/code/projects/' + segment(project) + '/graph/path', {
                source: field(f, 'source'),
                target: field(f, 'target'),
              })
            }
            onDone={start}
          >
            <Field name="source" label="Source symbol" />
            <Field name="target" label="Target symbol" />
          </Action>
          <Action
            label="Inspect graph symbol"
            run={(f) =>
              client.request('/api/tools/execute?mode=ENGINEER', {
                name: field(f, 'operation'),
                arguments: { project_id: project, node: field(f, 'node') },
              })
            }
            onDone={start}
          >
            <Select
              name="operation"
              label="Symbol operation"
              values={['graph.explain', 'graph.impact']}
            />
            <Field name="node" label="File-qualified symbol" />
          </Action>
          {!graphOnly && (
            <>
              <Chat client={client} mode="ENGINEER" scope={{ project_id: project }} />
              <details>
                <summary>Prepare an isolated change</summary>
                <p>
                  Uses the existing bounded ChangeRequest contract. Original sources stay unchanged.
                  Supply exact hashes, acceptance criteria, edits and declared python3 tests.
                </p>
                <Action
                  label="Submit isolated change"
                  run={(f) => {
                    const body = JSON.parse(field(f, 'change'));
                    if (body.project_id !== project) throw new Error('Project mismatch');
                    return client.request('/api/engineer/changes', body);
                  }}
                  onDone={start}
                >
                  <Field name="change" label="Change request JSON" type="textarea" max={24000} />
                </Action>
                <Details
                  label="Change request example"
                  value={{
                    project_id: project,
                    objective: 'Describe a small change',
                    acceptance_criteria: ['Declared test passes'],
                    edits: [
                      {
                        path: 'example.py',
                        content: '',
                        reason: 'Requested change',
                        expected_sha256: 'EXACT_SOURCE_SHA256',
                      },
                    ],
                    commands: [
                      { argv: ['python3', '-m', 'unittest'], purpose: 'Regression tests' },
                    ],
                    dry_run: true,
                  }}
                />
              </details>
            </>
          )}
        </section>
      )}
      {run && <RunView key={run} client={client} id={run} />}
    </>
  );
}
