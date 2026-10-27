// Preserve command output and reject Node/npm warnings or notices as validation failures.
// so we expose warnings/notices as errors in the ci jobs and they can be addressed

import { spawn } from "node:child_process";

const [command, ...args] = process.argv.slice(2);
if (!command) {
  throw new Error("Usage: node run-checked.mjs COMMAND [ARGUMENTS...]");
}

const child = spawn(command, args, { stdio: ["inherit", "pipe", "pipe"] });
let diagnostic = false;
const pattern =
  /npm\s+(?:warn(?:ing)?|notice)\b|\(node:\d+\)[^\n]*Warning\b|\b(?:DeprecationWarning|ExperimentalWarning):/i;
for (const [stream, output] of [
  [child.stdout, process.stdout],
  [child.stderr, process.stderr],
]) {
  let pending = "";
  stream.on("data", (chunk) => {
    output.write(chunk);
    pending += chunk.toString();
    const lines = pending.split(/\r?\n/);
    pending = lines.pop() ?? "";
    diagnostic ||= lines.some((line) => pattern.test(line));
  });
  stream.on("end", () => {
    diagnostic ||= pattern.test(pending);
  });
}
child.on("error", (error) => {
  console.error(error);
  process.exitCode = 1;
});
child.on("close", (code) => {
  if (diagnostic) {
    console.error("Validation failed: Node/npm emitted a warning or notice.");
  }
  process.exitCode = code === 0 && !diagnostic ? 0 : code || 1;
});
