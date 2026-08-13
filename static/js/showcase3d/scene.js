/**
 * Luxury showroom scene — navy, black, white, gold.
 */

import * as THREE from 'three';
import { LAYOUT } from './config.js';

export const SHOWROOM = {
  navy: '#0a1628',
  navyDeep: '#060d18',
  black: '#040608',
  white: '#f8f8f8',
  gold: '#d4af37',
  goldSoft: '#e8d5a0',
};

export function createShowcaseScene(THREE, canvas, RoomEnvironment, Reflector, RectAreaLightUniformsLib) {
  if (RectAreaLightUniformsLib) RectAreaLightUniformsLib.init();

  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: false,
    powerPreference: 'high-performance',
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, LAYOUT.dprMax));
  renderer.setSize(canvas.clientWidth, canvas.clientHeight, false);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.18;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(SHOWROOM.navy);
  scene.fog = new THREE.FogExp2(SHOWROOM.navyDeep, 0.028);

  const camera = new THREE.PerspectiveCamera(
    32,
    canvas.clientWidth / Math.max(canvas.clientHeight, 1),
    0.1,
    80
  );
  camera.position.set(LAYOUT.cameraIdle.x, LAYOUT.cameraIdle.y, LAYOUT.cameraIdle.z);
  camera.lookAt(0, 0.7, 0);

  const pmrem = new THREE.PMREMGenerator(renderer);
  pmrem.compileEquirectangularShader();
  const env = new RoomEnvironment();
  const envMap = pmrem.fromScene(env, 0.04).texture;
  scene.environment = envMap;

  const ambient = new THREE.AmbientLight(0xffffff, 0.18);
  scene.add(ambient);

  const hemi = new THREE.HemisphereLight(SHOWROOM.white, SHOWROOM.navyDeep, 0.42);
  scene.add(hemi);

  const key = new THREE.SpotLight(0xffffff, 2.4, 36, Math.PI / 5.5, 0.38, 1);
  key.position.set(3.8, 8.2, 6.2);
  key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048);
  key.shadow.bias = -0.00012;
  key.shadow.radius = 2;
  scene.add(key);
  scene.add(key.target);
  key.target.position.set(0, 0.6, 0);

  const goldRim = new THREE.SpotLight(SHOWROOM.gold, 2.6, 28, Math.PI / 4, 0.48, 1);
  goldRim.position.set(-5.8, 4.2, -2.2);
  scene.add(goldRim);

  const goldRim2 = new THREE.SpotLight(SHOWROOM.goldSoft, 1.4, 22, Math.PI / 3.5, 0.55, 1);
  goldRim2.position.set(5.5, 2.8, -1.5);
  scene.add(goldRim2);

  const fill = new THREE.PointLight(0xffffff, 0.45, 20);
  fill.position.set(0, 2.6, 4.5);
  scene.add(fill);

  let areaFront = null;
  let areaSide = null;
  if (THREE.RectAreaLight) {
    areaFront = new THREE.RectAreaLight(0xffffff, 2.8, 5, 2.4);
    areaFront.position.set(0, 3.4, 4.8);
    areaFront.lookAt(0, 0.8, 0);
    scene.add(areaFront);

    areaSide = new THREE.RectAreaLight(SHOWROOM.gold, 1.8, 2.8, 3.8);
    areaSide.position.set(-4.2, 2.4, 1.2);
    areaSide.lookAt(0, 0.8, 0);
    scene.add(areaSide);
  }

  // Soft volumetric cone
  const volBeam = new THREE.Mesh(
    new THREE.ConeGeometry(3.2, 9, 32, 1, true),
    new THREE.MeshBasicMaterial({
      color: SHOWROOM.gold,
      transparent: true,
      opacity: 0.018,
      side: THREE.DoubleSide,
      depthWrite: false,
    })
  );
  volBeam.position.set(1.2, 4.5, 2);
  volBeam.rotation.x = Math.PI;
  scene.add(volBeam);

  const reflectorSize = Math.min(
    1280,
    Math.max(512, canvas.clientWidth * Math.min(window.devicePixelRatio || 1, 1.5))
  );
  const reflector = new Reflector(new THREE.CircleGeometry(10, 72), {
    clipBias: 0.003,
    textureWidth: reflectorSize,
    textureHeight: reflectorSize,
    color: 0x0a101c,
  });
  reflector.rotation.x = -Math.PI / 2;
  reflector.position.y = -0.01;
  scene.add(reflector);

  const floorTint = new THREE.Mesh(
    new THREE.CircleGeometry(10, 72),
    new THREE.MeshPhysicalMaterial({
      color: 0x0a1628,
      metalness: 0.95,
      roughness: 0.18,
      transparent: true,
      opacity: 0.55,
      envMapIntensity: 1.5,
      clearcoat: 0.4,
    })
  );
  floorTint.rotation.x = -Math.PI / 2;
  floorTint.position.y = 0.002;
  floorTint.receiveShadow = true;
  scene.add(floorTint);

  const count = 220;
  const pos = new Float32Array(count * 3);
  for (let i = 0; i < count; i += 1) {
    pos[i * 3] = (Math.random() - 0.5) * 14;
    pos[i * 3 + 1] = Math.random() * 6;
    pos[i * 3 + 2] = (Math.random() - 0.5) * 10;
  }
  const pGeo = new THREE.BufferGeometry();
  pGeo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const particles = new THREE.Points(
    pGeo,
    new THREE.PointsMaterial({
      color: SHOWROOM.goldSoft,
      size: 0.032,
      transparent: true,
      opacity: 0.55,
      depthWrite: false,
      sizeAttenuation: true,
      blending: THREE.AdditiveBlending,
    })
  );
  scene.add(particles);

  return {
    renderer,
    scene,
    camera,
    lights: { ambient, hemi, key, goldRim, goldRim2, fill, areaFront, areaSide },
    reflector,
    floorTint,
    particles,
    volBeam,
    pmrem,
    envMap,
    mouse: { x: 0, y: 0, tx: 0, ty: 0 },
  };
}

export function applyTheme(api, perfume) {
  const t = perfume.theme;
  api.scene.background.set(t.bg);
  if (api.scene.fog) api.scene.fog.color.set(t.fog);
  api.lights.key.color.set(t.key);
  api.lights.goldRim.color.set(t.gold || t.rim);
  if (api.lights.goldRim2) api.lights.goldRim2.color.set(t.gold || t.rim);
  api.lights.fill.color.set(t.accent);
  if (api.lights.areaSide) api.lights.areaSide.color.set(t.gold || t.accent);
  if (api.particles?.material) {
    api.particles.material.color.set(t.particle || t.gold);
  }
  if (api.bloomPass) api.bloomPass.strength = t.bloom ?? 0.58;
  if (api.floorTint?.material) {
    api.floorTint.material.color.set(t.bg);
  }
  if (api.volBeam?.material) {
    api.volBeam.material.color.set(t.gold || t.rim);
  }
}

function blendColor(out, hexA, hexB, t) {
  out.set(hexA);
  out.lerp(new THREE.Color(hexB), t);
}

export function applyThemeBlend(api, perfumeA, perfumeB, t) {
  const ta = perfumeA.theme;
  const tb = perfumeB.theme;
  const c = new THREE.Color();

  blendColor(c, ta.bg, tb.bg, t);
  api.scene.background.copy(c);
  if (api.scene.fog) {
    blendColor(c, ta.fog, tb.fog, t);
    api.scene.fog.color.copy(c);
  }
  blendColor(c, ta.key, tb.key, t);
  api.lights.key.color.copy(c);
  blendColor(c, ta.gold || ta.rim, tb.gold || tb.rim, t);
  api.lights.goldRim.color.copy(c);
  if (api.lights.goldRim2) api.lights.goldRim2.color.copy(c);
  blendColor(c, ta.accent, tb.accent, t);
  api.lights.fill.color.copy(c);
  if (api.lights.areaSide) api.lights.areaSide.color.copy(c);
  if (api.particles?.material) {
    blendColor(c, ta.particle || ta.gold, tb.particle || tb.gold, t);
    api.particles.material.color.copy(c);
  }
  if (api.bloomPass) {
    api.bloomPass.strength = (ta.bloom ?? 0.58) + ((tb.bloom ?? 0.58) - (ta.bloom ?? 0.58)) * t;
  }
  if (api.floorTint?.material) {
    blendColor(c, ta.bg, tb.bg, t);
    api.floorTint.material.color.copy(c);
  }
  if (api.volBeam?.material) {
    blendColor(c, ta.gold || ta.rim, tb.gold || tb.rim, t);
    api.volBeam.material.color.copy(c);
  }
}

export function createComposer(THREE, api, EffectComposer, RenderPass, UnrealBloomPass, OutputPass) {
  const { renderer, scene, camera } = api;
  const size = new THREE.Vector2();
  renderer.getSize(size);
  const composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene, camera));
  const bloom = new UnrealBloomPass(new THREE.Vector2(size.x, size.y), 0.52, 0.65, 0.78);
  composer.addPass(bloom);
  composer.addPass(new OutputPass());
  api.composer = composer;
  api.bloomPass = bloom;
  return composer;
}

export function resizeShowcase(api, canvas) {
  const w = canvas.clientWidth;
  const h = Math.max(canvas.clientHeight, 1);
  api.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, LAYOUT.dprMax));
  api.renderer.setSize(w, h, false);
  api.camera.aspect = w / h;
  api.camera.updateProjectionMatrix();
  if (api.composer) api.composer.setSize(w, h);
}

export function updateMouseParallax(api, dt) {
  const m = api.mouse;
  m.x += (m.tx - m.x) * Math.min(1, dt * 3.2);
  m.y += (m.ty - m.y) * Math.min(1, dt * 3.2);
}
