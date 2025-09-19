'use client';

import React, { useState } from 'react';
import { useTheme } from '@/contexts/ThemeContext';
import { useSpeaker } from '@/contexts/SpeakerContext';
import { useData } from '@/contexts/DataContext';
import LoadingSpinner from '@/components/LoadingSpinner';
import AudioPlayer from '@/components/AudioPlayer';

interface NewCarResponse {
  success: boolean;
  message: string;
  data: {
    session: any;
    greeting_audio_url?: string;
  };
}

export default function CarControlComponent() {
  const { theme } = useTheme();
  const { setAISpeaking } = useSpeaker();
  const { restaurant } = useData();
  const [currentCar, setCurrentCar] = useState<number | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [greetingAudioUrl, setGreetingAudioUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleNewCar = async () => {
    setIsProcessing(true);
    setError(null);
    
    try {
      // Call the backend API to create a new car session
      const requestBody = {
        restaurant_id: restaurant?.id || 1
      };
      
      console.log('Sending request body:', requestBody);
      console.log('Stringified body:', JSON.stringify(requestBody));
      
      const response = await fetch('http://localhost:8000/api/sessions/new-car', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`HTTP error! status: ${response.status}, response: ${errorText}`);
        throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
      }

      const result: NewCarResponse = await response.json();
      
      if (result.success && result.data.greeting_audio_url) {
        // Set the greeting audio URL to trigger playback
        setGreetingAudioUrl(result.data.greeting_audio_url);
        setCurrentCar(Math.floor(Math.random() * 100) + 1);
      } else {
        throw new Error('No greeting audio URL received from server');
      }
    } catch (error) {
      console.error('Error creating new car session:', error);
      setError(error instanceof Error ? error.message : 'Failed to create new car session');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCarArrived = async () => {
    if (currentCar) {
      setIsProcessing(true);
      try {
        // Call the backend API to handle next car
        const response = await fetch('http://localhost:8000/api/sessions/next-car', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          }
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        
        if (result.success) {
          console.log(`Car ${currentCar} has arrived and order is ready`);
          setCurrentCar(null);
          setGreetingAudioUrl(null);
        } else {
          throw new Error(result.message || 'Failed to handle next car');
        }
      } catch (error) {
        console.error('Error handling next car:', error);
        setError(error instanceof Error ? error.message : 'Failed to handle next car');
      } finally {
        setIsProcessing(false);
      }
    }
  };

  const handleAudioPlayStart = () => {
    console.log('Greeting audio started playing');
    setAISpeaking(true);
  };

  const handleAudioPlayEnd = () => {
    console.log('Greeting audio finished playing');
    setAISpeaking(false);
    setGreetingAudioUrl(null); // Clear the URL after playback
  };

  const handleAudioError = (error: string) => {
    console.error('Audio playback error:', error);
    setAISpeaking(false);
    setError(`Audio playback failed: ${error}`);
    setGreetingAudioUrl(null);
  };

  return (
    <div className="space-y-4">
      <h3 
        className="text-lg font-semibold"
        style={{ color: theme.text.primary }}
      >
        Car Control
      </h3>
      
      {/* Audio Player - Hidden, plays greeting audio */}
      <AudioPlayer
        audioUrl={greetingAudioUrl}
        autoPlay={true}
        onPlayStart={handleAudioPlayStart}
        onPlayEnd={handleAudioPlayEnd}
        onError={handleAudioError}
      />
      
      {/* Error Display */}
      {error && (
        <div 
          className="p-3 rounded-lg text-sm"
          style={{ 
            backgroundColor: theme.error?.background || '#fee2e2',
            color: theme.error?.text || '#dc2626',
            border: `1px solid ${theme.error?.border || '#fca5a5'}`
          }}
        >
          {error}
        </div>
      )}
      
      {currentCar ? (
        <div 
          className="rounded-lg p-4"
          style={{ 
            backgroundColor: theme.surface,
            border: `1px solid ${theme.border.primary}`
          }}
        >
          <div className="flex items-center justify-between">
            <div>
              <p 
                className="font-medium"
                style={{ color: theme.text.primary }}
              >
                Car #{currentCar} Active
              </p>
              <p 
                className="text-sm"
                style={{ color: theme.text.secondary }}
              >
                Order in progress
              </p>
            </div>
            <button
              onClick={handleCarArrived}
              disabled={isProcessing}
              className="text-white font-medium py-2 px-4 rounded-lg transition-all duration-300 flex items-center gap-2 disabled:cursor-not-allowed shadow-lg hover:shadow-xl"
              style={{ 
                background: isProcessing ? theme.button.secondary : theme.button.primary,
              }}
              onMouseEnter={(e) => {
                if (!isProcessing) {
                  e.currentTarget.style.background = theme.button.primaryHover;
                  e.currentTarget.style.transform = 'translateY(-1px)';
                }
              }}
              onMouseLeave={(e) => {
                if (!isProcessing) {
                  e.currentTarget.style.background = theme.button.primary;
                  e.currentTarget.style.transform = 'translateY(0)';
                }
              }}
            >
              {isProcessing && <LoadingSpinner size="sm" color="text-white" />}
              {isProcessing ? 'Processing...' : 'Next Customer'}
            </button>
          </div>
        </div>
      ) : (
        <button
          onClick={handleNewCar}
          disabled={isProcessing}
          className="w-full py-3 px-4 rounded-lg font-medium transition-all duration-300 text-white shadow-lg hover:shadow-xl disabled:cursor-not-allowed flex items-center justify-center gap-2"
          style={{ 
            background: isProcessing ? theme.button.secondary : theme.button.primary 
          }}
          onMouseEnter={(e) => {
            if (!isProcessing) {
              e.currentTarget.style.background = theme.button.primaryHover;
              e.currentTarget.style.transform = 'translateY(-2px)';
            }
          }}
          onMouseLeave={(e) => {
            if (!isProcessing) {
              e.currentTarget.style.background = theme.button.primary;
              e.currentTarget.style.transform = 'translateY(0)';
            }
          }}
        >
          {isProcessing && <LoadingSpinner size="sm" color="text-white" />}
          {isProcessing ? 'Creating Session...' : 'New Car'}
        </button>
      )}
      
      <div 
        className="text-xs text-center"
        style={{ color: theme.text.muted }}
      >
        {currentCar 
          ? `Managing order for Car #${currentCar}`
          : 'Click "New Car" to start a new order'
        }
      </div>
    </div>
  );
}
