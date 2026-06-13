"""
WSGI config for clinique_elita project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinique_elita.settings')

from vercel_setup import run_vercel_setup

run_vercel_setup()

application = get_wsgi_application()
