import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { STLLoader } from "three/examples/jsm/loaders/STLLoader.js";
import { HEIGHT_UNIT, moduleY, placement, type Dataset } from "./model";
export class ProductScene {
  private scene = new THREE.Scene();
  private camera = new THREE.OrthographicCamera(-150, 150, 90, -90, 0.1, 2000);
  private renderer: THREE.WebGLRenderer;
  private controls: OrbitControls;
  private group = new THREE.Group();
  private modules?: THREE.InstancedMesh;
  private exactBase?: THREE.BufferGeometry;
  private exactCube?: THREE.BufferGeometry;
  private hidden = false;
  constructor(canvas: HTMLCanvasElement) {
    this.renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: true,
    });
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    this.camera.position.set(260, 230, 280);
    this.camera.lookAt(105, 0, 21);
    this.controls = new OrbitControls(this.camera, canvas);
    this.controls.enableDamping = !matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    this.scene.add(
      new THREE.HemisphereLight(0xbfefff, 0x11161b, 2.2),
      this.group,
    );
    const light = new THREE.DirectionalLight(0xffffff, 3);
    light.position.set(100, 180, 120);
    this.scene.add(light);
    this.resize();
    addEventListener("resize", () => this.resize());
    document.addEventListener("visibilitychange", () => {
      this.hidden = document.hidden;
      if (!this.hidden) this.render();
    });
    this.controls.addEventListener("change", () => this.render());
  }
  compose(data: Dataset, exploded = false) {
    this.group.clear();
    this.modules?.geometry.dispose();
    const baseGeometry = this.exactBase ?? new THREE.BoxGeometry(252, 7, 84);
    const base = new THREE.Mesh(
      baseGeometry,
      new THREE.MeshStandardMaterial({ color: 0x26323a, roughness: 0.72 }),
    );
    base.position.set(105, 3.5, 21);
    if (this.exactBase) base.rotation.x = -Math.PI / 2;
    this.group.add(base);
    const total = data.months.reduce((s, m) => s + m.blocks, 0);
    const geometry =
      this.exactCube ?? new THREE.BoxGeometry(40, HEIGHT_UNIT, 40);
    const material = new THREE.MeshStandardMaterial({
      color: 0x2ff5a5,
      roughness: 0.45,
    });
    this.modules = new THREE.InstancedMesh(geometry, material, total);
    const matrix = new THREE.Matrix4();
    let i = 0;
    for (const month of data.months) {
      const p = placement(month.month);
      for (let level = 0; level < month.blocks; level++) {
        matrix.compose(
          new THREE.Vector3(p.x, moduleY(level, exploded), p.z),
          new THREE.Quaternion().setFromEuler(
            new THREE.Euler(this.exactCube ? -Math.PI / 2 : 0, 0, 0),
          ),
          new THREE.Vector3(1, 1, 1),
        );
        this.modules.setMatrixAt(i++, matrix);
      }
    }
    this.group.add(this.modules);
    this.fit();
  }
  async parseStl(buffer: ArrayBuffer) {
    return new STLLoader().parse(buffer);
  }
  setExact(type: "baseplate" | "cube", geometry: THREE.BufferGeometry) {
    geometry.computeVertexNormals();
    geometry.computeBoundingBox();
    if (!geometry.boundingBox || geometry.boundingBox.isEmpty())
      throw new Error("STL has no plausible nonzero bounds.");
    if (type === "baseplate") this.exactBase = geometry;
    else this.exactCube = geometry;
  }
  setPaletteVisible(groups: number) {
    if (this.modules) this.modules.visible = groups > 0;
    this.render();
  }
  reset() {
    this.camera.position.set(260, 230, 280);
    this.controls.target.set(105, 0, 21);
    this.fit();
  }
  fit() {
    const aspect = innerWidth / Math.max(innerHeight, 1);
    const size = 300;
    this.camera.left = (-size * aspect) / 2;
    this.camera.right = (size * aspect) / 2;
    this.camera.top = size / 2;
    this.camera.bottom = -size / 2;
    this.camera.updateProjectionMatrix();
    this.controls.target.set(105, 20, 21);
    this.controls.update();
    this.render();
  }
  private resize() {
    this.renderer.setSize(innerWidth, innerHeight, false);
    this.fit();
  }
  render() {
    if (!this.hidden) this.renderer.render(this.scene, this.camera);
  }
  dispose() {
    this.controls.dispose();
    this.renderer.dispose();
  }
}
