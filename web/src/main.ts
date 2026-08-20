import "./style.css";
import { SAMPLE, type Dataset } from "./domain";
import { parseMetadata } from "./metadata";
import {
  appendLiteralFilename,
  parseStlGeometry,
  readStlFiles,
  type LocalStl,
} from "./files";
import { createManifest } from "./manifest";
import { analyzeBundle, ProductScene } from "./scene";
const app = document.querySelector<HTMLDivElement>("#app")!;
app.innerHTML = `<main><div id="scene" role="region" aria-label="Interactive orthographic model; drag to orbit, right-drag to pan, and scroll to zoom"></div><header><p class="eyebrow">GitShelves / monthly 2×6</p><h1>Activity,<br>made tangible.</h1><p class="lede">A local-first design preview for a reusable base and modular contribution cubes.</p></header><aside class="hud" aria-label="Design controls"><div class="status"><span id="state">Design preview</span><span id="sample">Synthetic sample</span></div><div class="controls"><button id="assembled" aria-pressed="true">Assembled</button><button id="exploded" aria-pressed="false">Exploded</button><button id="reset">Reset camera</button><button id="fit">Fit model</button><button class="color" data-group="1" aria-pressed="true">Color 1</button><button class="color" data-group="2" aria-pressed="true">Color 2</button><button class="color" data-group="3" aria-pressed="true">Color 3</button><button class="color" data-group="4" aria-pressed="true">Color 4</button></div><label>Load metadata or run summary<input id="metadata" type="file" accept="application/json,.json"></label><label>Load local STL files<input id="stls" type="file" accept=".stl" multiple></label><p class="privacy">Files stay in this browser. No GitHub or third-party API is contacted.</p><div id="downloads"><button id="base" disabled>Download base STL</button><button id="module" disabled>Download module STL</button><button id="manifest">Download print manifest</button></div><output id="message" aria-live="polite"></output></aside><section class="text"><h2>Print plan</h2><p id="geometry-note">Procedural geometry is a design preview, not printable STL. Run <code>npm run models:prepare</code> from <code>web/</code> to enable canonical exact models.</p><div class="table"><table><thead><tr><th>Month</th><th>Contributions</th><th>Cubes</th><th>Base cell</th></tr></thead><tbody id="months"></tbody></table></div><h3>Loaded STL files</h3><ul id="file-list"><li>None</li></ul><p id="total"></p></section></main>`;
let dataset: Dataset = SAMPLE,
  files: LocalStl[] = [],
  exploded = false;
const visible = new Set([1, 2, 3, 4]);
const scene = new ProductScene(document.querySelector("#scene")!);
function draw() {
  const bundle = analyzeBundle(dataset, files);
  scene.show(dataset, exploded, files, visible);
  document.querySelector("#state")!.textContent = bundle.exact
    ? "Exact STL geometry"
    : "Design preview";
  document.querySelector("#geometry-note")!.textContent = !files.length
    ? "Proxy geometry is a non-printable Design preview; both canonical downloads are unavailable. Run npm run models:prepare from web/ to enable canonical exact models."
    : bundle.exact
      ? "All required geometry is represented by exact STL meshes."
      : `Exact STL components are shown where available; proxy geometry supplies ${
          [
            bundle.proxyBase ? "the base" : "",
            bundle.proxyContributionGroups.length
              ? `contribution color group(s) ${bundle.proxyContributionGroups.join(", ")}`
              : "",
          ]
            .filter(Boolean)
            .join(" and ") || "no required components"
        }.`;
  document.querySelector("#months")!.innerHTML = dataset.months
    .map(
      (m) =>
        `<tr><td>${m.label}</td><td>${m.contributions.toLocaleString()}</td><td>${m.blocks}</td><td>${m.x / 42 + 1}, ${m.y / 42 + 1}</td></tr>`,
    )
    .join("");
  document.querySelector("#total")!.textContent =
    `${dataset.months.reduce((s, m) => s + m.blocks, 0)} reusable cubes total.`;
  const fileList = document.querySelector("#file-list")!;
  fileList.replaceChildren();
  for (const file of files.length ? files : [undefined]) {
    const label = file
      ? `${file.name} — ${file.type}, color ${file.colorGroup || "base"}, ${file.bytes.byteLength.toLocaleString()} bytes`
      : "None";
    const item = appendLiteralFilename(fileList as HTMLElement, label);
    if (file) {
      const action = document.createElement("button");
      action.textContent = "Download";
      action.addEventListener("click", () =>
        download(file.name, file.bytes, "model/stl"),
      );
      item.append(" ", action);
    }
  }
}
function message(text: string, error = false) {
  const el = document.querySelector<HTMLOutputElement>("#message")!;
  el.textContent = text;
  el.classList.toggle("error", error);
}
function download(name: string, bytes: BlobPart | Uint8Array, type: string) {
  const part = bytes instanceof Uint8Array ? bytes.slice().buffer : bytes;
  const url = URL.createObjectURL(new Blob([part], { type }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}
document.querySelector("#assembled")!.addEventListener("click", () => {
  exploded = false;
  setMode();
});
document.querySelector("#exploded")!.addEventListener("click", () => {
  exploded = true;
  setMode();
});
function setMode() {
  document
    .querySelector("#assembled")!
    .setAttribute("aria-pressed", String(!exploded));
  document
    .querySelector("#exploded")!
    .setAttribute("aria-pressed", String(exploded));
  draw();
  message(
    exploded
      ? "Exploded view shows the seating and vertical stack interfaces."
      : "Assembled view.",
  );
}
for (const button of document.querySelectorAll<HTMLButtonElement>(
  "button.color",
))
  button.addEventListener("click", () => {
    const group = Number(button.dataset.group);
    if (visible.has(group)) visible.delete(group);
    else visible.add(group);
    button.setAttribute("aria-pressed", String(visible.has(group)));
    draw();
  });
document
  .querySelector("#reset")!
  .addEventListener("click", () => scene.reset());
document.querySelector("#fit")!.addEventListener("click", () => scene.fit());
document
  .querySelector<HTMLInputElement>("#metadata")!
  .addEventListener("change", async (e) => {
    try {
      const file = ((e.target as HTMLInputElement).files ?? [])[0];
      if (!file) return;
      dataset = parseMetadata(await file.text());
      document.querySelector("#sample")!.textContent = "Local metadata";
      draw();
      message(`Loaded ${file.name}.`);
    } catch (err) {
      message((err as Error).message, true);
    }
  });
document
  .querySelector<HTMLInputElement>("#stls")!
  .addEventListener("change", async (e) => {
    try {
      const replacement = await readStlFiles(
        Array.from((e.target as HTMLInputElement).files ?? []),
      );
      files = replacement;
      draw();
      message(`Loaded ${files.length} STL file(s) locally.`);
    } catch (err) {
      message((err as Error).message, true);
    }
  });
document
  .querySelector("#manifest")!
  .addEventListener("click", () =>
    download(
      "gitshelves-print-manifest.json",
      JSON.stringify(createManifest(dataset, files), null, 2),
      "application/json",
    ),
  );
async function loadCanonical() {
  const targets: [[string, string], [string, string]] = [
    ["base", "/models/baseplate_2x6.stl"],
    ["module", "/models/contrib_cube.stl"],
  ];
  const loaded: LocalStl[] = [];
  for (const [id, url] of targets) {
    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error();
      const bytes = new Uint8Array(await response.arrayBuffer());
      parseStlGeometry(bytes).dispose();
      const type = id === "base" ? "base" : "module";
      loaded.push({ name: url.split("/").pop()!, type, colorGroup: 0, bytes });
      const button = document.querySelector<HTMLButtonElement>(`#${id}`)!;
      button.disabled = false;
      button.addEventListener("click", () =>
        download(
          loaded.find((f) => f.type === type)!.name,
          loaded.find((f) => f.type === type)!.bytes,
          "model/stl",
        ),
      );
    } catch (error) {
      message(
        `${url}: ${(error as Error).message || "canonical model is unavailable"}`,
        true,
      );
    }
  }
  if (loaded.length === 2) {
    files = loaded;
    draw();
  } else if (loaded.length) {
    files = loaded;
    draw();
  }
}
draw();
void loadCanonical();
