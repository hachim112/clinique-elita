from django import template

from main.utils.media import resolve_media_url

register = template.Library()


@register.filter
def media_url(image_field):
    return resolve_media_url(image_field)
