// Vehicle Types
export interface Vehicle {
  id: string;
  vin: string;
  make: string;
  model: string;
  year: number;
  trim?: string;
  mileage?: number;
  price?: number;
  originalPrice?: number;
  savings?: number;
  color?: string;
  transmission?: string;
  fuel_type?: string;
  body_type?: string;
  drivetrain?: string;
  condition?: string;
  description?: string;
  images?: VehicleImage[];
  features?: string[];
  matchScore?: number;
  availabilityStatus?: 'available' | 'reserved' | 'sold';
  currentViewers?: number;
  ottoRecommendation?: string;
  range?: number; // For EVs - miles range
  isFavorited?: boolean; // UI state only
  seller_id: string;
  created_at: string;
  updated_at: string;
}

export interface VehicleImage {
  url: string;
  description: string;
  category: 'hero' | 'carousel' | 'detail';
  altText: string;
}

export interface VehicleSpecs {
  mileage: number;
  range?: number; // For EVs
  trim?: string;
  transmission?: string;
  drivetrain?: string;
}

export interface MatchScore {
  score: number;
  tier: 'excellent' | 'good' | 'fair' | 'low';
}

export interface VehicleSearchParams {
  query?: string;
  make?: string;
  model?: string;
  year?: number;
  year_min?: number;
  year_max?: number;
  price_min?: number;
  price_max?: number;
  mileage_min?: number;
  mileage_max?: number;
  body_type?: string;
  transmission?: string;
  fuel_type?: string;
  drivetrain?: string;
  color?: string;
  limit?: number;
  offset?: number;
}

export interface VehicleSearchResponse {
  vehicles: Vehicle[];
  total: number;
  limit: number;
  offset: number;
}

// Search Types
export interface SemanticSearchRequest {
  query: string;
  filters?: VehicleSearchParams;
  limit?: number;
}

export interface SemanticSearchResponse {
  results: Array<{
    vehicle: Vehicle;
    score: number;
    match_highlights?: string[];
  }>;
  total: number;
  query: string;
}

// Conversation Types
export interface ConversationMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
}

export interface ConversationRequest {
  message: string;
  conversation_id?: string;
}

export interface ConversationResponse {
  response: string;
  conversation_id: string;
  suggestions?: string[];
  vehicle_recommendations?: Vehicle[];
}

// User Preference Types
export interface UserPreference {
  id: string;
  user_id: string;
  preference_type: string;
  preference_value: string;
  confidence?: number;
  created_at: string;
  updated_at: string;
}

// Collection Types
export interface VehicleCollection {
  id: string;
  name: string;
  description?: string;
  user_id: string;
  is_public: boolean;
  vehicle_count: number;
  created_at: string;
  updated_at: string;
}

export interface CollectionVehicle {
  collection_id: string;
  vehicle_id: string;
  added_at: string;
}

// Error Types
export interface APIError {
  message: string;
  code?: string;
  details?: unknown;
}

export type APIResponse<T> =
  | {
      data: T;
      error: null;
    }
  | {
      data: null;
      error: APIError;
    };

// Vehicle Grid Types (Story 3-2)
export interface SearchFilters {
  make?: string;
  model?: string;
  priceRange?: [number, number];
  yearRange?: [number, number];
  mileageMax?: number;
  features?: string[];
  location?: string;
}

export interface SearchResponse {
  vehicles: Vehicle[];
  totalCount: number;
  processingTime: number;
}

export type VehicleCardVariant = 'default' | 'compact' | 'comparison';
