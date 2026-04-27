import type { Track, AuthTokens, User, Playlist, ServerStatus, ScanStatus, PlaylistTrack } from './types';

const BASE_URL = '/api/v1';

class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
    public data?: unknown
  ) {
    super(detail);
    this.name = 'ApiError';
  }
}

export class ApiClient {
  private accessToken: string | null = null;
  private refreshTokenStr: string | null = null;
  private refreshPromise: Promise<AuthTokens> | null = null;

  setToken(access: string, refresh?: string) {
    this.accessToken = access;
    if (refresh) {
      this.refreshTokenStr = refresh;
      localStorage.setItem('refresh_token', refresh);
    }
  }

  clearToken() {
    this.accessToken = null;
    this.refreshTokenStr = null;
    localStorage.removeItem('refresh_token');
  }

  getAccessToken(): string | null {
    return this.accessToken;
  }

  async loadRefreshToken() {
    this.refreshTokenStr = localStorage.getItem('refresh_token');
    return this.refreshTokenStr;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${BASE_URL}${endpoint}`;
    const headers = new Headers(options.headers);
    headers.set('Content-Type', 'application/json');

    if (this.accessToken) {
      headers.set('Authorization', `Bearer ${this.accessToken}`);
    }

    const response = await fetch(url, { ...options, headers });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      
      if (response.status === 401) {
        // Попытка обновить токен
        await this.refreshToken();
        return this.request<T>(endpoint, options);
      }
      
      throw new ApiError(
        response.status,
        errorData.detail || `HTTP ${response.status}`,
        errorData
      );
    }

    return response.json();
  }

  private async refreshToken(): Promise<AuthTokens> {
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    const refreshToken = this.refreshTokenStr || localStorage.getItem('refresh_token');
    if (!refreshToken) {
      this.clearToken();
      throw new ApiError(401, 'No refresh token available');
    }

    this.refreshPromise = (async () => {
      try {
        const response = await fetch(`${BASE_URL}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });

        if (!response.ok) {
          this.clearToken();
          throw new ApiError(response.status, 'Refresh token expired');
        }

        const data: AuthTokens = await response.json();
        this.setToken(data.access_token, data.refresh_token);
        return data;
      } finally {
        this.refreshPromise = null;
      }
    })();

    return this.refreshPromise;
  }

  // Auth endpoints
  async login(username: string, password: string, deviceName?: string) {
    const data = await this.request<AuthTokens>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password, device_name: deviceName }),
    });
    this.setToken(data.access_token, data.refresh_token);
    return data;
  }

  async register(username: string, email: string, password: string) {
    return this.request<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, email, password }),
    });
  }

  async getCurrentUser() {
    return this.request<User>('/auth/me');
  }

  async logout() {
    try {
      await this.request('/auth/logout', { method: 'POST' });
    } finally {
      this.clearToken();
    }
  }

  // Tracks endpoints
  async getTracks(params?: { offset?: number; limit?: number; artist_id?: string; album_id?: string }) {
    const query = new URLSearchParams();
    if (params?.offset !== undefined) query.set('offset', String(params.offset));
    if (params?.limit !== undefined) query.set('limit', String(params.limit));
    if (params?.artist_id) query.set('artist_id', params.artist_id);
    if (params?.album_id) query.set('album_id', params.album_id);
    
    const queryString = query.toString();
    return this.request<{ items: Track[]; total: number }>(`/tracks${queryString ? `?${queryString}` : ''}`);
  }

  async getTrack(id: string) {
    return this.request<Track>(`/tracks/${id}`);
  }

  getStreamUrl(trackId: string, transcoded = false, bitrate: 'low' | 'medium' | 'high' = 'medium'): string {
    const endpoint = transcoded
      ? `/tracks/${trackId}/stream/transcoded?bitrate=${bitrate}`
      : `/tracks/${trackId}/stream`;
    return `${BASE_URL}${endpoint}`;
  }

  async incrementPlayCount(trackId: string) {
    return this.request<{ play_count: number }>(`/tracks/${trackId}/play`, {
      method: 'PUT',
    });
  }

  async getRandomTracks(_limit = 50) {
    return this.request<{ items: Track[] }>('/tracks/random', {
      method: 'GET',
    });
  }

  // Playlists endpoints
  async getPlaylists() {
    return this.request<Playlist[]>('/playlists');
  }

  async createPlaylist(name: string, description?: string, isPublic = false) {
    return this.request<Playlist>('/playlists', {
      method: 'POST',
      body: JSON.stringify({ name, description, is_public: isPublic }),
    });
  }

  async getPlaylist(id: string) {
    return this.request<Playlist>(`/playlists/${id}`);
  }

  async deletePlaylist(id: string) {
    return this.request<void>(`/playlists/${id}`, { method: 'DELETE' });
  }

  async addTrackToPlaylist(playlistId: string, trackId: string) {
    return this.request<PlaylistTrack>(`/playlists/${playlistId}/tracks`, {
      method: 'POST',
      body: JSON.stringify({ track_id: trackId }),
    });
  }

  async removeTrackFromPlaylist(playlistId: string, trackId: string) {
    return this.request<void>(`/playlists/${playlistId}/tracks/${trackId}`, {
      method: 'DELETE',
    });
  }

  // Search endpoint
  async search(query: string, type: 'all' | 'tracks' | 'albums' | 'artists' | 'playlists' = 'all', limit = 20) {
    const params = new URLSearchParams({ q: query, type, limit: String(limit) });
    return this.request<{
      tracks?: Track[];
      albums?: unknown[];
      artists?: unknown[];
      playlists?: Playlist[];
    }>(`/search?${params}`);
  }

  // Admin endpoints
  async startLibraryScan(path = '/data/music', forceRescan = false) {
    return this.request<ScanStatus>('/admin/scan', {
      method: 'POST',
      body: JSON.stringify({ path, force_rescan: forceRescan }),
    });
  }

  async getServerStatus() {
    return this.request<ServerStatus>('/admin/status');
  }

  async getUsers() {
    return this.request<User[]>('/admin/users');
  }

  async createUser(username: string, email: string, password: string, isAdmin = false) {
    return this.request<User>('/admin/users', {
      method: 'POST',
      body: JSON.stringify({ username, email, password, is_admin: isAdmin }),
    });
  }

  async updateUser(id: string, updates: Partial<{ is_admin: boolean; is_active: boolean }>) {
    return this.request<User>(`/admin/users/${id}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteUser(id: string) {
    return this.request<void>(`/admin/users/${id}`, { method: 'DELETE' });
  }
}

export const api = new ApiClient();
