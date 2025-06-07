from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.core.paginator import Paginator
from django.db.models import Count, Sum, F
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .forms import OrderForm, SimpleOrderForm
from .models import Product, Category, Order, OrderItem, Cart, CartItem
from datetime import datetime
import pytz

# Admin Login View
class AdminLoginView(LoginView):
    template_name = 'admin_panel/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return '/admin-panel/'

# Admin Logout View
class AdminLogoutView(LogoutView):
    next_page = '/admin-panel/login/'

# Admin Dashboard
@login_required
def admin_dashboard(request):
    orders_count = Order.objects.count()
    products_count = Product.objects.count()
    categories_count = Category.objects.count()
    return render(request, 'admin_panel/dashboard.html', {
        'orders_count': orders_count,
        'products_count': products_count,
        'categories_count': categories_count,
    })

# Admin Statistics
@login_required
def admin_statistics(request):
    # Asia/Tashkent timezone
    uzb_tz = pytz.timezone('Asia/Tashkent')
    now = timezone.now().astimezone(uzb_tz)  # Convert to Tashkent time
    print(f"Current Tashkent time: {now}")

    # Time ranges
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    yesterday_start = today_start - timedelta(days=1)
    yesterday_end = today_start

    print(f"Today range: {today_start} - {today_end}")
    print(f"Yesterday range: {yesterday_start} - {yesterday_end}")

    date_filter = request.GET.get('date_filter', 'today')
    category_filter = request.GET.get('category', 'all')

    # Today's orders
    today_orders = Order.objects.filter(created_at__range=[today_start, today_end])
    today_order_count = today_orders.count()

    # Today's status distribution
    today_status_distribution = today_orders.values('status').annotate(count=Count('id')).order_by('status')
    status_counts = {status: 0 for status, _ in Order.STATUS_CHOICES}
    for item in today_status_distribution:
        status_counts[item['status']] = item['count']
    today_status_distribution_list = [
        {'status': dict(Order.STATUS_CHOICES).get(status, status), 'count': count}
        for status, count in status_counts.items()
    ]

    # Today's top products
    today_top_products = OrderItem.objects.filter(
        order__created_at__range=[today_start, today_end]
    ).values(
        'product__name'
    ).annotate(
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity')[:5]

    # Yesterday's orders
    yesterday_orders = Order.objects.filter(created_at__range=[yesterday_start, yesterday_end])
    yesterday_order_count = yesterday_orders.count()

    # Yesterday status distribution
    yesterday_status_distribution = yesterday_orders.values('status').annotate(count=Count('id')).order_by('status')
    yesterday_status_counts = {status: 0 for status, _ in Order.STATUS_CHOICES}
    for item in yesterday_status_distribution:
        yesterday_status_counts[item['status']] = item['count']
    yesterday_status_distribution_list = [
        {'status': dict(Order.STATUS_CHOICES).get(status, status), 'count': count}
        for status, count in yesterday_status_counts.items()
    ]

    # Yesterday top-selling products
    yesterday_top_products = OrderItem.objects.filter(
        order__created_at__range=[yesterday_start, yesterday_end]
    ).values(
        'product__name'
    ).annotate(
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity')[:5]

    # Overall statistics
    orders_query = Order.objects.all()
    total_sales = orders_query.aggregate(total=Coalesce(Sum('total_price'), Decimal('0')))['total']
    total_orders = orders_query.count()

    # Date filter for general stats
    last_7_days = now - timedelta(days=7)
    last_30_days = now - timedelta(days=30)

    if date_filter == 'today':
        orders_query = orders_query.filter(created_at__range=[today_start, today_end])
    elif date_filter == 'last_7_days':
        orders_query = orders_query.filter(created_at__gte=last_7_days)
    elif date_filter == 'last_30_days':
        orders_query = orders_query.filter(created_at__gte=last_30_days)

    # Status percentages
    period_orders = orders_query.count()
    status_distribution = orders_query.values('status').annotate(count=Count('id')).order_by('status')
    status_percentages = []
    for item in status_distribution:
        percentage = (item['count'] / period_orders * 100) if period_orders > 0 else 0
        status_percentages.append({
            'status': dict(Order.STATUS_CHOICES).get(item['status'], item['status']),
            'count': item['count'],
            'percentage': round(percentage, 2)
        })

    # Product sales
    products_sales = OrderItem.objects.filter(
        order__status='bajarildi'
    ).values(
        'product__name',
        'product__category__name'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('price'))
    ).order_by('-total_quantity')

    if date_filter == 'today':
        products_sales = products_sales.filter(order__created_at__range=[today_start, today_end])
    elif date_filter == 'last_7_days':
        products_sales = products_sales.filter(order__created_at__gte=last_7_days)
    elif date_filter == 'last_30_days':
        products_sales = products_sales.filter(order__created_at__gte=last_30_days)

    if category_filter != 'all':
        products_sales = products_sales.filter(product__category__slug=category_filter)

    # Daily sales (last 7 days)
    daily_sales = []
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        day_sales = Order.objects.filter(
            status='bajarildi',
            created_at__range=[day_start, day_end]
        ).aggregate(total=Coalesce(Sum('total_price'), Decimal('0')))['total']
        daily_sales.append({
            'day': day.strftime('%a, %d %b'),
            'sales': float(day_sales),
        })

    # Monthly sales
    monthly_sales = Order.objects.filter(
        status='bajarildi',
        created_at__gte=last_30_days
    ).aggregate(total=Coalesce(Sum('total_price'), Decimal('0')))['total']

    context = {
        'today_order_count': today_order_count,
        'today_status_distribution': today_status_distribution_list,
        'today_top_products': today_top_products,
        'yesterday_order_count': yesterday_order_count,
        'yesterday_status_distribution': yesterday_status_distribution_list,
        'yesterday_top_products': yesterday_top_products,
        'total_sales': float(total_sales),
        'total_orders': total_orders,
        'status_percentages': status_percentages,
        'products_sales': products_sales[:5],
        'daily_sales': daily_sales,
        'monthly_sales': float(monthly_sales),
        'categories': Category.objects.all(),
        'date_filter': date_filter,
        'category_filter': category_filter,
        'last_updated': now,
    }
    return render(request, 'admin_panel/statistics.html', context)

# Admin Products
@login_required
def admin_products(request):
    products = Product.objects.all()
    return render(request, 'admin_panel/products.html', {'products': products})

# Admin Categories
@login_required
def admin_categories(request):
    categories = Category.objects.all()
    return render(request, 'admin_panel/categories.html', {'categories': categories})

# Admin Orders
@login_required
def admin_orders(request):
    status = request.GET.get('status', 'all')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    min_amount = request.GET.get('min_amount')
    max_amount = request.GET.get('max_amount')

    orders = Order.objects.all().order_by('-created_at')
    if status != 'all':
        orders = orders.filter(status=status)
    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        orders = orders.filter(created_at__date__range=[start_date, end_date])
    if min_amount:
        orders = orders.filter(total_price__gte=min_amount)
    if max_amount:
        orders = orders.filter(total_price__lte=max_amount)

    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    orders_page = paginator.get_page(page_number)

    return render(request, 'admin_panel/orders.html', {
        'orders': orders_page,
        'status': status,
        'start_date': start_date,
        'end_date': end_date,
    })

# Add Product
@login_required
def add_product(request):
    if request.method == 'POST':
        name = request.POST['name']
        category_id = request.POST['category']
        description = request.POST['description']
        price = request.POST['price']
        image = request.FILES.get('image')
        category = Category.objects.get(id=category_id)

        # Check if product with the same name already exists
        if Product.objects.filter(name=name).exists():
            messages.error(request, f"Mahsulot nomi '{name}' allaqachon mavjud! Iltimos, boshqa nom tanlang.")
            return redirect('add_product')

        # Create product if name is unique
        Product.objects.create(
            category=category, name=name, description=description, price=price, image=image
        )
        messages.success(request, "Mahsulot muvaffaqiyatli qo'shildi!")
        return redirect('admin_products')
    categories = Category.objects.all()
    return render(request, 'admin_panel/products.html', {'categories': categories})

# Edit Product
@login_required
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.name = request.POST['name']
        product.category_id = request.POST['category']
        product.description = request.POST['description']
        product.price = request.POST['price']
        if request.FILES.get('image'):
            product.image = request.FILES['image']
        product.save()
        messages.success(request, "Mahsulot muvaffaqiyatli yangilandi!")
        return redirect('admin_products')
    categories = Category.objects.all()
    return render(request, 'admin_panel/products.html', {'product': product, 'categories': categories})

# Delete Product
@login_required
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, "Mahsulot muvaffaqiyatli o'chirildi!")
        return redirect('admin_products')
    return render(request, 'admin_panel/products.html', {'product': product})

# Add Category
@login_required
def add_category(request):
    if request.method == 'POST':
        name = request.POST['name']
        # Check if category with the same name already exists
        if Category.objects.filter(name=name).exists():
            messages.error(request, f"Kategoriya nomi '{name}' allaqachon mavjud! Iltimos, boshqa nom tanlang.")
            return redirect('add_category')
        # Generate a unique slug
        base_slug = slugify(name)
        slug = base_slug
        counter = 1
        while Category.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        # Create category with unique name and slug
        Category.objects.create(name=name, slug=slug)
        messages.success(request, "Kategoriya muvaffaqiyatli qo'shildi!")
        return redirect('admin_categories')
    return render(request, 'admin_panel/categories.html')

# Edit Category
@login_required
def edit_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.name = request.POST['name']
        category.save()
        messages.success(request, "Kategoriya muvaffaqiyatli yangilandi!")
        return redirect('admin_categories')
    return render(request, 'admin_panel/categories.html', {'category': category})

# Delete Category
@login_required
def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, "Kategoriya muvaffaqiyatli o'chirildi!")
        return redirect('admin_categories')
    return render(request, 'admin_panel/categories.html', {'category': category})

# Edit Order Status
@login_required
def edit_order_status(request, pk):
    order = get_object_or_404(Order, id=pk)
    if request.method == 'POST':
        form = SimpleOrderForm(request.POST, instance=order)
        if form.is_valid():
            order = form.save(commit=False)
            order.admin_notes = request.POST.get('admin_notes', order.admin_notes or '')
            order.save()
            messages.success(request, f"Buyurtma #{order.id} holati yangilandi!")
            return redirect('admin_orders')
    else:
        form = SimpleOrderForm(instance=order)
    return render(request, 'admin_panel/edit_order.html', {'form': form, 'order': order})

# Delete Order
@login_required
def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        order_id = order.id
        order.delete()
        messages.success(request, f"Buyurtma #{order_id} muvaffaqiyatli o'chirildi!")
        return redirect('admin_orders')
    return redirect('admin_orders')

# Update Order Status (AJAX)
@csrf_exempt  # Remove in production, use CSRF token
@require_POST
@login_required
def update_order_status(request, pk):
    order = get_object_or_404(Order, id=pk)
    new_status = request.POST.get('status')
    if new_status in dict(Order.STATUS_CHOICES).keys():
        order.status = new_status
        order.save()
        return JsonResponse({
            'success': True,
            'status_display': order.get_status_display()
        })
    return JsonResponse({'success': False}, status=400)