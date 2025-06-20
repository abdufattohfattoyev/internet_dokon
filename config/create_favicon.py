from PIL import Image, ImageDraw, ImageFont
import os


def create_favicon(size=(32, 32), filename='favicon.ico', font_size=None, output_dir='static'):
    """Zamonaviy favicon va app ikonalarini yaratish"""
    # Oq fonli rasm (shaffof fon PNG uchun)
    image = Image.new('RGBA', size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)

    # Professional ko'rinishdagi savat dizayni
    basket_color = (40, 102, 191)  # Ko'k rangli korporativ stil
    text_color = (40, 102, 191)  # Matn uchun bir xil rang

    # O'lchamlarga nisbatan moslashuvchan parametrlar
    scale = min(size) / 32  # 32px asosiy o'lcham

    # Savat tanasi (yumshoq burchakli to'rtburchak)
    basket_width = 22 * scale
    basket_height = 12 * scale
    basket_x = (size[0] - basket_width) / 2
    basket_y = 8 * scale

    # Sifatli savat chizish
    draw.rounded_rectangle(
        (basket_x, basket_y, basket_x + basket_width, basket_y + basket_height),
        radius=2 * scale,
        fill=basket_color,
        outline=basket_color
    )

    # Savat tutqichi (yumshoq egri chiziq)
    handle_width = 14 * scale
    handle_height = 6 * scale
    handle_x = basket_x + (basket_width - handle_width) / 2
    handle_y = basket_y - handle_height / 2

    draw.arc(
        (handle_x, handle_y, handle_x + handle_width, handle_y + handle_height),
        start=0, end=180,
        fill=basket_color,
        width=int(2 * scale)
    )

    # Matnni avtomatik o'lchamda sozlash
    if font_size is None:
        font_size = int(6 * scale)

    # Matn uchun yaxshi shrift
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        try:
            font = ImageFont.truetype("arialbd.ttf", font_size)  # Qalin shrift
        except IOError:
            font = ImageFont.load_default()

    text = "OPTIM HALOL" if size[0] >= 64 else "HM"  # Katta o'lchamda to'liq nom

    # Matnni markazga joylashtirish
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    text_x = (size[0] - text_width) / 2
    text_y = basket_y + basket_height + (2 * scale)

    draw.text(
        (text_x, text_y),
        text,
        fill=text_color,
        font=font
    )

    # Chiqish papkasini yaratish
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)

    # Formatga qarab saqlash
    if filename.lower().endswith('.ico'):
        image.convert('RGBA').save(output_path, format='ICO', sizes=[size])
    else:
        image.save(output_path, format='PNG', optimize=True)

    print(f"Ikon {size[0]}x{size[1]} {output_path} ga saqlandi")


if __name__ == "__main__":
    # Turli o'lchamdagi faviconlar
    create_favicon(size=(16, 16), filename='favicon.ico')
    create_favicon(size=(32, 32), filename='favicon-32x32.png')
    create_favicon(size=(64, 64), filename='favicon-64x64.png')

    # Apple Touch Icon
    create_favicon(size=(180, 180), filename='apple-touch-icon.png')

    # Android va boshqa platformalar uchun
    create_favicon(size=(192, 192), filename='android-chrome-192x192.png')
    create_favicon(size=(512, 512), filename='android-chrome-512x512.png')