// Exercise the greeting API contract and explicit failure cases.
import assert from "node:assert/strict";
import { test } from "node:test";
import { fetchGreeting } from "../src/api";

test("greeting comes from the same-origin API response", async (t) => {
  const controller = new AbortController();
  t.mock.method(
    globalThis,
    "fetch",
    async (url: RequestInfo | URL, options?: RequestInit) => {
      assert.equal(url, "/api");
      assert.equal(options?.signal, controller.signal);
      return Response.json({ message: "A message supplied by the backend" });
    },
  );
  assert.equal(
    await fetchGreeting(controller.signal),
    "A message supplied by the backend",
  );
});

test("greeting rejects HTTP, network, JSON, and contract errors", async (t) => {
  const mock = t.mock.method(globalThis, "fetch");
  for (const [response, error] of [
    [new Response("", { status: 503 }), /HTTP 503/],
    [new Response("<html>wrong route</html>"), /non-JSON/],
    [Response.json({ error: "not a greeting" }), /invalid greeting/],
    [Response.json({ message: 123 }), /invalid greeting/],
    [Response.json({ message: " " }), /invalid greeting/],
    [
      new Response("{", { headers: { "content-type": "application/json" } }),
      /JSON/,
    ],
  ] as const) {
    mock.mock.mockImplementation(async () => response);
    await assert.rejects(fetchGreeting(new AbortController().signal), error);
  }
  mock.mock.mockImplementation(async () => {
    throw new Error("Network unavailable");
  });
  await assert.rejects(
    fetchGreeting(new AbortController().signal),
    /Network unavailable/,
  );
});
