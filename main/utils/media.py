from pathlib import Path

from django.conf import settings
from django.templatetags.static import static


def resolve_media_url(image_field):
    """Return a working URL for an ImageField (local media, Vercel /tmp, or static seed fallback)."""
    if not image_field:
        return ''

    name = getattr(image_field, 'name', None)
    if not name:
        return ''

    media_path = Path(settings.MEDIA_ROOT) / name
    if media_path.is_file():
        return image_field.url

    seed_path = Path(settings.BASE_DIR) / 'static' / 'seed' / Path(name)
    if seed_path.is_file():
        return static(f'seed/{name.replace(chr(92), "/")}')

    return image_field.url
