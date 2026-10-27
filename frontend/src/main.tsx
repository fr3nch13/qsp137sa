// Mount the browser application into the authored HTML entry document.
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "leaflet/dist/leaflet.css";
import "./styles.css";

// Trackpad pinches arrive as Ctrl+wheel; leave normal scrolling and keyboard zoom intact.
document.addEventListener(
  "wheel",
  (event) => {
    if (event.ctrlKey) event.preventDefault();
  },
  { passive: false },
);

const root = document.getElementById("root");
if (!root) {
  throw new Error("LinkScope could not start: the root element is missing.");
}
createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
