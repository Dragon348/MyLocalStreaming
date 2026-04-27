import { useState, useEffect } from 'react';
import { useAuthStore } from './store/auth';
import { api } from './lib/api';
import type { Track } from './lib/types';
import { usePlayerStore } from './store/player';
import { useLibraryStore } from './store/library';
import { useAudio } from './hooks/useAudio';
import { PlayerBar } from './components/Player/PlayerBar';
import { AdminPanel } from './components/Admin/AdminPanel';

function LoginPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login, register, error, clearError, isLoading } = useAuthStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (isLogin) {
        await login(username, password);
      } else {
        await register(username, email, password);
      }
    } catch {
      // Error is handled by store
    }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
      <form
        onSubmit={handleSubmit}
        style={{
          background: '#1a1a1a',
          padding: '32px',
          borderRadius: '8px',
          width: '100%',
          maxWidth: '400px',
        }}
      >
        <h1 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '24px', textAlign: 'center' }}>
          {isLogin ? 'Sign In' : 'Sign Up'}
        </h1>

        {error && (
          <div style={{ color: '#e74c3c', marginBottom: '16px', textAlign: 'center' }}>{error}</div>
        )}

        <div style={{ marginBottom: '16px' }}>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => {
              setUsername(e.target.value);
              clearError();
            }}
            required
            style={{ width: '100%', padding: '12px', background: '#2a2a2a', border: '1px solid #404040', borderRadius: '4px', color: '#fff' }}
          />
        </div>

        {!isLogin && (
          <div style={{ marginBottom: '16px' }}>
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                clearError();
              }}
              required
              style={{ width: '100%', padding: '12px', background: '#2a2a2a', border: '1px solid #404040', borderRadius: '4px', color: '#fff' }}
            />
          </div>
        )}

        <div style={{ marginBottom: '16px' }}>
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              clearError();
            }}
            required
            style={{ width: '100%', padding: '12px', background: '#2a2a2a', border: '1px solid #404040', borderRadius: '4px', color: '#fff' }}
          />
        </div>

        <button
          type="submit"
          disabled={isLoading}
          style={{ width: '100%', padding: '12px', marginBottom: '16px' }}
        >
          {isLoading ? 'Loading...' : isLogin ? 'Sign In' : 'Sign Up'}
        </button>

        <button
          type="button"
          onClick={() => {
            setIsLogin(!isLogin);
            clearError();
          }}
          style={{ width: '100%', padding: '12px', background: 'transparent', border: '1px solid #404040' }}
        >
          {isLogin ? 'Create Account' : 'Have an account?'}
        </button>
      </form>
    </div>
  );
}

function LibraryPage() {
  const { tracks, searchQuery, setSearchQuery, sortBy, setSortBy, sortOrder, toggleSortOrder, getFilteredAndSortedTracks } = useLibraryStore();
  const { play } = usePlayerStore();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTracks = async () => {
      try {
        const data = await api.getTracks({ limit: 200 });
        useLibraryStore.getState().setTracks(data.items);
      } catch (error) {
        console.error('Failed to fetch tracks:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTracks();
  }, []);

  const handlePlayTrack = (track: Track) => {
    play(track, getFilteredAndSortedTracks());
  };

  const filteredTracks = getFilteredAndSortedTracks();

  return (
    <div style={{ padding: '24px', paddingBottom: '120px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 'bold', marginBottom: '24px' }}>Library</h1>

      {/* Search and Sort */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '24px', flexWrap: 'wrap' }}>
        <input
          type="text"
          placeholder="Search tracks..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{ padding: '10px 16px', minWidth: '250px' }}
        />
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
          style={{ padding: '10px 16px', background: '#2a2a2a', border: '1px solid #404040', color: '#fff', borderRadius: '4px' }}
        >
          <option value="title">Title</option>
          <option value="artist">Artist</option>
          <option value="album">Album</option>
        </select>
        <button onClick={toggleSortOrder} style={{ padding: '10px 16px' }}>
          {sortOrder === 'asc' ? '↑ Ascending' : '↓ Descending'}
        </button>
      </div>

      {/* Tracks List */}
      {loading ? (
        <div style={{ color: '#b3b3b3' }}>Loading...</div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Title</th>
                <th>Artist</th>
                <th>Album</th>
                <th>Duration</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredTracks.map((track, index) => (
                <tr key={track.id}>
                  <td style={{ width: '40px' }}>{index + 1}</td>
                  <td style={{ fontWeight: 500 }}>{track.title}</td>
                  <td>{track.artist}</td>
                  <td>{track.album}</td>
                  <td>{Math.floor(track.duration_ms / 60000)}:{Math.floor((track.duration_ms % 60000) / 1000).toString().padStart(2, '0')}</td>
                  <td>
                    <button onClick={() => handlePlayTrack(track)} style={{ padding: '6px 12px', fontSize: '14px' }}>
                      ▶ Play
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filteredTracks.length === 0 && (
            <div style={{ color: '#b3b3b3', textAlign: 'center', padding: '48px' }}>
              No tracks found
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function App() {
  const { isAuthenticated, isLoading, restoreSession, logout, user } = useAuthStore();
  const [currentPage, setCurrentPage] = useState<'library' | 'admin'>('library');
  
  // Initialize audio player hook
  useAudio();

  useEffect(() => {
    restoreSession();
  }, [restoreSession]);

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <div>Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return (
    <div style={{ minHeight: '100vh' }}>
      {/* Header */}
      <header
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          height: '64px',
          background: '#000',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 24px',
          zIndex: 1001,
        }}
      >
        <nav style={{ display: 'flex', gap: '24px' }}>
          <button
            onClick={() => setCurrentPage('library')}
            style={{
              background: 'transparent',
              color: currentPage === 'library' ? '#fff' : '#b3b3b3',
              fontWeight: currentPage === 'library' ? 600 : 400,
            }}
          >
            Library
          </button>
          {user?.is_admin && (
            <button
              onClick={() => setCurrentPage('admin')}
              style={{
                background: 'transparent',
                color: currentPage === 'admin' ? '#fff' : '#b3b3b3',
                fontWeight: currentPage === 'admin' ? 600 : 400,
              }}
            >
              Admin
            </button>
          )}
        </nav>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <span style={{ color: '#b3b3b3' }}>{user?.username}</span>
          <button onClick={logout} style={{ padding: '6px 12px', fontSize: '14px' }}>
            Logout
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main style={{ paddingTop: '64px' }}>
        {currentPage === 'library' ? <LibraryPage /> : <AdminPanel />}
      </main>

      {/* Player Bar */}
      <PlayerBar />
    </div>
  );
}

export default App;
