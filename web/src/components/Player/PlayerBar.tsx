import { usePlayerStore } from '../../store/player';
import {
  PlayButton,
  ProgressBar,
  VolumeControl,
  ShuffleButton,
  RepeatButton,
  formatDurationSec,
} from './PlayerControls';

export function PlayerBar() {
  const {
    currentTrack,
    isPlaying,
    currentTime,
    duration,
    volume,
    isMuted,
    shuffle,
    repeat,
    isLoading,
    toggle,
    next,
    previous,
    seek,
    setVolume,
    toggleMute,
    toggleShuffle,
    setRepeat,
  } = usePlayerStore();

  const cycleRepeat = () => {
    const modes: ('off' | 'all' | 'one')[] = ['off', 'all', 'one'];
    const currentIndex = modes.indexOf(repeat);
    const nextIndex = (currentIndex + 1) % modes.length;
    setRepeat(modes[nextIndex]);
  };

  return (
    <div
      style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        height: '90px',
        background: '#181818',
        borderTop: '1px solid #282828',
        padding: '0 16px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        zIndex: 1000,
      }}
    >
      {/* Track Info */}
      <div style={{ width: '30%', minWidth: '180px' }}>
        {currentTrack ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div
              style={{
                width: '56px',
                height: '56px',
                background: '#282828',
                borderRadius: '4px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <svg width="32" height="32" viewBox="0 0 24 24" fill="#b3b3b3">
                <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z" />
              </svg>
            </div>
            <div style={{ overflow: 'hidden' }}>
              <div style={{ fontWeight: 600, marginBottom: '4px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {currentTrack.title}
              </div>
              <div style={{ color: '#b3b3b3', fontSize: '14px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {currentTrack.artist}
              </div>
            </div>
          </div>
        ) : (
          <div style={{ color: '#b3b3b3' }}>No track selected</div>
        )}
      </div>

      {/* Playback Controls */}
      <div style={{ width: '40%', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <ShuffleButton shuffle={shuffle} onToggle={toggleShuffle} />
          <button
            onClick={previous}
            disabled={!currentTrack}
            style={{
              background: 'transparent',
              color: currentTrack ? '#fff' : '#535353',
              border: 'none',
              padding: '8px',
              cursor: currentTrack ? 'pointer' : 'not-allowed',
              display: 'flex',
              alignItems: 'center',
            }}
            title="Previous"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M6 6h2v12H6zm3.5 6l8.5 6V6z" />
            </svg>
          </button>
          <PlayButton isPlaying={isPlaying} onClick={toggle} size="medium" />
          <button
            onClick={next}
            disabled={!currentTrack}
            style={{
              background: 'transparent',
              color: currentTrack ? '#fff' : '#535353',
              border: 'none',
              padding: '8px',
              cursor: currentTrack ? 'pointer' : 'not-allowed',
              display: 'flex',
              alignItems: 'center',
            }}
            title="Next"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z" />
            </svg>
          </button>
          <RepeatButton repeat={repeat} onCycle={cycleRepeat} />
        </div>
        <div style={{ width: '100%', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: '#b3b3b3' }}>
          <span style={{ minWidth: '40px', textAlign: 'right' }}>
            {formatDurationSec(currentTime)}
          </span>
          <ProgressBar
            currentTime={currentTime}
            duration={duration || 0}
            isLoading={isLoading}
            onSeek={seek}
          />
          <span style={{ minWidth: '40px' }}>
            {formatDurationSec(duration || 0)}
          </span>
        </div>
      </div>

      {/* Volume Control */}
      <div style={{ width: '30%', display: 'flex', justifyContent: 'flex-end' }}>
        <VolumeControl
          volume={volume}
          isMuted={isMuted}
          onVolumeChange={setVolume}
          onToggleMute={toggleMute}
        />
      </div>
    </div>
  );
}
