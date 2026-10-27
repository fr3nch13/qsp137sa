// Verify the shell exposes its identity and honest implementation status.
import assert from "node:assert/strict";
import { test } from "node:test";
import { renderToStaticMarkup } from "react-dom/server";
import { App } from "../src/App";

test("shell renders an accessible heading and implementation status", () => {
  const html = renderToStaticMarkup(<App />);
  assert.match(html, /<header/);
  assert.match(html, /<main /);
  assert.match(html, /<footer/);
  assert.match(html, /src="\/assets\/logo.svg"/);
  assert.match(html, /<h1>LinkScope<\/h1>/);
  assert.match(html, /Network resilience analysis/);
  assert.match(html, /not implemented yet/);
  assert.match(html, /Loading API greeting/);
  assert.doesNotMatch(html, /Hello, world!/);
});
