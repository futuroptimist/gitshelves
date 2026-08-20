import { SAMPLE_DATASET, parseMetadataText, type Dataset } from "./metadata";
import { createManifest } from "./manifest";
import { loadStlFile, type LocalStl } from "./files";
import { ProductScene } from "./scene";
import type { AssemblyMode } from "./transforms";
function save(
  name: string,
  bytes: BlobPart,
  type = "application/octet-stream",
) {
  const url = URL.createObjectURL(new Blob([bytes], { type })),
    a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}
export function startApp(root: HTMLElement) {
  let dataset: Dataset = SAMPLE_DATASET,
    mode: AssemblyMode = "assembled",
    exact = false;
  const visible = new Set([1, 2, 3, 4]),
    scene = new ProductScene(document.querySelector("#scene")!),
    status = document.querySelector("#status")!,
    table = document.querySelector("#month-list")!,
    files = document.querySelector("#file-list")!,
    error = document.querySelector("#errors")!;
  function render() {
    scene.setDataset(dataset, mode, visible);
    status.textContent = exact ? "Exact STL geometry" : "Design preview";
    table.innerHTML = dataset.months
      .map(
        (m) =>
          `<tr><th>${m.label}</th><td>${m.contributions.toLocaleString()}</td><td>${m.cubes}</td><td>${m.column + 1}, ${m.row + 1}</td></tr>`,
      )
      .join("");
    document.querySelector("#total")!.textContent = String(
      createManifest(dataset, exact).totalCubes,
    );
  }
  root.addEventListener("click", (e) => {
    const b = (e.target as HTMLElement).closest<HTMLButtonElement>("button");
    if (!b) return;
    if (b.dataset.mode) {
      mode = b.dataset.mode as AssemblyMode;
      document
        .querySelectorAll("[data-mode]")
        .forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
      render();
    }
    if (b.id === "reset") scene.reset();
    if (b.id === "fit") scene.fit();
    if (b.id === "manifest")
      save(
        "gitshelves-print-manifest.json",
        JSON.stringify(createManifest(dataset, exact), null, 2),
        "application/json",
      );
  });
  root.addEventListener("change", async (e) => {
    const input = e.target as HTMLInputElement;
    if (input.dataset.color) {
      if (input.checked) visible.add(Number(input.dataset.color));
      else visible.delete(Number(input.dataset.color));
      render();
    }
    if (input.id === "metadata" && input.files?.[0])
      try {
        dataset = parseMetadataText(await input.files[0].text());
        error.textContent = "";
        render();
      } catch (reason) {
        error.textContent =
          reason instanceof Error ? reason.message : String(reason);
      }
    if (input.id === "stls" && input.files) {
      const seen = new Set<string>(),
        loaded: LocalStl[] = [];
      for (const file of input.files)
        try {
          if (seen.has(file.name.toLowerCase()))
            throw new Error(`${file.name}: duplicate filename.`);
          seen.add(file.name.toLowerCase());
          const item = await loadStlFile(file);
          loaded.push(item);
          await scene.addExactStl(
            item.bytes.buffer.slice(
              item.bytes.byteOffset,
              item.bytes.byteOffset + item.bytes.byteLength,
            ) as ArrayBuffer,
          );
        } catch (reason) {
          error.textContent =
            reason instanceof Error ? reason.message : String(reason);
        }
      if (loaded.length) {
        exact = true;
        render();
        for (const item of loaded)
          await scene.addExactStl(
            item.bytes.buffer.slice(
              item.bytes.byteOffset,
              item.bytes.byteOffset + item.bytes.byteLength,
            ) as ArrayBuffer,
          );
        files.innerHTML = loaded
          .map(
            (f) =>
              `<li><button>${f.name}</button> — ${f.type}, ${f.colorGroup ? `color ${f.colorGroup}` : "no color"}, ${f.size.toLocaleString()} bytes</li>`,
          )
          .join("");
        files
          .querySelectorAll("button")
          .forEach((b, i) =>
            b.addEventListener("click", () =>
              save(
                loaded[i]!.name,
                loaded[i]!.bytes.slice().buffer as ArrayBuffer,
              ),
            ),
          );
      }
    }
  });
  fetch("/models/baseplate_2x6.stl")
    .then(async (r) => {
      if (!r.ok || r.headers.get("content-type")?.includes("text/html"))
        throw new Error();
      const base = await r.arrayBuffer(),
        cube = await fetch("/models/contrib_cube.stl").then((x) => {
          if (!x.ok || x.headers.get("content-type")?.includes("text/html"))
            throw new Error();
          return x.arrayBuffer();
        });
      exact = true;
      for (const [id, name, bytes] of [
        ["base-download", "baseplate_2x6.stl", base],
        ["cube-download", "contrib_cube.stl", cube],
      ] as const) {
        const b = document.querySelector<HTMLButtonElement>(`#${id}`)!;
        b.disabled = false;
        b.addEventListener("click", () => save(name, bytes));
      }
      exact = true;
      render();
      return Promise.all([
        scene.addExactStl(base, 0x263442),
        scene.addExactStl(cube),
      ]);
    })
    .then(() => undefined)
    .catch(() => {
      document.querySelector("#model-help")!.textContent =
        "Exact models unavailable. Run npm run prepare:models; proxy geometry is preview-only.";
      render();
    });
  render();
}
