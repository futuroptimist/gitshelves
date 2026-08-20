import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import type { Dataset } from "./domain";
import { parseStlGeometry, type LocalStl } from "./files";
import { moduleTransform } from "./transforms";
const COLORS = [0x263238, 0x39d98a, 0x36c5d0, 0x158f78, 0x8fffd0];
export type BundleAnalysis = {
  exactBase: boolean;
  proxyBase: boolean;
  exactModule: boolean;
  proxyModule: boolean;
  requiredContributionGroups: number[];
  exactContributionGroups: number[];
  proxyContributionGroups: number[];
  exact: boolean;
};
export function analyzeBundle(
  dataset: Dataset,
  files: LocalStl[],
): BundleAnalysis {
  const requiredContributionGroups = [
    ...new Set(
      dataset.months.flatMap((month) =>
        Array.from({ length: month.blocks }, (_, level) =>
          Math.min(level + 1, 4),
        ),
      ),
    ),
  ].sort();
  const exactBase = files.some((file) => file.type === "base");
  const exactModule = files.some((file) => file.type === "module");
  const importedGroups = new Set(
    files
      .filter((file) => file.type === "contribution")
      .map((file) => Math.min(file.colorGroup, 4)),
  );
  const exactContributionGroups = exactModule
    ? requiredContributionGroups
    : requiredContributionGroups.filter((group) => importedGroups.has(group));
  const proxyContributionGroups = requiredContributionGroups.filter(
    (group) => !exactContributionGroups.includes(group),
  );
  return {
    exactBase,
    proxyBase: !exactBase,
    exactModule,
    proxyModule: !exactModule && proxyContributionGroups.length > 0,
    requiredContributionGroups,
    exactContributionGroups,
    proxyContributionGroups,
    exact: exactBase && proxyContributionGroups.length === 0,
  };
}
export function exactInstancePlan(
  dataset: Dataset,
  exploded: boolean,
  visible = new Set([1, 2, 3, 4]),
) {
  return dataset.months.flatMap((month) =>
    Array.from({ length: month.blocks }, (_, level) => ({
      ...moduleTransform(month, level, exploded),
      group: Math.min(level + 1, 4),
      visible: visible.has(Math.min(level + 1, 4)),
    })),
  );
}
export class ProductScene {
  private scene = new THREE.Scene();
  private camera: THREE.OrthographicCamera;
  private renderer: THREE.WebGLRenderer;
  private controls: OrbitControls;
  private content = new THREE.Group();
  private frame = 0;
  private active = true;
  constructor(private host: HTMLElement) {
    this.scene.background = new THREE.Color(0x10171a);
    this.scene.fog = new THREE.Fog(0x10171a, 380, 720);
    this.scene.add(this.content);
    this.camera = new THREE.OrthographicCamera(-160, 160, 100, -100, 0.1, 1200);
    this.camera.position.set(310, -330, 260);
    this.camera.up.set(0, 0, 1);
    this.renderer = new THREE.WebGLRenderer({
      antialias: true,
      powerPreference: "high-performance",
    });
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    this.renderer.setSize(host.clientWidth, host.clientHeight);
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    host.append(this.renderer.domElement);
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = !matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    this.controls.target.set(126, 42, 20);
    this.scene.add(new THREE.HemisphereLight(0xbdefff, 0x071014, 1.8));
    const key = new THREE.DirectionalLight(0xffffff, 3);
    key.position.set(-100, -100, 300);
    this.scene.add(key);
    new ResizeObserver(() => this.resize()).observe(host);
    document.addEventListener("visibilitychange", () => {
      this.active = !document.hidden;
      if (this.active) this.render();
    });
    this.render();
  }
  show(
    dataset: Dataset,
    exploded: boolean,
    files: LocalStl[] = [],
    visible = new Set([1, 2, 3, 4]),
  ) {
    this.clear();
    const analysis = analyzeBundle(dataset, files);
    this.addProxy(dataset, exploded, visible, analysis);
    this.addExact(dataset, exploded, files, visible, analysis);
    this.fit();
  }
  private addProxy(
    dataset: Dataset,
    exploded: boolean,
    visible: Set<number>,
    analysis: BundleAnalysis,
  ) {
    if (analysis.proxyBase) {
      const base = new THREE.Mesh(
        new THREE.BoxGeometry(256, 88, 6),
        new THREE.MeshStandardMaterial({
          color: COLORS[0],
          roughness: 0.65,
          metalness: 0.15,
        }),
      );
      base.position.set(126, 42, 3);
      this.content.add(base);
    }
    const proxyGroups = new Set(analysis.proxyContributionGroups);
    const plan = exactInstancePlan(dataset, exploded, visible).filter((item) =>
      proxyGroups.has(item.group),
    );
    const geometry = new THREE.BoxGeometry(38, 38, 7);
    const mesh = new THREE.InstancedMesh(
      geometry,
      new THREE.MeshStandardMaterial({ color: COLORS[1], roughness: 0.45 }),
      plan.length,
    );
    const matrix = new THREE.Matrix4();
    plan.forEach((item, index) => {
      matrix.makeTranslation(item.x, item.y, item.z);
      if (!item.visible) matrix.makeScale(0, 0, 0);
      mesh.setMatrixAt(index, matrix);
      mesh.setColorAt(index, new THREE.Color(COLORS[item.group]));
    });
    if (plan.length) this.content.add(mesh);
    else {
      geometry.dispose();
      (mesh.material as THREE.Material).dispose();
    }
  }
  private addExact(
    dataset: Dataset,
    exploded: boolean,
    files: LocalStl[],
    visible: Set<number>,
    analysis: BundleAnalysis,
  ) {
    const base = files.find((file) => file.type === "base");
    const module = files.find((file) => file.type === "module");
    if (base) this.addMesh(base, parseStlGeometry(base.bytes));
    if (module && analysis.exactModule) {
      const geometry = parseStlGeometry(module.bytes);
      const plan = exactInstancePlan(dataset, exploded, visible);
      const total = plan.length;
      const mesh = new THREE.InstancedMesh(
        geometry,
        new THREE.MeshStandardMaterial({ color: COLORS[1] }),
        total,
      );
      const matrix = new THREE.Matrix4();
      let index = 0;
      for (const p of plan) {
        const group = p.group;
        matrix.makeTranslation(p.x, p.y, p.z);
        if (!p.visible) matrix.makeScale(0, 0, 0);
        mesh.setMatrixAt(index, matrix);
        mesh.setColorAt(index++, new THREE.Color(COLORS[group]));
      }
      this.content.add(mesh);
    }
    for (const file of files) {
      if (
        file === base ||
        file === module ||
        (analysis.exactModule && file.type === "contribution") ||
        !analysis.exactContributionGroups.includes(
          Math.min(file.colorGroup, 4),
        ) ||
        !visible.has(Math.min(file.colorGroup, 4))
      )
        continue;
      this.addMesh(file, parseStlGeometry(file.bytes));
    }
  }
  private addMesh(file: LocalStl, geometry: THREE.BufferGeometry) {
    geometry.computeVertexNormals();
    this.content.add(
      new THREE.Mesh(
        geometry,
        new THREE.MeshStandardMaterial({
          color: COLORS[Math.min(file.colorGroup, 4)],
        }),
      ),
    );
  }
  private clear() {
    for (const object of [...this.content.children]) {
      this.content.remove(object);
      const mesh = object as THREE.Mesh;
      mesh.geometry?.dispose();
      const material = mesh.material;
      if (Array.isArray(material)) material.forEach((m) => m.dispose());
      else material?.dispose();
    }
  }
  reset() {
    this.camera.position.set(310, -330, 260);
    this.controls.target.set(126, 42, 20);
    this.controls.update();
  }
  fit() {
    const box = new THREE.Box3().setFromObject(this.content);
    if (box.isEmpty()) return;
    const sphere = box.getBoundingSphere(new THREE.Sphere());
    this.controls.target.copy(sphere.center);
    const size = Math.max(sphere.radius * 2.5, 120);
    const aspect = this.host.clientWidth / Math.max(this.host.clientHeight, 1);
    this.camera.left = (-size * aspect) / 2;
    this.camera.right = (size * aspect) / 2;
    this.camera.top = size / 2;
    this.camera.bottom = -size / 2;
    this.camera.updateProjectionMatrix();
  }
  private resize() {
    const w = this.host.clientWidth,
      h = this.host.clientHeight;
    if (!w || !h) return;
    const vertical = this.camera.top - this.camera.bottom;
    const aspect = w / h;
    this.camera.left = (-vertical * aspect) / 2;
    this.camera.right = (vertical * aspect) / 2;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h, false);
  }
  private render = () => {
    if (!this.active) return;
    this.frame = requestAnimationFrame(this.render);
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  };
  dispose() {
    cancelAnimationFrame(this.frame);
    this.clear();
    this.controls.dispose();
    this.renderer.dispose();
    this.renderer.domElement.remove();
  }
}
