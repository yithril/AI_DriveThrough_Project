'use client';

import React from 'react';
import { useData } from '@/contexts/DataContext';
import { useTheme } from '@/contexts/ThemeContext';
import OrderComponent from '@/components/OrderComponent';
import CarControlComponent from '@/components/CarControlComponent';
import MenuListComponent from '@/components/MenuListComponent';
import RestaurantLogo from '@/components/RestaurantLogo';
import SpeakerIcon from '@/components/SpeakerIcon';
import LoadingSpinner from '@/components/LoadingSpinner';

export default function MainLayout() {
  const { restaurant, menu, isLoading, error } = useData();
  const { theme } = useTheme();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner size="lg" className="mx-auto mb-4" />
          <p style={{ color: theme.text.secondary }}>Loading restaurant data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="max-w-md w-full text-center">
          <div className="mb-8">
            <h1 className="text-6xl font-bold text-red-600 mb-4">⚠️</h1>
            <h2 
              className="text-2xl font-semibold mb-2"
              style={{ color: theme.text.primary }}
            >
              Failed to Load
            </h2>
            <p 
              className="mb-4"
              style={{ color: theme.text.secondary }}
            >
              {error}
            </p>
          </div>
          
          <button
            onClick={() => window.location.reload()}
            className="inline-block text-white font-medium py-3 px-6 rounded-lg transition-colors flex items-center gap-2 mx-auto"
            style={{ backgroundColor: theme.button.primary }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = theme.button.primaryHover;
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = theme.button.primary;
            }}
          >
            <LoadingSpinner size="sm" color="text-white" />
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div 
      className="min-h-screen flex relative"
      style={{
        '--primary-color': theme.primary,
        '--secondary-color': theme.secondary,
      } as React.CSSProperties}
    >
      {/* Left Panel - Order Management (1/3) */}
      <div 
        className="w-1/3 flex flex-col"
        style={{ 
          backgroundColor: theme.surface,
          borderRight: `1px solid ${theme.border.primary}`
        }}
      >
        {/* Car Controls - Above Order */}
        <div 
          className="p-4"
          style={{ borderBottom: `1px solid ${theme.border.primary}` }}
        >
          <CarControlComponent />
        </div>
        
        {/* Order Component */}
        <div className="flex-1 overflow-y-auto">
          <OrderComponent />
        </div>
      </div>

      {/* Right Panel - Menu Display (2/3) */}
      <div 
        className="w-2/3"
        style={{ backgroundColor: theme.surface }}
      >
        {/* Restaurant Logo */}
        <RestaurantLogo restaurant={restaurant} />
        
        {/* Menu List */}
        <div className="h-full overflow-y-auto">
          <MenuListComponent restaurant={restaurant} menu={menu} />
        </div>
      </div>
      
      {/* Sticky Speaker Icon - Lower Right of Screen */}
      <div className="fixed bottom-4 right-4 z-50">
        <SpeakerIcon />
      </div>
    </div>
  );
}
