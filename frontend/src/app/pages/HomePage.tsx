import { useAuth } from '../contexts/AuthContext';
import {
  VehicleGrid,
  VehicleGridErrorBoundary,
  useVehicleGrid,
} from '../../components/vehicle-grid';

export function HomePage() {
  const { user, signOut } = useAuth();

  const {
    vehicles,
    loading,
    error,
    totalCount,
    hasMore,
    loadMore,
    favoriteVehicle,
    compareVehicle,
    submitFeedback,
  } = useVehicleGrid({
    pageSize: 50,
    autoFetch: true,
  });

  const handleVehicleClick = (vehicle: any) => {
    console.log('Vehicle clicked:', vehicle);
    // TODO: Open vehicle detail modal (Story 3-12)
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="border-b border-gray-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 justify-between">
            <div className="flex">
              <div className="flex flex-shrink-0 items-center">
                <h1 className="text-xl font-bold text-gray-900">Otto.AI</h1>
              </div>
            </div>
            <div className="flex items-center">
              {user ? (
                <>
                  <span className="mr-4 text-sm text-gray-700">{user.email}</span>
                  <button
                    onClick={signOut}
                    className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
                  >
                    Sign Out
                  </button>
                </>
              ) : (
                <a
                  href="/login"
                  className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
                >
                  Sign In
                </a>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="bg-gradient-to-r from-blue-600 to-cyan-500 py-12">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="text-4xl font-bold tracking-tight text-white sm:text-5xl">
              Find Your Perfect Vehicle
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-lg text-blue-100">
              AI-powered semantic search with personalized recommendations from Otto
            </p>
            <div className="mt-6 flex justify-center gap-4 text-sm text-blue-100">
              <div className="flex items-center gap-2">
                <span className="font-semibold">{totalCount}</span>
                <span>vehicles available</span>
              </div>
              {vehicles.length > 0 && (
                <div className="flex items-center gap-2">
                  <span className="font-semibold">{vehicles.length}</span>
                  <span>shown</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Vehicle Grid */}
      <main className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <VehicleGridErrorBoundary>
          <VehicleGrid
            vehicles={vehicles}
            loading={loading}
            error={error}
            onFavorite={favoriteVehicle}
            onCompare={compareVehicle}
            onFeedback={submitFeedback}
            onVehicleClick={handleVehicleClick}
            emptyMessage="No vehicles found. Check back soon for new inventory!"
          />
        </VehicleGridErrorBoundary>

        {/* Load More Button */}
        {hasMore && !loading && vehicles.length > 0 && (
          <div className="my-8 flex justify-center">
            <button
              onClick={() => loadMore()}
              className="rounded-md bg-blue-600 px-8 py-3 text-base font-medium text-white hover:bg-blue-700 transition-colors"
            >
              Load More Vehicles
            </button>
          </div>
        )}
      </main>

      {/* Feature Highlights (below grid) */}
      <div className="bg-white border-t border-gray-200 py-12">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 gap-8 sm:grid-cols-3">
            <div className="text-center">
              <div className="text-4xl mb-4">🔍</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Semantic Search
              </h3>
              <p className="text-sm text-gray-600">
                Search using natural language like "family SUV under $30k"
              </p>
            </div>

            <div className="text-center">
              <div className="text-4xl mb-4">🤖</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Otto AI Assistant
              </h3>
              <p className="text-sm text-gray-600">
                Get personalized recommendations based on your preferences
              </p>
            </div>

            <div className="text-center">
              <div className="text-4xl mb-4">⭐</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Match Scores
              </h3>
              <p className="text-sm text-gray-600">
                Smart scoring to find vehicles that match your needs
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
