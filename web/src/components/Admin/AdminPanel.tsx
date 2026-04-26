import { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import type { Track, ServerStatus, ScanStatus, User } from '../../lib/types';
import { usePlayerStore } from '../../store/player';
import { useLibraryStore } from '../../store/library';

export function AdminPanel() {
  const [status, setStatus] = useState<ServerStatus | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [scanStatus, setScanStatus] = useState<ScanStatus | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [newUser, setNewUser] = useState({ username: '', email: '', password: '', is_admin: false });

  const { setTracks } = useLibraryStore();
  const { play } = usePlayerStore();

  // Fetch server status periodically
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const data = await api.getServerStatus();
        setStatus(data);
      } catch (error) {
        console.error('Failed to fetch server status:', error);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  // Fetch users
  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const data = await api.getUsers();
        setUsers(data);
      } catch (error) {
        console.error('Failed to fetch users:', error);
      }
    };

    fetchUsers();
  }, []);

  // Fetch tracks for library management
  useEffect(() => {
    const fetchTracks = async () => {
      try {
        const data = await api.getTracks({ limit: 200 });
        setTracks(data.items);
      } catch (error) {
        console.error('Failed to fetch tracks:', error);
      }
    };

    fetchTracks();
  }, [setTracks]);

  const handleScan = async () => {
    setIsScanning(true);
    try {
      const result = await api.startLibraryScan('/data/music', false);
      setScanStatus(result);

      // Poll for scan progress
      const pollInterval = setInterval(async () => {
        try {
          const currentStatus = await api.getServerStatus();
          // In a real implementation, you'd have a dedicated endpoint for scan status
          setScanStatus((prev) => prev ? { ...prev, status: 'running' } : null);
        } catch {
          clearInterval(pollInterval);
          setIsScanning(false);
          setScanStatus(null);
        }
      }, 2000);

      // Stop polling after 30 seconds
      setTimeout(() => {
        clearInterval(pollInterval);
        setIsScanning(false);
        setScanStatus({ task_id: '', status: 'completed' });
      }, 30000);
    } catch (error) {
      console.error('Failed to start scan:', error);
      setIsScanning(false);
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createUser(newUser.username, newUser.email, newUser.password, newUser.is_admin);
      setNewUser({ username: '', email: '', password: '', is_admin: false });
      setShowCreateUser(false);
      const updatedUsers = await api.getUsers();
      setUsers(updatedUsers);
    } catch (error) {
      console.error('Failed to create user:', error);
      alert('Failed to create user');
    }
  };

  const handleDeleteUser = async (userId: string) => {
    if (!confirm('Are you sure you want to delete this user?')) return;
    try {
      await api.deleteUser(userId);
      setUsers(users.filter((u) => u.id !== userId));
    } catch (error) {
      console.error('Failed to delete user:', error);
      alert('Failed to delete user');
    }
  };

  const handlePlayTrack = (track: Track) => {
    play(track, useLibraryStore.getState().tracks);
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  const tracks = useLibraryStore.getState().tracks;

  return (
    <div style={{ padding: '24px', paddingBottom: '120px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 'bold', marginBottom: '24px' }}>Admin Panel</h1>

      {/* Server Status */}
      <section style={{ marginBottom: '32px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '16px' }}>Server Status</h2>
        {status ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
            <div style={{ background: '#1a1a1a', padding: '16px', borderRadius: '8px' }}>
              <div style={{ color: '#b3b3b3', fontSize: '14px', marginBottom: '4px' }}>CPU Usage</div>
              <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{status.cpu_percent.toFixed(1)}%</div>
            </div>
            <div style={{ background: '#1a1a1a', padding: '16px', borderRadius: '8px' }}>
              <div style={{ color: '#b3b3b3', fontSize: '14px', marginBottom: '4px' }}>Memory Used</div>
              <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{formatBytes(status.memory_used)}</div>
            </div>
            <div style={{ background: '#1a1a1a', padding: '16px', borderRadius: '8px' }}>
              <div style={{ color: '#b3b3b3', fontSize: '14px', marginBottom: '4px' }}>Disk Free</div>
              <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{formatBytes(status.disk_free)}</div>
            </div>
            <div style={{ background: '#1a1a1a', padding: '16px', borderRadius: '8px' }}>
              <div style={{ color: '#b3b3b3', fontSize: '14px', marginBottom: '4px' }}>Active Sessions</div>
              <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{status.active_sessions}</div>
            </div>
            <div style={{ background: '#1a1a1a', padding: '16px', borderRadius: '8px' }}>
              <div style={{ color: '#b3b3b3', fontSize: '14px', marginBottom: '4px' }}>Total Tracks</div>
              <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{status.tracks_count}</div>
            </div>
          </div>
        ) : (
          <div style={{ color: '#b3b3b3' }}>Loading...</div>
        )}
      </section>

      {/* Library Management */}
      <section style={{ marginBottom: '32px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '16px' }}>Library Management</h2>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '16px' }}>
          <button onClick={handleScan} disabled={isScanning}>
            {isScanning ? 'Scanning...' : 'Scan Library'}
          </button>
          {scanStatus && (
            <span style={{ color: scanStatus.status === 'completed' ? '#1db954' : '#b3b3b3' }}>
              Status: {scanStatus.status}
            </span>
          )}
        </div>
      </section>

      {/* Tracks Table */}
      <section style={{ marginBottom: '32px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '16px' }}>Tracks ({tracks.length})</h2>
        <div style={{ overflowX: 'auto' }}>
          <table>
            <thead>
              <tr>
                <th>Title</th>
                <th>Artist</th>
                <th>Album</th>
                <th>Duration</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {tracks.map((track) => (
                <tr key={track.id}>
                  <td>{track.title}</td>
                  <td>{track.artist}</td>
                  <td>{track.album}</td>
                  <td>{Math.floor(track.duration_ms / 1000 / 60)}:{Math.floor((track.duration_ms / 1000) % 60).toString().padStart(2, '0')}</td>
                  <td>
                    <button onClick={() => handlePlayTrack(track)} style={{ padding: '4px 8px', fontSize: '12px' }}>
                      Play
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* User Management */}
      <section>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h2 style={{ fontSize: '20px', fontWeight: '600' }}>Users</h2>
          <button onClick={() => setShowCreateUser(!showCreateUser)}>
            {showCreateUser ? 'Cancel' : 'Create User'}
          </button>
        </div>

        {showCreateUser && (
          <form onSubmit={handleCreateUser} style={{ background: '#1a1a1a', padding: '16px', borderRadius: '8px', marginBottom: '16px' }}>
            <div style={{ display: 'grid', gap: '12px', marginBottom: '16px' }}>
              <input
                type="text"
                placeholder="Username"
                value={newUser.username}
                onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                required
                style={{ padding: '8px 12px' }}
              />
              <input
                type="email"
                placeholder="Email"
                value={newUser.email}
                onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                required
                style={{ padding: '8px 12px' }}
              />
              <input
                type="password"
                placeholder="Password"
                value={newUser.password}
                onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                required
                style={{ padding: '8px 12px' }}
              />
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <input
                  type="checkbox"
                  checked={newUser.is_admin}
                  onChange={(e) => setNewUser({ ...newUser, is_admin: e.target.checked })}
                />
                Administrator
              </label>
            </div>
            <button type="submit">Create User</button>
          </form>
        )}

        <div style={{ overflowX: 'auto' }}>
          <table>
            <thead>
              <tr>
                <th>Username</th>
                <th>Email</th>
                <th>Admin</th>
                <th>Active</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td>{user.username}</td>
                  <td>{user.email}</td>
                  <td>{user.is_admin ? 'Yes' : 'No'}</td>
                  <td>{user.is_active ? 'Yes' : 'No'}</td>
                  <td>
                    <button
                      onClick={() => handleDeleteUser(user.id)}
                      style={{ padding: '4px 8px', fontSize: '12px', background: '#e74c3c' }}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
