import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { NotificationProvider, useNotifications } from '../../../context/NotificationContext';

describe('NotificationContext', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    vi.clearAllTimers();
  });

  describe('AC4: In-App Notification System', () => {
    it('should add notification to queue', async () => {
      const TestComponent = () => {
        const { notifications, addNotification } = useNotifications();

        return (
          <div>
            <div data-testid="notification-count">{notifications.length}</div>
            <button
              onClick={() =>
                addNotification({
                  type: 'availability',
                  vehicleId: 'vehicle-1',
                  title: '2024 Tesla Model 3',
                  message: 'This vehicle is now available!',
                })
              }
              data-testid="add-notification"
            >
              Add Notification
            </button>
          </div>
        );
      };

      render(
        <NotificationProvider>
          <TestComponent />
        </NotificationProvider>
      );

      // Initially no notifications
      expect(screen.getByTestId('notification-count')).toHaveTextContent('0');

      // Add notification
      screen.getByTestId('add-notification').click();

      // Should have one notification (wait for state update)
      await waitFor(() => {
        expect(screen.getByTestId('notification-count')).toHaveTextContent('1');
      });
    });

    it('should dismiss notification', async () => {
      let notificationIdToDismiss = '';

      const TestComponent = () => {
        const { notifications, addNotification, dismissNotification } = useNotifications();

        // Capture the ID when notification is added
        const handleAdd = () => {
          const id = `notification-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
          notificationIdToDismiss = id;
          addNotification({
            type: 'availability',
            vehicleId: 'vehicle-1',
            title: '2024 Tesla Model 3',
            message: 'Vehicle is available',
          });
        };

        return (
          <div>
            <div data-testid="notification-count">{notifications.filter((n) => !n.dismissed).length}</div>
            <button onClick={handleAdd} data-testid="add-notification">
              Add
            </button>
            <button onClick={() => {
              // Use the most recent notification ID
              const activeNotifs = notifications.filter((n) => !n.dismissed);
              if (activeNotifs.length > 0) {
                dismissNotification(activeNotifs[0].id);
              }
            }} data-testid="dismiss-notification">
              Dismiss
            </button>
          </div>
        );
      };

      render(
        <NotificationProvider>
          <TestComponent />
        </NotificationProvider>
      );

      // Add notification
      screen.getByTestId('add-notification').click();
      await waitFor(() => {
        expect(screen.getByTestId('notification-count')).toHaveTextContent('1');
      });

      // Dismiss notification
      screen.getByTestId('dismiss-notification').click();
      await waitFor(() => {
        expect(screen.getByTestId('notification-count')).toHaveTextContent('0');
      }, { timeout: 3000 });
    });

    it('should dismiss all notifications', async () => {
      const TestComponent = () => {
        const { notifications, addNotification, dismissAll } = useNotifications();

        return (
          <div>
            <div data-testid="notification-count">{notifications.filter((n) => !n.dismissed).length}</div>
            <button
              onClick={() => {
                // Add with unique vehicleIds to avoid collapsing
                addNotification({ type: 'availability', vehicleId: 'v1', title: 'Vehicle 1', message: 'Available' });
                addNotification({ type: 'availability', vehicleId: 'v2', title: 'Vehicle 2', message: 'Sold' });
                addNotification({ type: 'availability', vehicleId: 'v3', title: 'Vehicle 3', message: 'Reserved' });
              }}
              data-testid="add-multiple"
            >
              Add Multiple
            </button>
            <button onClick={() => dismissAll()} data-testid="dismiss-all">
              Dismiss All
            </button>
          </div>
        );
      };

      render(
        <NotificationProvider>
          <TestComponent />
        </NotificationProvider>
      );

      // Add multiple notifications
      screen.getByTestId('add-multiple').click();
      await waitFor(() => {
        expect(screen.getByTestId('notification-count')).toHaveTextContent('3');
      }, { timeout: 3000 });

      // Dismiss all
      screen.getByTestId('dismiss-all').click();
      await waitFor(() => {
        expect(screen.getByTestId('notification-count')).toHaveTextContent('0');
      }, { timeout: 3000 });
    });

    it('should queue multiple notifications', async () => {
      const TestComponent = () => {
        const { notifications, addNotification } = useNotifications();

        return (
          <div>
            <div data-testid="notification-count">{notifications.length}</div>
            <button
              onClick={() => {
                for (let i = 1; i <= 5; i++) {
                  addNotification({
                    type: 'availability',
                    vehicleId: `vehicle-${i}`,
                    title: `Vehicle ${i}`,
                    message: `Status changed`,
                  });
                }
              }}
              data-testid="add-queue"
            >
              Add Queue
            </button>
          </div>
        );
      };

      render(
        <NotificationProvider>
          <TestComponent />
        </NotificationProvider>
      );

      // Add queue of notifications
      screen.getByTestId('add-queue').click();
      await waitFor(() => {
        expect(screen.getByTestId('notification-count')).toHaveTextContent('5');
      });
    });
  });

  describe('Notification Filtering', () => {
    it('should filter notifications by type', async () => {
      const TestComponent = () => {
        const { notifications, addNotification, notificationsByType } = useNotifications();
        const availabilityNotifications = notificationsByType('availability');

        return (
          <div>
            <div data-testid="total-count">{notifications.length}</div>
            <div data-testid="availability-count">{availabilityNotifications.length}</div>
            <button
              onClick={() => {
                // Add with unique vehicleIds to avoid collapsing
                addNotification({ type: 'availability', vehicleId: 'v1', title: 'A1', message: 'M1' });
                addNotification({ type: 'price', vehicleId: 'p1', title: 'P1', message: 'M2' });
                addNotification({ type: 'availability', vehicleId: 'v2', title: 'A2', message: 'M3' });
              }}
              data-testid="add-mixed"
            >
              Add Mixed
            </button>
          </div>
        );
      };

      render(
        <NotificationProvider>
          <TestComponent />
        </NotificationProvider>
      );

      // Add mixed type notifications
      screen.getByTestId('add-mixed').click();

      // Should have 3 total, 2 availability
      await waitFor(() => {
        expect(screen.getByTestId('total-count')).toHaveTextContent('3');
        expect(screen.getByTestId('availability-count')).toHaveTextContent('2');
      }, { timeout: 3000 });
    });
  });

  describe('Duplicate Notification Collapsing', () => {
    it('should collapse similar notifications within 5 seconds', async () => {
      const TestComponent = () => {
        const { notifications, addNotification } = useNotifications();

        return (
          <div>
            <div data-testid="notification-count">{notifications.length}</div>
            <button
              onClick={() => {
                // Add same notification twice quickly
                addNotification({
                  type: 'availability',
                  vehicleId: 'vehicle-1',
                  title: '2024 Tesla Model 3',
                  message: 'Available',
                });
                addNotification({
                  type: 'availability',
                  vehicleId: 'vehicle-1',
                  title: '2024 Tesla Model 3',
                  message: 'Available',
                });
              }}
              data-testid="add-duplicate"
            >
              Add Duplicate
            </button>
          </div>
        );
      };

      render(
        <NotificationProvider>
          <TestComponent />
        </NotificationProvider>
      );

      // Add duplicate notification
      screen.getByTestId('add-duplicate').click();

      // Should only have 1 notification (duplicate collapsed)
      await waitFor(() => {
        expect(screen.getByTestId('notification-count')).toHaveTextContent('1');
      });
    });
  });

  describe('LocalStorage Persistence', () => {
    it('should persist notifications to localStorage', async () => {
      const TestComponent = () => {
        const { addNotification } = useNotifications();

        return (
          <button
            onClick={() =>
              addNotification({
                type: 'availability',
                title: 'Test Vehicle',
                message: 'Available',
              })
            }
            data-testid="add-notification"
          >
            Add
          </button>
        );
      };

      render(
        <NotificationProvider>
          <TestComponent />
        </NotificationProvider>
      );

      // Add notification
      screen.getByTestId('add-notification').click();

      // Wait for localStorage to be updated (useEffect)
      await waitFor(() => {
        // Should be persisted to localStorage
        const stored = localStorage.getItem('otto-ai-notifications');
        expect(stored).toBeTruthy();

        const parsed = JSON.parse(stored!);
        expect(parsed).toHaveLength(1);
        expect(parsed[0].title).toBe('Test Vehicle');
      });
    });

    it('should load notifications from localStorage on mount', () => {
      // Pre-populate localStorage
      const mockNotifications = [
        {
          id: 'notification-1',
          type: 'availability',
          title: 'Pre-existing Notification',
          message: 'Test',
          timestamp: new Date().toISOString(),
          dismissed: false,
        },
      ];
      localStorage.setItem('otto-ai-notifications', JSON.stringify(mockNotifications));

      const TestComponent = () => {
        const { notifications } = useNotifications();
        return <div data-testid="notification-count">{notifications.length}</div>;
      };

      render(
        <NotificationProvider>
          <TestComponent />
        </NotificationProvider>
      );

      // Should load notification from localStorage
      expect(screen.getByTestId('notification-count')).toHaveTextContent('1');
    });
  });
});
