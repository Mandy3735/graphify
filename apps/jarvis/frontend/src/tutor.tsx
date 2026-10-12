import { useState } from 'react';
import { Client, segment } from './api';
import { Chat } from './runs';
import { Action, Details, Empty, Field, LoadState, Select, Text, field, useLoad } from './ui';
export function Tutor({ client }: { client: Client }) {
  const q = useLoad<any[]>(client, '/api/tutor/objectives');
  const [id, setId] = useState('');
  return (
    <>
      <h2>Learning dashboard</h2>
      <p>
        Mastery is backed by your evaluated quiz attempts. Generated lessons alone do not count.
      </p>
      <LoadState {...q} retry={q.refresh} />
      <div className="cards">
        {q.data?.map((o) => (
          <button key={o.id} className="card" onClick={() => setId(o.id)}>
            <span className="badge">{o.status}</span>
            <strong>{o.title}</strong>
          </button>
        ))}
      </div>
      {q.data?.length === 0 && <Empty>Create a learning objective with a source to begin.</Empty>}
      <section className="panel">
        <h3>New objective</h3>
        <Action
          label="Create objective"
          run={(f) =>
            client.request('/api/tutor/objectives', {
              title: field(f, 'title'),
              description: field(f, 'description'),
              sources: [
                { kind: 'USER_NOTE', locator: field(f, 'locator'), quote: field(f, 'quote') },
              ],
            })
          }
          onDone={(r) => {
            q.refresh();
            setId(r.id);
          }}
        >
          <Field name="title" label="Objective title" />
          <Field name="description" label="Learning goal" type="textarea" max={4000} />
          <Field name="locator" label="Learning source locator" max={300} />
          <Field name="quote" label="Source excerpt" type="textarea" max={2000} />
        </Action>
      </section>
      {id && <Objective key={id} client={client} id={id} />}
      <Reviews client={client} />
    </>
  );
}
function Objective({ client, id }: { client: Client; id: string }) {
  const base = '/api/tutor/objectives/' + segment(id);
  const q = useLoad<any>(client, base + '/context');
  const attempts = useLoad<any[]>(client, base + '/attempts');
  const [result, setResult] = useState<any>();
  const [authoring, setAuthoring] = useState(false);
  const refresh = () => {
    q.refresh();
    attempts.refresh();
  };
  const sources = q.data?.objective.sources.map((s: any) => s.id) ?? [];
  return (
    <section className="panel">
      <LoadState {...q} retry={q.refresh} />
      {q.data && (
        <>
          <h2>{q.data.objective.title}</h2>
          <Text value={q.data.objective.description} />
          <span className="badge">{q.data.objective.status}</span>
          <Details label="Sources and mastery evidence" value={q.data.objective} />
          {q.data.lessons.map((l: any) => (
            <article key={l.id}>
              <h3>
                {l.title} · {l.kind}
              </h3>
              <Text value={l.content} />
              <Details label="Lesson source references" value={l.source_ids} />
            </article>
          ))}
          <h3>Practice quizzes</h3>
          {q.data.quizzes.length === 0 && <Empty>No quizzes yet.</Empty>}
          {q.data.quizzes.map((quiz: any) => (
            <section className="panel" key={quiz.id}>
              <Text value={quiz.prompt} />
              <Action
                label="Submit human answer"
                run={(f) =>
                  client.request('/api/tutor/quizzes/' + segment(quiz.id) + '/attempts', {
                    submission_id: crypto.randomUUID(),
                    answer: field(f, 'answer'),
                  })
                }
                onDone={(r) => {
                  setResult(r);
                  refresh();
                }}
              >
                <Field name="answer" label="Your answer" max={4000} />
              </Action>
            </section>
          ))}
          {result && (
            <div role="status">
              <Text value={result} />
            </div>
          )}
          <Details label="Human attempt history" value={attempts.data ?? []} />
          <details open={authoring} onToggle={(e) => setAuthoring(e.currentTarget.open)}>
            <summary>Create a cited lesson or quiz</summary>
            <Action
              label="Create lesson"
              run={(f) =>
                client.request(base + '/lessons', {
                  title: field(f, 'title'),
                  content: field(f, 'content'),
                  kind: field(f, 'kind'),
                  source_ids: sources,
                })
              }
              onDone={q.refresh}
            >
              <Field name="title" label="Lesson title" />
              <Select
                name="kind"
                label="Teaching approach"
                values={['EXPLANATION', 'WORKED_EXAMPLE', 'SOCRATIC']}
              />
              <Field name="content" label="Lesson content" type="textarea" max={8000} />
            </Action>
            <Action
              label="Create quiz"
              run={(f) =>
                client.request(base + '/quizzes', {
                  prompt: field(f, 'prompt'),
                  accepted_answers: [field(f, 'accepted')],
                  source_ids: sources,
                })
              }
              onDone={q.refresh}
            >
              <Field name="prompt" label="Quiz prompt" type="textarea" max={4000} />
              <Field name="accepted" label="Accepted short answer" max={1000} />
            </Action>
          </details>
          <Chat client={client} mode="TUTOR" scope={{ learning_objective_id: id }} />
        </>
      )}
    </section>
  );
}
function Reviews({ client }: { client: Client }) {
  const [now] = useState(() => new Date().toISOString());
  const q = useLoad<any[]>(client, '/api/tutor/reviews?due_before=' + segment(now));
  return (
    <>
      <h3>Due reviews</h3>
      <LoadState {...q} retry={q.refresh} />
      {q.data?.length === 0 && <Empty>No reviews due.</Empty>}
      {q.data?.map((r) => (
        <section className="panel" key={r.id}>
          <Text value={r} />
          <Action
            label="Complete due review"
            run={(f) =>
              client.request('/api/tutor/reviews/' + segment(r.id) + '/complete', {
                attempt_id: field(f, 'attempt'),
              })
            }
            onDone={q.refresh}
          >
            <Field name="attempt" label="Fresh correct human attempt ID" max={36} />
          </Action>
        </section>
      ))}
    </>
  );
}
