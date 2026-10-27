// Initial frontend shell; network-analysis functionality is not implemented yet.
import { useEffect, useState } from "react";
import { fetchGreeting } from "./api";

type Greeting =
  | { status: "loading" }
  | { status: "ready"; message: string }
  | { status: "error"; message: string };

export function App() {
  const [greeting, setGreeting] = useState<Greeting>({ status: "loading" });
  useEffect(() => {
    const controller = new AbortController();
    fetchGreeting(controller.signal).then(
      (message) => {
        if (!controller.signal.aborted) {
          setGreeting({ status: "ready", message });
        }
      },
      (error: unknown) => {
        if (!controller.signal.aborted) {
          setGreeting({
            status: "error",
            message:
              error instanceof Error ? error.message : "API request failed.",
          });
        }
      },
    );
    return () => controller.abort();
  }, []);

  return (
    <div className="app-shell">
      <header className="site-header">
        <div className="layout-width brand">
          <img src="/assets/logo.svg" alt="" width="44" height="44" />
          <div>
            <h1>LinkScope</h1>
            <p>Network resilience analysis</p>
          </div>
        </div>
      </header>
      <main className="layout-width">
        <section className="welcome" aria-labelledby="welcome-heading">
          <h2 id="welcome-heading">Network workspace</h2>
          <p>
            Network analysis and the interactive map are not implemented yet.
          </p>
        </section>
        <section className="api-status" aria-label="API connection">
          {greeting.status === "error" ? (
            <p role="alert">
              Could not load the API greeting: {greeting.message}
            </p>
          ) : (
            <p role="status">
              {greeting.status === "ready"
                ? greeting.message
                : "Loading API greeting..."}
            </p>
          )}
        </section>
      </main>
      <footer className="site-footer">
        <div className="layout-width">
          <p>Quantum Sky · Project 137 · LinkScope</p>
          <p>Local demonstration</p>
        </div>
      </footer>
    </div>
  );
}
