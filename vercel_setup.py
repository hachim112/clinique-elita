import os
import time
import shutil
from pathlib import Path

import django
from django.conf import settings
from django.core.management import call_command
from django.db import OperationalError
from django.db.migrations.executor import MigrationExecutor


def _has_pending_migrations():
    from django.db import connection

    executor = MigrationExecutor(connection)
    targets = executor.loader.graph.leaf_nodes()
    return bool(executor.migration_plan(targets))


def _run_migrations():
    for attempt in range(3):
        try:
            if _has_pending_migrations():
                call_command('migrate', interactive=False, verbosity=0)
            return
        except OperationalError:
            if attempt == 2:
                raise
            time.sleep(0.5)


def _ensure_default_admin():
    if os.environ.get('AUTO_CREATE_ADMIN', '1') == '0':
        return

    from django.contrib.auth.models import User

    username = os.environ.get('ADMIN_USERNAME', 'admin')
    password = os.environ.get('ADMIN_PASSWORD', 'admin')
    email = os.environ.get('ADMIN_EMAIL', 'admin@cliniqueelita.local')

    user, created = User.objects.get_or_create(username=username)
    user.email = email
    user.is_staff = True
    user.is_superuser = True
    if created or os.environ.get('ADMIN_PASSWORD'):
        user.set_password(password)
    user.save()


def _bundle_static_media_into_tmp():
    from pathlib import Path
    from django.conf import settings

    media_root = Path(settings.MEDIA_ROOT)
    media_root.mkdir(parents=True, exist_ok=True)
    (media_root / 'categories').mkdir(parents=True, exist_ok=True)
    (media_root / 'products').mkdir(parents=True, exist_ok=True)

    bundled = Path(settings.BASE_DIR) / 'staticfiles' / 'images'
    if not bundled.exists():
        return

    tmp_categories = media_root / 'categories'
    tmp_products = media_root / 'products'

    bundled_categories = bundled / 'categories'
    if bundled_categories.exists() and bundled_categories.is_dir():
        for f in bundled_categories.iterdir():
            if f.is_file() and not (tmp_categories / f.name).exists():
                shutil.copy2(str(f), str(tmp_categories / f.name))

    bundled_products = bundled / 'products'
    if bundled_products.exists() and bundled_products.is_dir():
        for f in bundled_products.iterdir():
            if f.is_file() and not (tmp_products / f.name).exists():
                shutil.copy2(str(f), str(tmp_products / f.name))


def run_vercel_setup():
    if not os.environ.get('VERCEL'):
        return

    django.setup()

    _bundle_static_media_into_tmp()

    _run_migrations()
    _ensure_default_admin()
