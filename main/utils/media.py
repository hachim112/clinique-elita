from pathlib import Path
from urllib.parse import quote

from django.conf import settings
from django.templatetags.static import static
from django.utils.encoding import filepath_to_uri


PLACEHOLDER_SVG = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
    "viewBox='0 0 100 100'%3E%3Crect fill='%23f5f7fa' width='100' height='100'/%3E"
    "%3Ctext x='50' y='50' text-anchor='middle' dy='.35em' fill='%239ca3af' "
    "font-family='sans-serif' font-size='12'%3ENo Image%3C/text%3E%3C/svg%3E"
)


def resolve_media_url(image_field):
    """Return a working URL for an ImageField."""
    if not image_field:
        return ''

    name = getattr(image_field, 'name', None)
    if not name:
        return ''

    normalized_name = name.replace(chr(92), '/')
    rel_url = filepath_to_uri(normalized_name)
    expected_url = settings.MEDIA_URL + rel_url

    try:
        url = image_field.url
        if url and url != '/':
            return url
    except Exception:
        pass

    try:
        media_root = str(settings.MEDIA_ROOT)
        media_path = Path(media_root) / normalized_name
        if media_path.is_file():
            return expected_url
    except Exception:
        pass

    try:
        seed_path = Path(settings.BASE_DIR) / 'static' / 'seed' / normalized_name
        if seed_path.is_file():
            return static(f'seed/{normalized_name}')
    except Exception:
        pass

    return PLACEHOLDER_SVG
