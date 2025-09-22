'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiClient } from '@/lib/api';

interface SessionContextType {
  sessionId: string | null;
  restaurantId: number | null;
  isLoading: boolean;
  error: string | null;
  createSession: (restaurantId: number) => Promise<void>;
  clearSession: () => Promise<void>;
  refreshSession: () => Promise<void>;
}

const SessionContext = createContext<SessionContextType | undefined>(undefined);

interface SessionProviderProps {
  children: ReactNode;
}

export function SessionProvider({ children }: SessionProviderProps) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [restaurantId, setRestaurantId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createSession = async (newRestaurantId: number) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await apiClient.createNewSession(newRestaurantId);
      if (response.success) {
        setSessionId(response.data.session_id);
        setRestaurantId(newRestaurantId);
        console.log('New session created:', response.data.session_id);
      } else {
        throw new Error('Failed to create session');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create session';
      setError(errorMessage);
      console.error('Session creation error:', errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const clearSession = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await apiClient.clearCurrentSession();
      if (response.success) {
        setSessionId(null);
        setRestaurantId(null);
        console.log('Session cleared');
      } else {
        throw new Error('Failed to clear session');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to clear session';
      setError(errorMessage);
      console.error('Session clear error:', errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const refreshSession = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await apiClient.getCurrentSession();
      if (response.success) {
        const session = response.data.session;
        setSessionId(session.id);
        setRestaurantId(session.restaurant_id);
        console.log('Session refreshed:', session.id);
      } else {
        // No current session, that's okay
        setSessionId(null);
        setRestaurantId(null);
      }
    } catch (err) {
      // No current session is not an error
      setSessionId(null);
      setRestaurantId(null);
    } finally {
      setIsLoading(false);
    }
  };

  // Auto-refresh session on mount
  useEffect(() => {
    refreshSession();
  }, []);

  const value: SessionContextType = {
    sessionId,
    restaurantId,
    isLoading,
    error,
    createSession,
    clearSession,
    refreshSession,
  };

  return (
    <SessionContext.Provider value={value}>
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const context = useContext(SessionContext);
  if (context === undefined) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
}
