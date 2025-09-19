'use client';

import React, { useState, useEffect } from 'react';
import { useTheme } from '@/contexts/ThemeContext';
import { useSpeaker } from '@/contexts/SpeakerContext';
import { useAudioRecording } from '@/hooks/useVoiceRecording';

export default function SpeakerIcon() {
  const { theme } = useTheme();
  const { isAISpeaking, isUserSpeaking, setUserSpeaking } = useSpeaker();
  const [isHovered, setIsHovered] = useState(false);
  const [isMouseDown, setIsMouseDown] = useState(false);
  
  const {
    isRecording,
    isSupported,
    transcript,
    error,
    isProcessing,
    startRecording,
    stopRecording,
    clearTranscript
  } = useAudioRecording();

  // Update user speaking state based on recording
  useEffect(() => {
    setUserSpeaking(isRecording);
  }, [isRecording, setUserSpeaking]);

  // Handle mouse down (start recording)
  const handleMouseDown = () => {
    if (!isSupported) {
      console.error('Speech recognition not supported');
      return;
    }
    if (isAISpeaking) {
      console.log('Cannot record while AI is speaking');
      return;
    }
    setIsMouseDown(true);
    startRecording();
  };

  // Handle mouse up (stop recording)
  const handleMouseUp = () => {
    setIsMouseDown(false);
    stopRecording();
  };

  // Handle mouse leave (stop recording if mouse leaves while recording)
  const handleMouseLeave = () => {
    if (isMouseDown) {
      setIsMouseDown(false);
      stopRecording();
    }
  };

  // Combine both speaking states for visual indication
  const isSpeaking = isAISpeaking || isUserSpeaking;

  // Determine speaker state and color
  const getSpeakerState = () => {
    if (isAISpeaking) return { color: theme.button.primary, label: 'AI Speaking...' };
    if (isProcessing) return { color: '#f59e0b', label: 'Processing audio...' };
    if (isRecording) return { color: '#ef4444', label: 'Recording... Click and hold to speak' };
    if (isUserSpeaking) return { color: theme.secondary, label: 'Customer Speaking...' };
    return { color: theme.secondary, label: 'Click and hold to speak' };
  };

  const speakerState = getSpeakerState();

  // Debug: Show current state
  console.log('SpeakerIcon render:', { isSupported, isRecording, isAISpeaking, isUserSpeaking });

  // For Chrome/Edge, always show the microphone icon and let permission request happen on first use
  // Only show error for browsers that definitely don't support it
  if (!isSupported && error && error.includes('not supported')) {
    console.log('Audio recording not supported, showing fallback icon');
    return (
      <div className="fixed bottom-6 right-6 z-50">
        <div 
          className="w-20 h-20 rounded-full flex items-center justify-center shadow-lg bg-gray-400 cursor-not-allowed"
          title="Audio recording not supported - try Chrome or Edge"
        >
          <svg 
            className="w-10 h-10 text-white" 
            fill="currentColor" 
            viewBox="0 0 24 24"
          >
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
          </svg>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 z-50">
      <div 
        className={`w-20 h-20 rounded-full flex items-center justify-center shadow-lg hover:shadow-xl transition-all duration-300 ${
          isSpeaking ? 'animate-pulse' : ''
        } cursor-pointer select-none`}
        style={{ 
          backgroundColor: speakerState.color,
          transform: isHovered ? 'scale(1.1)' : 'scale(1)',
          boxShadow: isSpeaking ? `0 0 20px ${speakerState.color}` : undefined
        }}
        title={speakerState.label}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={handleMouseLeave}
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onTouchStart={handleMouseDown}
        onTouchEnd={handleMouseUp}
      >
        <svg 
          className="w-10 h-10 text-white" 
          fill="currentColor" 
          viewBox="0 0 24 24"
        >
          <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>
        </svg>
      </div>
      
      {/* Show transcript in a tooltip-like overlay */}
      {transcript && (
        <div 
          className="absolute bottom-24 right-0 bg-black bg-opacity-80 text-white p-3 rounded-lg max-w-xs text-sm"
          style={{ zIndex: 60 }}
        >
          <div className="font-semibold mb-1">Transcript:</div>
          <div>{transcript}</div>
          <button
            onClick={clearTranscript}
            className="mt-2 text-xs text-gray-300 hover:text-white underline"
          >
            Clear
          </button>
        </div>
      )}
      
      {/* Show error message */}
      {error && (
        <div 
          className="absolute bottom-24 right-0 bg-red-600 text-white p-3 rounded-lg max-w-xs text-sm"
          style={{ zIndex: 60 }}
        >
          <div className="font-semibold mb-1">Error:</div>
          <div>{error}</div>
          <button
            onClick={() => window.location.reload()}
            className="mt-2 text-xs text-gray-300 hover:text-white underline"
          >
            Reload Page
          </button>
        </div>
      )}
    </div>
  );
}
