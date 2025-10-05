import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

// Global styles first
import "./App.css";
import "./index.css";

// Component-specific styles
import "./components/layout/ContextOverlay.css";
import "./components/layout/GridContainer.css";
import "./components/layout/NestedAccordion.css";

// Components
import App from "./App.jsx";
import { ToastProvider } from "./components/feedback/Toast";

// Error boundary wrapper
const root = createRoot(document.getElementById("root"));

root.render(
  <StrictMode>
    <ToastProvider>
      <App />
    </ToastProvider>
  </StrictMode>
);
