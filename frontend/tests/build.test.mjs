// Build from source in isolation and check the emitted browser asset contract.
import assert from "node:assert/strict";
import { spawn, spawnSync } from "node:child_process";
import { once } from "node:events";
import {
  cp,
  mkdtemp,
  readFile,
  rm,
  symlink,
  writeFile,
} from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { test } from "node:test";
import { setTimeout } from "node:timers/promises";
import { fileURLToPath } from "node:url";

async function sourceFixture(t) {
  const root = fileURLToPath(new URL("../", import.meta.url));
  const temporary = await mkdtemp(path.join(tmpdir(), "linkscope-watch-"));
  t.after(() => rm(temporary, { recursive: true, force: true }));
  for (const entry of ["build.mjs", "index.html", "src", "package.json"]) {
    await cp(path.join(root, entry), path.join(temporary, entry), {
      recursive: true,
    });
  }
  await symlink(
    path.join(root, "node_modules"),
    path.join(temporary, "node_modules"),
  );
  return temporary;
}

test("watch rebuilds component, CSS, HTML, and logo changes", {
  timeout: 15000,
}, async (t) => {
  const directory = await sourceFixture(t);
  const child = spawn(process.execPath, ["build.mjs", "--watch"], {
    cwd: directory,
  });
  let diagnostics = "";
  child.stderr.on("data", (chunk) => {
    diagnostics += chunk;
  });
  child.stdout.resume();
  t.after(async () => {
    if (child.exitCode === null) {
      const exited = once(child, "exit");
      child.kill("SIGTERM");
      await exited;
    }
  });
  let builds = 0;
  child.stderr.on("data", (chunk) => {
    builds += String(chunk).split("build finished").length - 1;
  });
  async function waitForBuild(previous) {
    for (let attempt = 0; attempt < 200; attempt++) {
      assert.equal(child.exitCode, null, diagnostics);
      if (builds > previous) return;
      await setTimeout(20);
    }
    assert.fail(`Watch did not finish rebuilding: ${diagnostics}`);
  }
  await waitForBuild(0);
  for (const [source, output, marker] of [
    ["src/App.tsx", "assets/app.js", "Watch verification"],
    ["src/styles.css", "assets/app.css", "watch-verification"],
    ["index.html", "index.html", "HTML verification"],
    ["src/logo.svg", "assets/logo.svg", "Logo verification"],
  ]) {
    const before = builds;
    const file = path.join(directory, source);
    const original = await readFile(file, "utf8");
    const updated = source.endsWith(".tsx")
      ? original.replace("LinkScope", marker)
      : source.endsWith(".css")
        ? `${original}\n.watch-verification { color: red; }\n`
        : source.endsWith(".svg")
          ? original.replace("<svg", `<svg aria-label="${marker}"`)
          : original.replace(
              "<title>LinkScope</title>",
              `<title>${marker}</title>`,
            );
    await writeFile(file, updated);
    await waitForBuild(before);
    assert.ok(
      (await readFile(path.join(directory, "dist", output), "utf8")).includes(
        marker,
      ),
    );
  }
});

test("watch reports build errors, removes failed output, and recovers", {
  timeout: 15000,
}, async (t) => {
  const directory = await sourceFixture(t);
  const child = spawn(process.execPath, ["build.mjs", "--watch"], {
    cwd: directory,
  });
  let diagnostics = "";
  child.stderr.on("data", (chunk) => {
    diagnostics += chunk;
  });
  child.stdout.resume();
  t.after(async () => {
    if (child.exitCode === null) {
      const exited = once(child, "exit");
      child.kill("SIGTERM");
      await exited;
    }
  });
  async function waitForDiagnostic(pattern) {
    for (let attempt = 0; attempt < 200; attempt++) {
      assert.equal(child.exitCode, null, diagnostics);
      if (pattern.test(diagnostics)) return;
      await setTimeout(20);
    }
    assert.fail(`Watch diagnostic missing: ${diagnostics}`);
  }
  await waitForDiagnostic(/build finished/);
  const source = path.join(directory, "src/App.tsx");
  const bundle = path.join(directory, "dist/assets/app.js");
  const original = await readFile(source, "utf8");
  assert.ok((await readFile(bundle, "utf8")).length > 0);
  diagnostics = "";
  await writeFile(source, `${original}\nexport const broken = ;\n`);
  await waitForDiagnostic(/\[ERROR\][\s\S]*build finished/);
  await assert.rejects(readFile(bundle, "utf8"), { code: "ENOENT" });
  diagnostics = "";
  await writeFile(source, original.replace("LinkScope", "Watch recovery"));
  await waitForDiagnostic(/build finished/);
  assert.match(await readFile(bundle, "utf8"), /Watch recovery/);
});

test("clean source build emits HTML and bundled JavaScript/CSS", async () => {
  const root = fileURLToPath(new URL("../", import.meta.url));
  const temporary = await mkdtemp(path.join(tmpdir(), "linkscope-build-"));
  try {
    for (const entry of ["build.mjs", "index.html", "src"]) {
      await cp(path.join(root, entry), path.join(temporary, entry), {
        recursive: true,
      });
    }
    await symlink(
      path.join(root, "node_modules"),
      path.join(temporary, "node_modules"),
    );
    // ES modules need the package type in the isolated build directory.
    await cp(
      path.join(root, "package.json"),
      path.join(temporary, "package.json"),
    );
    const result = spawnSync(process.execPath, ["build.mjs"], {
      cwd: temporary,
      encoding: "utf8",
    });
    assert.equal(result.status, 0, result.stderr);
    const html = await readFile(
      path.join(temporary, "dist/index.html"),
      "utf8",
    );
    assert.match(html, /id="root"/);
    for (const asset of [
      "/assets/app.js",
      "/assets/app.css",
      "/assets/logo.svg",
    ]) {
      assert.ok(html.includes(asset));
      assert.ok(
        (await readFile(path.join(temporary, "dist", asset))).length > 0,
      );
    }
    const css = await readFile(
      path.join(temporary, "dist/assets/app.css"),
      "utf8",
    );
    const images = [...css.matchAll(/url\(["']?([^"')]+\.png)["']?\)/g)];
    assert.equal(
      images.length,
      3,
      "Leaflet CSS must reference its bundled images",
    );
    for (const match of images) {
      assert.ok(
        (await readFile(path.join(temporary, "dist/assets", match[1]))).length >
          0,
      );
    }
  } finally {
    await rm(temporary, { recursive: true, force: true });
  }
});
