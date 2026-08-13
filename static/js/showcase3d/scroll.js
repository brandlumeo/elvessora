/**
 * Wheel / touch / drag scroll for the fragrance carousel.
 * Scroll inside showcase → change bottle. Scroll past ends → page continues.
 */

export function bindShowcaseScroll(root, carousel, { onIndexChange } = {}) {
  const canvas = root.querySelector('.showcase3d-canvas');
  if (!canvas || !carousel) return () => {};

  let wheelLock = false;
  let touchStartX = 0;
  let touchStartY = 0;
  let dragStartX = 0;
  let dragging = false;
  let accum = 0;

  function setIndex(next) {
    const n = carousel.wraps.length;
    const idx = ((next % n) + n) % n;
    if (idx === carousel.activeIndex && !carousel.isFocusing) return;
    if (carousel.isFocusing) carousel.blur();
    carousel.goTo(idx);
    if (typeof onIndexChange === 'function') onIndexChange(idx);
  }

  function step(dir) {
    if (wheelLock) return;
    wheelLock = true;
    setIndex(carousel.activeIndex + dir);
    window.setTimeout(() => {
      wheelLock = false;
    }, 520);
  }

  function onWheel(e) {
    const rect = root.getBoundingClientRect();
    const inView = rect.top < window.innerHeight * 0.55 && rect.bottom > window.innerHeight * 0.35;
    if (!inView) return;

    const dominantY = Math.abs(e.deltaY) >= Math.abs(e.deltaX);
    const delta = dominantY ? e.deltaY : e.deltaX;

    // Near bottom of showcase + scrolling down → allow page scroll to hero
    if (dominantY && e.deltaY > 0 && rect.bottom <= window.innerHeight + 8) {
      const atLast = carousel.activeIndex >= carousel.wraps.length - 1;
      if (atLast) return; // let page scroll
    }
    // Near top + scrolling up → allow page scroll up
    if (dominantY && e.deltaY < 0 && rect.top >= -8) {
      const atFirst = carousel.activeIndex <= 0;
      if (atFirst) return;
    }

    e.preventDefault();
    accum += delta;
    if (Math.abs(accum) < 40) return;
    const dir = accum > 0 ? 1 : -1;
    accum = 0;
    step(dir);
  }

  function onTouchStart(e) {
    if (!e.touches[0]) return;
    touchStartX = e.touches[0].clientX;
    touchStartY = e.touches[0].clientY;
  }

  function onTouchEnd(e) {
    const t = e.changedTouches[0];
    if (!t) return;
    const dx = t.clientX - touchStartX;
    const dy = t.clientY - touchStartY;
    if (Math.abs(dx) < 40 && Math.abs(dy) < 40) return;
    if (Math.abs(dx) > Math.abs(dy)) {
      step(dx < 0 ? 1 : -1);
    } else {
      step(dy > 0 ? 1 : -1);
    }
  }

  function onPointerDown(e) {
    if (e.button !== 0) return;
    dragging = true;
    dragStartX = e.clientX;
    canvas.setPointerCapture?.(e.pointerId);
  }

  function onPointerUp(e) {
    if (!dragging) return;
    dragging = false;
    const dx = e.clientX - dragStartX;
    if (Math.abs(dx) > 50) step(dx < 0 ? 1 : -1);
  }

  // Keyboard
  function onKey(e) {
    if (!root.contains(document.activeElement) && document.activeElement !== document.body) return;
    const rect = root.getBoundingClientRect();
    if (rect.bottom < 0 || rect.top > window.innerHeight) return;
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
      e.preventDefault();
      step(1);
    } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
      e.preventDefault();
      step(-1);
    }
  }

  root.addEventListener('wheel', onWheel, { passive: false });
  canvas.addEventListener('touchstart', onTouchStart, { passive: true });
  canvas.addEventListener('touchend', onTouchEnd, { passive: true });
  canvas.addEventListener('pointerdown', onPointerDown);
  canvas.addEventListener('pointerup', onPointerUp);
  window.addEventListener('keydown', onKey);

  // Smooth scroll-to-hero link
  const scrollLink = root.querySelector('.showcase3d-scroll');
  if (scrollLink) {
    scrollLink.addEventListener('click', (e) => {
      e.preventDefault();
      const hero = document.getElementById('luxHero');
      if (hero) hero.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  }

  return function unbind() {
    root.removeEventListener('wheel', onWheel);
    canvas.removeEventListener('touchstart', onTouchStart);
    canvas.removeEventListener('touchend', onTouchEnd);
    canvas.removeEventListener('pointerdown', onPointerDown);
    canvas.removeEventListener('pointerup', onPointerUp);
    window.removeEventListener('keydown', onKey);
  };
}
