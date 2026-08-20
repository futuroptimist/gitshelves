import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { STLLoader } from "three/examples/jsm/loaders/STLLoader.js";
import { placement, type Dataset } from "./model";
export type Mode = "assembled" | "exploded";
export function moduleTransform(month: number, level: number, mode: Mode) {
  const p = placement(month);
  return new THREE.Matrix4().makeTranslation(
    p.x - 105,
    p.y - 21,
    7 + level * 7 + (mode === "exploded" ? level * 7 : 0),
  );
}
export function createScene(canvas: HTMLCanvasElement, data: Dataset) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x10151b);
  scene.fog = new THREE.Fog(0x10151b, 350, 700);
  const camera = new THREE.OrthographicCamera(-170, 170, 110, -110, 1, 1000);
  camera.position.set(260, -300, 250);
  camera.lookAt(0, 0, 0);
  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: false,
  });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.setSize(innerWidth, innerHeight);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  const controls = new OrbitControls(camera, canvas);
  controls.enableDamping = !matchMedia("(prefers-reduced-motion: reduce)")
    .matches;
  const baseMaterial = new THREE.MeshStandardMaterial({
    color: 0x18313a,
    roughness: 0.65,
  });
  let baseGeometry: THREE.BufferGeometry = new THREE.BoxGeometry(252, 84, 7);
  let base = new THREE.Mesh(baseGeometry, baseMaterial);
  scene.add(base);
  const count = data.months.reduce((n, m) => n + m.blocks, 0);
  let cubeGeometry: THREE.BufferGeometry = new THREE.BoxGeometry(41.5, 41.5, 7);
  const cubeMaterial = new THREE.MeshStandardMaterial({
    color: 0x39d98a,
    roughness: 0.55,
  });
  let cubes = new THREE.InstancedMesh(cubeGeometry, cubeMaterial, count);
  const palette = [0x65f0bd, 0x36dca5, 0x35cce8, 0x79f2ff];
  let activeMode: Mode = "assembled";
  let visibleGroups = 4;
  const updateInstances = () => {
    index = 0;
    for (const month of data.months)
      for (let level = 0; level < month.blocks; level++) {
        const transform = moduleTransform(month.month, level, activeMode);
        if (level + 1 > visibleGroups)
          transform.scale(new THREE.Vector3(0, 0, 0));
        cubes.setMatrixAt(index, transform);
        cubes.setColorAt(
          index,
          new THREE.Color(palette[Math.min(level, palette.length - 1)]),
        );
        index++;
      }
    cubes.instanceMatrix.needsUpdate = true;
    if (cubes.instanceColor) cubes.instanceColor.needsUpdate = true;
  };
  let index = 0;
  updateInstances();
  scene.add(cubes);
  scene.add(new THREE.HemisphereLight(0x9defff, 0x121722, 2));
  const key = new THREE.DirectionalLight(0xffffff, 4);
  key.position.set(-80, -120, 260);
  scene.add(key);
  let frame = 0;
  const render = () => {
    if (document.hidden) return;
    controls.update();
    renderer.render(scene, camera);
    frame = requestAnimationFrame(render);
  };
  render();
  const fit = () => {
    camera.zoom = Math.min(innerWidth / 340, innerHeight / 220);
    camera.updateProjectionMatrix();
  };
  addEventListener("resize", () => {
    renderer.setSize(innerWidth, innerHeight);
    fit();
  });
  return {
    scene,
    camera,
    controls,
    renderer,
    fit,
    reset() {
      camera.position.set(260, -300, 250);
      camera.lookAt(0, 0, 0);
      controls.target.set(0, 0, 0);
      fit();
    },
    setMode(mode: Mode) {
      activeMode = mode;
      updateInstances();
    },
    setColorGroups(groups: number) {
      visibleGroups = Math.max(1, Math.min(4, groups));
      updateInstances();
    },
    showExact(
      loadedBaseGeometry: THREE.BufferGeometry,
      loadedCubeGeometry: THREE.BufferGeometry,
    ) {
      const normalize = (loaded: THREE.BufferGeometry) => {
        const geometry = loaded.clone();
        geometry.computeBoundingBox();
        const bounds = geometry.boundingBox;
        if (!bounds) throw new Error("Exact STL has no finite bounds");
        geometry.translate(
          -(bounds.min.x + bounds.max.x) / 2,
          -(bounds.min.y + bounds.max.y) / 2,
          -bounds.min.z,
        );
        geometry.computeVertexNormals();
        return geometry;
      };
      scene.remove(base, cubes);
      baseGeometry.dispose();
      cubeGeometry.dispose();
      baseGeometry = normalize(loadedBaseGeometry);
      cubeGeometry = normalize(loadedCubeGeometry);
      base = new THREE.Mesh(baseGeometry, baseMaterial);
      cubes = new THREE.InstancedMesh(cubeGeometry, cubeMaterial, count);
      updateInstances();
      scene.add(base, cubes);
    },
    dispose() {
      cancelAnimationFrame(frame);
      controls.dispose();
      baseGeometry.dispose();
      cubeGeometry.dispose();
      baseMaterial.dispose();
      cubeMaterial.dispose();
      renderer.dispose();
    },
  };
}
export function parseStl(buffer: ArrayBuffer) {
  return new STLLoader().parse(buffer);
}
