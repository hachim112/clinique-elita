from django.db import migrations
import random


def generate_unique_tracking_id():
    return f"APT{random.randint(10000, 99999)}"


def populate_tracking_ids(apps, schema_editor):
    Appointment = apps.get_model('main', 'Appointment')
    for appointment in Appointment.objects.all():
        if not appointment.tracking_id:
            appointment.tracking_id = generate_unique_tracking_id()
            appointment.save()


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_appointment_tracking_id'),
    ]

    operations = [
        migrations.RunPython(populate_tracking_ids),
    ]