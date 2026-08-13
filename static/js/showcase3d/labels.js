/**
 * Canvas / file label textures — gold foil style like Elvessora product shots.
 */

const imageCache = new Map();
const textureCache = new Map();

function loadImage(url) {
  if (imageCache.has(url)) return imageCache.get(url);
  const promise = new Promise((resolve) => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => resolve(img);
    img.onerror = () => resolve(null);
    img.src = url;
  });
  imageCache.set(url, promise);
  return promise;
}

function drawCanvasLabel(perfume) {
  const canvas = document.createElement('canvas');
  canvas.width = 1024;
  canvas.height = 1024;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, 1024, 1024);

  // Cream luxury label like product photography
  const g = ctx.createLinearGradient(140, 120, 880, 900);
  g.addColorStop(0, 'rgba(250,245,235,0.98)');
  g.addColorStop(0.5, 'rgba(245,238,225,0.96)');
  g.addColorStop(1, 'rgba(235,225,210,0.94)');
  ctx.fillStyle = g;
  ctx.fillRect(130, 130, 764, 764);

  ctx.textAlign = 'center';
  const gold = perfume.theme.gold || perfume.theme.accent || '#d4af37';

  ctx.strokeStyle = gold;
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(512, 220);
  ctx.lineTo(560, 268);
  ctx.lineTo(512, 316);
  ctx.lineTo(464, 268);
  ctx.closePath();
  ctx.stroke();
  ctx.fillStyle = gold;
  ctx.font = '600 28px "Cormorant Garamond", Georgia, serif';
  ctx.fillText('E', 512, 278);

  ctx.fillStyle = gold;
  ctx.font = '600 52px "Cormorant Garamond", Georgia, serif';
  ctx.fillText('Elvessora', 512, 390);

  ctx.strokeStyle = gold;
  ctx.globalAlpha = 0.7;
  ctx.beginPath();
  ctx.moveTo(340, 430);
  ctx.lineTo(430, 430);
  ctx.moveTo(594, 430);
  ctx.lineTo(684, 430);
  ctx.stroke();
  ctx.globalAlpha = 1;

  ctx.fillStyle = '#3d3428';
  ctx.font = '500 20px Montserrat, sans-serif';
  ctx.fillText('Luxury Fragrance', 512, 438);

  ctx.fillStyle = gold;
  ctx.font = '600 48px "Cormorant Garamond", Georgia, serif';
  const name = (perfume.name || '').toUpperCase();
  ctx.fillText(name, 512, 560);

  ctx.fillStyle = 'rgba(255,255,255,0.45)';
  ctx.font = '500 18px Montserrat, sans-serif';
  ctx.letterSpacing = '0.2em';
  ctx.fillText('EAU DE PARFUM', 512, 640);

  ctx.fillStyle = gold;
  ctx.globalAlpha = 0.65;
  ctx.font = '500 16px Montserrat, sans-serif';
  ctx.fillText((perfume.tagline || '').toUpperCase(), 512, 720);
  ctx.globalAlpha = 1;

  return canvas;
}

export async function getLabelTexture(THREE, perfume, textureBase, labelFiles) {
  const cacheKey = perfume.id;
  if (textureCache.has(cacheKey)) return textureCache.get(cacheKey);

  const files = labelFiles[perfume.id] || [];
  let canvas = null;
  for (const file of files) {
    // eslint-disable-next-line no-await-in-loop
    const img = await loadImage(`${textureBase}${file}`);
    if (img) {
      canvas = document.createElement('canvas');
      canvas.width = 1024;
      canvas.height = 1024;
      canvas.getContext('2d').drawImage(img, 0, 0, 1024, 1024);
      break;
    }
  }
  if (!canvas) canvas = drawCanvasLabel(perfume);

  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 8;
  tex.needsUpdate = true;
  textureCache.set(cacheKey, tex);
  return tex;
}

export function applyFragranceStyle(THREE, root, perfume, labelTexture) {
  const accent = new THREE.Color(perfume.theme.accent);
  const gold = new THREE.Color(perfume.theme.gold || perfume.theme.accent);

  root.traverse((child) => {
    if (!child.isMesh || !child.material) return;
    const mats = Array.isArray(child.material) ? child.material : [child.material];
    const next = mats.map((mat) => {
      const m = mat.clone();
      const key = `${child.name || ''} ${mat.name || ''}`.toLowerCase();
      if (/label|decal|sticker|print|logo/.test(key)) {
        m.map = labelTexture;
        m.needsUpdate = true;
      } else if (/liquid|juice|perfume|fluid|content/.test(key)) {
        if (m.color) m.color.copy(accent).multiplyScalar(0.85);
        m.needsUpdate = true;
      } else if (/gold|collar|neck|metal|ring/.test(key) && !/black|crystal|crushed/.test(key)) {
        if (m.color) m.color.lerp(gold, 0.35);
        m.needsUpdate = true;
      }
      return m;
    });
    child.material = Array.isArray(child.material) ? next : next[0];
    child.castShadow = true;
    child.receiveShadow = true;
  });
}
