// Bundle browser assets; watch mode rebuilds files without starting a web server.
import { copyFile, mkdir, readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import * as esbuild from "esbuild";

const watch = process.argv.includes("--watch");
if (process.argv.slice(2).some((argument) => argument !== "--watch")) {
  throw new Error("Usage: node build.mjs [--watch]");
}

const root = fileURLToPath(new URL(".", import.meta.url));
const outdir = fileURLToPath(new URL("dist/assets/", import.meta.url));
const options = {
  absWorkingDir: root,
  entryPoints: { app: "src/main.tsx" },
  outdir,
  bundle: true,
  format: "esm",
  platform: "browser",
  target: ["es2022"],
  jsx: "automatic",
  minify: !watch,
  define: {
    "process.env.NODE_ENV": JSON.stringify(
      watch ? "development" : "production",
    ),
  },
  logLevel: "info",
  plugins: [
    {
      name: "html-entry",
      setup(build) {
        // Include the HTML entry in esbuild's dependency watch graph.
        build.onLoad({ filter: /[/\\]main\.tsx$/ }, async (args) => ({
          contents: await readFile(args.path, "utf8"),
          loader: "tsx",
          watchFiles: [fileURLToPath(new URL("index.html", import.meta.url))],
        }));
        build.onEnd(async (result) => {
          if (result.errors.length === 0) {
            await mkdir(outdir, { recursive: true });
            await copyFile(
              new URL("index.html", import.meta.url),
              new URL("dist/index.html", import.meta.url),
            );
          }
        });
      },
    },
  ],
};

if (watch) {
  const context = await esbuild.context(options);
  await context.watch();
  console.log(
    "Watching frontend source. Refresh the browser after rebuilding.",
  );
  for (const signal of ["SIGINT", "SIGTERM"]) {
    process.once(signal, async () => {
      await context.dispose();
      process.exit(0);
    });
  }
} else {
  await esbuild.build(options);
}
