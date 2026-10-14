import { Client, segment } from './api';

export type VoiceState =
  | 'Microphone off'
  | 'Microphone active'
  | 'Listening'
  | 'Speaking'
  | 'Processing/delegating'
  | 'Muted'
  | 'Stopped';
export type VoiceStatus = {
  enabled: boolean;
  provider: string;
  speech_enabled: boolean;
  realtime_enabled?: boolean;
  cleanup_pending?: { id: string; state: string }[];
};

/** Device lifetime is independent of React render timing and provider availability. */
export class VoiceController {
  private generation = 0;
  private stream?: MediaStream;
  private peer?: RTCPeerConnection;
  private channel?: RTCDataChannel;
  private session?: string;
  private audio?: HTMLAudioElement;
  private url?: string;
  private timer?: ReturnType<typeof setTimeout>;
  private text = '';
  private seen = new Set<string>();
  private detach: () => void;
  constructor(
    private client: Client,
    private state: (s: VoiceState) => void,
    private transcript: (text: string) => void,
    private error: () => void,
  ) {
    this.detach = client.onClose(() => this.stop());
  }
  private current(g: number) {
    return g === this.generation;
  }
  stop() {
    ++this.generation;
    clearTimeout(this.timer);
    this.stream?.getTracks().forEach((t) => t.stop());
    this.stream = undefined;
    this.channel?.close();
    this.channel = undefined;
    this.peer?.close();
    this.peer = undefined;
    if (this.audio) {
      this.audio.pause();
      this.audio.removeAttribute('src');
      this.audio.load();
      this.audio = undefined;
    }
    if (this.url) URL.revokeObjectURL(this.url);
    this.url = undefined;
    const id = this.session;
    this.session = undefined;
    if (id)
      void this.client
        .request('/api/voice/sessions/' + segment(id), undefined, 'DELETE')
        .catch(() => {});
    this.state('Stopped');
  }
  dispose() {
    this.stop();
    this.detach();
  }
  mute(muted: boolean) {
    this.stream?.getAudioTracks().forEach((t) => {
      t.enabled = !muted;
    });
    this.state(muted ? 'Muted' : 'Listening');
  }
  async start(status: VoiceStatus) {
    this.stop();
    const g = this.generation;
    this.text = '';
    this.seen.clear();
    this.transcript('');
    this.state('Processing/delegating');
    try {
      let offer = '';
      if (status.provider === 'openai') {
        if (
          !window.isSecureContext ||
          !navigator.mediaDevices?.getUserMedia ||
          !window.RTCPeerConnection
        )
          throw new Error('Device unavailable');
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
        if (!this.current(g)) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        this.stream = stream;
        this.state('Microphone active');
        const peer = new RTCPeerConnection({ iceServers: [] });
        this.peer = peer;
        stream.getAudioTracks().forEach((t) => peer.addTrack(t, stream));
        // No audio output or model tool event is used from the realtime connection.
        const channel = peer.createDataChannel('oai-events');
        this.channel = channel;
        channel.onopen = () => {
          if (this.current(g)) this.state('Listening');
        };
        channel.onmessage = (e) => {
          if (this.current(g)) this.event(e.data);
        };
        channel.onerror = () => {
          if (this.current(g)) {
            this.stop();
            this.error();
          }
        };
        peer.onconnectionstatechange = () => {
          if (
            this.current(g) &&
            ['failed', 'disconnected', 'closed'].includes(peer.connectionState)
          ) {
            this.stop();
            this.error();
          }
        };
        const description = await peer.createOffer();
        if (!this.current(g)) return;
        await peer.setLocalDescription(description);
        if (!this.current(g)) return;
        offer = description.sdp ?? '';
      }
      const session = await this.client.request<{ id: string; sdp: string; seconds: number }>(
        '/api/voice/sessions',
        { sdp: offer },
      );
      if (!this.current(g)) {
        void this.client
          .request('/api/voice/sessions/' + segment(session.id), undefined, 'DELETE')
          .catch(() => {});
        return;
      }
      this.session = session.id;
      this.timer = setTimeout(
        () => this.stop(),
        Math.min(300, Math.max(15, session.seconds)) * 1000,
      );
      if (this.peer) await this.peer.setRemoteDescription({ type: 'answer', sdp: session.sdp });
      else this.state('Listening');
    } catch {
      if (this.current(g)) {
        this.stop();
        this.error();
      }
    }
  }
  event(data: unknown) {
    if (typeof data !== 'string' || data.length > 16000) return;
    try {
      const event = JSON.parse(data);
      if (
        event.type === 'error' ||
        event.type === 'conversation.item.input_audio_transcription.failed'
      ) {
        this.stop();
        this.error();
        return;
      }
      if (
        event.type !== 'conversation.item.input_audio_transcription.completed' ||
        typeof event.transcript !== 'string' ||
        typeof event.item_id !== 'string' ||
        event.item_id.length > 128 ||
        this.seen.has(event.item_id)
      )
        return;
      if (
        this.seen.size >= 32 ||
        this.text.length + event.transcript.length + (this.text ? 1 : 0) > 11000
      ) {
        this.stop();
        this.error();
        return;
      }
      this.seen.add(event.item_id);
      this.text = [this.text, event.transcript].filter(Boolean).join('\n');
      this.transcript(this.text);
    } catch {
      /* Unknown provider data has no authority. */
    }
  }
  async speak(runId: string) {
    this.stop(); // Interrupt listening and any previous playback before speaking.
    const g = this.generation;
    this.state('Processing/delegating');
    try {
      const response = await this.client.request<{ audio: string }>('/api/voice/speech', {
        run_id: runId,
      });
      if (!this.current(g)) return;
      if (typeof response.audio !== 'string' || response.audio.length > 2666668)
        throw new Error('Audio too large');
      const bytes = Uint8Array.from(atob(response.audio), (c) => c.charCodeAt(0));
      if (
        String.fromCharCode(...bytes.slice(0, 4)) !== 'RIFF' ||
        String.fromCharCode(...bytes.slice(8, 12)) !== 'WAVE'
      )
        throw new Error('Invalid audio');
      this.url = URL.createObjectURL(new Blob([bytes], { type: 'audio/wav' }));
      const audio = new Audio(this.url);
      this.audio = audio;
      audio.onended = () => {
        if (this.current(g)) this.stop();
      };
      audio.onerror = () => {
        if (this.current(g)) {
          this.stop();
          this.error();
        }
      };
      this.state('Speaking');
      this.timer = setTimeout(() => this.stop(), 120000);
      await audio.play();
    } catch {
      if (this.current(g)) {
        this.stop();
        this.error();
      }
    }
  }
}
