/**
 * Premium scroll-driven carousel — pin, scrub, snap through 5 fragrances.
 */

import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { ScrollToPlugin } from 'gsap/ScrollToPlugin';
import { DEFAULT_CENTER_INDEX } from './config.js';

export function bindShowcaseScrollTrigger(gsap, root, carousel, perfumes, { onIndexChange } = {}) {
  gsap.registerPlugin(ScrollTrigger, ScrollToPlugin);

  const wrap = root.closest('.showcase3d-wrap') || root;
  const canvas = root.querySelector('.showcase3d-canvas');
  const n = perfumes.length;
  const steps = Math.max(n - 1, 1);
  const progressBar = root.querySelector('.showcase3d-scroll-fill');
  const progressName = root.querySelector('[data-s3d-scroll-name]');
  const hint = root.querySelector('.showcase3d-hint');

  let lastIndex = DEFAULT_CENTER_INDEX;
  let scrollActive = false;

  function emitProgress(p, force = false) {
    if (carousel.isFocusing && !force) return;
    carousel.setScrollProgress(p);

    const idx = Math.round(p * steps);
    if (idx !== lastIndex) {
      lastIndex = idx;
      if (typeof onIndexChange === 'function') onIndexChange(idx);
      if (progressName) progressName.textContent = perfumes[idx]?.name || '';
    }
    if (progressBar) progressBar.style.transform = `scaleX(${Math.max(0.04, p)})`;
  }

  const startProgress = DEFAULT_CENTER_INDEX / steps;
  emitProgress(startProgress, true);
  if (progressName) progressName.textContent = perfumes[DEFAULT_CENTER_INDEX]?.name || '';

  const st = ScrollTrigger.create({
    trigger: wrap,
    start: 'top top',
    end: () => `+=${window.innerHeight * steps * 1.2}`,
    pin: root,
    pinSpacing: true,
    scrub: 0.55,
    anticipatePin: 1,
    snap: {
      snapTo: (value) => Math.round(value * steps) / steps,
      duration: { min: 0.4, max: 0.75 },
      delay: 0.04,
      ease: 'power3.inOut',
    },
    onToggle(self) {
      scrollActive = self.isActive;
    },
    onUpdate(self) {
      if (carousel.isFocusing) return;
      emitProgress(self.progress);
    },
    onLeave() {
      if (hint) hint.style.opacity = '0';
    },
    onLeaveBack() {
      if (hint) hint.style.opacity = '1';
      if (!carousel.isFocusing) emitProgress(startProgress, true);
    },
    onEnterBack() {
      if (hint) hint.style.opacity = '1';
    },
  });

  function scrollToIndex(idx) {
    const clamped = Math.max(0, Math.min(steps, idx));
    const p = clamped / steps;
    const targetY = st.start + p * (st.end - st.start);
    gsap.to(window, { scrollTo: targetY, duration: 0.85, ease: 'power3.inOut' });
  }

  let dragX = 0;
  let dragging = false;

  function onPointerDown(e) {
    if (!scrollActive || carousel.isFocusing) return;
    dragging = true;
    dragX = e.clientX;
    canvas?.setPointerCapture?.(e.pointerId);
  }

  function onPointerUp(e) {
    if (!dragging) return;
    dragging = false;
    const dx = e.clientX - dragX;
    if (Math.abs(dx) < 40) return;
    scrollToIndex(lastIndex + (dx < 0 ? 1 : -1));
  }

  canvas?.addEventListener('pointerdown', onPointerDown);
  canvas?.addEventListener('pointerup', onPointerUp);

  root.querySelector('.showcase3d-scroll')?.addEventListener('click', (e) => {
    e.preventDefault();
    const hero = document.getElementById('luxHero');
    if (!hero) return;
    gsap.to(window, { scrollTo: { y: hero, offsetY: 0 }, duration: 1.1, ease: 'power3.inOut' });
  });

  function onKey(e) {
    if (!scrollActive || carousel.isFocusing) return;
    let next = lastIndex;
    if (e.key === 'ArrowDown' || e.key === 'ArrowRight') next += 1;
    else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') next -= 1;
    else return;
    e.preventDefault();
    scrollToIndex(next);
  }
  window.addEventListener('keydown', onKey);

  ScrollTrigger.addEventListener('refreshInit', () => {
    if (!scrollActive && !carousel.isFocusing) emitProgress(startProgress, true);
  });

  window.addEventListener('resize', () => ScrollTrigger.refresh());
  requestAnimationFrame(() => ScrollTrigger.refresh());

  return {
    destroy() {
      st.kill();
      window.removeEventListener('keydown', onKey);
      canvas?.removeEventListener('pointerdown', onPointerDown);
      canvas?.removeEventListener('pointerup', onPointerUp);
    },
    scrollToIndex,
  };
}
