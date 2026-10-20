"""Shared link-preview metadata; Open Graph image URLs must be absolute."""
from html import escape
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://farouk-yusuf.github.io/'
PREVIEWS = json.loads((ROOT/'site/social.json').read_text())


def metadata(page):
    if page not in PREVIEWS:
        return ''
    item = PREVIEWS[page]
    values = {
        'og:type': 'website', 'og:site_name': 'Farouk Yusuf',
        'og:locale': 'en_GB', 'og:url': ORIGIN+('' if page=='index.html' else page),
        'og:title': item['title'], 'og:description': item['description'],
        'og:image': ORIGIN+item['image'], 'og:image:type': 'image/png',
        'og:image:width': '1200', 'og:image:height': '627',
        'og:image:alt': item['alt'],
        'twitter:card': 'summary_large_image', 'twitter:title': item['title'],
        'twitter:description': item['description'],
        'twitter:image': ORIGIN+item['image'], 'twitter:image:alt': item['alt'],
    }
    return '\n'.join(f'<meta {"property" if key.startswith("og:") else "name"}="{key}" content="{escape(value,quote=True)}">' for key,value in values.items())
