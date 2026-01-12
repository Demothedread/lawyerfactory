import { createRoot } from "react-dom/client";
import { StrictMode, Suspense, Component } from "react";
import { lazy } from "react";

// Global styles only - component styles should be in their respective files
import "./App.css";
import "./index.css";

// Lazy load App for code splitting
const App = lazy(() => import("./App.jsx"));
const ToastProvider = lazy(() => import("./components/feedback/Toast").then(module => ({ default: module.ToastProvider })));

// Error Boundary Component
class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("React Error Boundary caught an error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: "2rem", textAlign: "center" }}>
          <h1>Something went wrong</h1>
          <p>{this.state.error?.message}</p>
          <button onClick={() => window.location.reload()}>Reload Application</button>
        </div>
      );
    }
    return this.props.children;
  }
}

// Loading fallback component
const LoadingFallback = () => (
  <div style={{ 
    display: "flex", 
    justifyContent: "center", 
    alignItems: "center", 
    height: "100vh" 
  }}>
    <img src="apps/ui/react-app/src/assets/briefcaselogo.png" alt="Loading Briefcaser..." />  
    <div>Loading Briefcaser...</div>
  </div>
);

const root = createRoot(document.getElementById("root"));

root.render(
  <StrictMode>
    <ErrorBoundary>
      <Suspense fallback={<LoadingFallback />}>
        <ToastProvider>
          <App />
        </ToastProvider>
      </Suspense>
    </ErrorBoundary>
  </StrictMode>
);
