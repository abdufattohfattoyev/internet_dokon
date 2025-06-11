# internet_dukon_zakaz/internet_dukon_zakaz/celery.py
import os
from celery import Celery

# Django sozlamalar modulini aniqlash
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Celery ilovasini yaratish
app = Celery('config')

# Django sozlamalaridan Celery konfiguratsiyasini yuklash
app.config_from_object('django.conf:settings', namespace='CELERY')

# Loyihadagi tasklarni avtomatik topish
app.autodiscover_tasks()