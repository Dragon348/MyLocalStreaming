export interface Track {
  id: string;
  title: string;
  artist: string;
  album: string;
  duration_ms: number;
  file_path: string;
  mime_type: string;
  artist_id?: string;
  album_id?: string;
  created_at?: string;
}

export interface User {
  id: string;
  username: string;
  email: string;
  is_admin: boolean;
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

export interface Playlist {
  id: string;
  name: string;
  description?: string;
  owner_id: string;
  is_public: boolean;
  tracks?: PlaylistTrack[];
  created_at: string;
  updated_at: string;
}

export interface PlaylistTrack {
  id: string;
  playlist_id: string;
  track_id: string;
  position: number;
  track?: Track;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface ServerStatus {
  cpu_percent: number;
  memory_used: number;
  memory_total: number;
  disk_free: number;
  disk_total: number;
  active_sessions: number;
  tracks_count: number;
}

export interface ScanStatus {
  task_id: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  progress?: number;
  scanned_count?: number;
  error?: string;
}
