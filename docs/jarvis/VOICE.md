# Optional voice — Phase 10

Voice is an optional transport over the existing text/run engine. It never gains
application tools, approval authority, campaign membership, human quiz evidence
or canonical-state authority. Graphify and schema migrations 0001–0004 are unchanged.

## Offline preview

Follow [LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md), build the frontend and set
`JARVIS_VOICE_PROVIDER=fake` on the backend. Restart, sign in and open Conversation.
Press **Start fake voice preview**, type a sample into **Review voice transcript**,
then press **Send reviewed transcript**. Inspect the durable mission and its
untrusted/noncanonical voice label. **Read completed answer aloud** produces a
short silent fixture, explicitly labeled as fake; it does not synthesize speech.
No device, model key or external service is needed. Text remains available with
`JARVIS_VOICE_PROVIDER=disabled`, the default.

## Live setup

Configure an accessible model for each purpose rather than assuming example IDs
exist. Set `JARVIS_VOICE_PROVIDER=openai`, `JARVIS_VOICE_MODEL`,
`JARVIS_TRANSCRIPTION_MODEL`, and optionally `JARVIS_SPEECH_MODEL` and
`JARVIS_SPEECH_VOICE`. `OPENAI_API_KEY` stays on the server. These operations incur
provider usage when explicitly enabled; no live paid call was made for this checkpoint.
Missing credentials/models fail individual voice requests while text startup
continues. Unknown voice-provider values disable voice; invalid session durations
use 120 seconds. Session duration is operator-bounded to 15–300 seconds.

Microphone use requires HTTPS or loopback secure context, browser permission and
an explicit **Enable microphone** click. FastAPI permits microphone only to its
own origin when live voice is configured. Camera/geolocation remain denied. The
browser offers audio-only WebRTC with no configured third-party ICE server. The
official OpenAI SDK negotiates SDP on the backend and returns only a local
session ID, answer and lifetime. No durable or ephemeral provider key is sent to
the browser; SDP relay replaces browser credential issuance. Provider transport
may require operator network access to OpenAI's WebRTC endpoints. CSP retains
same-origin HTTP connections and enables only blob audio playback.

The realtime session has no application tools, no backend context/history and
automatic responses disabled. The browser consumes only completed input
transcription events, with duplicate, event-count and character bounds. Captured
speech stays in tab memory until the user reviews/edits and explicitly sends it.
That endpoint creates an ordinary scoped AgentRun; policy/approval, memory,
Tutor, Game Master membership/visibility and human PC rolls retain their existing
authority. Speech cannot invoke a human-only decision or evidence endpoint.
Voice transcripts are untrusted input, not voice authentication or canonical state.

Read-aloud is a separate explicit action. The backend loads an owner-scoped
completed run and synthesizes at most its first 4,000 characters; callers cannot
supply an arbitrary result or another owner's run. Historical run access follows
the existing run-retention contract. Audio is synthetic and can include sensitive
content already visible in that result. Playback uses a bounded ephemeral blob
and never enters a service-worker cache. Speech failure leaves results readable.

## Lifecycle and budgets

Indicators cover microphone off/active, listening, speaking, processing/delegating,
muted and stopped. **Stop / mute voice** synchronously stops every track, closes
the data channel/peer, pauses audio and revokes its blob. Starting capture
interrupts playback; starting playback stops capture. Mute disables capture tracks
without closing the peer. Scope changes, sign-out, pagehide, a hidden tab, offline,
provider errors and the local deadline stop capture. A late permission grant or
negotiation response cannot reactivate a stopped controller. Reconnect always
requires another explicit start; no background surveillance or effect queue exists.

An authenticated DELETE also requests SDK hangup. The server expires sessions on
its own deadline and hangs up on shutdown. Provider hangup failures are recorded
as `voice.stop_failed`, not successful stops. Network outages or process crashes
can delay remote cleanup; local devices still stop immediately. Provider calls
have configured timeouts and no automatic retries. In-flight speech/transcription
can finish after local cancellation, within its provider deadline; late results
are discarded. Stop does not cancel a delegated mission; use **Cancel run**.

At most one live session and one serialized provider operation are admitted
at a time per single-user server, with
30 negotiation/transcription/speech admissions per rolling hour. Backend sessions
are ephemeral, not restart-resumable or multi-worker coordinated. This is a local,
single-worker prototype; global cost quotas, production identity/TLS/rate limiting,
server-side realtime usage aggregation and crash-time remote reconciliation remain
Phase 11 work. Realtime data-channel reconfiguration cannot grant backend authority,
but stronger provider-level budget enforcement remains necessary for production.

## API and verification

All endpoints are bearer-authenticated, same-origin and no-store:

| Endpoint | Contract |
|---|---|
| `GET /api/voice/status` | Safe enablement/provider/transport/speech/lifetime metadata |
| `POST /api/voice/sessions` | Strict bounded audio-only SDP; server-controlled SDK session configuration |
| `DELETE /api/voice/sessions/{id}` | Idempotent local stop and best-effort remote hangup |
| `POST /api/voice/transcribe` | Base64 PCM WAV, 2 MB/120 seconds, 16-bit mono/stereo, 8–48 kHz; no audio retention |
| `POST /api/voice/submit` | Reviewed ChatRequest, 11,000-character transcript, untrusted label and ordinary scoped run |
| `POST /api/voice/speech` | Owned completed run UUID only; 4,000 characters/2 MB WAV response |

`VoiceProvider`, `TranscriptionProvider`, `FakeVoiceProvider`,
`FakeTranscriptionProvider`, `OpenAILiveVoiceProvider` and
`OpenAITranscriptionProvider` are replaceable; live clients are lazy official SDK
adapters. No new dependency, migration or model tool is registered. Audit events
retain session/run/provider identifiers without SDP, transcript, audio or secrets.
Tests use real SDK mock transports, fake voice, deterministic lifecycle/device
doubles and a production Chromium fake-provider journey. See the
[Phase 10 report](PHASE10_REPORT.md) for measured results and commands.

## Phase 11 update

The earlier admission/cleanup limits above describe Phase 10. Application 0.8.0 adds
a durable UTC provider estimate ledger and saved remote-session identifiers in
migration 0005. Known sessions are hung up during bounded background recovery;
unknown creation outcomes require explicit operator reconciliation. No audio is
replayed, and saved provider IDs never reach the browser. Live calls now require
configured prices or upper operation estimates. Production keeps live microphone
transport disabled because its data channel cannot enforce a backend generation-cost
ceiling; fake preview, text, reviewed input and bounded configured speech/transcription
remain available. See [HARDENING.md](HARDENING.md) for exact current behavior.

## Phase 12 device lifecycle

Local microphone setup and capture share a 120-second deadline starting before
permission. Stalled offers or permissions cannot keep later capture active; a late
stream is stopped and a late server session is hung up. A server duration can shorten
but cannot extend this local deadline. Sign-out clears credentials and aborts requests
before isolated device cleanup; local tracks/peers stop, while failed authenticated
remote cleanup remains covered by session expiry/journal recovery. Live production
microphone stays disabled. No paid interoperability test is claimed.
