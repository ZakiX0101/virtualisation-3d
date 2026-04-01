import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

const viewer = document.getElementById("viewer");
const instrumentEl = document.getElementById("instrument");
const woodToneEl = document.getElementById("woodTone");
const textureNameEl = document.getElementById("textureName");
const historyTextEl = document.getElementById("historyText");
const partsListEl = document.getElementById("partsList");

const btnReset = document.getElementById("btnReset");
const btnExplode = document.getElementById("btnExplode");
const btnTable = document.getElementById("btnTable");
const btnChevilles = document.getElementById("btnChevilles");
const btnStrings = document.getElementById("btnStrings");
const btnAll = document.getElementById("btnAll");

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xffffff);

const camera = new THREE.PerspectiveCamera(
  45,
  viewer.clientWidth / viewer.clientHeight,
  0.1,
  100
);
camera.position.set(0, 1.0, 4.5);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(viewer.clientWidth, viewer.clientHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
viewer.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.target.set(0, 0.6, 0);

const hemiLight = new THREE.HemisphereLight(0xffffff, 0xe8edf2, 1.35);
scene.add(hemiLight);

const dirLight = new THREE.DirectionalLight(0xffffff, 1.4);
dirLight.position.set(4, 5, 3);
scene.add(dirLight);

const fillLight = new THREE.DirectionalLight(0xffffff, 0.7);
fillLight.position.set(-3, 3, 4);
scene.add(fillLight);

const floor = new THREE.Mesh(
  new THREE.CircleGeometry(3.5, 64),
  new THREE.MeshStandardMaterial({
    color: 0xf1f4f8,
    roughness: 1.0,
    metalness: 0.0,
  })
);
floor.rotation.x = -Math.PI / 2;
floor.position.y = -1.0;
scene.add(floor);

let instrumentModel = null;
let currentModelUrl = null;
let currentTextureUrl = null;

let lastSeenAt = 0;
const HOLD_MS = 1500;

const textureLoader = new THREE.TextureLoader();
const gltfLoader = new GLTFLoader();

function updateParts(parts = []) {
  partsListEl.innerHTML = "";
  for (const part of parts) {
    const wrapper = document.createElement("div");
    wrapper.className = "part";

    const title = document.createElement("div");
    title.className = "part-title";
    title.textContent = part.name;

    const role = document.createElement("div");
    role.className = "part-role";
    role.textContent = part.role;

    wrapper.appendChild(title);
    wrapper.appendChild(role);
    partsListEl.appendChild(wrapper);
  }
}

function disposeMaterial(material) {
  if (!material) return;
  if (material.map) material.map.dispose?.();
  material.dispose?.();
}

function removeCurrentModel() {
  if (!instrumentModel) return;

  scene.remove(instrumentModel);
  instrumentModel.traverse((obj) => {
    if (obj.isMesh) {
      obj.geometry?.dispose?.();
      if (Array.isArray(obj.material)) {
        obj.material.forEach(disposeMaterial);
      } else {
        disposeMaterial(obj.material);
      }
    }
  });

  instrumentModel = null;
}

function storeBasePositions(model) {
  model.traverse((obj) => {
    if (obj.isMesh && !obj.userData.basePosition) {
      obj.userData.basePosition = obj.position.clone();
    }
  });
}

function resetModelPose() {
  if (!instrumentModel) return;

  instrumentModel.traverse((obj) => {
    if (obj.isMesh && obj.userData.basePosition) {
      obj.position.copy(obj.userData.basePosition);
      obj.visible = true;
    }
  });
}

function getNodeHierarchyName(obj) {
  const names = [];
  let current = obj;

  while (current) {
    if (current.name) names.push(current.name.toLowerCase());
    current = current.parent;
  }

  return names.join(" > ");
}

function getPartType(obj) {
  const fullName = getNodeHierarchyName(obj);

  if (fullName.includes("string")) return "string";
  if (fullName.includes("cheville")) return "cheville";
  if (fullName.includes("table")) return "table";

  return "table";
}

function explodeModel() {
  if (!instrumentModel) return;

  resetModelPose();

  instrumentModel.traverse((obj) => {
    if (!obj.isMesh || !obj.userData.basePosition) return;

    const partType = getPartType(obj);
    const base = obj.userData.basePosition.clone();

    if (partType === "table") {
      obj.position.copy(base.add(new THREE.Vector3(-0.15, 0, 0.10)));
    } else if (partType === "cheville") {
      obj.position.copy(base.add(new THREE.Vector3(0.25, 0.15, 0)));
    } else if (partType === "string") {
      obj.position.copy(base.add(new THREE.Vector3(0.10, 0.02, 0.18)));
    }
  });
}

function showOnlyPart(partKeyword) {
  if (!instrumentModel) return;

  instrumentModel.traverse((obj) => {
    if (!obj.isMesh) return;
    obj.visible = getPartType(obj) === partKeyword;
  });
}

function showAllParts() {
  if (!instrumentModel) return;

  instrumentModel.traverse((obj) => {
    if (obj.isMesh) obj.visible = true;
  });
}

function applyTextureToModel(textureUrl) {
  if (!instrumentModel || !textureUrl) return;

  textureLoader.load(
    textureUrl,
    (loadedTex) => {
      const woodTex = loadedTex.clone();
      woodTex.needsUpdate = true;
      woodTex.flipY = false;
      woodTex.wrapS = THREE.RepeatWrapping;
      woodTex.wrapT = THREE.RepeatWrapping;
      woodTex.colorSpace = THREE.SRGBColorSpace;
      woodTex.anisotropy = renderer.capabilities.getMaxAnisotropy();

      instrumentModel.traverse((obj) => {
        if (!obj.isMesh) return;

        if (Array.isArray(obj.material)) {
          obj.material.forEach(disposeMaterial);
        } else if (obj.material) {
          disposeMaterial(obj.material);
        }

        const partType = getPartType(obj);

        let material;

        if (partType === "string") {
          material = new THREE.MeshStandardMaterial({
            color: 0xffffff,
            roughness: 0.25,
            metalness: 0.35,
          });
        } else if (partType === "cheville") {
          material = new THREE.MeshStandardMaterial({
            color: 0x111111,
            roughness: 0.7,
            metalness: 0.05,
          });
        } else if (partType === "table") {
          material = new THREE.MeshStandardMaterial({
            map: woodTex,
            color: 0xffffff,
            roughness: 0.82,
            metalness: 0.03,
          });
        } else {
          material = new THREE.MeshStandardMaterial({
            color: 0xb58d6b,
            roughness: 0.8,
            metalness: 0.05,
          });
        }

        obj.material = material;
        obj.material.needsUpdate = true;

        if (obj.geometry) {
          obj.geometry.computeVertexNormals();
        }

        obj.castShadow = true;
        obj.receiveShadow = true;
      });
    },
    undefined,
    (err) => {
      console.error("Erreur texture :", err);
    }
  );
}

function centerAndScaleModel(model) {
  const box = new THREE.Box3().setFromObject(model);
  const size = new THREE.Vector3();
  const center = new THREE.Vector3();

  box.getSize(size);
  box.getCenter(center);

  model.position.sub(center);

  const maxDim = Math.max(size.x, size.y, size.z);
  const scale = 2.4 / maxDim;
  model.scale.setScalar(scale);
}

function loadModel(modelUrl, textureUrl) {
  removeCurrentModel();

  gltfLoader.load(
    modelUrl,
    (gltf) => {
      instrumentModel = gltf.scene;
      scene.add(instrumentModel);
      centerAndScaleModel(instrumentModel);
      storeBasePositions(instrumentModel);

      if (textureUrl) {
        applyTextureToModel(textureUrl);
      }
    },
    undefined,
    (err) => {
      console.error("Erreur chargement GLB :", err);
    }
  );
}

async function fetchState() {
  try {
    const res = await fetch("/api/state", { cache: "no-store" });
    const state = await res.json();

    instrumentEl.textContent = state.instrument || "Aucun";
    woodToneEl.textContent = state.wood_tone || "-";
    textureNameEl.textContent = state.texture_name || "-";
    historyTextEl.textContent = state.history || "En attente de détection...";
    updateParts(state.parts || []);

    const shouldShowModel = state.visible && !!state.model_url;

    if (shouldShowModel) {
      lastSeenAt = Date.now();

      if (currentModelUrl !== state.model_url) {
        currentModelUrl = state.model_url;
        currentTextureUrl = state.texture_url || null;
        loadModel(state.model_url, state.texture_url || null);
      } else if ((state.texture_url || null) !== currentTextureUrl) {
        currentTextureUrl = state.texture_url || null;
        if (currentTextureUrl) {
          applyTextureToModel(currentTextureUrl);
        }
      }
    } else if (Date.now() - lastSeenAt > HOLD_MS) {
      removeCurrentModel();
      currentModelUrl = null;
      currentTextureUrl = null;
    }
  } catch (e) {
    console.error("Erreur API :", e);
  }
}

btnReset?.addEventListener("click", () => {
  resetModelPose();
  showAllParts();
});

btnExplode?.addEventListener("click", () => {
  explodeModel();
  showAllParts();
});

btnTable?.addEventListener("click", () => {
  resetModelPose();
  showOnlyPart("table");
});

btnChevilles?.addEventListener("click", () => {
  resetModelPose();
  showOnlyPart("cheville");
});

btnStrings?.addEventListener("click", () => {
  resetModelPose();
  showOnlyPart("string");
});

btnAll?.addEventListener("click", () => {
  resetModelPose();
  showAllParts();
});

function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}

window.addEventListener("resize", () => {
  camera.aspect = viewer.clientWidth / viewer.clientHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(viewer.clientWidth, viewer.clientHeight);
});

setInterval(fetchState, 700);
fetchState();
animate();