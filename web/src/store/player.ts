import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Track } from '../lib/types';

export type RepeatMode = 'off' | 'all' | 'one';

interface ShuffleState {
  originalQueue: Track[];
  shuffledIndices: number[];
  currentIndexInOriginal: number;
}

interface PlayerState {
  // Current playback state
  isPlaying: boolean;
  currentTrack: Track | null;
  currentTime: number;
  duration: number;
  volume: number;
  isMuted: boolean;
  shuffle: boolean;
  repeat: RepeatMode;
  isLoading: boolean;
  error: string | null;

  // Queue management
  queue: Track[];
  queueIndex: number;

  // Shuffle state (for Fisher-Yates with state preservation)
  shuffleState: ShuffleState | null;

  // Actions
  play: (track: Track, queue?: Track[], startIndex?: number) => void;
  pause: () => void;
  toggle: () => void;
  next: () => void;
  previous: () => void;
  seek: (time: number) => void;
  setDuration: (duration: number) => void;
  setVolume: (volume: number) => void;
  toggleMute: () => void;
  toggleShuffle: () => void;
  setRepeat: (mode: RepeatMode) => void;
  addToQueue: (track: Track, playNext?: boolean) => void;
  removeFromQueue: (index: number) => void;
  clearQueue: () => void;
  setCurrentTime: (time: number) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  onTrackEnded: () => void;

  // Internal helpers for shuffle
  _getNextIndex: () => number;
  _getPreviousIndex: () => number;
}

// Fisher-Yates shuffle algorithm that returns indices
function fisherYatesShuffleIndices(length: number): number[] {
  const indices = Array.from({ length }, (_, i) => i);
  for (let i = length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [indices[i], indices[j]] = [indices[j], indices[i]];
  }
  return indices;
}

export const usePlayerStore = create<PlayerState>()(
  persist(
    (set, get) => ({
      isPlaying: false,
      currentTrack: null,
      currentTime: 0,
      duration: 0,
      volume: 0.8,
      isMuted: false,
      shuffle: false,
      repeat: 'off',
      isLoading: false,
      error: null,
      queue: [],
      queueIndex: -1,
      shuffleState: null,

      play: (track, queue, startIndex = 0) => {
        const state = get();
        let newQueue = queue || state.queue;
        let newIndex = startIndex;

        if (queue) {
          newQueue = queue;
          // Find the track in the queue
          newIndex = newQueue.findIndex((t) => t.id === track.id);
          if (newIndex === -1) {
            newIndex = startIndex;
          }
        } else if (state.queue.length === 0) {
          newQueue = [track];
          newIndex = 0;
        } else {
          newIndex = state.queue.findIndex((t) => t.id === track.id);
          if (newIndex === -1) {
            newQueue = [...state.queue, track];
            newIndex = newQueue.length - 1;
          }
        }

        // Reset shuffle state when starting new playback
        const newShuffleState = state.shuffle
          ? {
              originalQueue: newQueue,
              shuffledIndices: fisherYatesShuffleIndices(newQueue.length),
              currentIndexInOriginal: newIndex,
            }
          : null;

        set({
          currentTrack: track,
          isPlaying: true,
          queue: newQueue,
          queueIndex: newIndex,
          currentTime: 0,
          shuffleState: newShuffleState,
          error: null,
        });
      },

      pause: () => set({ isPlaying: false }),

      toggle: () => set((state) => ({ isPlaying: !state.isPlaying })),

      next: () => {
        const state = get();
        if (state.queue.length === 0) return;

        const nextIndex = state._getNextIndex();
        
        // If next index is beyond queue length (end of queue with no repeat), stop playback
        if (nextIndex >= state.queue.length) {
          set({ isPlaying: false });
          return;
        }
        
        const nextTrack = state.queue[nextIndex];

        set({
          currentTrack: nextTrack,
          queueIndex: nextIndex,
          isPlaying: true,
          currentTime: 0,
          shuffleState: state.shuffleState
            ? { ...state.shuffleState, currentIndexInOriginal: nextIndex }
            : null,
        });
      },

      previous: () => {
        const state = get();
        if (state.currentTime > 5) {
          set({ currentTime: 0 });
          return;
        }

        if (state.queue.length === 0) return;

        const prevIndex = state._getPreviousIndex();
        const prevTrack = state.queue[prevIndex];

        set({
          currentTrack: prevTrack,
          queueIndex: prevIndex,
          isPlaying: true,
          currentTime: 0,
          shuffleState: state.shuffleState
            ? { ...state.shuffleState, currentIndexInOriginal: prevIndex }
            : null,
        });
      },

      seek: (time) => {
        set({ currentTime: Math.max(0, time) });
        // If we have an audio element, also seek it directly
        // This is handled by the useAudio hook's seek function
      },

      setDuration: (duration) => set({ duration }),

      setVolume: (volume) => set({ volume, isMuted: volume === 0 }),

      toggleMute: () => set((state) => ({ isMuted: !state.isMuted })),

      toggleShuffle: () => {
        const state = get();
        const newShuffle = !state.shuffle;
        
        if (newShuffle && state.queue.length > 0) {
          // Initialize shuffle state
          const shuffledIndices = fisherYatesShuffleIndices(state.queue.length);
          set({
            shuffle: true,
            shuffleState: {
              originalQueue: state.queue,
              shuffledIndices,
              currentIndexInOriginal: state.queueIndex,
            },
          });
        } else {
          set({ shuffle: false, shuffleState: null });
        }
      },

      setRepeat: (mode) => set({ repeat: mode }),

      addToQueue: (track, playNext = false) => {
        const state = get();
        if (playNext && state.queueIndex >= 0) {
          const newQueue = [
            ...state.queue.slice(0, state.queueIndex + 1),
            track,
            ...state.queue.slice(state.queueIndex + 1),
          ];
          set({ queue: newQueue });
        } else {
          set((s) => ({ queue: [...s.queue, track] }));
        }
      },

      removeFromQueue: (index) => {
        const state = get();
        if (index < 0 || index >= state.queue.length) return;
        
        const newQueue = state.queue.filter((_, i) => i !== index);
        let newQueueIndex = state.queueIndex;
        
        if (index < state.queueIndex) {
          newQueueIndex = state.queueIndex - 1;
        } else if (index === state.queueIndex) {
          // If removing current track, move to next or stop
          if (newQueue.length > 0) {
            newQueueIndex = Math.min(index, newQueue.length - 1);
            set({
              queue: newQueue,
              queueIndex: newQueueIndex,
              currentTrack: newQueue[newQueueIndex],
              currentTime: 0,
            });
            return;
          } else {
            // Queue is empty, stop playback
            set({
              queue: [],
              queueIndex: -1,
              currentTrack: null,
              isPlaying: false,
              currentTime: 0,
            });
            return;
          }
        }
        
        set({ queue: newQueue, queueIndex: newQueueIndex });
      },

      clearQueue: () => set({ queue: [], queueIndex: -1, currentTrack: null, isPlaying: false, currentTime: 0 }),

      setCurrentTime: (time) => set({ currentTime: time }),

      setLoading: (loading) => set({ isLoading: loading }),

      setError: (error) => set({ error }),

      onTrackEnded: () => {
        const state = get();
        
        if (state.repeat === 'one') {
          set({ currentTime: 0 });
          return;
        }

        if (state.queueIndex < state.queue.length - 1 || state.repeat === 'all') {
          state.next();
        } else {
          set({ isPlaying: false });
        }
      },

      // Fisher-Yates shuffle implementation
      _shuffleArray: (array: Track[]) => {
        return fisherYatesShuffleIndices(array.length);
      },

      _getNextIndex: () => {
        const state = get();
        if (state.queue.length === 0) return 0;

        if (state.shuffle && state.shuffleState) {
          // Use shuffled order
          const currentOriginalIndex = state.shuffleState.currentIndexInOriginal;
          const shuffledPos = state.shuffleState.shuffledIndices.indexOf(currentOriginalIndex);
          const nextShuffledPos = (shuffledPos + 1) % state.shuffleState.shuffledIndices.length;
          
          // Handle repeat all
          if (nextShuffledPos === 0 && state.repeat !== 'all') {
            return state.queueIndex;
          }
          
          return state.shuffleState.shuffledIndices[nextShuffledPos];
        }

        // Normal sequential order
        let nextIndex = state.queueIndex + 1;
        if (nextIndex >= state.queue.length) {
          if (state.repeat === 'all') {
            nextIndex = 0;
          } else {
            // Return a value > queue length to signal end of queue
            return state.queue.length;
          }
        }
        return nextIndex;
      },

      _getPreviousIndex: () => {
        const state = get();
        if (state.queue.length === 0) return 0;

        if (state.shuffle && state.shuffleState) {
          const currentOriginalIndex = state.shuffleState.currentIndexInOriginal;
          const shuffledPos = state.shuffleState.shuffledIndices.indexOf(currentOriginalIndex);
          const prevShuffledPos = shuffledPos === 0 
            ? state.shuffleState.shuffledIndices.length - 1 
            : shuffledPos - 1;
          return state.shuffleState.shuffledIndices[prevShuffledPos];
        }

        let prevIndex = state.queueIndex - 1;
        if (prevIndex < 0) {
          prevIndex = state.queue.length - 1;
        }
        return prevIndex;
      },
    }),
    {
      name: 'player-storage',
      partialize: (state) => ({
        volume: state.volume,
        shuffle: state.shuffle,
        repeat: state.repeat,
      }),
    }
  )
);
