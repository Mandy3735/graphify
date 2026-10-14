import { useEffect, useRef, useState } from 'react';
import { Client, type Mode } from './api';
import { VoiceController, type VoiceState, type VoiceStatus } from './voice';
import { useLoad } from './ui';

export function VoicePanel({
  client,
  mode,
  scope,
  runId,
  onRun,
}: {
  client: Client;
  mode: Mode;
  scope: Record<string, string>;
  runId: string;
  onRun: (id: string) => void;
}) {
  const status = useLoad<VoiceStatus>(client, '/api/voice/status');
  const [state, setState] = useState<VoiceState>('Microphone off');
  const [text, setText] = useState('');
  const [error, setError] = useState('');
  const [sending, setSending] = useState(false);
  const voice = useRef<VoiceController | undefined>(undefined);
  const generation = useRef(0);
  useEffect(() => {
    const controller = new VoiceController(client, setState, setText, () =>
      setError('Voice unavailable. Check microphone permission and connection, or use text.'),
    );
    voice.current = controller;
    const stop = () => controller.stop();
    const hidden = () => {
      if (document.hidden) stop();
    };
    window.addEventListener('pagehide', stop);
    window.addEventListener('offline', stop);
    document.addEventListener('visibilitychange', hidden);
    return () => {
      ++generation.current;
      controller.dispose();
      window.removeEventListener('pagehide', stop);
      window.removeEventListener('offline', stop);
      document.removeEventListener('visibilitychange', hidden);
    };
  }, [client, mode]);
  const active = ['Microphone active', 'Listening', 'Muted'].includes(state);
  return (
    <section aria-label="Optional voice">
      <h3>Optional voice</h3>
      <p role="status">{state}</p>
      <p className="muted">
        Review captured speech before sending. Voice never approves an operation or changes
        canonical state.
      </p>
      {status.data?.enabled ? (
        <>
          {status.data.provider === 'fake' && (
            <p>
              Fake voice preview: no microphone, network or real speech. Playback is a silent test
              clip.
            </p>
          )}
          <button
            disabled={active || sending || state === 'Processing/delegating'}
            onClick={() => {
              setError('');
              void voice.current?.start(status.data!);
            }}
          >
            {status.data.provider === 'fake' ? 'Start fake voice preview' : 'Enable microphone'}
          </button>
          <button onClick={() => voice.current?.stop()}>Stop / mute voice</button>
          {active && status.data.provider === 'openai' && (
            <button onClick={() => voice.current?.mute(state !== 'Muted')}>
              {state === 'Muted' ? 'Unmute microphone' : 'Mute microphone'}
            </button>
          )}
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              if (sending || !text.trim()) return;
              voice.current?.stop();
              const g = generation.current;
              setSending(true);
              setState('Processing/delegating');
              setError('');
              try {
                const result = await client.request<{ run_id: string }>('/api/voice/submit', {
                  message: text,
                  mode,
                  ...scope,
                });
                if (g === generation.current) {
                  onRun(result.run_id);
                  setText('');
                }
              } catch {
                if (g === generation.current)
                  setError('Voice submission failed. Use text or retry.');
              } finally {
                if (g === generation.current) {
                  setSending(false);
                  setState('Stopped');
                }
              }
            }}
          >
            <label>
              Review voice transcript
              <textarea value={text} maxLength={11000} onChange={(e) => setText(e.target.value)} />
            </label>
            <button disabled={sending || !text.trim()}>Send reviewed transcript</button>
          </form>
          {runId && status.data.speech_enabled && (
            <button
              disabled={sending}
              onClick={() => {
                setError('');
                void voice.current?.speak(runId);
              }}
            >
              Read completed answer aloud
            </button>
          )}
          <p className="muted">
            Read-aloud uses synthetic audio, up to 4,000 characters of the completed answer. To
            interrupt, press Stop.
          </p>
        </>
      ) : (
        <p>Voice is disabled or unavailable. Text remains ready.</p>
      )}
      {error && <p role="alert">{error}</p>}
    </section>
  );
}
