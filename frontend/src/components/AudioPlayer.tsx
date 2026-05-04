import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Play, Pause, Download, Volume2, VolumeX } from 'lucide-react';

interface AudioPlayerProps {
  audioUrl: string;
  title?: string;
  onDownload?: () => void;
  className?: string;
}

export const AudioPlayer: React.FC<AudioPlayerProps> = ({
  audioUrl,
  title = 'Podcast',
  onDownload,
  className = '',
}) => {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Audio waveform data (simplified visualization)
  const [waveformData, setWaveformData] = useState<number[]>([]);

  useEffect(() => {
    // Generate mock waveform data
    const mockWaveform = Array.from({ length: 100 }, () => Math.random() * 100);
    setWaveformData(mockWaveform);
  }, [audioUrl]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleLoadedMetadata = () => {
      setDuration(audio.duration);
      setIsLoading(false);
    };

    const handleTimeUpdate = () => {
      setCurrentTime(audio.currentTime);
    };

    const handleEnded = () => {
      setIsPlaying(false);
      setCurrentTime(0);
    };

    const handleCanPlay = () => {
      setIsLoading(false);
    };

    audio.addEventListener('loadedmetadata', handleLoadedMetadata);
    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('canplay', handleCanPlay);

    return () => {
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('canplay', handleCanPlay);
    };
  }, []);

  const togglePlayPause = useCallback(() => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
      setIsPlaying(false);
    } else {
      audio.play();
      setIsPlaying(true);
    }
  }, [isPlaying]);

  const handleSeek = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const audio = audioRef.current;
    if (!audio) return;

    const time = parseFloat(e.target.value);
    audio.currentTime = time;
    setCurrentTime(time);
  }, []);

  const handleSpeedChange = useCallback((rate: number) => {
    const audio = audioRef.current;
    if (!audio) return;

    audio.playbackRate = rate;
    setPlaybackRate(rate);
  }, []);

  const handleVolumeChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const audio = audioRef.current;
    if (!audio) return;

    const vol = parseFloat(e.target.value);
    audio.volume = vol;
    setVolume(vol);
    setIsMuted(vol === 0);
  }, []);

  const toggleMute = useCallback(() => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isMuted) {
      audio.volume = volume || 0.5;
      setIsMuted(false);
    } else {
      audio.volume = 0;
      setIsMuted(true);
    }
  }, [isMuted, volume]);

  const formatTime = (time: number): string => {
    if (!isFinite(time)) return '0:00';
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const SPEED_OPTIONS = [0.5, 0.75, 1, 1.25, 1.5, 1.75, 2];

  return (
    <div className={`bg-white rounded-lg shadow-lg p-6 space-y-4 ${className}`}>
      <audio ref={audioRef} src={audioUrl} preload="metadata" />

      {/* Title */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-800 truncate">
          {title}
        </h3>
        {onDownload && (
          <button
            onClick={onDownload}
            className="
              p-2 rounded-lg text-blue-600 hover:bg-blue-50
              transition-colors duration-200
            "
            aria-label="Download podcast"
          >
            <Download size={20} />
          </button>
        )}
      </div>

      {/* Waveform Visualization */}
      <div className="relative h-20 bg-gray-100 rounded-lg overflow-hidden">
        <div className="flex items-end justify-around h-full px-1">
          {waveformData.map((height, index) => {
            const progress = (currentTime / duration) * 100;
            const barProgress = (index / waveformData.length) * 100;
            const isPlayed = barProgress <= progress;

            return (
              <div
                key={index}
                className={`
                  w-1 rounded-t transition-all duration-200
                  ${isPlayed ? 'bg-blue-600' : 'bg-gray-300'}
                  ${isPlaying && isPlayed ? 'animate-pulse' : ''}
                `}
                style={{ height: `${height}%` }}
              />
            );
          })}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <input
          type="range"
          min="0"
          max={duration || 0}
          value={currentTime}
          onChange={handleSeek}
          disabled={isLoading}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
          style={{
            background: `linear-gradient(to right, #3B82F6 0%, #3B82F6 ${(currentTime / duration) * 100}%, #E5E7EB ${(currentTime / duration) * 100}%, #E5E7EB 100%)`,
          }}
        />
        <div className="flex justify-between text-sm text-gray-600">
          <span>{formatTime(currentTime)}</span>
          <span>{formatTime(duration)}</span>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between">
        {/* Play/Pause Button */}
        <button
          onClick={togglePlayPause}
          disabled={isLoading}
          className={`
            p-4 rounded-full transition-all duration-200
            ${
              isLoading
                ? 'bg-gray-300 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 active:scale-95'
            }
            text-white shadow-md
          `}
          aria-label={isPlaying ? 'Pause' : 'Play'}
        >
          {isPlaying ? <Pause size={24} /> : <Play size={24} className="ml-1" />}
        </button>

        {/* Speed Control */}
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">Speed:</span>
          <div className="flex space-x-1">
            {SPEED_OPTIONS.map((rate) => (
              <button
                key={rate}
                onClick={() => handleSpeedChange(rate)}
                className={`
                  px-3 py-1 rounded text-sm font-medium transition-all duration-200
                  ${
                    playbackRate === rate
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }
                `}
              >
                {rate}x
              </button>
            ))}
          </div>
        </div>

        {/* Volume Control */}
        <div className="flex items-center space-x-2">
          <button
            onClick={toggleMute}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors duration-200"
            aria-label={isMuted ? 'Unmute' : 'Mute'}
          >
            {isMuted ? <VolumeX size={20} /> : <Volume2 size={20} />}
          </button>
          <input
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={isMuted ? 0 : volume}
            onChange={handleVolumeChange}
            className="w-20 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
          />
        </div>
      </div>

      {isLoading && (
        <div className="text-center text-sm text-gray-500 animate-pulse">
          Loading audio...
        </div>
      )}
    </div>
  );
};

export default AudioPlayer;
