from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import OrderForm
from .models import Category, Product, Cart, CartItem, Order, OrderItem

def get_cart(request):
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    cart, created = Cart.objects.get_or_create(session_key=session_key)
    return cart


def home(request):
    categories = Category.objects.all()
    products = Product.objects.all()

    # Qidiruv funksiyasi
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    # Kategoriya filtri
    category_slug = request.GET.get('category')
    if category_slug:
        products = products.filter(category__slug=category_slug)

    # Pagination (har sahifada 10 ta mahsulot)
    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    products_page = paginator.get_page(page_number)

    return render(request, 'index.html', {
        'categories': categories,
        'products': products_page,
        'cart': get_cart(request)
    })




def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, 'product_detail.html', {'product': product})

def cart_detail(request):
    cart = get_cart(request)
    return render(request, 'cart.html', {'cart': cart})


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category)
    query = request.GET.get('q')
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    products_page = paginator.get_page(page_number)
    return render(request, 'category_detail.html', {
        'category': category,
        'categories': Category.objects.all(),
        'products': products_page,
        'cart': get_cart(request)
    })

@require_POST
def add_to_cart(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        cart = get_cart(request)
        quantity = int(request.POST.get('quantity', 1))
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()
        cart_count = cart.cartitem_set.count()
        return JsonResponse({'cart_count': cart_count, 'message': 'Savatga qo‘shildi!'})
    return redirect('home')


@require_POST
def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart=get_cart(request))
    quantity = int(request.POST.get('quantity', 1))

    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
    else:
        cart_item.delete()

    return JsonResponse({
        'success': True,
        'item_total': cart_item.get_total_price(),
        'cart_total': cart_item.cart.get_total_price(),
        'cart_count': cart_item.cart.cartitem_set.count()
    })


@require_POST
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart=get_cart(request))
    cart_item.delete()

    return JsonResponse({
        'success': True,
        'cart_total': cart_item.cart.get_total_price(),
        'cart_count': cart_item.cart.cartitem_set.count()
    })


def checkout(request):
    cart = Cart.objects.get(session_key=request.session.session_key)

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.total_price = cart.get_total_price()
            order.save()

            # Create order items
            for item in cart.cartitem_set.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )

            # Clear the cart
            cart.cartitem_set.all().delete()
            return redirect('order_success')
    else:
        form = OrderForm()

    return render(request, 'checkout.html', {
        'form': form,
        'cart': cart
    })

def order_success(request):
    return render(request, 'order_success.html')

def get_cities(request):
    region = request.GET.get('region')
    cities = {
        'samarqand': [
            {'id': 'samarqand_city', 'name': 'Samarqand shahri'},
            {'id': 'kattaqurghon', 'name': 'Kattaqurghon'},
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
            {'id': 'toyloq', 'name': 'Toyloq'},
        ],
    }
    return JsonResponse({
        'cities': cities.get(region, [])
    })