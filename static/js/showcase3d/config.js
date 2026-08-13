/**
 * Elvessora Premium 3D Showcase — five fragrances from two GLB clones.
 *
 * Bottle A (Round Red Crystal Cap) → Amber Petals, Moon Blossom
 * Bottle B (Square Black Gold Cap) → Secret Romance, Enchante Bloom, Divine Aura
 *
 * Curved order (left → right), Moon Blossom centered by default:
 *   Amber Petals · Enchante Bloom · Moon Blossom · Secret Romance · Divine Aura
 */

export const SHOWCASE_PATHS = {
  bottleA: [
    '/static/models/Bottle_A.glb',
    '/static/models/BottleA.glb',
    '/static/models/bottle_a.glb',
  ],
  bottleB: [
    '/static/models/Bottle_B.glb',
    '/static/models/BottleB.glb',
    '/static/models/bottle_b.glb',
  ],
  textures: '/static/textures/',
  labels: {
    'amber-petals': [
      'label-amber-petals.png',
      'Amber Petals.png',
      'amber-petals.png',
      'AmberPetals.png',
    ],
    'enchante-bloom': [
      'label-enchante-bloom.png',
      'Enchante Bloom.png',
      'enchante-bloom.png',
      'EnchanteBloom.png',
    ],
    'moon-blossom': [
      'label-moon-blossom.png',
      'Moon Blossom.png',
      'moon-blossom.png',
      'MoonBlossom.png',
    ],
    'secret-romance': [
      'label-secret-romance.png',
      'Secret Romance.png',
      'secret-romance.png',
      'SecretRomance.png',
    ],
    'divine-aura': [
      'label-divine-aura.png',
      'Divine Aura.png',
      'divine-aura.png',
      'DivineAura.png',
      'label-divine-perfume.png',
      'Divine Perfume.png',
    ],
  },
};

/**
 * Exactly five products — geometry cloned from A or B only.
 * Index 2 (Moon Blossom) is the default center hero.
 */
export const PERFUMES = [
  {
    id: 'amber-petals',
    sku: 'ELV-AMBER-003',
    name: 'Amber Petals',
    tagline: 'Warm amber · Floral petals',
    description:
      'Warm golden amber meets delicate floral petals in a luxurious oriental blend — enveloping, refined, and timeless.',
    topNotes: 'Saffron, Bergamot, Pink Pepper',
    heartNotes: 'Rose Petals, Jasmine, Orange Blossom',
    baseNotes: 'Amber, Vanilla, Benzoin',
    bottle: 'A',
    liquidColor: '#d4a040',
    glassTint: '#ede6dc',
    theme: {
      accent: '#d4af37',
      bg: '#0a1628',
      fog: '#060d18',
      key: '#f8f8f8',
      rim: '#d4af37',
      gold: '#d4af37',
      particle: '#e8c878',
      bloom: 0.58,
    },
  },
  {
    id: 'enchante-bloom',
    sku: 'ELV-ENCHANT-004',
    name: 'Enchante Bloom',
    tagline: 'Fresh apple · Jasmine glow',
    description:
      'A fresh, enchanting floral with crisp apple and jasmine, resting on a smooth vanilla base — radiant and modern.',
    topNotes: 'Sweet Apple',
    heartNotes: 'Jasmine Flowers',
    baseNotes: 'Vanilla',
    bottle: 'B',
    liquidColor: '#c8a850',
    glassTint: '#f0ebe3',
    theme: {
      accent: '#d4af37',
      bg: '#0c1424',
      fog: '#070e1a',
      key: '#ffffff',
      rim: '#d4af37',
      gold: '#e0c078',
      particle: '#d8e8a0',
      bloom: 0.56,
    },
  },
  {
    id: 'moon-blossom',
    sku: 'ELV-MOON-001',
    name: 'Moon Blossom',
    tagline: 'Night floral · Moonlit petals',
    description:
      'A luminous night-floral that captures the quiet elegance of moonlit petals — soft, romantic, and beautifully refined.',
    topNotes: 'Bergamot, Pear, Pink Pepper',
    heartNotes: 'Moonflower, White Rose, Peony',
    baseNotes: 'White Musk, Soft Amber, Cedarwood',
    bottle: 'A',
    liquidColor: '#8ea8e0',
    glassTint: '#e8ecf8',
    theme: {
      accent: '#b8c8f0',
      bg: '#081220',
      fog: '#050c16',
      key: '#f0f4ff',
      rim: '#d4af37',
      gold: '#d4af37',
      particle: '#a8c0ff',
      bloom: 0.62,
    },
  },
  {
    id: 'secret-romance',
    sku: 'ELV-SECRET-002',
    name: 'Secret Romance',
    tagline: 'Intimate floral · Whispered moments',
    description:
      'An intimate floral-fruity fragrance woven for whispered moments and timeless romance — elegant and unmistakably sensual.',
    topNotes: 'Red Berries, Mandarin, Bergamot',
    heartNotes: 'Rose, Peony, Violet',
    baseNotes: 'Vanilla, Patchouli, Musk',
    bottle: 'B',
    liquidColor: '#d87898',
    glassTint: '#f5e8ec',
    theme: {
      accent: '#e8b8c8',
      bg: '#100818',
      fog: '#0a0610',
      key: '#fff5f8',
      rim: '#d4af37',
      gold: '#d4af37',
      particle: '#f0b0c8',
      bloom: 0.58,
    },
  },
  {
    id: 'divine-aura',
    sku: 'ELV-DIVINE-005',
    name: 'Divine Aura',
    tagline: 'Celestial fresh · Soft musk',
    description:
      'A celestial fresh-floral opening with lavender and Sicilian orange, blooming into lily and jasmine — grounded by white musk.',
    topNotes: 'Lavender, Watermelon, Sicilian Orange',
    heartNotes: 'Lily of the Valley, Jasmine, Lotus',
    baseNotes: 'White Musk, Ambroxan, Sandalwood',
    bottle: 'B',
    liquidColor: '#6ab0d0',
    glassTint: '#e5f2f8',
    theme: {
      accent: '#a8d0e8',
      bg: '#061018',
      fog: '#040c14',
      key: '#f0faff',
      rim: '#d4af37',
      gold: '#d4af37',
      particle: '#90d0f0',
      bloom: 0.6,
    },
  },
];

/** Default center = Moon Blossom (index 2) */
export const DEFAULT_CENTER_INDEX = 2;

export const LAYOUT = {
  radius: 3.9,
  arcSpan: Math.PI * 1.05,
  centerScale: 1.42,
  sideScale: 0.8,
  farScale: 0.66,
  idleFloat: 0.05,
  idleSpin: 0.1,
  breath: 0.01,
  mouseParallax: 0.28,
  bottleParallax: 0.06,
  cameraIdle: { x: 0, y: 1.08, z: 7.4 },
  cameraFocus: { x: 0, y: 1.12, z: 3.75 },
  dprMax: 1.75,
};
