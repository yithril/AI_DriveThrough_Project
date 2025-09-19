import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { Restaurant, MenuCategory, RestaurantMenuResponse } from '@/types/restaurant';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

class ApiClient {
  private client: AxiosInstance;

  constructor(baseUrl: string = API_BASE_URL) {
    this.client = axios.create({
      baseURL: baseUrl,
      timeout: 10000, // 10 second timeout
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor for logging
    this.client.interceptors.request.use(
      (config) => {
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('API Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Response Error:', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  private async request<T>(endpoint: string, options: any = {}): Promise<T> {
    try {
      const response: AxiosResponse<T> = await this.client.request({
        url: endpoint,
        ...options,
      });
      return response.data;
    } catch (error: any) {
      if (error.response) {
        throw new Error(`API request failed: ${error.response.status} ${error.response.statusText}`);
      } else if (error.request) {
        throw new Error('Network error: Unable to reach the server');
      } else {
        throw new Error(`Request error: ${error.message}`);
      }
    }
  }

  // Restaurant & Menu endpoints
  async getRestaurantMenu(restaurantId: number): Promise<RestaurantMenuResponse> {
    return this.request<RestaurantMenuResponse>(`/api/restaurants/${restaurantId}/menu`);
  }

  // AI endpoints
  async processAudio(audioFile: File, restaurantId: number, orderId?: number, language: string = 'en'): Promise<any> {
    const formData = new FormData();
    formData.append('audio_file', audioFile);
    formData.append('restaurant_id', restaurantId.toString());
    if (orderId) {
      formData.append('order_id', orderId.toString());
    }
    formData.append('language', language);

    return this.request('/api/ai/process-audio', {
      method: 'POST',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  // Health checks
  async checkRestaurantHealth(): Promise<{ status: string; message: string }> {
    return this.request('/api/restaurants/health');
  }

  async checkAiHealth(): Promise<{ status: string; services: any; message: string }> {
    return this.request('/api/ai/health');
  }
}

// Create singleton instance
export const apiClient = new ApiClient();

// Export types for convenience
export type { Restaurant, MenuCategory, RestaurantMenuResponse };
