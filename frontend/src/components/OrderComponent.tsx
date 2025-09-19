'use client';

import React, { useState } from 'react';
import { useTheme } from '@/contexts/ThemeContext';

interface OrderItem {
  id: number;
  name: string;
  price: number;
  quantity: number;
}

export default function OrderComponent() {
  const { theme } = useTheme();
  const [orderItems, setOrderItems] = useState<OrderItem[]>([]);

  const addItem = (item: { id: number; name: string; price: number }) => {
    setOrderItems(prev => {
      const existing = prev.find(i => i.id === item.id);
      if (existing) {
        return prev.map(i => 
          i.id === item.id 
            ? { ...i, quantity: i.quantity + 1 }
            : i
        );
      }
      return [...prev, { ...item, quantity: 1 }];
    });
  };

  const removeItem = (id: number) => {
    setOrderItems(prev => {
      const existing = prev.find(i => i.id === id);
      if (existing && existing.quantity > 1) {
        return prev.map(i => 
          i.id === id 
            ? { ...i, quantity: i.quantity - 1 }
            : i
        );
      }
      return prev.filter(i => i.id !== id);
    });
  };

  const clearOrder = () => {
    setOrderItems([]);
  };

  const total = orderItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 
          className="text-2xl font-bold mb-2"
          style={{ color: theme.text.primary }}
        >
          Current Order
        </h2>
        <div 
          className="text-sm"
          style={{ color: theme.text.secondary }}
        >
          Order #{Math.floor(Math.random() * 1000) + 1}
        </div>
      </div>

      {orderItems.length === 0 ? (
        <div className="text-center py-12">
          <div 
            className="mb-4"
            style={{ color: theme.text.muted }}
          >
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
          <p style={{ color: theme.text.secondary }}>No items in order</p>
          <p 
            className="text-sm mt-1"
            style={{ color: theme.text.muted }}
          >
            Add items from the menu
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {orderItems.map(item => (
            <div 
              key={item.id} 
              className="rounded-lg p-4 shadow-sm"
              style={{ 
                backgroundColor: theme.surface,
                border: `1px solid ${theme.border.primary}`
              }}
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 
                    className="font-medium"
                    style={{ color: theme.text.primary }}
                  >
                    {item.name}
                  </h3>
                  <p 
                    className="text-sm"
                    style={{ color: theme.text.secondary }}
                  >
                    ${item.price.toFixed(2)} each
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => removeItem(item.id)}
                    className="w-8 h-8 rounded-full flex items-center justify-center text-white transition-colors"
                    style={{ 
                      backgroundColor: theme.button.secondary,
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = theme.button.secondaryHover;
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = theme.button.secondary;
                    }}
                  >
                    -
                  </button>
                  <span 
                    className="w-8 text-center font-medium"
                    style={{ color: theme.text.primary }}
                  >
                    {item.quantity}
                  </span>
                  <button
                    onClick={() => addItem(item)}
                    className="w-8 h-8 rounded-full flex items-center justify-center text-white transition-colors"
                    style={{ 
                      backgroundColor: theme.button.secondary,
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = theme.button.secondaryHover;
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = theme.button.secondary;
                    }}
                  >
                    +
                  </button>
                </div>
              </div>
              <div className="mt-2 text-right">
                <span 
                  className="font-medium"
                  style={{ color: theme.text.primary }}
                >
                  ${(item.price * item.quantity).toFixed(2)}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {orderItems.length > 0 && (
        <div 
          className="mt-6 pt-4"
          style={{ borderTop: `1px solid ${theme.border.primary}` }}
        >
          <div className="flex justify-between items-center mb-4">
            <span 
              className="text-lg font-semibold"
              style={{ color: theme.text.primary }}
            >
              Total:
            </span>
            <span 
              className="text-xl font-bold"
              style={{ color: theme.text.accent }}
            >
              ${total.toFixed(2)}
            </span>
          </div>
          
          <button
            onClick={clearOrder}
            className="w-full bg-red-500 hover:bg-red-600 text-white font-medium py-2 px-4 rounded-lg transition-colors"
          >
            Clear Order
          </button>
        </div>
      )}
    </div>
  );
}
