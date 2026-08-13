/**
 * Curved luxury carousel — center larger, sides smaller & rotated.
 * GSAP focus timelines + idle cinematic motion + mouse reaction.
 */

import { LAYOUT, DEFAULT_CENTER_INDEX } from './config.js';
import { applyTheme, applyThemeBlend } from './scene.js';

function lerp(a, b, t) {
  return a + (b - a) * t;
}

export class ShowcaseCarousel {
  constructor({ THREE, gsap, api, bottles, perfumes, onFocus, onBlur }) {
    this.THREE = THREE;
    this.gsap = gsap;
    this.api = api;
    this.bottles = bottles;
    this.perfumes = perfumes;
    this.onFocus = onFocus;
    this.onBlur = onBlur;

    this.root = new THREE.Group();
    this.root.name = 'showcase-curve';
    api.scene.add(this.root);

    // Always show all five; Moon Blossom centered by default
    this.activeIndex = Math.min(
      DEFAULT_CENTER_INDEX,
      Math.max(0, bottles.length - 1)
    );
    this.scrollCenter = this.activeIndex;
    this.focusedIndex = -1;
    this.isFocusing = false;
    this.raycaster = new THREE.Raycaster();
    this.pointer = new THREE.Vector2();
    this.clock = 0;
    this._tl = null;

    bottles.forEach((bottle, i) => {
      const wrap = new THREE.Group();
      wrap.userData.index = i;
      wrap.userData.perfumeId = bottle.userData.perfumeId;
      bottle.userData.index = i;
      bottle.userData.baseY = 0;
      wrap.add(bottle);
      this.root.add(wrap);
    });

    this._layoutInstant(this.activeIndex);
    applyTheme(api, perfumes[this.activeIndex]);
  }

  get wraps() {
    return this.root.children;
  }

  _slotPose(i, centerIndex) {
    const n = this.wraps.length;
    const mid = (n - 1) / 2;
    const offset = i - centerIndex;
    const t = offset / Math.max(mid, 1);
    const angle = t * (LAYOUT.arcSpan / 2);
    const x = Math.sin(angle) * LAYOUT.radius;
    const z = Math.cos(angle) * LAYOUT.radius - LAYOUT.radius;
    const dist = Math.abs(offset);
    let scale = LAYOUT.sideScale;
    if (dist < 0.02) {
      scale = LAYOUT.centerScale;
    } else if (dist >= 2) {
      scale = LAYOUT.farScale;
    } else if (dist <= 1) {
      scale = lerp(LAYOUT.centerScale, LAYOUT.sideScale, dist);
    } else {
      scale = lerp(LAYOUT.sideScale, LAYOUT.farScale, dist - 1);
    }
    const rotY = -angle * 0.9;
    const y = dist < 0.02 ? 0.08 : dist >= 2 ? -0.12 : lerp(-0.02, 0.08, Math.max(0, 1 - dist));
    return { x, z, y, scale, rotY, isCenter: dist < 0.02 };
  }

  _layoutInstant(centerIndex) {
    this.scrollCenter = centerIndex;
    this._layoutFractional(centerIndex);
  }

  _layoutFractional(centerIndex) {
    this.wraps.forEach((wrap, i) => {
      const pose = this._slotPose(i, centerIndex);
      wrap.position.set(pose.x, pose.y, pose.z);
      wrap.rotation.y = pose.rotY;
      wrap.scale.setScalar(pose.scale);
    });
  }

  /** Smooth scroll-driven carousel (0 → 1 maps to first → last fragrance). */
  setScrollProgress(progress) {
    if (this.isFocusing) return;
    const n = this.wraps.length;
    const steps = Math.max(n - 1, 1);
    const center = progress * steps;
    this.scrollCenter = center;
    this.activeIndex = Math.round(center);
    this._layoutFractional(center);

    const idxA = Math.min(Math.floor(center), n - 1);
    const idxB = Math.min(idxA + 1, n - 1);
    const t = center - idxA;
    if (idxA === idxB) applyTheme(this.api, this.perfumes[idxA]);
    else applyThemeBlend(this.api, this.perfumes[idxA], this.perfumes[idxB], t);
  }

  update(dt) {
    this.clock += dt;
    const mouse = this.api.mouse;
    const px = mouse.x * LAYOUT.bottleParallax;
    const py = mouse.y * LAYOUT.bottleParallax * 0.5;

    this.wraps.forEach((wrap, i) => {
      const bottle = wrap.children[0];
      if (!bottle) return;
      const phase = this.clock * 0.75 + i * 0.9;
      const floatY = Math.sin(phase) * LAYOUT.idleFloat;
      const breath = 1 + Math.sin(phase * 0.55) * LAYOUT.breath;

      if (!this.isFocusing) {
        bottle.position.y = floatY;
        bottle.rotation.y += dt * LAYOUT.idleSpin * (i % 2 === 0 ? 0.35 : 0.28);
        bottle.scale.setScalar(breath);
        wrap.userData._mx = (wrap.userData._mx || 0) + (px - (wrap.userData._mx || 0)) * 0.06;
        wrap.userData._my = (wrap.userData._my || 0) + (py * 0.35 - (wrap.userData._my || 0)) * 0.06;
        wrap.position.y = wrap.userData._my;
      } else if (i === this.focusedIndex) {
        bottle.position.y = Math.sin(this.clock * 0.85) * (LAYOUT.idleFloat * 0.35);
      }
    });

    if (this.api.particles) {
      this.api.particles.rotation.y += dt * 0.025;
      this.api.particles.position.y = Math.sin(this.clock * 0.2) * 0.05;
    }

    // Camera mouse parallax (idle)
    if (!this.isFocusing) {
      const cam = this.api.camera;
      const targetX = LAYOUT.cameraIdle.x + mouse.x * LAYOUT.mouseParallax;
      const targetY = LAYOUT.cameraIdle.y + mouse.y * LAYOUT.mouseParallax * 0.35;
      cam.position.x += (targetX - cam.position.x) * Math.min(1, dt * 2.5);
      cam.position.y += (targetY - cam.position.y) * Math.min(1, dt * 2.5);
      cam.lookAt(0, 0.75, 0);
    }
  }

  pick(clientX, clientY, canvas) {
    const rect = canvas.getBoundingClientRect();
    this.pointer.x = ((clientX - rect.left) / rect.width) * 2 - 1;
    this.pointer.y = -((clientY - rect.top) / rect.height) * 2 + 1;
    this.raycaster.setFromCamera(this.pointer, this.api.camera);
    const meshes = [];
    this.root.traverse((o) => {
      if (o.isMesh) meshes.push(o);
    });
    const hits = this.raycaster.intersectObjects(meshes, false);
    for (const hit of hits) {
      let obj = hit.object;
      while (obj) {
        if (typeof obj.userData.index === 'number') return obj.userData.index;
        obj = obj.parent;
      }
    }
    return -1;
  }

  focus(index) {
    if (index < 0 || index >= this.wraps.length) return;
    const gsap = this.gsap;
    const perfume = this.perfumes[index];
    const { camera } = this.api;
    const self = this;

    if (this._tl) this._tl.kill();

    this.isFocusing = true;
    this.focusedIndex = index;
    this.activeIndex = index;
    applyTheme(this.api, perfume);

    const tl = gsap.timeline({
      defaults: { ease: 'power3.inOut' },
    });
    this._tl = tl;

    this.wraps.forEach((wrap, i) => {
      const pose = this._slotPose(i, index);
      const isSel = i === index;
      tl.to(
        wrap.position,
        {
          x: isSel ? 0 : pose.x * 1.35,
          z: isSel ? 0.65 : pose.z - 0.85,
          y: isSel ? 0.1 : -0.12,
          duration: 1.15,
        },
        0
      );
      tl.to(
        wrap.scale,
        {
          x: isSel ? 1.35 : pose.scale * 0.72,
          y: isSel ? 1.35 : pose.scale * 0.72,
          z: isSel ? 1.35 : pose.scale * 0.72,
          duration: 1.05,
          ease: 'power2.out',
        },
        0
      );
      tl.to(
        wrap.rotation,
        {
          y: isSel ? 0 : pose.rotY * 1.4,
          duration: 1.1,
        },
        0
      );

      const bottle = wrap.children[0];
      if (bottle && isSel) {
        const start = bottle.rotation.y;
        tl.to(
          bottle.rotation,
          {
            y: start + Math.PI * 2,
            duration: 2.0,
            ease: 'power1.inOut',
          },
          0.18
        );
      }
    });

    tl.to(
      camera.position,
      {
        x: LAYOUT.cameraFocus.x,
        y: LAYOUT.cameraFocus.y,
        z: LAYOUT.cameraFocus.z,
        duration: 1.2,
        onUpdate() {
          camera.lookAt(0, 0.85, 0);
        },
      },
      0
    );

    tl.add(() => {
      if (typeof self.onFocus === 'function') self.onFocus(perfume, index);
    }, 0.4);
  }

  blur() {
    if (!this.isFocusing) return;
    const gsap = this.gsap;
    const { camera } = this.api;
    const self = this;
    const center = this.activeIndex;

    if (this._tl) this._tl.kill();
    if (typeof this.onBlur === 'function') this.onBlur();

    const tl = gsap.timeline({
      onComplete() {
        self.isFocusing = false;
        self.focusedIndex = -1;
        self._layoutInstant(self.scrollCenter ?? center);
      },
    });
    this._tl = tl;

    this.wraps.forEach((wrap, i) => {
      const pose = this._slotPose(i, center);
      tl.to(
        wrap.position,
        { x: pose.x, y: pose.y, z: pose.z, duration: 0.95, ease: 'power2.inOut' },
        0
      );
      tl.to(wrap.scale, { x: pose.scale, y: pose.scale, z: pose.scale, duration: 0.9 }, 0);
      tl.to(wrap.rotation, { y: pose.rotY, duration: 0.9 }, 0);
    });

    tl.to(
      camera.position,
      {
        x: LAYOUT.cameraIdle.x,
        y: LAYOUT.cameraIdle.y,
        z: LAYOUT.cameraIdle.z,
        duration: 1.0,
        ease: 'power2.inOut',
        onUpdate() {
          camera.lookAt(0, 0.75, 0);
        },
      },
      0
    );
  }

  goTo(index) {
    if (this.isFocusing) {
      this.focus(index);
      return;
    }
    this.activeIndex = index;
    const gsap = this.gsap;
    applyTheme(this.api, this.perfumes[index]);
    this.wraps.forEach((wrap, i) => {
      const pose = this._slotPose(i, index);
      gsap.to(wrap.position, { x: pose.x, y: pose.y, z: pose.z, duration: 0.9, ease: 'power2.inOut' });
      gsap.to(wrap.scale, { x: pose.scale, y: pose.scale, z: pose.scale, duration: 0.9 });
      gsap.to(wrap.rotation, { y: pose.rotY, duration: 0.9 });
    });
  }
}
