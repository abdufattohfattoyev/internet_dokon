FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Foydalanuvchi yaratish
RUN useradd -m appuser && chown -R appuser:appuser /app

# Requirements o'rnatish
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Loyiha fayllarini ko'chirish
COPY --chown=appuser:appuser . .

# Static files papkasini tayyorlash
RUN mkdir -p /app/staticfiles && chown -R appuser:appuser /app/staticfiles

# Static fayllarni yig'ish
RUN python manage.py collectstatic --noinput --clear

# Foydalanuvchini o'zgartirish
USER appuser

# Serverni ishga tushirish
CMD ["gunicorn", "--bind", "0.0.0.0:8005", "--workers", "3", "--timeout", "120", "config.wsgi:application"]