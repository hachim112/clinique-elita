from pathlib import Path
from urllib.parse import quote

from django.conf import settings
from django.templatetags.static import static


PLACEHOLDER_SVG = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
    "viewBox='0 0 100 100'%3E%3Crect fill='%23f5f7fa' width='100' height='100'/%3E"
    "%3Ctext x='50' y='50' text-anchor='middle' dy='.35em' fill='%239ca3af' "
    "font-family='sans-serif' font-size='12'%3ENo Image%3C/text%3E%3C/svg%3E"
)


def resolve_media_url(image_field):
    """Return a working URL for an ImageField (local media, Vercel /tmp, or static seed fallback)."""
    if not image_field:
        return ''

    name = getattr(image_field, 'name', None)
    if not name:
        return ''

    normalized_name = name.replace(chr(92), '/')

    media_path = Path(settings.MEDIA_ROOT) / normalized_name
    if media_path.is_file():
        return image_field.url

    seed_path = Path(settings.BASE_DIR) / 'static' / 'seed' / normalized_name
    if seed_path.is_file():
        return static(f'seed/{normalized_name}')

    return PLACEHOLDER_SVG
