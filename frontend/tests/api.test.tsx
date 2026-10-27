// Verify network response validation before data reaches the map.
import assert from "node:assert/strict";
import { test } from "node:test";
import { type Analysis, fetchAnalysis, fetchNetwork } from "../src/api";
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

test("single failures fetch the selected element and validate separate R8 reports", async (t) => {
  const mock = t.mock.method(globalThis, "fetch");
  for (const failure of [
    { kind: "node", id: "A" },
    { kind: "link", id: "L1" },
  ] as const) {
    const result: Analysis = {
      failure,
      links: [],
      top_five: [],
      overloaded: [],
      disconnected: failure.kind === "link",
      undeliverable: failure.kind === "link" ? networkFixture.demands : [],
      failed_endpoint_demands:
        failure.kind === "node" ? networkFixture.demands : [],
    };
    const controller = new AbortController();
    mock.mock.mockImplementation(async (url, options) => {
      assert.equal(url, `/api/analysis?kind=${failure.kind}&id=${failure.id}`);
      assert.equal(options?.signal, controller.signal);
      return Response.json(result);
    });
    assert.deepEqual(
      await fetchAnalysis(networkFixture, failure, controller.signal),
      result,
    );
  }
});

test("analysis rejects wrong scenarios, surviving links, demand categories and overloads", async (t) => {
  const failure = { kind: "node", id: "A" } as const;
  const valid: Analysis = {
    failure,
    links: [],
    top_five: [],
    overloaded: [],
    disconnected: false,
    undeliverable: [],
    failed_endpoint_demands: networkFixture.demands,
  };
  const mock = t.mock.method(globalThis, "fetch");
  for (const result of [
    { ...valid, failure: null },
    { ...valid, failure: { kind: "node", id: "DC" } },
    { ...valid, links: networkFixture.baseline.links },
    { ...valid, failed_endpoint_demands: [] },
    { ...valid, undeliverable: networkFixture.demands },
    { ...valid, overloaded: networkFixture.baseline.links },
    { ...valid, top_five: networkFixture.baseline.top_five },
    { ...valid, disconnected: "no" },
    {
      ...valid,
      failed_endpoint_demands: [{ ...networkFixture.demands[0], units: 99 }],
    },
  ]) {
    mock.mock.mockImplementation(async () => Response.json(result));
    await assert.rejects(
      fetchAnalysis(networkFixture, failure, new AbortController().signal),
      /invalid analysis|does not match/,
    );
  }
  mock.mock.mockImplementation(async () => new Response("", { status: 500 }));
  await assert.rejects(
    fetchAnalysis(networkFixture, failure, new AbortController().signal),
    { message: "The server ran into a problem." },
  );
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
    [
      new Response('{"error": "nobel-eu.txt: row 7: bad"}', { status: 503 }),
      {
        message:
          "The server could not read its network data files. Check the server logs for details.",
      },
    ],
    [
      new Response("", { status: 404 }),
      { message: "The server could not handle this request." },
    ],
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
  await assert.rejects(fetchNetwork(new AbortController().signal), {
    message: "Could not reach the LinkScope server.",
  });
  const controller = new AbortController();
  controller.abort();
  mock.mock.mockImplementation(async () => {
    throw new DOMException("Aborted", "AbortError");
  });
  await assert.rejects(fetchNetwork(controller.signal), { name: "AbortError" });
});
