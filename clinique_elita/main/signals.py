from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Appointment
import random


@receiver(pre_save, sender=Appointment)
def generate_tracking_id(sender, instance, **kwargs):
    if not instance.tracking_id:
        while True:
            apt_id = f"APT{random.randint(10000, 99999)}"
            if not Appointment.objects.filter(tracking_id=apt_id).exists():
                instance.tracking_id = apt_id
                break