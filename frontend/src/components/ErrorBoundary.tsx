import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // В реальном проекте здесь был бы Sentry/Datadog. Сейчас — консоль.
    console.error('ErrorBoundary caught:', error, info);
  }

  reset = () => {
    this.setState({ error: null });
  };

  render() {
    if (!this.state.error) return this.props.children;

    if (this.props.fallback) return this.props.fallback;

    return (
      <div
        style={{
          padding: 32,
          color: 'var(--text-1, #fff)',
          background: 'var(--bg, #111)',
          minHeight: '100vh',
        }}
      >
        <h1>Что-то пошло не так</h1>
        <p style={{ opacity: 0.7 }}>{this.state.error.message}</p>
        <button
          onClick={this.reset}
          style={{
            marginTop: 16,
            padding: '8px 16px',
            borderRadius: 8,
            border: 'none',
            cursor: 'pointer',
          }}
        >
          Попробовать снова
        </button>
      </div>
    );
  }
}
