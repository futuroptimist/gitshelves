import "./style.css";
import { SAMPLE, type Dataset } from "./model";
import { parseMetadata } from "./metadata";
import { preserveStl, type LoadedStl } from "./files";
import { createManifest } from "./manifest";
import { ProductScene } from "./scene";
const app = document.querySelector<HTMLElement>("#app")!;
app.innerHTML = `<canvas aria-label="Interactive isometric GitShelves product preview"></canvas><section class="hud" aria-label="GitShelves controls"><div class="eyebrow">Git activity, made physical</div><h1>GitShelves</h1><span id="status" class="status">Design preview</span><p id="title"></p><div class="controls"><button id="assembled" aria-pressed="true">Assembled</button><button id="exploded" aria-pressed="false">Exploded</button><button id="fit">Fit model</button><button id="reset">Reset camera</button><button id="text">Text mode</button></div><div class="controls"><label class="file">Load metadata JSON<input id="json" type="file" accept="application/json,.json"></label><label class="file">Load local STLs<input id="stls" type="file" accept=".stl,model/stl" multiple></label></div><p class="hint">Files stay in this browser. Orbit: drag · pan: right-drag · zoom: wheel/pinch. No GitHub API is contacted.</p><div id="error" class="error" role="alert"></div><h2>Print downloads</h2><div class="controls"><button id="base" disabled>Base STL unavailable</button><button id="cube" disabled>Module STL unavailable</button><button id="manifest">Print manifest</button></div><p id="modelHint" class="hint">Exact assets unavailable? Run <code>npm run prepare:models</code>, then restart Vite.</p><h2>Months</h2><ol id="months"></ol><div id="files"></div></section>`;
let data: Dataset = SAMPLE;
let exploded = false;
const files: LoadedStl[] = [];
const scene = new ProductScene(document.querySelector("canvas")!);
const $ = <T extends HTMLElement>(id: string) =>
  document.querySelector<T>(`#${id}`)!;
const error = (message = "") => {
  $<HTMLElement>("error").textContent = message;
};
function render() {
  scene.compose(data, exploded);
  $("title").textContent =
    data.title + " — clearly synthetic until you import metadata";
  $("months").innerHTML = data.months
    .map(
      (m) =>
        `<li class="month"><b>${new Intl.DateTimeFormat("en", { month: "short" }).format(new Date(2024, m.month - 1))}</b><span>${m.count.toLocaleString()} contributions</span><span>${m.blocks} cube${m.blocks === 1 ? "" : "s"}</span></li>`,
    )
    .join("");
  $("files").innerHTML = files.length
    ? `<h2>Local STL files</h2><ul>${files.map((f) => `<li>${f.name} — ${f.type}, color ${f.colorGroup}, ${f.bytes.byteLength.toLocaleString()} bytes</li>`).join("")}</ul>`
    : "";
}
function save(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}
$("assembled").onclick = () => {
  exploded = false;
  render();
};
$("exploded").onclick = () => {
  exploded = true;
  render();
};
$("fit").onclick = () => scene.fit();
$("reset").onclick = () => scene.reset();
$("text").onclick = () =>
  document.querySelector("canvas")!.toggleAttribute("hidden");
$("manifest").onclick = () =>
  save(
    new Blob(
      [
        JSON.stringify(
          createManifest(
            data,
            files.map((f) => f.name),
          ),
          null,
          2,
        ),
      ],
      { type: "application/json" },
    ),
    "gitshelves-print-manifest.json",
  );
$("json").addEventListener("change", async (e) => {
  try {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (!file) return;
    data = parseMetadata(await file.text());
    error();
    render();
  } catch (e) {
    error(e instanceof Error ? e.message : "Could not load metadata.");
  }
});
$("stls").addEventListener("change", async (e) => {
  for (const file of Array.from((e.target as HTMLInputElement).files ?? [])) {
    try {
      if (files.some((f) => f.name === file.name))
        throw new Error(`Duplicate file ${file.name}.`);
      const loaded = preserveStl(file.name, await file.arrayBuffer());
      const geometry = await scene.parseStl(loaded.bytes.buffer as ArrayBuffer);
      if (loaded.type !== "unknown") scene.setExact(loaded.type, geometry);
      files.push(loaded);
    } catch (e) {
      error(e instanceof Error ? e.message : "Could not parse STL.");
    }
  }
  if (files.some((f) => f.type !== "unknown")) {
    $("status").textContent = "Exact STL geometry";
  }
  render();
});
async function canonical() {
  for (const [url, id, label] of [
    ["/models/baseplate_2x6.stl", "base", "Base STL"],
    ["/models/contrib_cube.stl", "cube", "Module STL"],
  ] as const)
    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error();
      const f = preserveStl(
        url.split("/").pop()!,
        await response.arrayBuffer(),
      );
      const geometry = await scene.parseStl(f.bytes.buffer as ArrayBuffer);
      if (f.type !== "unknown") scene.setExact(f.type, geometry);
      files.push(f);
      const button = $<HTMLButtonElement>(id);
      button.disabled = false;
      button.textContent = label;
      button.onclick = () =>
        save(new Blob([f.bytes as BlobPart], { type: "model/stl" }), f.name);
    } catch {
      /* documented proxy fallback */
    }
  if (files.length) {
    $("status").textContent = "Exact STL geometry";
    $("modelHint").hidden = true;
  }
  render();
}
render();
void canonical();
