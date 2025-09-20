'use client';

import React from 'react';
import { useTheme } from '@/contexts/ThemeContext';
import { Restaurant, MenuCategory } from '@/types/restaurant';
import MenuItemCard from './MenuItemCard';

interface MenuListComponentProps {
  restaurant: Restaurant | null;
  menu: MenuCategory[];
}

export default function MenuListComponent({ restaurant, menu }: MenuListComponentProps) {
  const { theme } = useTheme();

  return (
    <div className="h-full" style={{ background: 'transparent' }}>

      {/* Menu Categories */}
      <div className="p-6 space-y-8" style={{ background: 'transparent' }}>
        {menu.map((category) => (
          <div key={category.id} className="space-y-4">
            <div 
              className="pb-2"
              style={{ borderBottom: `1px solid ${theme.border.primary}` }}
            >
              <h2 
                className="text-xl font-semibold"
                style={{ color: theme.text.primary }}
              >
                {category.name}
              </h2>
              {category.description && (
                <p 
                  className="text-sm mt-1"
                  style={{ color: theme.text.secondary }}
                >
                  {category.description}
                </p>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {category.items.map((item) => (
                <MenuItemCard key={item.id} item={item} theme={theme} restaurantId={restaurant?.id} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

