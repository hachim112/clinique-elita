"""
WSGI config for clinique_elita project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
import sys
import stat
import posixpath
from pathlib import Path
from urllib.parse import unquote

from django.core.wsgi import get_wsgi_application
from django.utils.http import http_date
from django.utils.encoding import force_str
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinique_elita.settings')

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from vercel_setup import run_vercel_setup

run_vercel_setup()

_original_app = get_wsgi_application()


class _VercelMediaMiddleware:
    """Serve /media/ files from MEDIA_ROOT on Vercel (serverless, no DEBUG)."""
    
    def __init__(self, app, media_root, media_url):
        self._app = app
        self._media_root = str(media_root)
        self._media_url = media_url.rstrip('/')
    
    def _guess_type(self, path):
        import mimetypes
        return mimetypes.guess_type(path)[0] or 'application/octet-stream'
    
    def _serve_file(self, filepath, content_type):
        try:
            with open(filepath, 'rb') as f:
                st = os.fstat(f.fileno())
                etag = f'"{st.st_mtime:.3f}-{st.st_size:d}"'
                headers = [
                    ('Content-Type', content_type),
                    ('Content-Length', str(st.st_size)),
                    ('Last-Modified', http_date(st.st_mtime)),
                    ('ETag', etag),
                ]
                from wsgiref.util import FileWrapper
                return iter([f.read()]), headers, '200 OK'
        except (IOError, OSError):
            return None
    
    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        if not path.startswith(self._media_url + '/'):
            return self._app(environ, start_response)
        
        relative = path[len(self._media_url) + 1:]
        filepath = os.path.normpath(os.path.join(self._media_root, unquote(relative)))
        
        if not filepath.startswith(self._media_root) or not os.path.isfile(filepath):
            start_response('404 Not Found', [('Content-Type', 'text/plain')])
            return [b'Not Found']
        
        content_type = self._guess_type(filepath)
        result = self._serve_file(filepath, content_type)
        if result is None:
            start_response('403 Forbidden', [('Content-Type', 'text/plain')])
            return [b'Forbidden']
        
        body_iter, headers, status = result
        start_response(status, headers)
        return body_iter


if os.environ.get('VERCEL'):
    application = _VercelMediaMiddleware(
        _original_app,
        settings.MEDIA_ROOT,
        settings.MEDIA_URL
    )
else:
    application = _original_app
