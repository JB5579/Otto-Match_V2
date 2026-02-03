/**
 * Filter Types for Story 3-7: Intelligent Grid Filtering and Sorting
 *
 * Provides type definitions for filter state, sort options, and filter UI components.
 * Integrates with VehicleContext for filtered vehicle display and sessionStorage persistence.
 *
 * AC2: Filter Modal with Multi-Select Options
 * AC4: Intelligent Sort Options
 * AC7: Filter Persistence (30min expiry)
 */

import type { Vehicle } from './api';

/**
 * Sort options available in the vehicle grid
 * AC4: Intelligent Sort Options
 */
export type SortOption =
  | 'relevance'  // Sorted by Otto's match score (default)
  | 'price_asc'  // Price: Low to High
  | 'price_desc' // Price: High to Low
  | 'mileage'    // Mileage: Lowest first
  | 'year'       // Year: Newest first

/**
 * Display labels for sort options
 */
export const SORT_LABELS: Record<SortOption, string> = {
  relevance: 'Relevance',
  price_asc: 'Price: Low to High',
  price_desc: 'Price: High to Low',
  mileage: 'Mileage: Lowest First',
  year: 'Year: Newest First',
};

/**
 * Otto explanations for each sort option
 * AC4: Otto explains sorting choice
 */
export const SORT_EXPLANATIONS: Record<SortOption, string> = {
  relevance: "Sorted by relevance to your preferences",
  price_asc: "Sorted by price from lowest to highest",
  price_desc: "Sorted by price from highest to lowest",
  mileage: "Sorted by mileage from lowest to highest",
  year: "Sorted by year from newest to oldest",
};

/**
 * Vehicle body types available for filtering
 * AC2: Vehicle Type filter category
 */
export type VehicleTypeFilter =
  | 'SUV'
  | 'Sedan'
  | 'Truck'
  | 'EV'
  | 'Hybrid'
  | 'Coupe'
  | 'Convertible'
  | 'Wagon'
  | 'Van'
  | 'Crossover';

/**
 * Vehicle feature options for filtering
 * AC2: Features multi-select
 */
export type VehicleFeatureFilter =
  | 'Sunroof'
  | 'Leather Seats'
  | 'Navigation'
  | 'Backup Camera'
  | 'Bluetooth'
  | 'Heated Seats'
  | 'Cooled Seats'
  | 'Remote Start'
  | 'Apple CarPlay'
  | 'Android Auto'
  | 'Premium Audio'
  | 'Third Row Seating'
  | 'Towing Package'
  | 'All-Wheel Drive'
  | 'Four-Wheel Drive';

/**
 * Filter state representing all active filters
 * AC2: Filter Modal with Multi-Select Options
 */
export interface FilterState {
  /** Price range filter [min, max] */
  priceRange?: [number, number];
  /** Vehicle makes multi-select */
  makes?: string[];
  /** Vehicle types multi-select */
  vehicleTypes?: VehicleTypeFilter[];
  /** Year range filter [min, max] */
  yearRange?: [number, number];
  /** Maximum mileage filter */
  maxMileage?: number;
  // REMOVED: features (no database support) - 2026-01-19
  /** Fuel type filter (gas, diesel, electric, hybrid) */
  fuelTypes?: string[];
  /** Transmission filter (automatic, manual, cvt) */
  transmission?: string[];
  /** Drivetrain filter (fwd, rwd, awd, 4wd) */
  drivetrain?: string[];
  /** Color filter */
  colors?: string[];
}

/**
 * Filter state with metadata for UI display
 */
export interface FilterStateWithMeta extends FilterState {
  /** Timestamp when filters were last applied */
  appliedAt?: string;
  /** Source of filters (user, conversation, auto) */
  source?: 'user' | 'conversation' | 'auto';
}

/**
 * Filter chip for displaying active filters
 * AC5: Filter Chips Display
 */
export interface FilterChip {
  /** Unique key for the filter chip */
  key: string;
  /** Display label for the chip */
  label: string;
  /** Filter category (priceRange, makes, vehicleTypes, etc.) */
  category: keyof FilterState;
  /** Value to remove when chip is clicked */
  value: unknown;
}

/**
 * Filter category configuration for filter modal
 * AC2: Filter Modal with Multi-Select Options
 */
export interface FilterCategoryConfig {
  /** Category key */
  key: keyof FilterState;
  /** Display label */
  label: string;
  /** Category type */
  type: 'range' | 'multiselect' | 'checkbox' | 'slider';
  /** Available options for multiselect/checkbox types */
  options?: Array<{ value: string; label: string; count?: number }>;
  /** Min/max for range/slider types */
  min?: number;
  max?: number;
  /** Current selected count */
  selectedCount?: number;
}

/**
 * Filter result with metadata
 */
export interface FilterResult {
  /** Filtered vehicles */
  vehicles: Vehicle[];
  /** Total count before filtering */
  totalCount: number;
  /** Count after filtering */
  filteredCount: number;
  /** Active filter count */
  activeFilterCount: number;
}

/**
 * Storage schema for filter persistence
 * AC7: Filter Persistence (30min expiry)
 */
export interface FilterStorageSchema {
  /** Filter state */
  filters: FilterState;
  /** Current sort option */
  sortBy: SortOption;
  /** Timestamp when filters were applied */
  timestamp: number;
}

/**
 * Default filter state (no filters active)
 */
export const DEFAULT_FILTER_STATE: FilterState = {};

/**
 * Default sort option (relevance to user preferences)
 */
export const DEFAULT_SORT_OPTION: SortOption = 'relevance';

/**
 * Storage key for filter persistence in sessionStorage
 * AC7: sessionStorage with 30min expiry
 */
export const FILTER_STORAGE_KEY = 'otto_vehicle_filters';

/**
 * Storage expiry time (30 minutes in milliseconds)
 * AC7: Selections clear after 30 minutes of inactivity
 */
export const FILTER_STORAGE_EXPIRY_MS = 30 * 60 * 1000;

/**
 * Available makes for filter dropdown (can be populated from backend)
 */
export const AVAILABLE_MAKES = [
  'Toyota', 'Honda', 'Ford', 'Chevrolet', 'Nissan', 'BMW',
  'Mercedes-Benz', 'Audi', 'Lexus', 'Hyundai', 'Kia', 'Subaru',
  'Volkswagen', 'Mazda', 'Jeep', 'Ram', 'GMC', 'Buick',
  'Cadillac', 'Lincoln', 'Acura', 'Infiniti', 'Volvo', 'Tesla',
] as const;

/**
 * Available fuel types for filtering
 */
export const AVAILABLE_FUEL_TYPES = [
  'Gasoline',
  'Diesel',
  'Electric',
  'Hybrid',
  'Plug-in Hybrid',
] as const;

/**
 * Available transmission types for filtering
 */
export const AVAILABLE_TRANSMISSIONS = [
  'Automatic',
  'Manual',
  'CVT',
] as const;

/**
 * Available drivetrain types for filtering
 */
export const AVAILABLE_DRIVETRAINS = [
  'FWD',    // Front-Wheel Drive
  'RWD',    // Rear-Wheel Drive
  'AWD',    // All-Wheel Drive
  '4WD',    // Four-Wheel Drive
] as const;

/**
 * Type guard to check if a value is a valid SortOption
 */
export function isValidSortOption(value: string): value is SortOption {
  return ['relevance', 'price_asc', 'price_desc', 'mileage', 'year'].includes(value);
}

/**
 * Type guard to check if filter state is empty (no active filters)
 */
export function isFilterEmpty(filters: FilterState): boolean {
  return Object.values(filters).every(
    value => value === undefined || value === null || (Array.isArray(value) && value.length === 0)
  );
}

/**
 * Count active filters in filter state
 * AC3: Filter bar shows active filter count
 */
export function countActiveFilters(filters: FilterState): number {
  let count = 0;
  for (const value of Object.values(filters)) {
    if (value === undefined || value === null) continue;
    if (Array.isArray(value)) {
      if (value.length > 0) count++;
    } else {
      count++;
    }
  }
  return count;
}

/**
 * Generate filter chips from active filters
 * AC5: Filter chips display applied filters as removable pills
 */
export function generateFilterChips(filters: FilterState): FilterChip[] {
  const chips: FilterChip[] = [];

  if (filters.priceRange) {
    const [min, max] = filters.priceRange;
    const label = max >= 100000
      ? `Price: $${(min / 1000).toFixed(0)}k+`
      : `Price: $${(min / 1000).toFixed(0)}k-$${(max / 1000).toFixed(0)}k`;
    chips.push({ key: 'priceRange', label, category: 'priceRange', value: filters.priceRange });
  }

  if (filters.makes && filters.makes.length > 0) {
    filters.makes.forEach(make => {
      chips.push({ key: `makes-${make}`, label: `Make: ${make}`, category: 'makes', value: make });
    });
  }

  if (filters.vehicleTypes && filters.vehicleTypes.length > 0) {
    filters.vehicleTypes.forEach(type => {
      chips.push({ key: `vehicleTypes-${type}`, label: `Type: ${type}`, category: 'vehicleTypes', value: type });
    });
  }

  if (filters.yearRange) {
    const [min, max] = filters.yearRange;
    const currentYear = new Date().getFullYear();
    const label = max >= currentYear
      ? `Year: ${min}+`
      : `Year: ${min}-${max}`;
    chips.push({ key: 'yearRange', label, category: 'yearRange', value: filters.yearRange });
  }

  if (filters.maxMileage !== undefined) {
    const label = filters.maxMileage >= 200000
      ? 'Mileage: Any'
      : `Mileage: <${(filters.maxMileage / 1000).toFixed(0)}k mi`;
    chips.push({ key: 'maxMileage', label, category: 'maxMileage', value: filters.maxMileage });
  }

  if (filters.fuelTypes && filters.fuelTypes.length > 0) {
    filters.fuelTypes.forEach(fuel => {
      chips.push({ key: `fuelTypes-${fuel}`, label: `Fuel: ${fuel}`, category: 'fuelTypes', value: fuel });
    });
  }

  if (filters.transmission && filters.transmission.length > 0) {
    filters.transmission.forEach(trans => {
      chips.push({ key: `transmission-${trans}`, label: `Trans: ${trans}`, category: 'transmission', value: trans });
    });
  }

  if (filters.drivetrain && filters.drivetrain.length > 0) {
    filters.drivetrain.forEach(drive => {
      chips.push({ key: `drivetrain-${drive}`, label: `Drive: ${drive}`, category: 'drivetrain', value: drive });
    });
  }

  if (filters.colors && filters.colors.length > 0) {
    filters.colors.forEach(color => {
      chips.push({ key: `colors-${color}`, label: `Color: ${color}`, category: 'colors', value: color });
    });
  }

  return chips;
}

/**
 * Sort vehicles based on sort option
 * AC4: Intelligent Sort Options
 */
export function sortVehicles(vehicles: Vehicle[], sortBy: SortOption): Vehicle[] {
  const sorted = [...vehicles];

  switch (sortBy) {
    case 'relevance':
      // Sort by match score (highest first)
      return sorted.sort((a, b) => (b.matchScore || 0) - (a.matchScore || 0));

    case 'price_asc':
      // Sort by price (lowest first)
      return sorted.sort((a, b) => (a.price || 0) - (b.price || 0));

    case 'price_desc':
      // Sort by price (highest first)
      return sorted.sort((a, b) => (b.price || 0) - (a.price || 0));

    case 'mileage':
      // Sort by mileage (lowest first)
      return sorted.sort((a, b) => (a.mileage || 0) - (b.mileage || 0));

    case 'year':
      // Sort by year (newest first)
      return sorted.sort((a, b) => b.year - a.year);

    default:
      return sorted;
  }
}

/**
 * Filter vehicles based on filter state
 * AC3: Grid updates to show only matching vehicles
 */
export function filterVehicles(vehicles: Vehicle[], filters: FilterState): Vehicle[] {
  return vehicles.filter(vehicle => {
    // Price range filter
    if (filters.priceRange) {
      const [min, max] = filters.priceRange;
      const price = vehicle.price || 0;
      if (price < min || price > max) return false;
    }

    // Makes filter
    if (filters.makes && filters.makes.length > 0) {
      if (!filters.makes.includes(vehicle.make)) return false;
    }

    // Vehicle types filter (body_type)
    if (filters.vehicleTypes && filters.vehicleTypes.length > 0) {
      if (!vehicle.body_type || !filters.vehicleTypes.some(type =>
        vehicle.body_type?.toLowerCase().includes(type.toLowerCase())
      )) return false;
    }

    // Year range filter
    if (filters.yearRange) {
      const [min, max] = filters.yearRange;
      if (vehicle.year < min || vehicle.year > max) return false;
    }

    // Max mileage filter
    if (filters.maxMileage !== undefined) {
      const mileage = vehicle.mileage || 0;
      if (mileage > filters.maxMileage) return false;
    }

    // Fuel type filter
    if (filters.fuelTypes && filters.fuelTypes.length > 0) {
      if (!vehicle.fuel_type || !filters.fuelTypes.some(fuel =>
        vehicle.fuel_type?.toLowerCase().includes(fuel.toLowerCase())
      )) return false;
    }

    // Transmission filter
    if (filters.transmission && filters.transmission.length > 0) {
      if (!vehicle.transmission || !filters.transmission.some(trans =>
        vehicle.transmission?.toLowerCase().includes(trans.toLowerCase())
      )) return false;
    }

    // Drivetrain filter
    if (filters.drivetrain && filters.drivetrain.length > 0) {
      if (!vehicle.drivetrain || !filters.drivetrain.some(drive =>
        vehicle.drivetrain?.toLowerCase().includes(drive.toLowerCase())
      )) return false;
    }

    // Color filter
    if (filters.colors && filters.colors.length > 0) {
      if (!vehicle.color || !filters.colors.some(color =>
        vehicle.color?.toLowerCase().includes(color.toLowerCase())
      )) return false;
    }

    return true;
  });
}

/**
 * Apply filters and sort to vehicles
 * AC3: Real-Time Filter Application
 * AC4: Sorting applied within current filter constraints
 */
export function applyFiltersAndSort(
  vehicles: Vehicle[],
  filters: FilterState,
  sortBy: SortOption
): FilterResult {
  // First filter
  const filteredVehicles = filterVehicles(vehicles, filters);

  // Then sort the filtered results
  const sortedVehicles = sortVehicles(filteredVehicles, sortBy);

  return {
    vehicles: sortedVehicles,
    totalCount: vehicles.length,
    filteredCount: sortedVehicles.length,
    activeFilterCount: countActiveFilters(filters),
  };
}
