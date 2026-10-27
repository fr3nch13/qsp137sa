// Verify warning enforcement without depending on npm's update-check timing.
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const wrapper = fileURLToPath(new URL("../run-checked.mjs", import.meta.url));

function run(source) {
  return spawnSync(
    process.execPath,
    [wrapper, process.execPath, "-e", source],
    {
      encoding: "utf8",
    },
  );
}

test("checked command preserves successful output", () => {
  const result = run('console.log("build complete")');
  assert.equal(result.status, 0);
  assert.match(result.stdout, /build complete/);
});

test("checked command preserves unsuccessful exit status", () => {
  assert.equal(run("process.exit(7)").status, 7);
});

test("checked command rejects diagnostic output on either stream", () => {
  for (const message of [
    "npm warn install-scripts review required",
    "npm notice New major version available",
    "(node:123) Warning: example",
    "(node:123) [DEP0001] DeprecationWarning: example",
    "ExperimentalWarning: example",
  ]) {
    for (const stream of ["stdout", "stderr"]) {
      const result = run(`process.${stream}.write(${JSON.stringify(message)})`);
      assert.equal(result.status, 1, message);
      assert.ok(result[stream].includes(message));
      assert.match(result.stderr, /Validation failed/);
    }
  }
});
