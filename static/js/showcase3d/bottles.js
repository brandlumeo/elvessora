/**
 * GLB-first · PBR procedural bottles only — never image-on-box billboards.
 */

import { SHOWCASE_PATHS } from './config.js';
import { getLabelTexture, applyFragranceStyle } from './labels.js';
import { createBottleA, createBottleB } from './proceduralBottles.js';

const GLB_TIMEOUT_MS = 6000;

async function urlExists(url) {
  try {
    const ctrl = new AbortController();
    const timer = window.setTimeout(() => ctrl.abort(), 2000);
    const res = await fetch(url, { method: 'HEAD', signal: ctrl.signal });
    window.clearTimeout(timer);
    return res.ok;
  } catch (_err) {
    return false;
  }
}

async function loadFirstGltf(loader, urls) {
  for (const url of urls) {
    // eslint-disable-next-line no-await-in-loop
    if (!(await urlExists(url))) continue;
    try {
      // eslint-disable-next-line no-await-in-loop
      const gltf = await Promise.race([
        loader.loadAsync(url),
        new Promise((_, reject) => {
          window.setTimeout(() => reject(new Error('GLB timeout')), GLB_TIMEOUT_MS);
        }),
      ]);
      if (gltf?.scene) return gltf.scene;
    } catch (_err) {
      /* try next path */
    }
  }
  return null;
}

function normalizeTemplate(THREE, root, targetHeight = 2.35) {
  root.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(root);
  const size = new THREE.Vector3();
  const center = new THREE.Vector3();
  box.getSize(size);
  box.getCenter(center);
  const maxDim = Math.max(size.x, size.y, size.z) || 1;
  const scale = targetHeight / maxDim;
  root.scale.setScalar(scale);
  root.position.sub(center.multiplyScalar(scale));
  root.position.y += (size.y * scale) / 2;
  return root;
}

function styleClone(THREE, clone, perfume, label) {
  applyFragranceStyle(THREE, clone, perfume, label);
  clone.traverse((child) => {
    if (!child.isMesh) return;
    const n = `${child.name || ''} ${child.material?.name || ''}`.toLowerCase();
    if (n.includes('label')) {
      const mat = child.material.clone();
      mat.map = label;
      mat.transparent = true;
      mat.depthWrite = true;
      mat.metalness = 0.55;
      mat.roughness = 0.38;
      mat.envMapIntensity = 1.4;
      mat.needsUpdate = true;
      child.material = mat;
    }
    if (n.includes('liquid') && perfume.liquidColor) {
      const mat = child.material.clone();
      mat.color.set(perfume.liquidColor);
      if (mat.emissive) {
        mat.emissive.set(perfume.liquidColor);
        mat.emissiveIntensity = 0.2;
      }
      if (mat.attenuationColor) mat.attenuationColor.set(perfume.liquidColor);
      mat.needsUpdate = true;
      child.material = mat;
    }
    if (n.includes('glass') && perfume.liquidColor) {
      const mat = child.material.clone();
      if (mat.attenuationColor) mat.attenuationColor.set(perfume.liquidColor);
      if (perfume.glassTint && mat.color) mat.color.set(perfume.glassTint);
      mat.needsUpdate = true;
      child.material = mat;
    }
  });
}

export async function loadBottleTemplates(THREE, GLTFLoader) {
  const loader = new GLTFLoader();
  const [gltfA, gltfB] = await Promise.all([
    loadFirstGltf(loader, SHOWCASE_PATHS.bottleA),
    loadFirstGltf(loader, SHOWCASE_PATHS.bottleB),
  ]);

  return {
    A: gltfA ? normalizeTemplate(THREE, gltfA) : createBottleA(THREE),
    B: gltfB ? normalizeTemplate(THREE, gltfB) : createBottleB(THREE),
    source: { A: gltfA ? 'glb' : 'procedural', B: gltfB ? 'glb' : 'procedural' },
  };
}

export async function buildFragranceBottles(THREE, templates, perfumes) {
  const bottles = [];

  for (const perfume of perfumes) {
    const type = perfume.bottle === 'B' ? 'B' : 'A';
    const clone = templates[type].clone(true);

    // eslint-disable-next-line no-await-in-loop
    const label = await getLabelTexture(
      THREE,
      perfume,
      SHOWCASE_PATHS.textures,
      SHOWCASE_PATHS.labels
    );

    styleClone(THREE, clone, perfume, label);

    clone.userData.perfumeId = perfume.id;
    clone.userData.sku = perfume.sku;
    clone.userData.bottleType = perfume.bottle;
    clone.userData.source = templates.source[type];
    bottles.push(clone);
  }

  return bottles;
}
