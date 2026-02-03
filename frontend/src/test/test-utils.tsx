import React from 'react';
import { render } from '@testing-library/react';
import type { RenderOptions } from '@testing-library/react';
import { AuthProvider } from '../app/contexts/AuthContext';
import { ComparisonProvider } from '../context/ComparisonContext';

interface AllTheProvidersProps {
  children: React.ReactNode;
}

function AllTheProviders({ children }: AllTheProvidersProps) {
  return (
    <AuthProvider>
      <ComparisonProvider>
        {children}
      </ComparisonProvider>
    </AuthProvider>
  );
}

function renderWithProviders(
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  return render(ui, { wrapper: AllTheProviders, ...options });
}

// Re-export everything from React Testing Library
export * from '@testing-library/react';
export { renderWithProviders as render };
