// Accessible single-failure controls and separate R8 demand/overload reporting.
import type { Analysis, Demand, Failure, Network } from "./api";

export function FailureControls({
  network,
  selected,
  onSelect,
  onFail,
  onRestore,
  analysis,
  pending,
  error,
}: {
  network: Network;
  selected: Failure;
  onSelect: (failure: Failure) => void;
  onFail: () => void;
  onRestore: () => void;
  analysis: Analysis;
  pending: Failure | null;
  error: string | null;
}) {
  const elements = selected.kind === "node" ? network.nodes : network.links;
  return (
    <section className="findings-panel" aria-labelledby="simulation-heading">
      <h3 id="simulation-heading">Single failure simulation</h3>
      <p>
        Fail one element at a time. Choosing another replaces the previous
        failure.
      </p>
      <div className="failure-controls">
        <label>
          Element type
          <select
            value={selected.kind}
            onChange={(event) => {
              const kind = event.target.value === "node" ? "node" : "link";
              const first = (
                kind === "node" ? network.nodes : network.links
              )[0];
              onSelect({ kind, id: first?.id ?? "" });
            }}
          >
            <option value="node">Node</option>
            <option value="link">Link</option>
          </select>
        </label>
        <label>
          Element
          <select
            value={selected.id}
            disabled={elements.length === 0}
            onChange={(event) =>
              onSelect({ ...selected, id: event.target.value })
            }
          >
            {elements.map((item) => (
              <option key={item.id} value={item.id}>
                {"source" in item
                  ? `${item.id}: ${item.source} – ${item.target}`
                  : item.id}
              </option>
            ))}
          </select>
        </label>
        <div className="failure-actions">
          <button type="button" onClick={onFail} disabled={!selected.id}>
            Fail selected
          </button>
          <button
            type="button"
            onClick={onRestore}
            disabled={!analysis.failure && !pending && !error}
          >
            Restore baseline
          </button>
        </div>
      </div>
      <p role="status">
        {pending
          ? `Analyzing failed ${pending.kind}: ${pending.id}. Previous results remain displayed.`
          : analysis.failure
            ? `Showing failed ${analysis.failure.kind}: ${analysis.failure.id}.`
            : "Showing baseline: no active failure."}
      </p>
      {error && (
        <p role="alert">
          Could not analyze the failure. {error} Previous results remain
          displayed. Try again or restore baseline.
        </p>
      )}
      <p className="scope-note">
        One request-local failure at a time; criticality markers describe
        baseline single-failure risks. Restore baseline clears the simulation
        without reloading.
      </p>
    </section>
  );
}

function DemandReport({
  title,
  demands,
}: {
  title: string;
  demands: Demand[];
}) {
  const units = demands.reduce((sum, item) => sum + item.units, 0);
  return (
    <details>
      <summary>
        {title}: {demands.length} demands · {units.toLocaleString("en-US")}{" "}
        units
      </summary>
      {demands.length === 0 ? (
        <p>None.</p>
      ) : (
        <ul className="demand-list">
          {demands.map((item) => (
            <li key={item.id}>
              {item.id}: {item.source} – {item.target} · {item.units} units
            </li>
          ))}
        </ul>
      )}
    </details>
  );
}

export function AnalysisReport({ analysis }: { analysis: Analysis }) {
  return (
    <section className="findings-panel" aria-labelledby="analysis-heading">
      <h3 id="analysis-heading">
        {analysis.failure ? "Failure impact" : "Baseline status"}
      </h3>
      <p>
        Physical network: {analysis.disconnected ? "disconnected" : "connected"}
        .
      </p>
      <DemandReport
        title="Failed-node endpoint demands"
        demands={analysis.failed_endpoint_demands}
      />
      <DemandReport
        title="Other undeliverable demands"
        demands={analysis.undeliverable}
      />
      <h4>Overloaded links ({analysis.overloaded.length})</h4>
      {analysis.overloaded.length === 0 ? (
        <p>No overloaded links.</p>
      ) : (
        <ul className="overloaded-list">
          {analysis.overloaded.map((item) => (
            <li key={item.id}>
              <strong>
                {item.id}: {item.source} – {item.target}
              </strong>
              <span>
                {item.load.toFixed(2)} / {item.capacity} units ·{" "}
                {item.utilization_percent.toFixed(2)}%
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
