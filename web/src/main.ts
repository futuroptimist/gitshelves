import "./style.css";
import { preserveFile, validateStl, type Classified } from "./files";
import { createManifest } from "./manifest";
import { parseMetadata } from "./metadata";
import { sampleDataset, type Dataset } from "./model";
import { createScene, parseStl } from "./scene";

const app = document.querySelector<HTMLElement>("#app")!;
const canvas = document.querySelector<HTMLCanvasElement>("#scene")!;
let dataset: Dataset = sampleDataset();
let files: Classified[] = [];
let exactAvailable = false;
let scene = createScene(canvas, dataset);

function download(name: string, bytes: BlobPart, type: string) {
  const url = URL.createObjectURL(new Blob([bytes], { type }));
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

async function loadCanonical() {
  const names = ["baseplate_2x6.stl", "contrib_cube.stl"];
  const loaded: Classified[] = [];
  for (const name of names) {
    const response = await fetch(`/models/${name}`);
    if (!response.ok) return;
    const buffer = await response.arrayBuffer();
    validateStl(new Uint8Array(buffer));
    parseStl(buffer);
    loaded.push(preserveFile(name, buffer));
  }
  scene.showExact(
    parseStl(loaded[0]!.bytes.slice().buffer),
    parseStl(loaded[1]!.bytes.slice().buffer),
  );
  files = loaded;
  exactAvailable = true;
  render();
}

function render(message = "") {
  const manifest = createManifest(dataset, files);
  app.innerHTML = `<header><p class="eyebrow">Physical GitHub activity</p><h1>GitShelves</h1><p class="lede">Twelve months. One reusable 2×6 system.</p><span class="state">${exactAvailable ? "Exact STL geometry" : "Design preview"}</span></header>
  <section class="controls" aria-label="Viewer controls"><button id="assembled">Assembled</button><button id="exploded">Exploded</button><button id="reset">Reset camera</button><button id="fit">Fit to model</button><label class="file">Load metadata JSON<input id="metadata" type="file" accept="application/json,.json"/></label><label class="file">Load local STLs<input id="stls" type="file" accept=".stl" multiple/></label><label>Visible color groups <select id="colors">${[1, 2, 3, 4].map((n) => `<option>${n}</option>`).join("")}</select></label><button id="text-toggle" aria-expanded="false">Text mode</button></section>
  <aside id="status" role="status" aria-live="polite">${message || dataset.source}${!exactAvailable ? ". Exact downloads unavailable: run npm run prepare:models." : ""}</aside>
  <section class="details" id="text" hidden><h2>Print plan</h2><p>Total reusable cube quantity: <strong>${manifest.totalCubeQuantity}</strong></p><table><thead><tr><th>Month</th><th>Contributions</th><th>Cubes</th><th>Position</th></tr></thead><tbody>${manifest.months.map((m) => `<tr><th>${m.label}</th><td>${m.contributions}</td><td>${m.blocks}</td><td>${m.placement.column + 1}, ${m.placement.row + 1}</td></tr>`).join("")}</tbody></table><h3>Local STL files</h3><ul>${files.length ? files.map((f) => `<li>${f.name} — ${f.component} — ${f.colorGroup ? `color ${f.colorGroup}` : "no color group"} — ${f.bytes.byteLength} bytes</li>`).join("") : "<li>No exact files loaded.</li>"}</ul><div class="downloads"><button id="base-download" ${!files.some((f) => f.component === "baseplate") ? "disabled" : ""}>Download canonical base STL</button><button id="cube-download" ${!files.some((f) => f.component === "cube") ? "disabled" : ""}>Download canonical reusable module STL</button><button id="manifest-download">Download print manifest</button></div></section>`;
  document
    .querySelector("#assembled")!
    .addEventListener("click", () => scene.setMode("assembled"));
  document
    .querySelector("#exploded")!
    .addEventListener("click", () => scene.setMode("exploded"));
  document
    .querySelector("#reset")!
    .addEventListener("click", () => scene.reset());
  document.querySelector("#fit")!.addEventListener("click", () => scene.fit());
  document.querySelector<HTMLSelectElement>("#colors")!.value = "4";
  document
    .querySelector<HTMLSelectElement>("#colors")!
    .addEventListener("change", (event) =>
      scene.setColorGroups(
        Number((event.currentTarget as HTMLSelectElement).value),
      ),
    );
  document.querySelector("#text-toggle")!.addEventListener("click", (e) => {
    const button = e.currentTarget as HTMLButtonElement;
    const text = document.querySelector<HTMLElement>("#text")!;
    text.hidden = !text.hidden;
    button.setAttribute("aria-expanded", String(!text.hidden));
  });
  document
    .querySelector<HTMLInputElement>("#metadata")!
    .addEventListener("change", async (e) => {
      try {
        const input = e.currentTarget as HTMLInputElement;
        const file = input.files?.[0];
        if (!file) return;
        dataset = parseMetadata(await file.text());
        scene.dispose();
        scene = createScene(canvas, dataset);
        render("Loaded metadata locally; nothing was uploaded.");
      } catch (error) {
        render(
          error instanceof Error ? error.message : "Could not load metadata",
        );
      }
    });
  document
    .querySelector<HTMLInputElement>("#stls")!
    .addEventListener("change", async (e) => {
      const next: Classified[] = [];
      const names = new Set<string>();
      try {
        const input = e.currentTarget as HTMLInputElement;
        for (const file of Array.from(input.files ?? [])) {
          if (names.has(file.name))
            throw new Error(`Duplicate STL: ${file.name}`);
          names.add(file.name);
          const buffer = await file.arrayBuffer();
          validateStl(new Uint8Array(buffer));
          parseStl(buffer);
          next.push(preserveFile(file.name, buffer));
        }
        files = next;
        const localBase = next.find((file) => file.component === "baseplate");
        const localCube = next.find((file) => file.component === "cube");
        exactAvailable = Boolean(localBase && localCube);
        if (localBase && localCube)
          scene.showExact(
            parseStl(localBase.bytes.slice().buffer),
            parseStl(localCube.bytes.slice().buffer),
          );
        render(
          `Loaded ${next.length} STL file(s) locally; original bytes are preserved.${exactAvailable ? " Exact base and reusable module geometry is active." : " Load both a baseplate and reusable cube/module for exact assembly geometry."}`,
        );
      } catch (error) {
        render(error instanceof Error ? error.message : "Could not parse STL");
      }
    });
  document
    .querySelector("#manifest-download")!
    .addEventListener("click", () =>
      download(
        "gitshelves-print-manifest.json",
        JSON.stringify(manifest, null, 2),
        "application/json",
      ),
    );
  for (const [id, type] of [
    ["#base-download", "baseplate"],
    ["#cube-download", "cube"],
  ] as const)
    document.querySelector(id)?.addEventListener("click", () => {
      const file = files.find((f) => f.component === type);
      if (file) download(file.name, file.bytes.slice().buffer, "model/stl");
    });
}
render();
void loadCanonical().catch(() =>
  render(
    "Canonical models are unavailable; procedural preview remains active.",
  ),
);
