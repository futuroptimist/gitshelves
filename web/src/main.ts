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
import {
  activityDays,
  bindGithubSearch,
  type GithubActivity,
} from "./githubActivity";
import { analyzeBundle, ProductScene } from "./scene";
const app = document.querySelector<HTMLDivElement>("#app")!;
app.innerHTML = `<main><header><p class="eyebrow" id="view-mode">GitShelves / monthly 2×6</p><h1>Activity,<br>made tangible.</h1><p class="lede">A local-first design preview for a reusable base and modular contribution cubes.</p></header><form id="github-search" class="github-search" role="search" aria-label="Search GitHub public commits" novalidate><label for="github-username">Search GitHub activity</label><div class="search-row"><input id="github-username" name="username" type="text" placeholder="GitHub username" maxlength="39" required autocapitalize="none" autocomplete="off" spellcheck="false" aria-describedby="github-search-help github-search-status"><button type="submit">Show commits</button></div><p id="github-search-help">Preview up to 100 public default-branch commits over the last 30 UTC days. Each day gets its own stack.</p><output id="github-search-status" role="status" aria-live="polite" aria-atomic="true" for="github-username"></output></form><div id="scene" role="region" aria-label="Interactive orthographic model; drag to orbit, right-drag to pan, and scroll to zoom"></div><aside class="hud" aria-label="Design controls"><div class="status"><span id="state">Design preview</span><span id="sample">Synthetic sample</span><button id="clear-activity" hidden type="button">Clear activity</button></div><div class="controls"><button id="assembled" aria-pressed="true">Assembled</button><button id="exploded" aria-pressed="false">Exploded</button><button id="reset">Reset camera</button><button id="fit">Fit model</button><button class="color" data-group="1" aria-pressed="true">Color 1</button><button class="color" data-group="2" aria-pressed="true">Color 2</button><button class="color" data-group="3" aria-pressed="true">Color 3</button><button class="color" data-group="4" aria-pressed="true">Color 4</button></div><label>Load metadata or run summary<input id="metadata" type="file" accept="application/json,.json"></label><label>Load local STL files<input id="stls" type="file" accept=".stl" multiple></label><p class="privacy">Imported files stay in this browser. GitHub is contacted only when you submit a username.</p><div id="downloads"><button id="base" disabled>Download base STL</button><button id="module" disabled>Download module STL</button><button id="manifest">Download print manifest</button></div><output id="message" aria-live="polite"></output></aside><section class="text" id="activity-plan" hidden><h2>Daily GitHub activity</h2><p id="activity-caption"></p><p>Stacks are logarithmic. Empty cells contain no sampled commits, not proof of inactivity. This preview is not a print plan.</p><div class="table"><table><thead><tr><th>Date (UTC)</th><th>Public commits shown</th><th>Tiles stacked</th></tr></thead><tbody id="days"></tbody></table></div></section><section class="text" id="print-plan"><h2>Print plan</h2><p id="geometry-note">Procedural geometry is a design preview, not printable STL. Run <code>npm run models:prepare</code> from <code>web/</code> to enable canonical exact models.</p><div class="table"><table><thead><tr><th>Month</th><th>Contributions</th><th>Cubes</th><th>Base cell</th></tr></thead><tbody id="months"></tbody></table></div><h3>Loaded STL files</h3><ul id="file-list"><li>None</li></ul><p id="total"></p></section></main>`;
let dataset: Dataset = SAMPLE,
  githubActivity: GithubActivity | undefined,
  metadataRequest = 0,
  printSource = "Synthetic sample",
  files: LocalStl[] = [],
  exploded = false;
const visible = new Set([1, 2, 3, 4]);
const canonicalReady = new Set<string>();
const scene = new ProductScene(document.querySelector("#scene")!);
const githubSearch = bindGithubSearch(
  document.querySelector("#github-search")!,
  document.querySelector("#github-username")!,
  document.querySelector("#github-search-status")!,
  (activity) => {
    githubActivity = activity;
    draw();
  },
  undefined,
  () => {
    metadataRequest++;
  },
);
const clearActivity =
  document.querySelector<HTMLButtonElement>("#clear-activity")!;
clearActivity.addEventListener("click", () => {
  githubSearch.cancel();
  githubActivity = undefined;
  const input = document.querySelector<HTMLInputElement>("#github-username")!;
  input.value = "";
  draw();
  input.focus();
});
function toggleView(showActivity: boolean) {
  document.querySelector<HTMLElement>("#activity-plan")!.hidden = !showActivity;
  document.querySelector<HTMLElement>("#print-plan")!.hidden = showActivity;
  clearActivity.hidden = !showActivity;
  document.querySelector("#view-mode")!.textContent = showActivity
    ? "GitShelves / public activity"
    : "GitShelves / monthly 2×6";
  if (!showActivity) {
    document.querySelector("#activity-caption")!.replaceChildren();
    document.querySelector("#days")!.replaceChildren();
  }
  document.querySelector<HTMLButtonElement>("#manifest")!.disabled =
    showActivity;
  for (const id of ["base", "module"])
    document.querySelector<HTMLButtonElement>(`#${id}`)!.disabled =
      showActivity || !canonicalReady.has(id);
}
function draw() {
  const activity = githubActivity;
  toggleView(Boolean(activity));
  if (activity) {
    const days = activityDays(activity);
    scene.showActivity(days, exploded, visible);
    document.querySelector("#state")!.textContent = "Daily design preview";
    document.querySelector("#sample")!.textContent =
      `@${activity.username} · 30 days`;
    document.querySelector("#activity-caption")!.textContent =
      `@${activity.username} · ${days[0]!.date} through ${days.at(-1)!.date} (UTC) · ${activity.sampled} ${activity.limited ? "sampled " : ""}public commits.`;
    document.querySelector("#days")!.innerHTML = days
      .map(
        ({ date, commits, blocks }) =>
          `<tr><td>${date}</td><td>${commits}</td><td>${blocks}</td></tr>`,
      )
      .join("");
    return;
  }
  const bundle = analyzeBundle(dataset, files);
  scene.show(dataset, exploded, files, visible);
  document.querySelector("#sample")!.textContent = printSource;
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
document.querySelector("#reset")!.addEventListener("click", () => {
  scene.reset();
  if (githubActivity) scene.fit();
});
document.querySelector("#fit")!.addEventListener("click", () => scene.fit());
document
  .querySelector<HTMLInputElement>("#metadata")!
  .addEventListener("change", async (e) => {
    const file = ((e.target as HTMLInputElement).files ?? [])[0];
    if (!file) return;
    const request = ++metadataRequest;
    githubSearch.cancel();
    try {
      const contents = await file.text();
      if (request !== metadataRequest) return;
      dataset = parseMetadata(contents);
      githubActivity = undefined;
      printSource = "Local metadata";
      draw();
      message(`Loaded ${file.name}.`);
    } catch (err) {
      if (request !== metadataRequest) return;
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
      loaded.push({
        name: url.split("/").pop()!,
        type,
        colorGroup: 0,
        bytes,
        canonicalBase: type === "base",
      });
      const button = document.querySelector<HTMLButtonElement>(`#${id}`)!;
      canonicalReady.add(id);
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
  if (loaded.length) {
    // Canonical models are defaults, so a late response must not overwrite a
    // local import made while the page was loading.
    if (!files.length) files = loaded;
    draw();
  }
}
draw();
void loadCanonical();
