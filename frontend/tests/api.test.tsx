// Verify network response validation before data reaches the map.
import assert from "node:assert/strict";
import { test } from "node:test";
import { fetchNetwork } from "../src/api";
import { networkFixture } from "./network-fixture";

test("network data comes from the same-origin API with cancellation", async (t) => {
  const controller = new AbortController();
  t.mock.method(
    globalThis,
    "fetch",
    async (url: RequestInfo | URL, options?: RequestInit) => {
      assert.equal(url, "/api/network");
      assert.equal(options?.signal, controller.signal);
      return Response.json(networkFixture);
    },
  );
  assert.deepEqual(await fetchNetwork(controller.signal), networkFixture);
});

test("network rejects HTTP, network, JSON and invalid contract responses", async (t) => {
  const mock = t.mock.method(globalThis, "fetch");
  const invalid = [
    { ...networkFixture, criticality: [] },
    {
      ...networkFixture,
      nodes: [...networkFixture.nodes, networkFixture.nodes[0]],
    },
    {
      ...networkFixture,
      nodes: [{ ...networkFixture.nodes[0], latitude: 100 }],
    },
    {
      ...networkFixture,
      links: [{ ...networkFixture.links[0], target: "missing" }],
    },
    { ...networkFixture, baseline: { ...networkFixture.baseline, links: [] } },
    {
      ...networkFixture,
      criticality: [
        { kind: "node", id: "A", critical: true, reasons: ["unknown"] },
      ],
    },
    {
      ...networkFixture,
      baseline: {
        ...networkFixture.baseline,
        top_five: [{ ...networkFixture.baseline.top_five[0], load: "bad" }],
      },
    },
    { message: "Hello" },
  ];
  for (const data of invalid) {
    mock.mock.mockImplementation(async () => Response.json(data));
    await assert.rejects(
      fetchNetwork(new AbortController().signal),
      /invalid network/,
    );
  }
  for (const [response, error] of [
    [new Response("", { status: 503 }), /HTTP 503/],
    [new Response("<html>wrong route</html>"), /non-JSON/],
    [
      new Response("{", { headers: { "content-type": "application/json" } }),
      /JSON/,
    ],
  ] as const) {
    mock.mock.mockImplementation(async () => response);
    await assert.rejects(fetchNetwork(new AbortController().signal), error);
  }
  mock.mock.mockImplementation(async () => {
    throw new Error("Network unavailable");
  });
  await assert.rejects(
    fetchNetwork(new AbortController().signal),
    /Network unavailable/,
  );
});
