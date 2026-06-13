 import os
 import sys

 sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '.'))

 os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinique_elita.settings')

 from clinique_elita.wsgi import application  # noqa: F401
 from vercel_setup import run_vercel_setup  # noqa: E402
 run_vercel_setup()
