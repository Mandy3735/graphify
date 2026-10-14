export class ApiError extends Error {
  constructor(public status: number) {
    super(
      (
        {
          401: 'Authentication expired. Sign in again.',
          403: 'Access denied. Your current identity cannot perform this action.',
          404: 'Resource unavailable.',
          409: 'State changed. Refresh before trying again.',
          422: 'Check the form values and try again.',
          429: 'Request budget reached. Wait before retrying.',
          503: 'Service unavailable. Retry when the backend is ready.',
        } as Record<number, string>
      )[status] || 'Request failed. Please retry.',
    );
  }
}
export class Client {
  private token: string;
  private controllers = new Set<AbortController>();
  private closers = new Set<() => void>();
  constructor(
    token: string,
    private unauthorized: () => void = () => {},
  ) {
    this.token = token;
  }
  close() {
    this.token = '';
    for (const c of this.controllers) c.abort();
    this.controllers.clear();
    for (const close of this.closers) {
      try {
        close();
      } catch {
        // One device cleanup failure must not retain credentials or other devices.
      }
    }
    this.closers.clear();
  }
  onClose(close: () => void) {
    this.closers.add(close);
    return () => {
      this.closers.delete(close);
    };
  }
  async request<T = any>(
    path: string,
    body?: unknown,
    method = body === undefined ? 'GET' : 'POST',
  ): Promise<T> {
    if (!path.startsWith('/api/') || path.includes('://') || path.includes('#') || !this.token)
      throw new Error('Invalid API request');
    const c = new AbortController();
    this.controllers.add(c);
    const timer = setTimeout(() => c.abort(), 20000);
    try {
      const r = await fetch(path, {
        method,
        credentials: 'omit',
        cache: 'no-store',
        redirect: 'error',
        signal: c.signal,
        headers: {
          Authorization: `Bearer ${this.token}`,
          ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
        },
        body: body === undefined ? undefined : JSON.stringify(body),
      });
      if (!this.token || c.signal.aborted) throw new Error('Request cancelled');
      if (r.status === 401) {
        this.close();
        this.unauthorized();
      }
      if (!r.ok) throw new ApiError(r.status);
      if (r.status === 204) return undefined as T;
      // Bound bytes before parsing or rendering an untrusted response.
      if (Number(r.headers.get('Content-Length')) > 2_000_000)
        throw new Error('Response exceeds display budget.');
      const reader = r.body?.getReader();
      if (!reader) throw new Error('Empty response');
      const parts: Uint8Array[] = [];
      let size = 0;
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        size += value.byteLength;
        if (size > 2_000_000) {
          await reader.cancel();
          throw new Error('Response exceeds display budget.');
        }
        parts.push(value);
      }
      const bytes = new Uint8Array(size);
      let offset = 0;
      for (const p of parts) {
        bytes.set(p, offset);
        offset += p.length;
      }
      if (!this.token || c.signal.aborted) throw new Error('Request cancelled');
      return JSON.parse(new TextDecoder().decode(bytes)) as T;
    } finally {
      clearTimeout(timer);
      this.controllers.delete(c);
    }
  }
}
export const segment = (value: string) => encodeURIComponent(value);
export const modes = ['CHIEF_OF_STAFF', 'ENGINEER', 'TUTOR', 'GAME_MASTER'] as const;
export type Mode = (typeof modes)[number];
export const modeNames: Record<Mode, string> = {
  CHIEF_OF_STAFF: 'Chief of Staff',
  ENGINEER: 'Engineer',
  TUTOR: 'Tutor',
  GAME_MASTER: 'Game Master',
};
export const terminal = (state: string) => ['COMPLETED', 'FAILED', 'CANCELLED'].includes(state);
