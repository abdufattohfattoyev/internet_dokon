#!/bin/bash
# ============================================================
#  COMBINED SSL setup  —  Ikkala loyiha uchun
#  Server: 147.93.130.94
#
#  Foydalanish:
#    cd /root/internet_dokon
#    bash ssl_setup.sh
#
#  Agar loyihalar boshqa yo'lda bo'lsa, quyidagi 2 qatorni o'zgartiring:
# ============================================================

set -e

DOKON_PATH="/root/internet_dokon"
DORIXONA_PATH="/root/internet_dorixona"
DOKON_DOMAIN="optimhalolmarket.uz"
DORIXONA_DOMAIN="vitagum-gummy.uz"

# ─────────────────────────────────────────────
echo "▶ 1. Nginx va Certbot o'rnatish"
# ─────────────────────────────────────────────
apt-get update -y
apt-get install -y nginx certbot python3-certbot-nginx

# ─────────────────────────────────────────────
echo "▶ 2. Eski Docker nginx konteynerlarini to'xtatish"
# ─────────────────────────────────────────────
cd $DORIXONA_PATH
docker compose down 2>/dev/null || docker-compose down 2>/dev/null || true

cd $DOKON_PATH
docker compose down 2>/dev/null || docker-compose down 2>/dev/null || true

# ─────────────────────────────────────────────
echo "▶ 3. Certbot uchun vaqtinchalik HTTP nginx"
# ─────────────────────────────────────────────
mkdir -p /var/www/certbot
rm -f /etc/nginx/sites-enabled/*

cat > /etc/nginx/sites-available/certbot-temp << TMPEOF
server {
    listen 80;
    server_name $DORIXONA_DOMAIN www.$DORIXONA_DOMAIN $DOKON_DOMAIN www.$DOKON_DOMAIN;
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    location / { return 200 "OK"; add_header Content-Type text/plain; }
}
TMPEOF

ln -sf /etc/nginx/sites-available/certbot-temp /etc/nginx/sites-enabled/certbot-temp
nginx -t && systemctl restart nginx

# ─────────────────────────────────────────────
echo "▶ 4. SSL sertifikatlar olish"
# ─────────────────────────────────────────────

# vitagum-gummy.uz uchun
certbot certonly --webroot -w /var/www/certbot \
    -d $DORIXONA_DOMAIN -d www.$DORIXONA_DOMAIN \
    --non-interactive --agree-tos \
    --email webmaster@$DORIXONA_DOMAIN \
    || echo "⚠  $DORIXONA_DOMAIN sertifikat allaqachon mavjud yoki DNS hali ulanganda emas"

# optimhalolmarket.uz uchun
certbot certonly --webroot -w /var/www/certbot \
    -d $DOKON_DOMAIN -d www.$DOKON_DOMAIN \
    --non-interactive --agree-tos \
    --email webmaster@$DOKON_DOMAIN \
    || echo "⚠  $DOKON_DOMAIN sertifikat allaqachon mavjud yoki DNS hali ulanganda emas"

# ─────────────────────────────────────────────
echo "▶ 5. Host nginx configlarini o'rnatish"
# ─────────────────────────────────────────────
rm -f /etc/nginx/sites-enabled/*

# vitagum-gummy.uz config
cp $DORIXONA_PATH/nginx/nginx.conf /etc/nginx/sites-available/$DORIXONA_DOMAIN
sed -i "s|/root/internet_dorixona|$DORIXONA_PATH|g" /etc/nginx/sites-available/$DORIXONA_DOMAIN
ln -sf /etc/nginx/sites-available/$DORIXONA_DOMAIN /etc/nginx/sites-enabled/

# optimhalolmarket.uz config
cp $DOKON_PATH/nginx/nginx.conf /etc/nginx/sites-available/$DOKON_DOMAIN
sed -i "s|/root/internet_dokon|$DOKON_PATH|g" /etc/nginx/sites-available/$DOKON_DOMAIN
ln -sf /etc/nginx/sites-available/$DOKON_DOMAIN /etc/nginx/sites-enabled/

nginx -t && systemctl reload nginx

# ─────────────────────────────────────────────
echo "▶ 6. Docker ilovalarini ishga tushirish"
# ─────────────────────────────────────────────
cd $DORIXONA_PATH
docker compose up -d --build 2>/dev/null || docker-compose up -d --build

cd $DOKON_PATH
docker compose up -d --build 2>/dev/null || docker-compose up -d --build

# ─────────────────────────────────────────────
echo "▶ 7. Sertifikat auto-yangilanish (cron)"
# ─────────────────────────────────────────────
CRON_JOB="0 3 * * * certbot renew --quiet && systemctl reload nginx"
( crontab -l 2>/dev/null | grep -v "certbot renew"; echo "$CRON_JOB" ) | crontab -

# ─────────────────────────────────────────────
echo ""
echo "✅  TAYYOR!"
echo ""
echo "   🌐  https://$DORIXONA_DOMAIN   (internet_dorixona — port 8005)"
echo "   🌐  https://$DOKON_DOMAIN    (internet_dokon     — port 8000)"
echo ""
echo "   📋  Tekshirish buyruqlari:"
echo "   docker compose -f $DORIXONA_PATH/docker-compose.yml logs --tail=50"
echo "   docker compose -f $DOKON_PATH/docker-compose.yml logs --tail=50"
echo "   systemctl status nginx"
echo "   certbot certificates"
