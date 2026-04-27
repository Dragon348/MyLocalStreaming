import { useEffect, useRef, useCallback } from 'react';
import { usePlayerStore } from '../store/player';
import { api } from '../lib/api';

export function useAudio() {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const progressInterval = useRef<number | null>(null);

  const {
    currentTrack,
    isPlaying,
    volume,
    isMuted,
    currentTime,
    duration,
    setCurrentTime,
    setDuration,
    setLoading,
    setError,
    onTrackEnded,
  } = usePlayerStore();

  // Initialize audio element
  useEffect(() => {
    audioRef.current = new Audio();
    audioRef.current.preload = 'metadata';

    const audio = audioRef.current;

    const handleTimeUpdate = () => {
      setCurrentTime(audio.currentTime);
    };

    const handleLoadedMetadata = () => {
      setDuration(audio.duration || 0);
      setLoading(false);
    };

    const handleWaiting = () => {
      setLoading(true);
    };

    const handleCanPlay = () => {
      setLoading(false);
    };

    const handleError = () => {
      setError('Failed to load audio');
      setLoading(false);
    };

    const handleEnded = () => {
      onTrackEnded();
    };

    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('loadedmetadata', handleLoadedMetadata);
    audio.addEventListener('waiting', handleWaiting);
    audio.addEventListener('canplay', handleCanPlay);
    audio.addEventListener('error', handleError);
    audio.addEventListener('ended', handleEnded);

    return () => {
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
      audio.removeEventListener('waiting', handleWaiting);
      audio.removeEventListener('canplay', handleCanPlay);
      audio.removeEventListener('error', handleError);
      audio.removeEventListener('ended', handleEnded);
      audio.pause();
      audio.src = '';
      audioRef.current = null;
    };
  }, [setCurrentTime, setDuration, setLoading, setError, onTrackEnded]);

  // Handle track changes
  useEffect(() => {
    if (!audioRef.current || !currentTrack) return;

    const audio = audioRef.current;
    setLoading(true);
    setError(null);

    const streamUrl = api.getStreamUrl(currentTrack.id, false);
    audio.src = streamUrl;
    audio.load();

    // Always attempt to play when a new track is loaded
    // The isPlaying state should be true when play() is called from the store
    audio.play().catch((err) => {
      console.error('Playback failed:', err);
      setError('Playback failed');
      setLoading(false);
    });
  }, [currentTrack?.id]);

  // Handle play/pause
  useEffect(() => {
    if (!audioRef.current) return;

    const audio = audioRef.current;

    if (isPlaying && audio.paused) {
      audio.play().catch((err) => {
        console.error('Playback failed:', err);
        usePlayerStore.getState().pause();
      });
    } else if (!isPlaying && !audio.paused) {
      audio.pause();
    }
  }, [isPlaying]);

  // Handle volume and mute
  useEffect(() => {
    if (!audioRef.current) return;
    audioRef.current.volume = isMuted ? 0 : volume;
  }, [volume, isMuted]);

  // Handle seeking
  const seek = useCallback((time: number) => {
    if (!audioRef.current) return;
    audioRef.current.currentTime = time;
    setCurrentTime(time);
  }, [setCurrentTime]);

  // Manual progress update for smoother UI
  useEffect(() => {
    if (isPlaying) {
      progressInterval.current = window.setInterval(() => {
        if (audioRef.current && !audioRef.current.paused) {
          setCurrentTime(audioRef.current.currentTime);
        }
      }, 500);
    } else {
      if (progressInterval.current) {
        clearInterval(progressInterval.current);
        progressInterval.current = null;
      }
    }

    return () => {
      if (progressInterval.current) {
        clearInterval(progressInterval.current);
      }
    };
  }, [isPlaying, setCurrentTime]);

  return {
    audio: audioRef.current,
    seek,
  };
}
