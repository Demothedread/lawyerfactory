import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./App.css";
import App from "./App.jsx";
import { ToastProvider } from "./components/feedback/Toast";
import "./components/layout/ContextOverlay.css";
import "./components/layout/GridContainer.css";
import "./components/layout/NestedAccordion.css";
import "./index.css";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <ToastProvider>
      <App />
    </ToastProvider>
  </StrictMode>
);
