/**
 * Photo-accurate Elvessora PBR bottles — real 3D geometry only.
 * Bottle A: frosted square glass + round red crystal cap
 * Bottle B: frosted square glass + black ring + crushed-gold cap
 */

import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';

let frostRoughnessMap = null;
let frostNormalMap = null;

function ensureFrostMaps(THREE) {
  if (frostRoughnessMap) return { roughnessMap: frostRoughnessMap, normalMap: frostNormalMap };

  const size = 512;
  const roughCanvas = document.createElement('canvas');
  roughCanvas.width = size;
  roughCanvas.height = size;
  const rctx = roughCanvas.getContext('2d');
  const roughImg = rctx.createImageData(size, size);
  const normCanvas = document.createElement('canvas');
  normCanvas.width = size;
  normCanvas.height = size;
  const nctx = normCanvas.getContext('2d');
  const normImg = nctx.createImageData(size, size);

  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      const i = (y * size + x) * 4;
      const n = 0.55 + Math.random() * 0.45;
      const v = Math.floor(n * 255);
      roughImg.data[i] = v;
      roughImg.data[i + 1] = v;
      roughImg.data[i + 2] = v;
      roughImg.data[i + 3] = 255;
      normImg.data[i] = 128 + Math.floor((Math.random() - 0.5) * 22);
      normImg.data[i + 1] = 128 + Math.floor((Math.random() - 0.5) * 22);
      normImg.data[i + 2] = 255;
      normImg.data[i + 3] = 255;
    }
  }

  rctx.putImageData(roughImg, 0, 0);
  nctx.putImageData(normImg, 0, 0);

  frostRoughnessMap = new THREE.CanvasTexture(roughCanvas);
  frostRoughnessMap.wrapS = frostRoughnessMap.wrapT = THREE.RepeatWrapping;
  frostRoughnessMap.repeat.set(3, 3);

  frostNormalMap = new THREE.CanvasTexture(normCanvas);
  frostNormalMap.wrapS = frostNormalMap.wrapT = THREE.RepeatWrapping;
  frostNormalMap.repeat.set(3, 3);

  return { roughnessMap: frostRoughnessMap, normalMap: frostNormalMap };
}

function glassMat(THREE, liquidHex, glassHex = '#f8f4ee') {
  const { roughnessMap, normalMap } = ensureFrostMaps(THREE);
  return new THREE.MeshPhysicalMaterial({
    color: glassHex,
    metalness: 0.03,
    roughness: 0.42,
    roughnessMap,
    normalMap,
    normalScale: new THREE.Vector2(0.22, 0.22),
    transmission: 0.78,
    thickness: 1.5,
    ior: 1.52,
    transparent: true,
    attenuationColor: new THREE.Color(liquidHex),
    attenuationDistance: 0.72,
    envMapIntensity: 1.85,
    clearcoat: 0.9,
    clearcoatRoughness: 0.18,
  });
}

function liquidMat(THREE, hex) {
  return new THREE.MeshPhysicalMaterial({
    color: hex,
    metalness: 0.1,
    roughness: 0.25,
    transmission: 0.08,
    thickness: 0.5,
    emissive: new THREE.Color(hex),
    emissiveIntensity: 0.22,
    envMapIntensity: 0.9,
  });
}

function goldMat(THREE) {
  return new THREE.MeshPhysicalMaterial({
    color: 0xd4af37,
    metalness: 1,
    roughness: 0.16,
    envMapIntensity: 2.4,
    clearcoat: 0.65,
    clearcoatRoughness: 0.12,
  });
}

function addLabelPanel(THREE, group, w, h, z) {
  const mat = new THREE.MeshPhysicalMaterial({
    color: 0xf5efe4,
    metalness: 0.62,
    roughness: 0.34,
    clearcoat: 0.92,
    clearcoatRoughness: 0.1,
    envMapIntensity: 1.6,
  });
  mat.name = 'label';
  const mesh = new THREE.Mesh(new RoundedBoxGeometry(w, h, 0.035, 4, 0.01), mat);
  mesh.name = 'label_decal';
  mesh.position.set(0, 0.05, z);
  mesh.castShadow = true;
  group.add(mesh);
}

function addPedestal(THREE, group, y) {
  const marble = new THREE.MeshPhysicalMaterial({
    color: 0x080c14,
    metalness: 0.78,
    roughness: 0.26,
    envMapIntensity: 1.2,
  });
  const gold = goldMat(THREE);
  const base = new THREE.Mesh(new THREE.CylinderGeometry(0.74, 0.8, 0.09, 64), marble);
  base.position.y = y;
  base.receiveShadow = true;
  base.castShadow = true;
  group.add(base);
  const rim = new THREE.Mesh(new THREE.TorusGeometry(0.74, 0.013, 12, 64), gold);
  rim.rotation.x = Math.PI / 2;
  rim.position.y = y + 0.048;
  group.add(rim);
}

function addFloorShadow(THREE, group, y) {
  const shadow = new THREE.Mesh(
    new THREE.CircleGeometry(0.74, 48),
    new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.42 })
  );
  shadow.rotation.x = -Math.PI / 2;
  shadow.position.y = y;
  group.add(shadow);
}

function addCrushedGoldCap(THREE, group, crushed, cx, cy, cz, size) {
  const base = new THREE.Mesh(new RoundedBoxGeometry(size, size * 0.55, size, 4, 0.035), crushed);
  base.position.set(cx, cy, cz);
  base.castShadow = true;
  group.add(base);

  const grid = 5;
  const step = size / (grid + 1);
  for (let row = 0; row < grid; row += 1) {
    for (let col = 0; col < grid; col += 1) {
      const fx = (col - (grid - 1) / 2) * step * 0.85;
      const fz = (row - (grid - 1) / 2) * step * 0.85;
      const h = 0.025 + Math.random() * 0.055;
      const gem = new THREE.Mesh(new RoundedBoxGeometry(step * 0.72, h, step * 0.72, 2, 0.008), crushed);
      gem.position.set(cx + fx, cy + size * 0.28 + h * 0.5, cz + fz);
      gem.rotation.set(Math.random() * 0.5, Math.random() * Math.PI, Math.random() * 0.4);
      gem.castShadow = true;
      group.add(gem);
    }
  }
}

/** Bottle A — frosted glass + gold collar + red crystal sphere cap */
export function createBottleA(THREE) {
  const group = new THREE.Group();
  group.name = 'BottleA_template';

  const glass = glassMat(THREE, '#d4a040', '#f8f4ee');
  const liquid = liquidMat(THREE, '#d4a040');
  const gold = goldMat(THREE);
  const crystal = new THREE.MeshPhysicalMaterial({
    color: 0x8b1530,
    metalness: 0.12,
    roughness: 0.03,
    transmission: 0.58,
    thickness: 0.9,
    ior: 1.78,
    transparent: true,
    envMapIntensity: 2.5,
    attenuationColor: new THREE.Color(0xff2038),
    attenuationDistance: 0.25,
    clearcoat: 1,
    clearcoatRoughness: 0.02,
  });

  const body = new THREE.Mesh(new RoundedBoxGeometry(0.8, 1.18, 0.8, 8, 0.1), glass);
  body.name = 'glass_body';
  body.position.y = 0.18;
  body.castShadow = true;
  body.receiveShadow = true;
  group.add(body);

  const juice = new THREE.Mesh(new RoundedBoxGeometry(0.62, 0.92, 0.62, 4, 0.06), liquid);
  juice.name = 'liquid';
  juice.position.y = 0.06;
  group.add(juice);

  addLabelPanel(THREE, group, 0.6, 0.76, 0.415);

  const collar = new THREE.Mesh(new THREE.CylinderGeometry(0.21, 0.26, 0.05, 48), gold);
  collar.name = 'gold_collar';
  collar.position.y = 0.8;
  group.add(collar);

  const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.17, 0.08, 32), gold);
  neck.name = 'gold_neck';
  neck.position.y = 0.87;
  group.add(neck);

  const cap = new THREE.Mesh(new THREE.SphereGeometry(0.34, 64, 48), crystal);
  cap.name = 'cap_crystal';
  cap.position.y = 1.18;
  cap.castShadow = true;
  group.add(cap);

  addPedestal(THREE, group, -0.44);
  addFloorShadow(THREE, group, -0.5);
  return group;
}

/** Bottle B — matches Elvessora square bottle + crushed gold cap (photo reference) */
export function createBottleB(THREE) {
  const group = new THREE.Group();
  group.name = 'BottleB_template';

  const glass = glassMat(THREE, '#d4a030', '#faf6f0');
  const liquid = liquidMat(THREE, '#d4a030');
  const gold = goldMat(THREE);
  const crushed = new THREE.MeshPhysicalMaterial({
    color: 0xe2c060,
    metalness: 1,
    roughness: 0.38,
    envMapIntensity: 2.2,
    clearcoat: 0.4,
  });
  const black = new THREE.MeshPhysicalMaterial({
    color: 0x0a0a0a,
    metalness: 0.85,
    roughness: 0.2,
    envMapIntensity: 1.5,
  });

  const body = new THREE.Mesh(new RoundedBoxGeometry(0.84, 1.2, 0.84, 8, 0.1), glass);
  body.name = 'glass_body';
  body.position.y = 0.16;
  body.castShadow = true;
  body.receiveShadow = true;
  group.add(body);

  const juice = new THREE.Mesh(new RoundedBoxGeometry(0.66, 0.94, 0.66, 4, 0.06), liquid);
  juice.name = 'liquid';
  juice.position.y = 0.04;
  group.add(juice);

  addLabelPanel(THREE, group, 0.62, 0.78, 0.428);

  const collar = new THREE.Mesh(new RoundedBoxGeometry(0.44, 0.045, 0.44, 3, 0.015), gold);
  collar.name = 'gold_collar';
  collar.position.y = 0.79;
  group.add(collar);

  const blackRing = new THREE.Mesh(new RoundedBoxGeometry(0.56, 0.085, 0.56, 3, 0.025), black);
  blackRing.name = 'cap_black_ring';
  blackRing.position.y = 0.88;
  group.add(blackRing);

  addCrushedGoldCap(THREE, group, crushed, 0, 1.12, 0, 0.52);

  addPedestal(THREE, group, -0.44);
  addFloorShadow(THREE, group, -0.5);
  return group;
}
