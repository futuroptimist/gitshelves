import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { STLLoader } from "three/examples/jsm/loaders/STLLoader.js";
import type { Dataset } from "./metadata";
import { cubeTransform, type AssemblyMode } from "./transforms";
const COLORS = [0x39d98a, 0x41c7d9, 0x6d83f2, 0xb56cff];
export class ProductScene {
  private scene = new THREE.Scene();
  private camera: THREE.OrthographicCamera;
  private renderer: THREE.WebGLRenderer;
  private controls: OrbitControls;
  private content = new THREE.Group();
  private frame = 0;
  private visible = true;
  private reduced: boolean;
  constructor(private host: HTMLElement) {
    this.reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
    this.scene.background = new THREE.Color(0x090d12);
    this.camera = new THREE.OrthographicCamera(-130, 130, 90, -90, 0.1, 2000);
    this.camera.position.set(210, -230, 190);
    this.camera.up.set(0, 0, 1);
    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    host.append(this.renderer.domElement);
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = !this.reduced;
    this.controls.addEventListener("change", () => this.render());
    this.scene.add(
      this.content,
      new THREE.HemisphereLight(0xbcecff, 0x12141c, 2),
    );
    const key = new THREE.DirectionalLight(0xffffff, 3);
    key.position.set(100, -80, 180);
    this.scene.add(key);
    this.resize();
    addEventListener("resize", () => this.resize());
    document.addEventListener("visibilitychange", () => {
      this.visible = !document.hidden;
      if (this.visible) this.animate();
    });
    this.reset();
    this.animate();
  }
  setDataset(
    dataset: Dataset,
    mode: AssemblyMode,
    visible: ReadonlySet<number>,
  ) {
    this.clear();
    const base = new THREE.Mesh(
      new THREE.BoxGeometry(252, 84, 7),
      new THREE.MeshStandardMaterial({ color: 0x202a35 }),
    );
    base.position.set(105, 21, 3.5);
    this.content.add(base);
    for (let group = 0; group < 4; group++) {
      const entries = dataset.months
        .flatMap((m) =>
          Array.from({ length: m.cubes }, (_, level) => ({ m, level })),
        )
        .filter((x) => Math.min(x.level, 3) === group);
      const mesh = new THREE.InstancedMesh(
        new THREE.BoxGeometry(38, 38, 7),
        new THREE.MeshStandardMaterial({ color: COLORS[group] }),
        entries.length,
      );
      entries.forEach(({ m, level }, i) => {
        const t = cubeTransform(m, level, mode);
        mesh.setMatrixAt(
          i,
          new THREE.Matrix4().makeTranslation(t.x, t.y, t.z + 3.5),
        );
      });
      mesh.visible = visible.has(group + 1);
      this.content.add(mesh);
    }
    this.fit();
  }
  async addExactStl(bytes: ArrayBuffer, color = 0x39d98a) {
    const geometry = new STLLoader().parse(bytes);
    geometry.computeVertexNormals();
    this.content.add(
      new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({ color })),
    );
    this.fit();
  }
  reset() {
    this.camera.position.set(210, -230, 190);
    this.controls.target.set(105, 21, 20);
    this.controls.update();
    this.fit();
  }
  fit() {
    const box = new THREE.Box3().setFromObject(this.content);
    if (box.isEmpty()) return;
    const size = box.getSize(new THREE.Vector3()),
      center = box.getCenter(new THREE.Vector3()),
      span = Math.max(size.x, size.y, size.z * 1.4, 100) * 0.72;
    this.controls.target.copy(center);
    this.camera.left = -span;
    this.camera.right = span;
    this.camera.top = span * 0.7;
    this.camera.bottom = -span * 0.7;
    this.camera.updateProjectionMatrix();
    this.render();
  }
  private resize() {
    const w = this.host.clientWidth,
      h = this.host.clientHeight || 1;
    this.renderer.setSize(w, h, false);
    this.camera.top = (this.camera.right * h) / w;
    this.camera.bottom = -this.camera.top;
    this.camera.updateProjectionMatrix();
    this.render();
  }
  private animate = () => {
    if (!this.visible) return;
    this.frame = requestAnimationFrame(this.animate);
    if (!this.reduced) this.controls.update();
    this.render();
  };
  private render() {
    this.renderer.render(this.scene, this.camera);
  }
  private clear() {
    for (const child of [...this.content.children]) {
      this.content.remove(child);
      if (child instanceof THREE.Mesh) {
        child.geometry.dispose();
        (Array.isArray(child.material)
          ? child.material
          : [child.material]
        ).forEach((x) => x.dispose());
      }
    }
  }
  dispose() {
    cancelAnimationFrame(this.frame);
    this.clear();
    this.controls.dispose();
    this.renderer.dispose();
  }
}
