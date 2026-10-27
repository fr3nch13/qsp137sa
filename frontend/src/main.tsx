// Mount the browser application into the authored HTML entry document.
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "./styles.css";

const root = document.getElementById("root");
if (!root) {
  throw new Error("LinkScope could not start: the root element is missing.");
}
createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
