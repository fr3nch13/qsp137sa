// Findings are available without Leaflet initialization or online map tiles.
import assert from "node:assert/strict";
import { test } from "node:test";
import { renderToStaticMarkup } from "react-dom/server";
import { NetworkSummary, NetworkWorkspace } from "../src/NetworkWorkspace";
import { networkFixture } from "./network-fixture";

test("baseline findings show actual numbers, attribution-independent legend and reasons", () => {
  const html = renderToStaticMarkup(
    <NetworkWorkspace network={networkFixture} />,
  );
  assert.match(html, /2 nodes/);
  assert.doesNotMatch(html, /network-summary/);
  assert.match(html, /25%/);
  assert.match(html, /25 \/ 100/);
  assert.match(html, /#1 A/);
  assert.match(html, /2 nodes · 1 links/);
  assert.match(html, /Disconnects network/);
  assert.match(html, /failed-node endpoints/);
  assert.match(html, /Dashed line: critical link/);
  assert.match(html, /Critical node/);
  assert.match(html, /aria-label="European network map"/);
  assert.ok(
    html.indexOf('id="critical-heading"') <
      html.indexOf('id="traffic-heading"'),
  );
  assert.ok(
    html.indexOf('id="traffic-heading"') < html.indexOf('id="map-heading"'),
  );
  assert.match(html, /scope="col"/);
  assert.match(html, /scope="row"/);
});

test("header summary presents network totals separately from findings", () => {
  const html = renderToStaticMarkup(
    <NetworkSummary network={networkFixture} />,
  );
  assert.match(html, /2 nodes/);
  assert.match(html, /25 demand units/);
  assert.match(html, /Critical: 2 nodes · 1 links/);
});

test("empty network is explicit, not a broken map or success-shaped fallback", () => {
  const html = renderToStaticMarkup(
    <NetworkWorkspace network={{ ...networkFixture, nodes: [], links: [] }} />,
  );
  assert.match(html, /No network data is available/);
  assert.doesNotMatch(html, /network-map/);
});
