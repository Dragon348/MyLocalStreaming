import { useEffect, useState } from 'react';
import { usePlayerStore } from '../../store/player';

export function formatDuration(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

export function formatDurationSec(seconds: number): string {
  if (!isFinite(seconds)) return '0:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

interface ProgressBarProps {
  currentTime: number;
  duration: number;
  isLoading?: boolean;
  onSeek?: (time: number) => void;
}

export function ProgressBar({ currentTime, duration, isLoading, onSeek }: ProgressBarProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [localTime, setLocalTime] = useState(currentTime);

  useEffect(() => {
    if (!isDragging) {
      setLocalTime(currentTime);
    }
  }, [currentTime, isDragging]);

  const percentage = duration > 0 ? (localTime / duration) * 100 : 0;

  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!onSeek || !duration) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const newTime = (x / rect.width) * duration;
    onSeek(newTime);
  };

  const handleMouseDown = () => setIsDragging(true);

  const handleMouseUp = () => {
    setIsDragging(false);
    if (onSeek && duration) {
      onSeek(localTime);
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isDragging || !duration) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const newTime = Math.max(0, Math.min((x / rect.width) * duration, duration));
    setLocalTime(newTime);
  };

  return (
    <div
      className="progress-bar"
      onClick={handleClick}
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
      onMouseMove={handleMouseMove}
      onMouseLeave={() => isDragging && setIsDragging(false)}
      style={{
        width: '100%',
        height: '6px',
        background: '#404040',
        borderRadius: '3px',
        cursor: 'pointer',
        position: 'relative',
      }}
    >
      <div
        style={{
          width: `${percentage}%`,
          height: '100%',
          background: isLoading ? '#ff9800' : '#1db954',
          borderRadius: '3px',
          transition: isDragging ? 'none' : 'width 0.1s',
        }}
      />
      {isDragging && (
        <div
          style={{
            position: 'absolute',
            left: `${percentage}%`,
            top: '50%',
            transform: 'translate(-50%, -50%)',
            width: '12px',
            height: '12px',
            background: '#fff',
            borderRadius: '50%',
            boxShadow: '0 2px 4px rgba(0,0,0,0.5)',
          }}
        />
      )}
    </div>
  );
}

interface PlayButtonProps {
  isPlaying?: boolean;
  onClick?: () => void;
  size?: 'small' | 'medium' | 'large';
}

export function PlayButton({ isPlaying, onClick, size = 'medium' }: PlayButtonProps) {
  const sizes = {
    small: { width: '32px', height: '32px' },
    medium: { width: '48px', height: '48px' },
    large: { width: '64px', height: '64px' },
  };

  const iconSize = size === 'small' ? 16 : size === 'medium' ? 24 : 32;

  return (
    <button
      onClick={onClick}
      style={{
        ...sizes[size],
        borderRadius: '50%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 0,
      }}
    >
      {isPlaying ? (
        // Pause icon
        <svg width={iconSize} height={iconSize} viewBox="0 0 24 24" fill="currentColor">
          <rect x="6" y="4" width="4" height="16" />
          <rect x="14" y="4" width="4" height="16" />
        </svg>
      ) : (
        // Play icon
        <svg width={iconSize} height={iconSize} viewBox="0 0 24 24" fill="currentColor">
          <path d="M8 5v14l11-7z" />
        </svg>
      )}
    </button>
  );
}

interface VolumeControlProps {
  volume: number;
  isMuted: boolean;
  onVolumeChange: (volume: number) => void;
  onToggleMute: () => void;
}

export function VolumeControl({ volume, isMuted, onVolumeChange, onToggleMute }: VolumeControlProps) {
  const getVolumeIcon = () => {
    if (isMuted || volume === 0) {
      return (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z" />
        </svg>
      );
    }
    if (volume < 0.5) {
      return (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M18.5 12c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM5 9v6h4l5 5V4L9 9H5z" />
        </svg>
      );
    }
    return (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
        <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z" />
      </svg>
    );
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <button
        onClick={onToggleMute}
        style={{
          background: 'transparent',
          color: '#fff',
          border: 'none',
          padding: '4px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
        }}
      >
        {getVolumeIcon()}
      </button>
      <input
        type="range"
        min="0"
        max="1"
        step="0.01"
        value={isMuted ? 0 : volume}
        onChange={(e) => onVolumeChange(parseFloat(e.target.value))}
        style={{
          width: '80px',
          accentColor: '#1db954',
        }}
      />
    </div>
  );
}

interface ShuffleButtonProps {
  shuffle: boolean;
  onToggle: () => void;
}

export function ShuffleButton({ shuffle, onToggle }: ShuffleButtonProps) {
  return (
    <button
      onClick={onToggle}
      style={{
        background: shuffle ? '#1db954' : 'transparent',
        color: shuffle ? '#000' : '#b3b3b3',
        border: 'none',
        padding: '8px',
        cursor: 'pointer',
        borderRadius: '4px',
        display: 'flex',
        alignItems: 'center',
      }}
      title="Shuffle"
    >
      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
        <path d="M10.59 9.17L5.41 4 4 5.41l5.17 5.17 1.42-1.41zM14.5 4l2.04 2.04L4 18.59 5.41 20 17.96 7.46 20 9.5V4h-5.5zm.33 9.41l-1.41 1.41 3.13 3.13L14.5 20H20v-5.5l-2.04 2.04-3.13-3.13z" />
      </svg>
    </button>
  );
}

interface RepeatButtonProps {
  repeat: 'off' | 'all' | 'one';
  onCycle: () => void;
}

export function RepeatButton({ repeat, onCycle }: RepeatButtonProps) {
  const getLabel = () => {
    switch (repeat) {
      case 'all':
        return '';
      case 'one':
        return '1';
      default:
        return '';
    }
  };

  return (
    <button
      onClick={onCycle}
      style={{
        background: repeat !== 'off' ? '#1db954' : 'transparent',
        color: repeat !== 'off' ? '#000' : '#b3b3b3',
        border: 'none',
        padding: '8px',
        cursor: 'pointer',
        borderRadius: '4px',
        display: 'flex',
        alignItems: 'center',
        position: 'relative',
      }}
      title={`Repeat: ${repeat}`}
    >
      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
        <path d="M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4z" />
      </svg>
      {getLabel() && (
        <span
          style={{
            position: 'absolute',
            fontSize: '10px',
            fontWeight: 'bold',
            bottom: '2px',
            right: '2px',
          }}
        >
          {getLabel()}
        </span>
      )}
    </button>
  );
}
