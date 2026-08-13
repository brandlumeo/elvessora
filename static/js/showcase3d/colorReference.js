/**
 * Sample product photography for material tints only — never rendered as geometry.
 */

const cache = new Map();

function loadImage(url) {
  if (cache.has(url)) return cache.get(url);
  const p = new Promise((resolve) => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => resolve(img);
    img.onerror = () => resolve(null);
    img.src = url;
  });
  cache.set(url, p);
  return p;
}

function rgbToHex(r, g, b) {
  return `#${[r, g, b].map((v) => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, '0')).join('')}`;
}

/** Extract liquid / glass tint hints from a reference photo URL. */
export async function extractReferenceColors(imageUrl) {
  if (!imageUrl) return null;
  try {
    const img = await loadImage(imageUrl);
    if (!img) return null;

    const canvas = document.createElement('canvas');
    canvas.width = 72;
    canvas.height = 72;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(img, 0, 0, 72, 72);
    const { data } = ctx.getImageData(0, 0, 72, 72);

    let r = 0;
    let g = 0;
    let b = 0;
    let n = 0;

    for (let i = 0; i < data.length; i += 4) {
      if (data[i + 3] < 140) continue;
      const lum = data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114;
      if (lum < 28 || lum > 238) continue;
      r += data[i];
      g += data[i + 1];
      b += data[i + 2];
      n += 1;
    }

    if (!n) return null;

    r /= n;
    g /= n;
    b /= n;

    return {
      liquidColor: rgbToHex(r, g, b),
      glassTint: rgbToHex(r + 38, g + 36, b + 32),
      accent: rgbToHex(r * 1.08, g * 1.05, b * 0.95),
    };
  } catch (_err) {
    return null;
  }
}
