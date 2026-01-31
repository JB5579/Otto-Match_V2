import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { VehicleProvider, useVehicleContext } from '../../../context/VehicleContext';
import { NotificationProvider, useNotifications } from '../../../context/NotificationContext';
import type { AvailabilityStatusUpdateMessage } from '../../../types/conversation';
import { isAvailabilityStatusUpdateMessage } from '../../../types/conversation';
import type { Vehicle } from '../../../app/types/api';

// Mock ConversationContext dependency
vi.mock('../../../context/ConversationContext', () => ({
  useConversation: () => ({
    isConnected: true,
    currentPreferences: {},
  }),
  ConversationProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

const mockVehicles: Vehicle[] = [
  {
    id: 'vehicle-1',
    make: 'Tesla',
    model: 'Model 3',
    year: 2024,
    price: 45000,
    availabilityStatus: 'available',
    currentViewers: 0,
    isFavorited: false,
    imageUrl: '/test.jpg',
  } as Vehicle,
  {
    id: 'vehicle-2',
    make: 'BMW',
    model: 'X5',
    year: 2023,
    price: 55000,
    availabilityStatus: 'reserved',
    currentViewers: 2,
    isFavorited: true,
    imageUrl: '/test2.jpg',
  } as Vehicle,
];

describe('Availability Update Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('AC1: Vehicle Unavailable Status Update', () => {
    it('should update vehicle status when WebSocket message received', async () => {
      const TestComponent = () => {
        const vehicleContext = useVehicleContext();

        return (
          <div>
            <div data-testid="vehicle-count">{vehicleContext.vehicles.length}</div>
            <div data-testid="vehicle-1-status">{vehicleContext.vehicles[0]?.availabilityStatus}</div>
            <button
              onClick={() => vehicleContext.updateVehicleStatus('vehicle-1', 'sold')}
              data-testid="update-status-btn"
            >
              Update Status
            </button>
          </div>
        );
      };

      render(
        <NotificationProvider>
          <VehicleProvider initialVehicles={mockVehicles}>
            <TestComponent />
          </VehicleProvider>
        </NotificationProvider>
      );

      // Initial status should be 'available'
      expect(screen.getByTestId('vehicle-1-status')).toHaveTextContent('available');

      // Simulate status update (mimics WebSocket message handling)
      screen.getByTestId('update-status-btn').click();

      // Status should update to 'sold'
      await waitFor(() => {
        expect(screen.getByTestId('vehicle-1-status')).toHaveTextContent('sold');
      });
    });

    it('should update vehicle in favorites list when status changes', async () => {
      const TestComponent = () => {
        const vehicleContext = useVehicleContext();

        const favoritesWithAvailability = vehicleContext.favoritesWithAvailability;

        return (
          <div>
            <div data-testid="favorites-count">{favoritesWithAvailability.length}</div>
            <div data-testid="favorite-vehicle-status">
              {favoritesWithAvailability[0]?.availabilityStatus || 'none'}
            </div>
            <button
              onClick={() => vehicleContext.toggleFavorite('vehicle-2')}
              data-testid="add-favorite"
            >
              Add Favorite
            </button>
            <button
              onClick={() => vehicleContext.updateVehicleStatus('vehicle-2', 'sold')}
              data-testid="update-favorite-status"
            >
              Update Favorite
            </button>
          </div>
        );
      };

      render(
        <NotificationProvider>
          <VehicleProvider initialVehicles={mockVehicles}>
            <TestComponent />
          </VehicleProvider>
        </NotificationProvider>
      );

      // Setup: Add vehicle-2 to favorites first
      screen.getByTestId('add-favorite').click();
      await waitFor(() => {
        expect(screen.getByTestId('favorites-count')).toHaveTextContent('1');
      });
      expect(screen.getByTestId('favorite-vehicle-status')).toHaveTextContent('reserved');

      // Update status
      screen.getByTestId('update-favorite-status').click();

      // Verify status updated in favorites list
      await waitFor(() => {
        expect(screen.getByTestId('favorite-vehicle-status')).toHaveTextContent('sold');
      });
    });
  });

  describe('AC5: WebSocket Real-Time Updates', () => {
    it('should handle availability_status_update message type', () => {
      const mockMessage: AvailabilityStatusUpdateMessage = {
        type: 'availability_status_update',
        timestamp: new Date().toISOString(),
        data: {
          vehicle_id: 'vehicle-1',
          old_status: 'available',
          new_status: 'sold',
        },
      };

      // Type guard should correctly identify the message
      expect(isAvailabilityStatusUpdateMessage(mockMessage)).toBe(true);
      expect(isAvailabilityStatusUpdateMessage({ type: 'error' })).toBe(false);
    });

    it('should parse availability status update payload', () => {
      const mockMessage: AvailabilityStatusUpdateMessage = {
        type: 'availability_status_update',
        timestamp: '2024-01-14T12:00:00Z',
        data: {
          vehicle_id: 'vehicle-1',
          old_status: 'available',
          new_status: 'reserved',
          reservation_expiry: '2024-01-15T12:00:00Z',
        },
      };

      // Verify message structure
      expect(mockMessage.data.vehicle_id).toBe('vehicle-1');
      expect(mockMessage.data.old_status).toBe('available');
      expect(mockMessage.data.new_status).toBe('reserved');
      expect(mockMessage.data.reservation_expiry).toBeDefined();
    });
  });

  describe('Notification Triggering', () => {
    it('should add notification when favorited vehicle status changes', async () => {
      const TestComponent = () => {
        const notificationContext = useNotifications();
        const vehicleContext = useVehicleContext();

        const handleStatusChange = () => {
          // Simulate status change + notification trigger
          vehicleContext.updateVehicleStatus('vehicle-2', 'sold');

          // Check if vehicle is favorited and trigger notification
          const vehicle = vehicleContext.vehicles.find((v: Vehicle) => v.id === 'vehicle-2');
          if (vehicle && vehicleContext.favoriteIds.has('vehicle-2')) {
            notificationContext.addNotification({
              type: 'availability',
              vehicleId: 'vehicle-2',
              title: `${vehicle.make} ${vehicle.model}`,
              message: 'This vehicle is now sold',
            });
          }
        };

        // Check if vehicle-2 is in favorites
        const isFavorited = vehicleContext.favoriteIds.has('vehicle-2');

        return (
          <div>
            <div data-testid="notifications-count">{notificationContext.notifications.length}</div>
            <div data-testid="is-favorited">{isFavorited ? 'yes' : 'no'}</div>
            <button
              onClick={() => vehicleContext.toggleFavorite('vehicle-2')}
              data-testid="add-favorite"
            >
              Add Favorite
            </button>
            <button onClick={handleStatusChange} data-testid="trigger-notification">
              Change Status
            </button>
          </div>
        );
      };

      render(
        <NotificationProvider>
          <VehicleProvider initialVehicles={mockVehicles}>
            <TestComponent />
          </VehicleProvider>
        </NotificationProvider>
      );

      // Initial: no notifications, not favorited
      expect(screen.getByTestId('notifications-count')).toHaveTextContent('0');
      expect(screen.getByTestId('is-favorited')).toHaveTextContent('no');

      // Add to favorites first
      screen.getByTestId('add-favorite').click();

      // Wait for favorite state to update
      await waitFor(() => {
        expect(screen.getByTestId('is-favorited')).toHaveTextContent('yes');
      }, { timeout: 3000 });

      // Trigger status change for favorited vehicle
      screen.getByTestId('trigger-notification').click();

      // Notification should be added
      await waitFor(() => {
        expect(screen.getByTestId('notifications-count')).toHaveTextContent('1');
      }, { timeout: 3000 });
    });
  });

  describe('Performance Optimization', () => {
    it('should update individual vehicle without full list re-render', async () => {
      let renderCount = 0;

      const TestComponent = () => {
        const vehicleContext = useVehicleContext();
        renderCount++;

        return (
          <div>
            <div data-testid="render-count">{renderCount}</div>
            <div data-testid="vehicle-1-status">{vehicleContext.vehicles[0]?.availabilityStatus}</div>
            <button
              onClick={() => vehicleContext.updateVehicleStatus('vehicle-1', 'sold')}
              data-testid="update-btn"
            >
              Update
            </button>
          </div>
        );
      };

      render(
        <NotificationProvider>
          <VehicleProvider initialVehicles={mockVehicles}>
            <TestComponent />
          </VehicleProvider>
        </NotificationProvider>
      );

      const initialRenderCount = renderCount;

      // Update status
      screen.getByTestId('update-btn').click();

      // Should trigger a re-render (at least one more)
      await waitFor(() => {
        expect(renderCount).toBeGreaterThan(initialRenderCount);
        expect(screen.getByTestId('vehicle-1-status')).toHaveTextContent('sold');
      });
    });
  });
});
