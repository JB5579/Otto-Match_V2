import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App.tsx';

// Story 3-8.15: Register Service Worker for asset caching (disabled - PWA plugin disabled)
// import { registerSW } from 'virtual:pwa-register';

// const updateSW = registerSW({
//   onNeedRefresh() {
//     // Show update prompt to user when new content is available
//     if (confirm('New content available. Reload to update?')) {
//       updateSW(true);
//     }
//   },
//   onOfflineReady() {
//     // Show offline ready notification
//     console.log('Otto.AI is ready to work offline!');
//   },
//   onRegistered(registration) {
//     // Periodically check for updates (every hour)
//     if (registration) {
//       setInterval(() => {
//         registration.update();
//       }, 60 * 60 * 1000);
//     }
//   },
//   onRegisterError(error) {
//     console.error('Service Worker registration failed:', error);
//   },
// });

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
