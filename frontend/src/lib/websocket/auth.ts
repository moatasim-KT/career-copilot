
import { jwtDecode } from 'jwt-decode';

// Simple token management (would typically come from auth/cookies)
const getToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('auth_token');
};

const setToken = (token: string): void => {
  if (typeof window === 'undefined') return;
  localStorage.setItem('auth_token', token);
};

const REFRESH_THRESHOLD = 30 * 1000; // 30 seconds

export class WebSocketAuth {
  private timeoutId: NodeJS.Timeout | null = null;

  constructor(private ws: WebSocket) { }

  start() {
    this.scheduleTokenRefresh();
  }

  stop() {
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
    }
  }

  private scheduleTokenRefresh() {
    const token = getToken();
    if (!token) return;

    const decoded = jwtDecode<{ exp: number }>(token);
    const expiresIn = decoded.exp * 1000 - Date.now();

    if (expiresIn < REFRESH_THRESHOLD) {
      this.refreshToken();
    }

    this.timeoutId = setTimeout(() => {
      this.refreshToken();
      this.scheduleTokenRefresh();
    }, expiresIn - REFRESH_THRESHOLD);
  }

  private refreshToken() {
    const token = getToken();
    if (!token) return;

    this.ws.send(JSON.stringify({ type: 'refreshToken', payload: { token } }));

    this.ws.addEventListener('message', event => {
      const message = JSON.parse(event.data);
      if (message.type === 'refreshedToken') {
        setToken(message.payload.token);
      }
    });
  }
}
