import html
import logging
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.utils import timezone
from .utils import send_telegram_message
from .forms import OrderForm
from .models import Category, Product, Cart, CartItem, Order, OrderItem

logger = logging.getLogger(__name__)


def get_cart(request):
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    cart, created = Cart.objects.get_or_create(session_key=session_key)
    return cart


def filter_and_paginate_products(products, request, per_page=10):
    """Qidiruv va paginatsiya logikasini umumiy funksiyaga ajratish"""
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    products = products.order_by('created_at')  # Eng eski mahsulotlar boshida, eng yangilar oxirida
    paginator = Paginator(products, per_page)
    page_number = request.GET.get('page')
    products_page = paginator.get_page(page_number)
    return products_page

def home(request):
    all_categories = Category.objects.all()
    products = Product.objects.select_related('category').all().order_by('created_at')  # Boshlang'ich saralash

    cart = get_cart(request)
    cart_products = [item.product for item in cart.cartitem_set.all()]

    # Kategoriya filtri
    category_slug = request.GET.get('category')
    if category_slug:
        current_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category__slug=category_slug)
        current_index = list(all_categories).index(current_category)
        start_index = max(0, current_index - 2)
        end_index = min(len(all_categories), current_index + 3)
        visible_categories = all_categories[start_index:end_index]
    else:
        # Agar kategoriya tanlanmagan bo'lsa, birinchi 5 ta kategoriya
        visible_categories = all_categories[:5]

    products_page = filter_and_paginate_products(products, request)

    return render(request, 'index.html', {
        'categories': all_categories,
        'visible_categories': visible_categories,
        'products': products_page,
        'cart': cart,
        'cart_products': cart_products
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    cart = get_cart(request)
    product_in_cart = cart.cartitem_set.filter(product=product).exists()

    return render(request, 'product_detail.html', {
        'product': product,
        'cart': cart,
        'product_in_cart': product_in_cart
    })


def cart_detail(request):
    cart = get_cart(request)
    return render(request, 'cart.html', {'cart': cart})


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category)
    cart = get_cart(request)
    cart_products = [item.product for item in cart.cartitem_set.all()]

    all_categories = Category.objects.all()
    current_index = list(all_categories).index(category)
    start_index = max(0, current_index - 2)
    end_index = min(len(all_categories), current_index + 3)
    visible_categories = all_categories[start_index:end_index]

    products_page = filter_and_paginate_products(products, request)

    return render(request, 'category_detail.html', {
        'category': category,
        'categories': all_categories,
        'visible_categories': visible_categories,
        'products': products_page,
        'cart': cart,
        'cart_products': cart_products
    })


@require_POST
def add_to_cart(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id)
        cart = get_cart(request)

        cart_item_exists = CartItem.objects.filter(cart=cart, product=product).exists()

        if cart_item_exists:
            return JsonResponse({
                'success': False,
                'cart_count': cart.cartitem_set.count(),
                'already_in_cart': True,
                'message': 'Bu mahsulot allaqachon savatda!'
            }, status=400)

        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=1
        )
        logger.info(f"Mahsulot #{product.id} savatga qo'shildi (session: {cart.session_key})")

        return JsonResponse({
            'success': True,
            'cart_count': cart.cartitem_set.count(),
            'already_in_cart': False,
            'message': 'Savatga qo‘shildi!'
        })
    except Exception as e:
        logger.error(f"Savatga qo'shishda xato: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Xato yuz berdi, qayta urinib ko‘ring.'
        }, status=500)


@require_POST
def toggle_cart(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id)
        cart = get_cart(request)
        existing = CartItem.objects.filter(cart=cart, product=product).first()
        if existing:
            existing.delete()
            action = 'removed'
        else:
            CartItem.objects.create(cart=cart, product=product, quantity=1)
            action = 'added'
        return JsonResponse({'success': True, 'action': action, 'cart_count': cart.cartitem_set.count()})
    except Exception as e:
        logger.error(f"Toggle cart xatosi: {e}")
        return JsonResponse({'success': False, 'message': 'Xato yuz berdi'}, status=500)


@require_POST
def update_cart(request, item_id):
    try:
        cart_item = get_object_or_404(CartItem, id=item_id, cart=get_cart(request))
        quantity = int(request.POST.get('quantity', 1))

        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
            logger.info(f"Savat elementi #{item_id} yangilandi: quantity={quantity}")
        else:
            cart_item.delete()
            logger.info(f"Savat elementi #{item_id} o'chirildi")

        return JsonResponse({
            'success': True,
            'item_total': cart_item.get_total_price() if quantity > 0 else 0,
            'cart_total': cart_item.cart.get_total_price(),
            'cart_count': cart_item.cart.cartitem_set.count()
        })
    except Exception as e:
        logger.error(f"Savatni yangilashda xato: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Xato yuz berdi, qayta urinib ko‘ring.'
        }, status=500)


@require_POST
def remove_from_cart(request, item_id):
    try:
        cart_item = get_object_or_404(CartItem, id=item_id, cart=get_cart(request))
        cart_item.delete()
        logger.info(f"Savat elementi #{item_id} o'chirildi")

        return JsonResponse({
            'success': True,
            'cart_total': cart_item.cart.get_total_price(),
            'cart_count': cart_item.cart.cartitem_set.count()
        })
    except Exception as e:
        logger.error(f"Savatdan o'chirishda xato: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Xato yuz berdi, qayta urinib ko‘ring.'
        }, status=500)

def create_order_items(order, cart_items):
    order_items = [
        OrderItem(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price
        )
        for item in cart_items
    ]
    OrderItem.objects.bulk_create(order_items)
    logger.info(f"Buyurtma #{order.id} uchun {len(order_items)} ta element yaratildi")


def send_order_notification(order, cart_items):
    e = html.escape

    items_list = "\n".join(
        [
            f"{i}. {e(item.product.name)} — {item.quantity} dona\n"
            f" └─ {item.product.price:,.0f} x {item.quantity} = {item.get_total_price():,.0f} so’m"
            for i, item in enumerate(cart_items, start=1)
        ]
    )

    if order.latitude and order.longitude:
        location_line = (
            f"📍 <b>Lokatsiya:</b> "
            f"<a href=\"https://maps.google.com/?q={order.latitude},{order.longitude}\">Google Maps</a> | "
            f"<a href=\"https://yandex.com/maps/?pt={order.longitude},{order.latitude}&amp;z=16\">Yandex Maps</a>\n"
            f"🌐 {order.latitude:.5f}, {order.longitude:.5f}"
        )
    else:
        region_city = e(", ".join(filter(None, [order.region, order.city])))
        not_entered = "Kiritilmagan"
        location_line = (
            f"📍 <b>Viloyat/Shahar:</b> {region_city or not_entered}\n"
            f"🏠 <b>Manzil:</b> {e(order.address) if order.address else not_entered}"
        )

    notes_text = e(order.notes) if order.notes else "Yoq"
    message = (
        f"🛒 <b>Yangi Buyurtma! #{order.id}</b>\n\n"
        f"👤 <b>Mijoz:</b> {e(order.first_name)}\n"
        f"📞 <b>Telefon:</b> {e(order.phone)}\n"
        f"{location_line}\n"
        f"💬 <b>Izoh:</b> {notes_text}\n\n"
        f"🛍 <b>Mahsulotlar:</b>\n{items_list}\n\n"
        f"💰 <b>Jami summa:</b> {order.total_price:,.0f} so’m\n"
    )

    try:
        send_telegram_message(message)
        logger.info(f"Buyurtma #{order.id} uchun Telegram xabari yuborildi")
    except Exception as e:
        logger.error(f"Telegram xabarini yuborishda xato (buyurtma #{order.id}): {e}")


def checkout(request):
    cart = get_cart(request)
    all_categories = Category.objects.all()
    visible_categories = all_categories[:5]

    if not cart.cartitem_set.exists():
        messages.error(request, "Savat bo'sh! Iltimos, mahsulot qo'shing.")
        logger.warning(f"Bo'sh savat bilan checkoutga kirish (session: {cart.session_key})")
        return redirect('cart')

    if request.method == 'POST':
        delivery_method = request.POST.get('delivery_method', 'manual')
        lat_str = request.POST.get('latitude', '').strip()
        lng_str = request.POST.get('longitude', '').strip()

        # 'map' = xaritada tanlash, 'manual' = qo'lda kiritish
        if delivery_method in ('map', 'gps') and lat_str and lng_str:
            first_name = request.POST.get('first_name', '').strip()
            phone      = request.POST.get('phone', '').strip()
            notes      = request.POST.get('notes', '').strip()
            if not first_name or not phone:
                messages.error(request, "Iltimos, ism va telefon raqamni kiriting.")
                form = OrderForm()
            else:
                try:
                    lat = float(lat_str)
                    lng = float(lng_str)
                    maps_url = f'https://maps.google.com/?q={lat},{lng}'
                    order = Order(
                        first_name=first_name, phone=phone,
                        region='Xarita', city='Xarita', address=maps_url,
                        notes=notes, total_price=cart.get_total_price(),
                        latitude=lat, longitude=lng,
                    )
                    order.save()
                    cart_items = list(cart.cartitem_set.select_related('product').all())
                    create_order_items(order, cart_items)
                    send_order_notification(order, cart_items)
                    cart.cartitem_set.all().delete()
                    logger.info(f"Xarita buyurtma #{order.id} (session: {cart.session_key})")
                    return redirect('order_success')
                except (ValueError, Exception) as e:
                    logger.error(f"Xarita checkout xatosi: {e}")
                    messages.error(request, "Lokatsiya xatosi. Qaytadan urinib ko'ring.")
                    form = OrderForm()
        elif delivery_method in ('map', 'gps') and not lat_str:
            # Map rejimi tanlangan lekin pin qo'yilmagan
            messages.error(request, "Iltimos, xaritada joylashuvingizni belgilang.")
            form = OrderForm()
        else:
            # Qo'lda kiritish
            form = OrderForm(request.POST)
            if form.is_valid():
                order = form.save(commit=False)
                order.total_price = cart.get_total_price()
                order.save()
                cart_items = list(cart.cartitem_set.select_related('product').all())
                create_order_items(order, cart_items)
                send_order_notification(order, cart_items)
                cart.cartitem_set.all().delete()
                logger.info(f"Buyurtma #{order.id} (session: {cart.session_key})")
                return redirect('order_success')
            else:
                messages.error(request, "Iltimos, barcha maydonlarni to'ldiring.")
                logger.warning(f"Checkout formasi noto'g'ri (session: {cart.session_key})")
    else:
        form = OrderForm()

    return render(request, 'checkout.html', {
        'form': form,
        'cart': cart,
        'visible_categories': visible_categories
    })


def order_success(request):
    return render(request, 'order_success.html')


def get_cities(request):
    region = request.GET.get('region')
    if not region:
        return JsonResponse({'cities': [], 'message': 'Viloyat tanlanmadi'}, status=400)

    cities = {
        'samarqand': [
            {'id': 'samarqand_city', 'name': 'Samarqand shahri'},
            {'id': 'kattaqurghon_city', 'name': 'Kattaqurghon shahri'},
            {'id': 'kattaqurghon_tuman', 'name': 'Kattaqurghon tumani'},
            {'id': 'payshanba', 'name': 'Payshanba'},
            {'id': 'urgut', 'name': 'Urgut'},
            {'id': 'bulungur', 'name': 'Bulung‘ur'},
            {'id': 'jomboy', 'name': 'Jomboy'},
            {'id': 'ishtixon', 'name': 'Ishtixon'},
            {'id': 'narpay', 'name': 'Narpay'},
            {'id': 'nurobod', 'name': 'Nurobod'},
            {'id': 'oqdaryo', 'name': 'Oqdaryo'},
            {'id': 'pastdargom', 'name': 'Pastdarg‘om'},
            {'id': 'paxtachi', 'name': 'Paxtachi'},
            {'id': 'payariq', 'name': 'Payariq'},
            {'id': 'qoshrobod', 'name': 'Qoshrobod'},
            {'id': 'tayloq', 'name': 'Tayloq'},
            {'id': 'chelak', 'name': 'Chelak'},
            {'id': 'kushrobod', 'name': 'Kushrobod'},
        ],
        'navoiy': [
            {'id': 'navoiy_city', 'name': 'Navoiy shahri'},
            {'id': 'xatirchi', 'name': 'Xatirchi'},
            {'id': 'karmana', 'name': 'Karmana'},
            {'id': 'navbaxor', 'name': 'Navbaxor'},
            {'id': 'nurota', 'name': 'Nurota'},
            {'id': 'qiziltepa', 'name': 'Qiziltepa'},
            {'id': 'zarafshon', 'name': 'Zarafshon'},
        ],
    }
    cities_list = cities.get(region.lower(), [])
    if not cities_list:
        logger.warning(f"Noto'g'ri viloyat so'raldi: {region}")
        return JsonResponse({'cities': [], 'message': 'Viloyat topilmadi'}, status=404)

    return JsonResponse({'cities': cities_list})