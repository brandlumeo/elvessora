/**
 * Premium 3D perfume showcase — entry (isolated from existing Hero).
 */

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { Reflector } from 'three/addons/objects/Reflector.js';
import { RectAreaLightUniformsLib } from 'three/addons/lights/RectAreaLightUniformsLib.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import gsap from 'gsap';

import { PERFUMES, DEFAULT_CENTER_INDEX } from './config.js';
import { loadBottleTemplates, buildFragranceBottles } from './bottles.js';
import {
  createShowcaseScene,
  createComposer,
  resizeShowcase,
  applyTheme,
  updateMouseParallax,
} from './scene.js';
import { ShowcaseCarousel } from './carousel.js';
import { bindShowcaseScroll } from './scroll.js';

function readProductMap(root) {
  const map = {};
  try {
    JSON.parse(root.getAttribute('data-products') || '[]').forEach((p) => {
      if (p?.sku) map[p.sku] = p;
    });
  } catch (_e) {
    /* ignore */
  }
  return map;
}

function getCookie(name) {
  const m = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return m ? decodeURIComponent(m[2]) : '';
}

function mergePerfumeData(perfume, product) {
  return {
    ...perfume,
    topNotes: product.top_notes || perfume.topNotes,
    heartNotes: product.heart_notes || perfume.heartNotes,
    baseNotes: product.base_notes || perfume.baseNotes,
    description: product.description || perfume.description,
    priceDisplay: product.price_display || '',
    productId: product.id || '',
    productUrl: product.url || '',
  };
}

async function initShowcase() {
  const root = document.getElementById('showcase3d');
  if (!root) return;

  const canvas = root.querySelector('.showcase3d-canvas');
  const loaderEl = root.querySelector('.showcase3d-loader');
  const panel = root.querySelector('.showcase3d-panel');
  const nameEl = root.querySelector('[data-s3d-name]');
  const tagEl = root.querySelector('[data-s3d-tag]');
  const descEl = root.querySelector('[data-s3d-desc]');
  const topEl = root.querySelector('[data-s3d-top]');
  const heartEl = root.querySelector('[data-s3d-heart]');
  const baseEl = root.querySelector('[data-s3d-base]');
  const priceEl = root.querySelector('[data-s3d-price]');
  const buyBtn = root.querySelector('[data-s3d-buy]');
  const exploreBtn = root.querySelector('[data-s3d-explore]');
  const closeBtn = root.querySelector('[data-s3d-close]');
  const dotsRoot = root.querySelector('.showcase3d-dots');
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const productMap = readProductMap(root);
  const addUrl = root.getAttribute('data-add-url') || '/cart/add/';
  const collectionUrl = root.getAttribute('data-collection-url') || '/collection/';
  const csrf = root.getAttribute('data-csrf') || getCookie('csrftoken');

  if (loaderEl) loaderEl.hidden = false;

  try {
  const templates = await loadBottleTemplates(THREE, GLTFLoader);

  const api = createShowcaseScene(
    THREE,
    canvas,
    RoomEnvironment,
    Reflector,
    RectAreaLightUniformsLib
  );
  createComposer(THREE, api, EffectComposer, RenderPass, UnrealBloomPass, OutputPass);
  applyTheme(api, PERFUMES[DEFAULT_CENTER_INDEX]);

  const bottles = await buildFragranceBottles(THREE, templates, PERFUMES);
  if (!bottles.length) throw new Error('No showcase bottles could be built');
  if (loaderEl) loaderEl.hidden = true;

  function showPanel(perfume) {
    const product = productMap[perfume.sku] || {};
    const data = mergePerfumeData(perfume, product);

    if (nameEl) nameEl.textContent = data.name;
    if (tagEl) tagEl.textContent = data.tagline;
    if (descEl) descEl.textContent = data.description;
    if (topEl) topEl.textContent = data.topNotes;
    if (heartEl) heartEl.textContent = data.heartNotes;
    if (baseEl) baseEl.textContent = data.baseNotes;
    if (priceEl) {
      priceEl.textContent = data.priceDisplay;
      priceEl.hidden = !data.priceDisplay;
    }
    if (buyBtn) {
      buyBtn.disabled = !data.productId;
      buyBtn.dataset.productId = data.productId || '';
      if (data.productUrl) buyBtn.dataset.productUrl = data.productUrl;
    }
    if (exploreBtn) {
      exploreBtn.href = data.productUrl || collectionUrl;
    }

    if (panel) {
      panel.hidden = false;
      gsap.fromTo(
        panel,
        { autoAlpha: 0, y: 22 },
        { autoAlpha: 1, y: 0, duration: 0.55, ease: 'power2.out' }
      );
    }
    root.style.setProperty('--s3d-accent', perfume.theme.accent);
    dotsRoot?.querySelectorAll('.showcase3d-dot').forEach((d, i) => {
      d.classList.toggle('is-active', PERFUMES[i]?.id === perfume.id);
    });
  }

  function hidePanel() {
    if (!panel) return;
    gsap.to(panel, {
      autoAlpha: 0,
      y: 14,
      duration: 0.3,
      onComplete() {
        panel.hidden = true;
      },
    });
  }

  function syncDots(index) {
    dotsRoot?.querySelectorAll('.showcase3d-dot').forEach((d, i) => {
      d.classList.toggle('is-active', i === index);
    });
    const perfume = PERFUMES[index];
    if (perfume) {
      root.style.setProperty('--s3d-accent', perfume.theme.accent);
      applyTheme(api, perfume);
    }
  }

  const carousel = new ShowcaseCarousel({
    THREE,
    gsap,
    api,
    bottles,
    perfumes: PERFUMES,
    onFocus: showPanel,
    onBlur: hidePanel,
  });

  let scrollCtrl = null;

  if (dotsRoot) {
    dotsRoot.innerHTML = '';
    PERFUMES.forEach((p, i) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'showcase3d-dot' + (i === DEFAULT_CENTER_INDEX ? ' is-active' : '');
      btn.setAttribute('aria-label', p.name);
      btn.addEventListener('click', () => {
        if (carousel.isFocusing) carousel.focus(i);
        else if (scrollCtrl?.scrollToIndex) scrollCtrl.scrollToIndex(i);
        else carousel.goTo(i);
        syncDots(i);
      });
      dotsRoot.appendChild(btn);
    });
  }

  if (reduced) {
    bindShowcaseScroll(root, carousel, { onIndexChange: syncDots });
  } else {
    try {
      const { bindShowcaseScrollTrigger } = await import('./scrollTrigger.js');
      scrollCtrl = bindShowcaseScrollTrigger(gsap, root, carousel, PERFUMES, {
        onIndexChange: syncDots,
      });
    } catch (scrollErr) {
      console.warn('[showcase3d] ScrollTrigger fallback:', scrollErr);
      bindShowcaseScroll(root, carousel, { onIndexChange: syncDots });
    }
  }

  let suppressClick = false;
  canvas.addEventListener('pointermove', (e) => {
    const rect = canvas.getBoundingClientRect();
    api.mouse.tx = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    api.mouse.ty = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
  });

  canvas.addEventListener('pointerdown', (e) => {
    canvas._dragX = e.clientX;
  });

  canvas.addEventListener('click', (e) => {
    if (suppressClick) {
      suppressClick = false;
      return;
    }
    if (canvas._dragX != null && Math.abs(e.clientX - canvas._dragX) > 40) {
      return;
    }
    const idx = carousel.pick(e.clientX, e.clientY, canvas);
    if (idx >= 0) {
      carousel.focus(idx);
      syncDots(idx);
    }
  });

  closeBtn?.addEventListener('click', () => carousel.blur());

  buyBtn?.addEventListener('click', async () => {
    const productId = buyBtn.dataset.productId;
    if (!productId) return;
    buyBtn.classList.add('is-loading');
    buyBtn.disabled = true;
    try {
      const body = new FormData();
      body.append('product_id', productId);
      body.append('quantity', '1');
      body.append('csrfmiddlewaretoken', csrf);
      const res = await fetch(addUrl, {
        method: 'POST',
        body,
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        credentials: 'same-origin',
      });
      if (res.redirected) {
        window.location.href = res.url;
        return;
      }
      if (res.ok) window.location.reload();
    } finally {
      buyBtn.classList.remove('is-loading');
      buyBtn.disabled = false;
    }
  });

  const ro = new ResizeObserver(() => resizeShowcase(api, canvas));
  ro.observe(root);

  let visible = true;
  let raf = 0;
  const clock = new THREE.Clock();

  function frame() {
    raf = requestAnimationFrame(frame);
    if (!visible) return;
    const dt = Math.min(clock.getDelta(), 0.05);
    updateMouseParallax(api, dt);
    if (!reduced) carousel.update(dt);
    if (api.composer) api.composer.render();
    else api.renderer.render(api.scene, api.camera);
  }
  frame();

  new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        visible = entry.isIntersecting;
      });
    },
    { threshold: 0.04 }
  ).observe(root);

  root._showcase3d = { api, carousel, templates };
  } catch (err) {
    console.error('[showcase3d] init failed:', err);
    if (loaderEl) {
      loaderEl.textContent = 'Showcase unavailable — refresh to retry';
      window.setTimeout(() => {
        loaderEl.hidden = true;
      }, 2200);
    }
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initShowcase);
} else {
  initShowcase();
}
