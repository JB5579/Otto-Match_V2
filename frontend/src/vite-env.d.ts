/// <reference types="vite/client" />

// Story 3-8.15: Type declarations for vite-plugin-pwa
declare module 'virtual:pwa-register' {
  export interface RegisterSWOptions {
    onNeedRefresh?: () => void;
    onOfflineReady?: () => void;
    onRegistered?: (registration: ServiceWorkerRegistration | undefined) => void;
    onRegisterError?: (error: any) => void;
  }

  export function registerSW(options: RegisterSWOptions): (reloadPage?: boolean) => void;
}
