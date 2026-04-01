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
scene.background = new THREE.Color(0x11151b);

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
viewer.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.target.set(0, 0.6, 0);

const hemiLight = new THREE.HemisphereLight(0xffffff, 0x334455, 1.2);
scene.add(hemiLight);

const dirLight = new THREE.DirectionalLight(0xffffff, 1.3);
dirLight.position.set(4, 5, 3);
scene.add(dirLight);

const floor = new THREE.Mesh(
  new THREE.CircleGeometry(3.5, 64),
  new THREE.MeshStandardMaterial({ color: 0x1b222b, roughness: 1.0 })
);
floor.rotation.x = -Math.PI / 2;
floor.position.y = -1.0;
scene.add(floor);

let oudModel = null;
let currentModelUrl = null;
let currentTextureUrl = null;

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

function removeCurrentModel() {
  if (!oudModel) return;
  scene.remove(oudModel);
  oudModel.traverse((obj) => {
    if (obj.isMesh) {
      obj.geometry?.dispose?.();
      if (Array.isArray(obj.material)) {
        obj.material.forEach((m) => m.dispose?.());
      } else {
        obj.material?.dispose?.();
      }
    }
  });
  oudModel = null;
}

function storeBasePositions(model) {
  model.traverse((obj) => {
    if (obj.isMesh && !obj.userData.basePosition) {
      obj.userData.basePosition = obj.position.clone();
    }
  });
}

function resetModelPose() {
  if (!oudModel) return;
  oudModel.traverse((obj) => {
    if (obj.isMesh && obj.userData.basePosition) {
      obj.position.copy(obj.userData.basePosition);
      obj.visible = true;
    }
  });
}

function explodeModel() {
  if (!oudModel) return;

  resetModelPose();

  oudModel.traverse((obj) => {
    if (!obj.isMesh || !obj.userData.basePosition) return;

    const name = obj.name.toLowerCase();
    const base = obj.userData.basePosition.clone();

    if (name.includes("table")) {
      obj.position.copy(base.add(new THREE.Vector3(-0.15, 0, 0.10)));
    } else if (name.includes("cheville")) {
      obj.position.copy(base.add(new THREE.Vector3(0.25, 0.15, 0)));
    } else if (name.includes("string")) {
      obj.position.copy(base.add(new THREE.Vector3(0.10, 0.02, 0.18)));
    }
  });
}

function showOnlyPart(partKeyword) {
  if (!oudModel) return;

  oudModel.traverse((obj) => {
    if (!obj.isMesh) return;
    const name = obj.name.toLowerCase();
    obj.visible = name.includes(partKeyword);
  });
}

function showAllParts() {
  if (!oudModel) return;
  oudModel.traverse((obj) => {
    if (obj.isMesh) obj.visible = true;
  });
}

function applyTextureToModel(textureUrl) {
  if (!oudModel || !textureUrl) return;

  textureLoader.load(
    textureUrl,
    (tex) => {
      tex.flipY = false;
      tex.wrapS = THREE.RepeatWrapping;
      tex.wrapT = THREE.RepeatWrapping;

      oudModel.traverse((obj) => {
        if (!obj.isMesh) return;

        const name = obj.name.toLowerCase();

        if (name.includes("string")) {
          obj.material = new THREE.MeshStandardMaterial({
            color: 0xe6e6e6,
            roughness: 0.3,
            metalness: 0.45,
          });
        } else if (name.includes("cheville")) {
          obj.material = new THREE.MeshStandardMaterial({
            map: tex,
            roughness: 0.75,
            metalness: 0.05,
          });
        } else if (name.includes("table")) {
          obj.material = new THREE.MeshStandardMaterial({
            map: tex,
            roughness: 0.82,
            metalness: 0.03,
          });
        } else {
          obj.material = new THREE.MeshStandardMaterial({
            color: 0xb58d6b,
            roughness: 0.8,
            metalness: 0.05,
          });
        }
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
      oudModel = gltf.scene;
      scene.add(oudModel);

      centerAndScaleModel(oudModel);
      storeBasePositions(oudModel);
      applyTextureToModel(textureUrl);
    },
    undefined,
    (err) => {
      console.error("Erreur chargement GLB :", err);
    }
  );
}

async function fetchState() {
  try {
    const res = await fetch("/api/state");
    const state = await res.json();

    instrumentEl.textContent = state.instrument || "Aucun";
    woodToneEl.textContent = state.wood_tone || "-";
    textureNameEl.textContent = state.texture_name || "-";
    historyTextEl.textContent = state.history || "En attente de détection...";
    updateParts(state.parts || []);

    if (state.visible && state.instrument === "oud") {
      if (currentModelUrl !== state.model_url) {
        currentModelUrl = state.model_url;
        currentTextureUrl = state.texture_url;
        loadModel(state.model_url, state.texture_url);
      } else if (currentTextureUrl !== state.texture_url) {
        currentTextureUrl = state.texture_url;
        applyTextureToModel(state.texture_url);
      }
    } else {
      removeCurrentModel();
      currentModelUrl = null;
      currentTextureUrl = null;
    }
  } catch (e) {
    console.error("Erreur API :", e);
  }
}

btnReset.addEventListener("click", () => {
  resetModelPose();
  showAllParts();
});

btnExplode.addEventListener("click", () => {
  explodeModel();
  showAllParts();
});

btnTable.addEventListener("click", () => {
  resetModelPose();
  showOnlyPart("table");
});

btnChevilles.addEventListener("click", () => {
  resetModelPose();
  showOnlyPart("cheville");
});

btnStrings.addEventListener("click", () => {
  resetModelPose();
  showOnlyPart("string");
});

btnAll.addEventListener("click", () => {
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