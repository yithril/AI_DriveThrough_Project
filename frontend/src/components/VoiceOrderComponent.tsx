'use client';

import React, { useState } from 'react';
import { useTheme } from '@/contexts/ThemeContext';
import VoiceRecorder from './VoiceRecorder';
import TextToSpeech from './TextToSpeech';

interface VoiceOrderComponentProps {
  onOrderReceived?: (orderText: string) => void;
}

export default function VoiceOrderComponent({ onOrderReceived }: VoiceOrderComponentProps) {
  const { theme } = useTheme();
  const [isListening, setIsListening] = useState(false);
  const [lastRecording, setLastRecording] = useState<Blob | null>(null);
  const [orderText, setOrderText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  const handleRecordingComplete = async (audioBlob: Blob) => {
    setLastRecording(audioBlob);
    setIsProcessing(true);
    
    try {
      // Here you would typically send the audio to your backend for speech-to-text processing
      // For now, we'll simulate it with a placeholder
      await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate processing time
      
      // Simulate speech-to-text result
      const simulatedOrderText = "I'd like a burger and fries, please";
      setOrderText(simulatedOrderText);
      onOrderReceived?.(simulatedOrderText);
      
    } catch (error) {
      console.error('Error processing voice order:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleRecordingStart = () => {
    setIsListening(true);
  };

  const handleRecordingStop = () => {
    setIsListening(false);
  };

  const speakOrder = () => {
    if (orderText) {
      // This will trigger the TextToSpeech component
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h3 
          className="text-xl font-semibold mb-2"
          style={{ color: theme.text.primary }}
        >
          Voice Order
        </h3>
        <p 
          className="text-sm"
          style={{ color: theme.text.secondary }}
        >
          Record your order or listen to menu items
        </p>
      </div>

      {/* Voice Recorder */}
      <div 
        className="rounded-lg p-4"
        style={{ 
          backgroundColor: theme.surface,
          border: `1px solid ${theme.border.primary}`
        }}
      >
        <VoiceRecorder
          onRecordingComplete={handleRecordingComplete}
          onRecordingStart={handleRecordingStart}
          onRecordingStop={handleRecordingStop}
        />
      </div>

      {/* Processing Status */}
      {isProcessing && (
        <div className="text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-lg" style={{ backgroundColor: theme.surface }}>
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-transparent border-t-current" style={{ color: theme.button.primary }}></div>
            <span style={{ color: theme.text.secondary }}>Processing your order...</span>
          </div>
        </div>
      )}

      {/* Order Text Display */}
      {orderText && (
        <div 
          className="rounded-lg p-4"
          style={{ 
            backgroundColor: theme.surface,
            border: `1px solid ${theme.border.primary}`
          }}
        >
          <h4 
            className="font-medium mb-2"
            style={{ color: theme.text.primary }}
          >
            Your Order:
          </h4>
          <p 
            className="text-sm mb-3"
            style={{ color: theme.text.secondary }}
          >
            {orderText}
          </p>
          <button
            onClick={speakOrder}
            className="px-4 py-2 rounded-lg font-medium transition-colors"
            style={{ 
              backgroundColor: theme.button.primary,
              color: 'white'
            }}
          >
            🔊 Read Order
          </button>
        </div>
      )}

      {/* Text-to-Speech for Menu Items */}
      <div 
        className="rounded-lg p-4"
        style={{ 
          backgroundColor: theme.surface,
          border: `1px solid ${theme.border.primary}`
        }}
      >
        <h4 
          className="font-medium mb-3"
          style={{ color: theme.text.primary }}
        >
          Menu Announcements
        </h4>
        <TextToSpeech 
          text="Welcome to our drive-thru! Please take a look at our menu and let us know what you'd like to order."
          autoPlay={false}
        />
      </div>

      {/* Quick Menu Announcements */}
      <div className="grid grid-cols-2 gap-2">
        <button
          onClick={() => {
            const text = "Our special today is the Cosmic Burger with galactic fries!";
            // This would trigger the TextToSpeech component
          }}
          className="p-3 rounded-lg font-medium text-sm transition-colors"
          style={{ 
            backgroundColor: theme.button.secondary,
            color: 'white'
          }}
        >
          🌟 Specials
        </button>
        <button
          onClick={() => {
            const text = "We have vegetarian options available!";
            // This would trigger the TextToSpeech component
          }}
          className="p-3 rounded-lg font-medium text-sm transition-colors"
          style={{ 
            backgroundColor: theme.button.secondary,
            color: 'white'
          }}
        >
          🌱 Vegetarian
        </button>
      </div>
    </div>
  );
}


