"""Copy uploaded client assets and extract perfume bottles with transparent backgrounds."""
from pathlib import Path

from PIL import Image

try:
    from rembg import remove as rembg_remove
    HAS_REMBG = True
except ImportError:
    HAS_REMBG = False

ROOT = Path(__file__).resolve().parents[1]
ASSETS = Path(r'C:\Users\M S I\.cursor\projects\c-Users-M-S-I-Desktop-Elvassora-perfumes\assets')
OUT_PRODUCTS = ROOT / 'static' / 'images' / 'products'
OUT_BRAND = ROOT / 'static' / 'images' / 'brand'

# Exact uploaded source files mapped to signature SKUs
PRODUCT_SOURCES = {
    'ELV-MOON-001': ASSETS / (
        'c__Users_M_S_I_AppData_Roaming_Cursor_User_workspaceStorage_544d1d6df95f8b680a89deec03b37b7e_'
        'images_bcaf54ff-3c73-4709-bc2f-1d7ac6436725-fe0d018f-39b2-442f-9ab5-c223ea5929fa.png'
    ),
    'ELV-SECRET-002': ASSETS / (
        'c__Users_M_S_I_AppData_Roaming_Cursor_User_workspaceStorage_544d1d6df95f8b680a89deec03b37b7e_'
        'images_ELVESSORA_secret_romance-2e26a25f-e61d-41e5-bcb7-a4ff26ff3ba5.png'
    ),
    'ELV-AMBER-003': ASSETS / (
        'c__Users_M_S_I_AppData_Roaming_Cursor_User_workspaceStorage_544d1d6df95f8b680a89deec03b37b7e_'
        'images_ELVESSORA_amber_petals-47c323f0-5e99-4906-9c6c-a17850926cfc.png'
    ),
    'ELV-ENCHANT-004': ASSETS / (
        'c__Users_M_S_I_AppData_Roaming_Cursor_User_workspaceStorage_544d1d6df95f8b680a89deec03b37b7e_'
        'images_7b192493-7b84-4cae-a219-f4a5e353ef3e-e1a5ee94-e099-40b8-840e-cf6811bac397.png'
    ),
    'ELV-DIVINE-005': ASSETS / (
        'c__Users_M_S_I_AppData_Roaming_Cursor_User_workspaceStorage_544d1d6df95f8b680a89deec03b37b7e_'
        'images_ELVESSORA_Divine_Aura-441dd257-b427-4236-9e56-40c25c1f5464.png'
    ),
}

SKU_TO_FILENAME = {
    'ELV-MOON-001': 'elvessora-moon-blossom.png',
    'ELV-SECRET-002': 'elvessora-secret-romance.png',
    'ELV-AMBER-003': 'elvessora-amber-petals.png',
    'ELV-ENCHANT-004': 'elvessora-enchante-bloom.png',
    'ELV-DIVINE-005': 'elvessora-divine-aura.png',
}

LOGO_SOURCE = ASSETS / 'elvessora-logo.png'


def extract_bottle(src: Path, dest: Path) -> None:
    raw = Image.open(src).convert('RGBA')
    if HAS_REMBG:
        result = rembg_remove(raw)
        if isinstance(result, bytes):
            from io import BytesIO
            result = Image.open(BytesIO(result)).convert('RGBA')
        else:
            result = result.convert('RGBA')
    else:
        result = raw

    # Trim transparent margins
    bbox = result.getbbox()
    if bbox:
        result = result.crop(bbox)

    # Max height for web while preserving proportions
    max_h = 1400
    if result.height > max_h:
        ratio = max_h / result.height
        result = result.resize(
            (int(result.width * ratio), max_h),
            Image.LANCZOS,
        )

    dest.parent.mkdir(parents=True, exist_ok=True)
    result.save(dest, optimize=True)
    print(f'  saved {dest.name} ({result.size[0]}x{result.size[1]})')


def main():
    OUT_PRODUCTS.mkdir(parents=True, exist_ok=True)
    OUT_BRAND.mkdir(parents=True, exist_ok=True)

    if LOGO_SOURCE.exists():
        logo_dest = OUT_BRAND / 'elvessora-logo-gold.png'
        Image.open(LOGO_SOURCE).convert('RGBA').save(logo_dest, optimize=True)
        print(f'logo -> {logo_dest}')

    for sku, src in PRODUCT_SOURCES.items():
        if not src.exists():
            print(f'MISSING: {src.name}')
            continue
        dest = OUT_PRODUCTS / SKU_TO_FILENAME[sku]
        print(f'processing {sku}...')
        extract_bottle(src, dest)


if __name__ == '__main__':
    main()
