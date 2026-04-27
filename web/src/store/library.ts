import { create } from 'zustand';
import type { Track, Playlist } from '../lib/types';

interface LibraryState {
  tracks: Track[];
  playlists: Playlist[];
  isLoading: boolean;
  error: string | null;
  searchQuery: string;
  sortBy: 'title' | 'artist' | 'album' | 'created_at';
  sortOrder: 'asc' | 'desc';

  setTracks: (tracks: Track[]) => void;
  setPlaylists: (playlists: Playlist[]) => void;
  addTrack: (track: Track) => void;
  removeTrack: (trackId: string) => void;
  setSearchQuery: (query: string) => void;
  setSortBy: (sortBy: 'title' | 'artist' | 'album' | 'created_at') => void;
  toggleSortOrder: () => void;
  getFilteredAndSortedTracks: () => Track[];
}

export const useLibraryStore = create<LibraryState>()((set, get) => ({
  tracks: [],
  playlists: [],
  isLoading: false,
  error: null,
  searchQuery: '',
  sortBy: 'title',
  sortOrder: 'asc',

  setTracks: (tracks) => set({ tracks }),

  setPlaylists: (playlists) => set({ playlists }),

  addTrack: (track) =>
    set((state) => ({
      tracks: [...state.tracks.filter((t) => t.id !== track.id), track],
    })),

  removeTrack: (trackId) =>
    set((state) => ({
      tracks: state.tracks.filter((t) => t.id !== trackId),
    })),

  setSearchQuery: (query) => set({ searchQuery: query }),

  setSortBy: (sortBy) => set({ sortBy }),

  toggleSortOrder: () =>
    set((state) => ({
      sortOrder: state.sortOrder === 'asc' ? 'desc' : 'asc',
    })),

  getFilteredAndSortedTracks: () => {
    const state = get();
    let filtered = [...state.tracks];

    // Filter by search query
    if (state.searchQuery) {
      const query = state.searchQuery.toLowerCase();
      filtered = filtered.filter(
        (track) =>
          track.title.toLowerCase().includes(query) ||
          track.artist.toLowerCase().includes(query) ||
          track.album.toLowerCase().includes(query)
      );
    }

    // Sort
    filtered.sort((a, b) => {
      let comparison = 0;
      switch (state.sortBy) {
        case 'title':
          comparison = a.title.localeCompare(b.title);
          break;
        case 'artist':
          comparison = a.artist.localeCompare(b.artist);
          break;
        case 'album':
          comparison = a.album.localeCompare(b.album);
          break;
        case 'created_at':
          comparison = new Date(a.created_at || 0).getTime() - new Date(b.created_at || 0).getTime();
          break;
      }
      return state.sortOrder === 'asc' ? comparison : -comparison;
    });

    return filtered;
  },
}));
