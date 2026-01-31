import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class VehicleGridErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('VehicleGrid Error Boundary caught an error:', error, errorInfo);

    this.setState({
      error,
      errorInfo,
    });

    // TODO: Send error to error reporting service (e.g., Sentry)
  }

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '400px',
            padding: '40px',
            textAlign: 'center',
            background: 'rgba(255, 255, 255, 0.85)',
            backdropFilter: 'blur(20px)',
            borderRadius: '12px',
            border: '1px solid rgba(255, 255, 255, 0.18)',
          }}
        >
          <div
            style={{
              fontSize: '64px',
              marginBottom: '16px',
            }}
          >
            🚗💥
          </div>

          <h3
            style={{
              fontSize: '20px',
              fontWeight: 600,
              color: '#ef4444',
              margin: '0 0 8px 0',
            }}
          >
            Something went wrong
          </h3>

          <p
            style={{
              fontSize: '14px',
              color: '#666',
              margin: '0 0 24px 0',
              maxWidth: '400px',
            }}
          >
            We encountered an error while loading the vehicle grid. Please try again or
            contact support if the problem persists.
          </p>

          <div
            style={{
              display: 'flex',
              gap: '12px',
            }}
          >
            <button
              onClick={this.handleReset}
              style={{
                padding: '10px 20px',
                borderRadius: '8px',
                border: 'none',
                background: '#0EA5E9',
                color: 'white',
                fontSize: '14px',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s ease-out',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = '#0284c7';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = '#0EA5E9';
              }}
            >
              Try Again
            </button>

            <button
              onClick={() => window.location.reload()}
              style={{
                padding: '10px 20px',
                borderRadius: '8px',
                border: '1px solid rgba(0, 0, 0, 0.2)',
                background: 'white',
                color: '#333',
                fontSize: '14px',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s ease-out',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = '#f5f5f5';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'white';
              }}
            >
              Reload Page
            </button>
          </div>

          {/* Error Details (development only) */}
          {import.meta.env.DEV && this.state.error && (
            <details
              style={{
                marginTop: '24px',
                padding: '16px',
                background: 'rgba(0, 0, 0, 0.04)',
                borderRadius: '8px',
                textAlign: 'left',
                fontSize: '12px',
                color: '#666',
                maxWidth: '600px',
              }}
            >
              <summary
                style={{
                  cursor: 'pointer',
                  fontWeight: 600,
                  marginBottom: '8px',
                  color: '#333',
                }}
              >
                Error Details (Development)
              </summary>
              <pre
                style={{
                  margin: 0,
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
              >
                {this.state.error.toString()}
                {this.state.errorInfo?.componentStack}
              </pre>
            </details>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

export default VehicleGridErrorBoundary;
