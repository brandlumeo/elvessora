"""Build locale/*/LC_MESSAGES/django.po and django.mo without system gettext."""
from __future__ import annotations

import struct
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
LOCALE = BASE / 'locale'

# msgid -> {lang: msgstr}
TRANSLATIONS = {
    'Language': {
        'ar': 'اللغة', 'hi': 'भाषा', 'fr': 'Langue', 'ru': 'Язык',
    },
    'Select language': {
        'ar': 'اختر اللغة', 'hi': 'भाषा चुनें', 'fr': 'Choisir la langue', 'ru': 'Выберите язык',
    },
    'Luxury Perfumes': {
        'ar': 'عطور فاخرة', 'hi': 'लक्ज़री परफ्यूम', 'fr': 'Parfums de luxe', 'ru': 'Люксовые ароматы',
    },
    'Discover luxury fragrances at %(brand)s. Shop perfumes by fragrance family, occasion, and more.': {
        'ar': 'اكتشف العطور الفاخرة لدى %(brand)s. تسوّق حسب العائلة العطرية والمناسبة والمزيد.',
        'hi': '%(brand)s पर लक्ज़री खुशबू खोजें। परिवार, अवसर और अधिक के अनुसार खरीदें।',
        'fr': 'Découvrez les fragrances de luxe chez %(brand)s. Achetez par famille olfactive, occasion et plus.',
        'ru': 'Откройте люксовые ароматы в %(brand)s. Покупайте по семействам, поводам и другому.',
    },
    'Free shipping on orders above %(amount)s': {
        'ar': 'شحن مجاني للطلبات فوق %(amount)s',
        'hi': '%(amount)s से ऊपर के ऑर्डर पर मुफ़्त शिपिंग',
        'fr': 'Livraison gratuite dès %(amount)s',
        'ru': 'Бесплатная доставка от %(amount)s',
    },
    'Free shipping %(amount)s+': {
        'ar': 'شحن مجاني %(amount)s+',
        'hi': 'मुफ़्त शिपिंग %(amount)s+',
        'fr': 'Livraison gratuite %(amount)s+',
        'ru': 'Бесплатная доставка %(amount)s+',
    },
    'Track Order': {
        'ar': 'تتبع الطلب', 'hi': 'ऑर्डर ट्रैक करें', 'fr': 'Suivre la commande', 'ru': 'Отследить заказ',
    },
    'Contact': {
        'ar': 'اتصل بنا', 'hi': 'संपर्क', 'fr': 'Contact', 'ru': 'Контакты',
    },
    'Chat on WhatsApp': {
        'ar': 'تواصل عبر واتساب', 'hi': 'व्हाट्सऐप पर चैट करें', 'fr': 'Discuter sur WhatsApp', 'ru': 'Написать в WhatsApp',
    },
    'Shop': {
        'ar': 'تسوق', 'hi': 'शॉप', 'fr': 'Boutique', 'ru': 'Магазин',
    },
    'All Perfumes': {
        'ar': 'جميع العطور', 'hi': 'सभी परफ्यूम', 'fr': 'Tous les parfums', 'ru': 'Все ароматы',
    },
    'Best Sellers': {
        'ar': 'الأكثر مبيعاً', 'hi': 'बेस्ट सेलर', 'fr': 'Meilleures ventes', 'ru': 'Бестселлеры',
    },
    'New Arrivals': {
        'ar': 'وصل حديثاً', 'hi': 'नए आगमन', 'fr': 'Nouveautés', 'ru': 'Новинки',
    },
    'Gift Sets': {
        'ar': 'أطقم الهدايا', 'hi': 'गिफ्ट सेट', 'fr': 'Coffrets cadeaux', 'ru': 'Подарочные наборы',
    },
    'Policies': {
        'ar': 'السياسات', 'hi': 'नीतियाँ', 'fr': 'Politiques', 'ru': 'Политики',
    },
    'Privacy Policy': {
        'ar': 'سياسة الخصوصية', 'hi': 'गोपनीयता नीति', 'fr': 'Politique de confidentialité', 'ru': 'Политика конфиденциальности',
    },
    'Terms & Conditions': {
        'ar': 'الشروط والأحكام', 'hi': 'नियम और शर्तें', 'fr': 'Conditions générales', 'ru': 'Условия использования',
    },
    'Shipping Policy': {
        'ar': 'سياسة الشحن', 'hi': 'शिपिंग नीति', 'fr': 'Politique de livraison', 'ru': 'Политика доставки',
    },
    'Return & Refund': {
        'ar': 'الإرجاع والاسترداد', 'hi': 'वापसी और रिफंड', 'fr': 'Retours et remboursements', 'ru': 'Возврат и возмещение',
    },
    'Help': {
        'ar': 'المساعدة', 'hi': 'सहायता', 'fr': 'Aide', 'ru': 'Помощь',
    },
    'FAQ': {
        'ar': 'الأسئلة الشائعة', 'hi': 'अक्सर पूछे जाने वाले प्रश्न', 'fr': 'FAQ', 'ru': 'FAQ',
    },
    'Contact Us': {
        'ar': 'تواصل معنا', 'hi': 'हमसे संपर्क करें', 'fr': 'Nous contacter', 'ru': 'Связаться с нами',
    },
    'Returns': {
        'ar': 'المرتجعات', 'hi': 'रिटर्न', 'fr': 'Retours', 'ru': 'Возвраты',
    },
    'Newsletter': {
        'ar': 'النشرة البريدية', 'hi': 'न्यूज़लेटर', 'fr': 'Newsletter', 'ru': 'Рассылка',
    },
    'Subscribe for exclusive offers and new arrivals.': {
        'ar': 'اشترك للحصول على عروض حصرية والوصول الجديد.',
        'hi': 'विशेष ऑफ़र और नए आगमन के लिए सदस्यता लें।',
        'fr': 'Abonnez-vous pour des offres exclusives et les nouveautés.',
        'ru': 'Подпишитесь на эксклюзивные предложения и новинки.',
    },
    'Your email': {
        'ar': 'بريدك الإلكتروني', 'hi': 'आपका ईमेल', 'fr': 'Votre e-mail', 'ru': 'Ваш email',
    },
    'Subscribe': {
        'ar': 'اشترك', 'hi': 'सब्सक्राइब', 'fr': "S'abonner", 'ru': 'Подписаться',
    },
    'All rights reserved.': {
        'ar': 'جميع الحقوق محفوظة.', 'hi': 'सर्वाधिकार सुरक्षित।', 'fr': 'Tous droits réservés.', 'ru': 'Все права защищены.',
    },
    'Privacy': {
        'ar': 'الخصوصية', 'hi': 'गोपनीयता', 'fr': 'Confidentialité', 'ru': 'Конфиденциальность',
    },
    'Terms': {
        'ar': 'الشروط', 'hi': 'शर्तें', 'fr': 'Conditions', 'ru': 'Условия',
    },
    'Shipping': {
        'ar': 'الشحن', 'hi': 'शिपिंग', 'fr': 'Livraison', 'ru': 'Доставка',
    },
    'Cookies': {
        'ar': 'ملفات تعريف الارتباط', 'hi': 'कुकीज़', 'fr': 'Cookies', 'ru': 'Cookies',
    },
    'Home': {
        'ar': 'الرئيسية', 'hi': 'होम', 'fr': 'Accueil', 'ru': 'Главная',
    },
    'Collection': {
        'ar': 'المجموعة', 'hi': 'कलेक्शन', 'fr': 'Collection', 'ru': 'Коллекция',
    },
    'Perfume Finder': {
        'ar': 'مكتشف العطور', 'hi': 'परफ्यूम फाइंडर', 'fr': 'Trouver mon parfum', 'ru': 'Подбор аромата',
    },
    'About Us': {
        'ar': 'من نحن', 'hi': 'हमारे बारे में', 'fr': 'À propos', 'ru': 'О нас',
    },
    'Search': {
        'ar': 'بحث', 'hi': 'खोज', 'fr': 'Rechercher', 'ru': 'Поиск',
    },
    'Search perfumes': {
        'ar': 'ابحث عن العطور', 'hi': 'परफ्यूम खोजें', 'fr': 'Rechercher des parfums', 'ru': 'Искать ароматы',
    },
    'Wishlist': {
        'ar': 'قائمة الأمنيات', 'hi': 'विशलिस्ट', 'fr': 'Liste de souhaits', 'ru': 'Избранное',
    },
    'Cart': {
        'ar': 'السلة', 'hi': 'कार्ट', 'fr': 'Panier', 'ru': 'Корзина',
    },
    'Account': {
        'ar': 'الحساب', 'hi': 'खाता', 'fr': 'Compte', 'ru': 'Аккаунт',
    },
    'My Profile': {
        'ar': 'ملفي الشخصي', 'hi': 'मेरी प्रोफ़ाइल', 'fr': 'Mon profil', 'ru': 'Мой профиль',
    },
    'Orders': {
        'ar': 'طلباتي', 'hi': 'ऑर्डर', 'fr': 'Commandes', 'ru': 'Заказы',
    },
    'Addresses': {
        'ar': 'العناوين', 'hi': 'पते', 'fr': 'Adresses', 'ru': 'Адреса',
    },
    'Admin Dashboard': {
        'ar': 'لوحة التحكم', 'hi': 'एडमिन डैशबोर्ड', 'fr': "Tableau d'administration", 'ru': 'Админ-панель',
    },
    'Logout': {
        'ar': 'تسجيل الخروج', 'hi': 'लॉग आउट', 'fr': 'Déconnexion', 'ru': 'Выйти',
    },
    'Sign In': {
        'ar': 'تسجيل الدخول', 'hi': 'साइन इन', 'fr': 'Connexion', 'ru': 'Войти',
    },
    'Menu': {
        'ar': 'القائمة', 'hi': 'मेनू', 'fr': 'Menu', 'ru': 'Меню',
    },
    'Search fragrances...': {
        'ar': 'ابحث عن العطور...', 'hi': 'खुशबू खोजें...', 'fr': 'Rechercher des fragrances...', 'ru': 'Искать ароматы...',
    },
}


def _escape_po(s: str) -> str:
    return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')


def write_po(lang: str, pairs: dict[str, str]) -> Path:
    folder = LOCALE / lang / 'LC_MESSAGES'
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / 'django.po'
    lines = [
        'msgid ""',
        'msgstr ""',
        '"Content-Type: text/plain; charset=UTF-8\\n"',
        '"Language: %s\\n"' % lang,
        '',
    ]
    for msgid, msgstr in pairs.items():
        lines.append('msgid "%s"' % _escape_po(msgid))
        lines.append('msgstr "%s"' % _escape_po(msgstr))
        lines.append('')
    path.write_text('\n'.join(lines), encoding='utf-8')
    return path


def write_mo(po_path: Path) -> Path:
    """Minimal .mo writer (GNU gettext binary) with UTF-8 catalog header."""
    entries: list[tuple[str, str]] = []
    msgid = msgstr = None
    for raw in po_path.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if line.startswith('msgid '):
            if msgid is not None and msgstr is not None:
                entries.append((msgid, msgstr))
            msgid = line[6:].strip()
            if msgid.startswith('"') and msgid.endswith('"'):
                msgid = msgid[1:-1].replace('\\"', '"').replace('\\\\', '\\')
            msgstr = None
        elif line.startswith('msgstr '):
            msgstr = line[7:].strip()
            if msgstr.startswith('"') and msgstr.endswith('"'):
                msgstr = msgstr[1:-1].replace('\\"', '"').replace('\\\\', '\\')
        elif line.startswith('"') and msgstr is not None and msgid == '':
            # continuation of header msgstr
            part = line.strip('"').replace('\\n', '\n').replace('\\"', '"')
            msgstr += part
    if msgid is not None and msgstr is not None:
        entries.append((msgid, msgstr))

    # Ensure charset header exists for non-ASCII translations
    mapping = {k: v for k, v in entries}
    if '' not in mapping or 'charset=UTF-8' not in mapping.get('', ''):
        mapping[''] = 'Content-Type: text/plain; charset=UTF-8\n'

    keys = sorted(mapping.keys(), key=lambda k: (k != '', k))
    ids = b''.join(k.encode('utf-8') + b'\x00' for k in keys)
    strs = b''.join(mapping[k].encode('utf-8') + b'\x00' for k in keys)

    keystart = 7 * 4 + 16 * len(keys)
    valuestart = keystart + len(ids)
    keyoffsets = []
    offset = 0
    for k in keys:
        bl = len(k.encode('utf-8'))
        keyoffsets.append((bl, keystart + offset))
        offset += bl + 1
    valueoffsets = []
    offset = 0
    for k in keys:
        bl = len(mapping[k].encode('utf-8'))
        valueoffsets.append((bl, valuestart + offset))
        offset += bl + 1

    output = struct.pack(
        'Iiiiiii',
        0x950412DE,
        0,
        len(keys),
        7 * 4,
        7 * 4 + 8 * len(keys),
        0,
        0,
    )
    for length, off in keyoffsets:
        output += struct.pack('ii', length, off)
    for length, off in valueoffsets:
        output += struct.pack('ii', length, off)
    output += ids + strs

    mo_path = po_path.with_suffix('.mo')
    mo_path.write_bytes(output)
    return mo_path


def main():
    langs = ['ar', 'hi', 'fr', 'ru']
    for lang in langs:
        pairs = {msgid: trans[lang] for msgid, trans in TRANSLATIONS.items() if lang in trans}
        po = write_po(lang, pairs)
        mo = write_mo(po)
        print(f'{lang}: {len(pairs)} strings -> {mo.relative_to(BASE)}')


if __name__ == '__main__':
    main()
