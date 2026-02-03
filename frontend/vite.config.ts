import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
// import { visualizer } from 'rollup-plugin-visualizer'; // Disabled: package not installed
// import { VitePWA } from 'vite-plugin-pwa'; // Disabled: peer dependency conflict with vite 7

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    // Story 3-8.16: Bundle analyzer plugin (disabled - requires rollup-plugin-visualizer)
    // visualizer({
    //   open: false,
    //   gzipSize: true,
    //   brotliSize: true,
    //   filename: 'bundle-analysis.html',
    // }),
    // Story 3-8.14: PWA plugin for Service Worker asset caching (disabled - vite 7 incompatibility)
    // VitePWA({
    //   registerType: 'autoUpdate',
    //   includeAssets: ['favicon.ico', 'robots.txt', 'apple-touch-icon.png'],
    //   manifest: {
    //     name: 'Otto.AI - Intelligent Vehicle Discovery',
    //     short_name: 'Otto.AI',
    //     description: 'AI-powered vehicle discovery platform',
    //     theme_color: '#0EA5E9',
    //     background_color: '#ffffff',
    //     display: 'standalone',
    //     icons: [
    //       {
    //         src: '/icon-192x192.png',
    //         sizes: '192x192',
    //         type: 'image/png',
    //       },
    //       {
    //         src: '/icon-512x512.png',
    //         sizes: '512x512',
    //         type: 'image/png',
    //       },
    //     ],
    //   },
    //   workbox: {
    //     // Story 3-8.14: Asset caching strategies
    //     runtimeCaching: [
    //       {
    //         // Cache API responses
    //         urlPattern: /^https:\/\/.*\/api\/.*/i,
    //         handler: 'NetworkFirst',
    //         options: {
    //           cacheName: 'api-cache',
    //           expiration: {
    //             maxEntries: 50,
    //             maxAgeSeconds: 5 * 60, // 5 minutes
    //           },
    //           cacheableResponse: {
    //             statuses: [0, 200],
    //           },
    //         },
    //       },
    //       {
    //         // Cache images with StaleWhileRevalidate
    //         urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp)$/i,
    //         handler: 'CacheFirst',
    //         options: {
    //           cacheName: 'image-cache',
    //           expiration: {
    //             maxEntries: 100,
    //             maxAgeSeconds: 30 * 24 * 60 * 60, // 30 days
    //           },
    //         },
    //       },
    //       {
    //         // Cache static assets
    //         urlPattern: /\.(?:js|css|woff2?|ttf|otf)$/i,
    //         handler: 'StaleWhileRevalidate',
    //         options: {
    //           cacheName: 'static-assets',
    //           expiration: {
    //             maxEntries: 100,
    //             maxAgeSeconds: 7 * 24 * 60 * 60, // 7 days
    //           },
    //         },
    //       },
    //     ],
    //   },
    // }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  // Story 3-8.3: Manual code splitting strategy
  build: {
    rollupOptions: {
      output: {
        // Story 3-8.3: Separate vendor chunks for better caching
        manualChunks: (id) => {
          // Vendor chunks - separate large libraries
          if (id.includes('node_modules')) {
            // Framer Motion
            if (id.includes('framer-motion')) {
              return 'framer-motion';
            }
            // Radix UI
            if (id.includes('@radix-ui')) {
              return 'radix-ui';
            }
            // React
            if (id.includes('react') || id.includes('react-dom')) {
              return 'react';
            }
            // All other node_modules
            return 'vendor';
          }

          // Vehicle detail modal (Story 3-8.2)
          if (id.includes('VehicleDetailModal')) {
            return 'vehicle-detail-modal';
          }

          // Comparison view (Story 3-8.2)
          if (id.includes('ComparisonView')) {
            return 'comparison-view';
          }

          // Otto chat components
          if (id.includes('OttoChatWidget') || id.includes('otto-chat')) {
            return 'otto-chat';
          }

          // Filter components
          if (id.includes('Filter')) {
            return 'filters';
          }

          // Vehicle grid components
          if (id.includes('VehicleGrid') || id.includes('VehicleCard')) {
            return 'vehicle-grid';
          }

          // Default: include in main chunk
          return 'index';
        },
        // Story 3-8.3: Chunk file naming
        chunkFileNames: 'assets/[name]-[hash].js',
        entryFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]',
      },
    },
    // Story 3-8.3: Chunk size warnings
    chunkSizeWarningLimit: 500,
  },
});
