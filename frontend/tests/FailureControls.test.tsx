// Check accessible selection, honest scenario status and complete R8 presentation.
import assert from "node:assert/strict";
import { test } from "node:test";
import { renderToStaticMarkup } from "react-dom/server";
import type { Analysis } from "../src/api";
import { AnalysisReport, FailureControls } from "../src/FailureControls";
import { networkFixture } from "./network-fixture";

test("controls offer every element and distinguish pending, applied and error states", () => {
  for (const kind of ["node", "link"] as const) {
    const html = renderToStaticMarkup(
      <FailureControls
        network={networkFixture}
        selected={{ kind, id: kind === "node" ? "A" : "L1" }}
        onSelect={() => {}}
        onFail={() => {}}
        onRestore={() => {}}
        analysis={networkFixture.baseline}
        pending={null}
        error={null}
      />,
    );
    for (const item of kind === "node"
      ? networkFixture.nodes
      : networkFixture.links) {
      assert.ok(html.includes(`value="${item.id}"`));
    }
    assert.match(html, /Element type/);
    assert.match(html, /Fail selected/);
    assert.match(html, /Restore baseline/);
    assert.match(html, /Showing baseline: no active failure/);
    assert.match(html, /class="failure-actions"/);
    assert.match(html, /<p class="scope-note">One request-local failure/);
    assert.ok(
      html.indexOf('role="status"') < html.indexOf('class="scope-note"'),
    );
  }
  const html = renderToStaticMarkup(
    <FailureControls
      network={networkFixture}
      selected={{ kind: "node", id: "A" }}
      onSelect={() => {}}
      onFail={() => {}}
      onRestore={() => {}}
      analysis={networkFixture.baseline}
      pending={{ kind: "node", id: "A" }}
      error="HTTP 503"
    />,
  );
  assert.match(html, /Analyzing failed node: A/);
  assert.match(html, /Previous results remain displayed/);
  assert.match(html, /role="alert"/);
  assert.match(html, /HTTP 503/);
});

test("R8 report keeps endpoint loss, other demands and every overloaded link separate", () => {
  const analysis: Analysis = {
    ...networkFixture.baseline,
    failure: { kind: "node", id: "A" },
    failed_endpoint_demands: networkFixture.demands,
    undeliverable: [{ id: "D2", source: "B", target: "C", units: 10 }],
    overloaded: [
      {
        ...networkFixture.baseline.links[0],
        load: 125,
        utilization_percent: 125,
      },
    ],
    disconnected: true,
  };
  const html = renderToStaticMarkup(<AnalysisReport analysis={analysis} />);
  assert.match(html, /Failure impact/);
  assert.match(html, /Physical network: disconnected/);
  assert.match(html, /Failed-node endpoint demands: 1 demands · 25 units/);
  assert.match(html, /Other undeliverable demands: 1 demands · 10 units/);
  assert.match(html, /D1: A – DC/);
  assert.match(html, /D2: B – C/);
  assert.match(html, /Overloaded links \(1\)/);
  assert.match(html, /125\.00 \/ 100 units · 125\.00%/);
  const baseline = renderToStaticMarkup(
    <AnalysisReport analysis={networkFixture.baseline} />,
  );
  assert.match(baseline, /Baseline status/);
  assert.match(baseline, /No overloaded links/);
});
