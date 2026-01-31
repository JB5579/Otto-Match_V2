import { getAuthToken } from '../lib/supabaseClient';
import type {
  Vehicle,
  VehicleSearchParams,
  VehicleSearchResponse,
  SemanticSearchRequest,
  SemanticSearchResponse,
  ConversationRequest,
  ConversationResponse,
  UserPreference,
  VehicleCollection,
  APIResponse,
} from '../types/api';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

class APIClient {
  protected async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<APIResponse<T>> {
    try {
      const token = await getAuthToken();

      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...(options.headers as Record<string, string>),
      };

      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }

      const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers,
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          data: null,
          error: {
            message: data.message || data.detail || 'An error occurred',
            code: response.status.toString(),
            details: data,
          },
        };
      }

      return { data, error: null };
    } catch (error) {
      return {
        data: null,
        error: {
          message: error instanceof Error ? error.message : 'Network error',
          details: error,
        },
      };
    }
  }

  // Vehicle Endpoints
  async searchVehicles(
    params: VehicleSearchParams
  ): Promise<APIResponse<VehicleSearchResponse>> {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        queryParams.append(key, value.toString());
      }
    });

    return this.request<VehicleSearchResponse>(
      `/api/v1/vehicles/search?${queryParams.toString()}`
    );
  }

  async getVehicle(id: string): Promise<APIResponse<Vehicle>> {
    return this.request<Vehicle>(`/api/v1/vehicles/${id}`);
  }

  async getVehicles(
    limit = 20,
    offset = 0
  ): Promise<APIResponse<VehicleSearchResponse>> {
    return this.request<VehicleSearchResponse>(
      `/api/v1/vehicles?limit=${limit}&offset=${offset}`
    );
  }

  // Semantic Search Endpoints
  async semanticSearch(
    request: SemanticSearchRequest
  ): Promise<APIResponse<SemanticSearchResponse>> {
    return this.request<SemanticSearchResponse>('/api/v1/search/semantic', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Conversation Endpoints
  async sendMessage(
    request: ConversationRequest
  ): Promise<APIResponse<ConversationResponse>> {
    return this.request<ConversationResponse>('/api/v1/conversation/chat', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getConversationHistory(
    conversationId: string,
    limit = 50
  ): Promise<APIResponse<ConversationResponse[]>> {
    return this.request<ConversationResponse[]>(
      `/api/v1/conversation/history/${conversationId}?limit=${limit}`
    );
  }

  // User Preference Endpoints
  async getUserPreferences(): Promise<APIResponse<UserPreference[]>> {
    return this.request<UserPreference[]>('/api/v1/user/preferences');
  }

  async updateUserPreference(
    preference: Partial<UserPreference>
  ): Promise<APIResponse<UserPreference>> {
    return this.request<UserPreference>('/api/v1/user/preferences', {
      method: 'PUT',
      body: JSON.stringify(preference),
    });
  }

  // Collection Endpoints
  async getCollections(): Promise<APIResponse<VehicleCollection[]>> {
    return this.request<VehicleCollection[]>('/api/v1/collections');
  }

  async getCollection(
    id: string
  ): Promise<APIResponse<VehicleCollection & { vehicles: Vehicle[] }>> {
    return this.request<VehicleCollection & { vehicles: Vehicle[] }>(
      `/api/v1/collections/${id}`
    );
  }

  async createCollection(
    collection: Partial<VehicleCollection>
  ): Promise<APIResponse<VehicleCollection>> {
    return this.request<VehicleCollection>('/api/v1/collections', {
      method: 'POST',
      body: JSON.stringify(collection),
    });
  }

  async addVehicleToCollection(
    collectionId: string,
    vehicleId: string
  ): Promise<APIResponse<void>> {
    return this.request<void>(
      `/api/v1/collections/${collectionId}/vehicles/${vehicleId}`,
      {
        method: 'POST',
      }
    );
  }

  async removeVehicleFromCollection(
    collectionId: string,
    vehicleId: string
  ): Promise<APIResponse<void>> {
    return this.request<void>(
      `/api/v1/collections/${collectionId}/vehicles/${vehicleId}`,
      {
        method: 'DELETE',
      }
    );
  }

  async deleteCollection(id: string): Promise<APIResponse<void>> {
    return this.request<void>(`/api/v1/collections/${id}`, {
      method: 'DELETE',
    });
  }
}

export const apiClient = new APIClient();

// Vehicle-specific API client for Story 3-2
export class VehicleAPIClient {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<APIResponse<T>> {
    try {
      const token = await getAuthToken();

      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...(options.headers as Record<string, string>),
      };

      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }

      const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers,
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          data: null,
          error: {
            message: data.message || data.detail || 'An error occurred',
            code: response.status.toString(),
            details: data,
          },
        };
      }

      return { data, error: null };
    } catch (error) {
      return {
        data: null,
        error: {
          message: error instanceof Error ? error.message : 'Network error',
          details: error,
        },
      };
    }
  }

  async getVehicles(filters?: {
    limit?: number;
    offset?: number;
    make?: string;
    model?: string;
    year?: number;
    year_min?: number;
    year_max?: number;
    price_min?: number;
    price_max?: number;
    mileage_min?: number;
    mileage_max?: number;
  }): Promise<{ vehicles: Vehicle[]; total: number }> {
    const params: VehicleSearchParams = {
      limit: filters?.limit || 50,
      offset: filters?.offset || 0,
      make: filters?.make,
      model: filters?.model,
      year: filters?.year,
      year_min: filters?.year_min,
      year_max: filters?.year_max,
      price_min: filters?.price_min,
      price_max: filters?.price_max,
      mileage_min: filters?.mileage_min,
      mileage_max: filters?.mileage_max,
    };

    const response = await apiClient.searchVehicles(params);

    if (response.error || !response.data) {
      throw new Error(response.error?.message || 'Failed to fetch vehicles');
    }

    return {
      vehicles: response.data.vehicles,
      total: response.data.total,
    };
  }

  async addFavorite(vehicleId: string): Promise<{ success: boolean; message: string }> {
    const response = await this.request<{ success: boolean; message: string }>(
      `/api/v1/favorites/${vehicleId}`,
      {
        method: 'POST',
      }
    );

    if (response.error || !response.data) {
      throw new Error(response.error?.message || 'Failed to add favorite');
    }

    return response.data;
  }

  async submitFeedback(
    vehicleId: string,
    type: 'more' | 'less'
  ): Promise<{ success: boolean; preferences_updated: string[] }> {
    const response = await this.request<{ success: boolean; preferences_updated: string[] }>(
      '/api/v1/feedback',
      {
        method: 'POST',
        body: JSON.stringify({ type, vehicle_id: vehicleId }),
      }
    );

    if (response.error || !response.data) {
      throw new Error(response.error?.message || 'Failed to submit feedback');
    }

    return response.data;
  }
}
