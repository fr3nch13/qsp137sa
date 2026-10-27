// Load the baseline network into the shared branded application shell.
import { useEffect, useState } from "react";
import { fetchNetwork, type Network } from "./api";
import { NetworkSummary, NetworkWorkspace } from "./NetworkWorkspace";

type NetworkState =
  | { status: "loading" }
  | { status: "ready"; network: Network }
  | { status: "error"; message: string };

export function App() {
  const [state, setState] = useState<NetworkState>({ status: "loading" });
  useEffect(() => {
    const controller = new AbortController();
    fetchNetwork(controller.signal).then(
      (network) => {
        if (!controller.signal.aborted) {
          setState({ status: "ready", network });
        }
      },
      (error: unknown) => {
        if (!controller.signal.aborted) {
          setState({
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
        <div className="workspace-heading workspace-columns">
          <section className="welcome" aria-labelledby="welcome-heading">
            <h2 id="welcome-heading">Network workspace</h2>
            <p>
              Explore baseline traffic and the impact of losing network
              elements.
            </p>
          </section>
          {state.status === "ready" && (
            <NetworkSummary network={state.network} />
          )}
        </div>
        <section
          className="network-workspace"
          aria-label="Network findings"
          aria-busy={state.status === "loading"}
        >
          {state.status === "error" ? (
            <p role="alert">
              Could not load the network. {state.message} Refresh to try again.
            </p>
          ) : state.status === "ready" ? (
            <NetworkWorkspace network={state.network} />
          ) : (
            <p role="status">Loading network and baseline findings...</p>
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
