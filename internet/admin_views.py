import csv
import logging

from _decimal import InvalidOperation
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.core.paginator import Paginator
from django.db.models import Count, Sum, F, Q
from django.db.models.functions import Coalesce
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
from .forms import OrderForm, SimpleOrderForm
from .models import Product, Category, Order, OrderItem, Cart, CartItem, ProductImage
import pytz
logger = logging.getLogger(__name__)

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
    uzb_tz = pytz.timezone('Asia/Tashkent')
    now = timezone.now().astimezone(uzb_tz)

    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    date_filter = request.GET.get('date_filter', 'today')
    category_filter = request.GET.get('category', 'all')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Today's orders
    today_orders = Order.objects.filter(created_at__range=[today_start, today_end])
    today_order_count = today_orders.count()
    today_completed_count = today_orders.filter(status='bajarildi').count()
    today_revenue = today_orders.filter(status='bajarildi').aggregate(
        total=Coalesce(Sum('total_price'), Decimal('0'))
    )['total']

    today_status_distribution = today_orders.values('status').annotate(count=Count('id'))
    status_counts = {status: 0 for status, _ in Order.STATUS_CHOICES}
    for item in today_status_distribution:
        status_counts[item['status']] = item['count']
    today_status_distribution_list = [
        {'status': dict(Order.STATUS_CHOICES).get(status, status), 'count': count}
        for status, count in status_counts.items()
    ]

    # Period orders
    period_orders = Order.objects.all()
    if date_filter == 'today':
        period_orders = period_orders.filter(created_at__range=[today_start, today_end])
    elif date_filter == 'last_7_days':
        period_orders = period_orders.filter(created_at__gte=now - timedelta(days=7))
    elif date_filter == 'last_30_days':
        period_orders = period_orders.filter(created_at__gte=now - timedelta(days=30))
    elif date_filter == 'custom' and start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=uzb_tz)
            end_date = datetime.strptime(end_date, '%Y-%m-%d').replace(tzinfo=uzb_tz, hour=23, minute=59, second=59)
            period_orders = period_orders.filter(created_at__range=[start_date, end_date])
        except ValueError:
            pass

    period_total_orders = period_orders.count()
    period_completed_orders = period_orders.filter(status='bajarildi').count()
    period_total_sales = period_orders.filter(status='bajarildi').aggregate(
        total=Coalesce(Sum('total_price'), Decimal('0'))
    )['total']

    # Status distribution for the period
    status_distribution = period_orders.values('status').annotate(count=Count('id'))
    status_percentages = [
        {
            'status': dict(Order.STATUS_CHOICES).get(item['status'], item['status']),
            'count': item['count'],
            'percentage': round((item['count'] / period_total_orders * 100) if period_total_orders > 0 else 0, 2)
        }
        for item in status_distribution
    ]

    # Products sold in the period
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
        products_sales = products_sales.filter(order__created_at__gte=now - timedelta(days=7))
    elif date_filter == 'last_30_days':
        products_sales = products_sales.filter(order__created_at__gte=now - timedelta(days=30))
    elif date_filter == 'custom' and start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=uzb_tz)
            end_date = datetime.strptime(end_date, '%Y-%m-%d').replace(tzinfo=uzb_tz, hour=23, minute=59, second=59)
            products_sales = products_sales.filter(order__created_at__range=[start_date, end_date])
        except ValueError:
            pass

    if category_filter != 'all':
        products_sales = products_sales.filter(product__category__slug=category_filter)

    # Period sales with daily breakdown
    period_sales = []
    if date_filter == 'custom' and start_date and end_date:
        try:
            current_date = datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=uzb_tz)
            end_date = datetime.strptime(end_date, '%Y-%m-%d').replace(tzinfo=uzb_tz, hour=23, minute=59, second=59)
            while current_date <= end_date:
                day_end = current_date.replace(hour=23, minute=59, second=59)
                day_orders = Order.objects.filter(created_at__range=[current_date, day_end])
                day_sales = day_orders.aggregate(
                    total=Coalesce(Sum('total_price', filter=Q(status='bajarildi')), Decimal('0')),
                    count=Count('id'),
                    completed_count=Count('id', filter=Q(status='bajarildi'))
                )
                period_sales.append({
                    'date': current_date,
                    'total': float(day_sales['total']),
                    'count': day_sales['count'],
                    'completed_count': day_sales['completed_count']
                })
                current_date += timedelta(days=1)
        except ValueError:
            pass
    else:
        for i in range(6, -1, -1):
            day = today_start - timedelta(days=i)
            day_end = day + timedelta(days=1)
            day_orders = Order.objects.filter(created_at__range=[day, day_end])
            day_sales = day_orders.aggregate(
                total=Coalesce(Sum('total_price', filter=Q(status='bajarildi')), Decimal('0')),
                count=Count('id'),
                completed_count=Count('id', filter=Q(status='bajarildi'))
            )
            period_sales.append({
                'date': day,
                'total': float(day_sales['total']),
                'count': day_sales['count'],
                'completed_count': day_sales['completed_count']
            })

    context = {
        'today_order_count': today_order_count,
        'today_completed_count': today_completed_count,
        'today_revenue': float(today_revenue),
        'today_status_distribution': today_status_distribution_list,
        'period_total_orders': period_total_orders,
        'period_completed_orders': period_completed_orders,
        'period_total_sales': float(period_total_sales),
        'status_percentages': status_percentages,
        'products_sales': products_sales,
        'period_sales': period_sales,
        'categories': Category.objects.all(),
        'date_filter': date_filter,
        'category_filter': category_filter,
        'start_date': start_date,
        'end_date': end_date,
        'last_updated': now,
    }
    return render(request, 'admin_panel/statistics.html', context)


@login_required
def admin_statistics_export(request):
    date_filter = request.GET.get('date_filter', 'today')
    category_filter = request.GET.get('category', 'all')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    uzb_tz = pytz.timezone('Asia/Tashkent')

    orders_query = Order.objects.filter(status='bajarildi')

    if date_filter == 'today':
        today_start = timezone.now().astimezone(uzb_tz).replace(hour=0, minute=0, second=0, microsecond=0)
        orders_query = orders_query.filter(created_at__range=[today_start, today_start + timedelta(days=1)])
    elif date_filter == 'last_7_days':
        orders_query = orders_query.filter(created_at__gte=timezone.now().astimezone(uzb_tz) - timedelta(days=7))
    elif date_filter == 'last_30_days':
        orders_query = orders_query.filter(created_at__gte=timezone.now().astimezone(uzb_tz) - timedelta(days=30))
    elif date_filter == 'custom' and start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=uzb_tz)
            end_date = datetime.strptime(end_date, '%Y-%m-%d').replace(tzinfo=uzb_tz, hour=23, minute=59, second=59)
            orders_query = orders_query.filter(created_at__range=[start_date, end_date])
        except ValueError:
            pass

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Sana', 'Buyurtma ID', 'Mijoz', 'Telefon', 'Manzil', 'Jami summa', 'Mahsulotlar'])

    for order in orders_query:
        items = OrderItem.objects.filter(order=order)
        items_str = "; ".join([f"{item.product.name} (x{item.quantity})" for item in items])
        writer.writerow([
            order.created_at.astimezone(uzb_tz).strftime('%Y-%m-%d %H:%M:%S'),
            order.id,
            order.first_name,
            order.phone,
            f"{order.region}, {order.city}",
            float(order.total_price),
            items_str
        ])

    return response


# Admin Products
@login_required
def admin_products(request):
    products = Product.objects.select_related('category').all()
    return render(request, 'admin_panel/products.html', {'products': products})


# Admin Categories
def admin_categories(request):
    categories = Category.objects.all()
    total_products = sum(category.product_set.count() for category in categories)
    context = {
        'categories': categories,
        'total_products': total_products,
    }
    return render(request, 'admin_panel/categories.html', context)


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

    # Status counts for all orders
    status_counts = Order.objects.values('status').annotate(count=Count('id')).order_by('status')
    status_counts_list = [
        {
            'status': item['status'],
            'status_display': dict(Order.STATUS_CHOICES).get(item['status'], item['status']),
            'count': item['count']
        }
        for item in status_counts
    ]

    return render(request, 'admin_panel/orders.html', {
        'orders': orders_page,
        'status': status,
        'start_date': start_date,
        'end_date': end_date,
        'status_counts': status_counts_list,
    })


# Admin Orders by Status
@login_required
def orders_by_status(request, status):
    orders = Order.objects.filter(status=status).order_by('-created_at')
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    orders_page = paginator.get_page(page_number)

    status_display = dict(Order.STATUS_CHOICES).get(status, status)
    status_counts = Order.objects.values('status').annotate(count=Count('id')).order_by('status')
    status_counts_list = [
        {
            'status': item['status'],
            'status_display': dict(Order.STATUS_CHOICES).get(item['status'], item['status']),
            'count': item['count']
        }
        for item in status_counts
    ]

    return render(request, 'admin_panel/orders_by_status.html', {
        'orders': orders_page,
        'status': status,
        'status_display': status_display,
        'status_counts': status_counts_list,
    })


# Add Product

@login_required
def add_product(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            category_id = request.POST.get('category')
            description = request.POST.get('description')
            price = request.POST.get('price')
            images = request.FILES.getlist('images')

            # Validatsiya
            if not all([name, category_id, description, price]):
                messages.error(request, "Barcha majburiy maydonlarni to'ldiring!")
                logger.warning("Mahsulot qo'shishda maydonlar to'liq emas")
                return redirect('add_product')

            # Narxni tozalash va validatsiya qilish
            try:
                # Vergul va boshqa belgilarni olib tashlash
                clean_price = ''.join(filter(str.isdigit, str(price)))
                if not clean_price:
                    messages.error(request, "Narx kiritilmagan!")
                    logger.warning("Narx kiritilmagan")
                    return redirect('add_product')

                price = Decimal(clean_price)
                if price <= 0:
                    messages.error(request, "Narx musbat son bo'lishi kerak!")
                    logger.warning(f"Noto'g'ri narx qiymati: {price}")
                    return redirect('add_product')
            except (InvalidOperation, ValueError) as e:
                messages.error(request, "Narx to'g'ri formatda kiritilmagan!")
                logger.warning(f"Noto'g'ri narx formati: {price}, xato: {e}")
                return redirect('add_product')

            # Kategoriyani olish
            try:
                category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                messages.error(request, "Tanlangan kategoriya topilmadi!")
                logger.error(f"Kategoriya topilmadi: ID {category_id}")
                return redirect('add_product')

            # Mahsulot nomini tekshirish
            if Product.objects.filter(name=name).exists():
                messages.error(request, f"Mahsulot nomi '{name}' allaqachon mavjud! Iltimos, boshqa nom tanlang.")
                logger.warning(f"Mahsulot nomi '{name}' allaqachon mavjud")
                return redirect('add_product')

            # Mahsulot yaratish
            product = Product.objects.create(
                category=category,
                name=name,
                description=description,
                price=price
            )

            # Rasmlarni qo'shish
            if not images:
                product.delete()
                messages.error(request, "Kamida bitta rasm qo'shish majburiy!")
                logger.warning(f"Mahsulot #{product.id} uchun rasm qo'shilmadi, mahsulot o'chirildi")
                return redirect('add_product')

            for index, image in enumerate(images):
                ProductImage.objects.create(
                    product=product,
                    image=image,
                    is_primary=(index == 0)
                )

            messages.success(request, "Mahsulot muvaffaqiyatli qo'shildi!")
            logger.info(f"Mahsulot #{product.id} muvaffaqiyatli qo'shildi")
            return redirect('admin_products')

        except Exception as e:
            logger.error(f"Mahsulot qo'shishda xato: {str(e)}", exc_info=True)
            messages.error(request, "Mahsulot qo'shishda xato yuz berdi. Iltimos, qayta urinib ko'ring.")
            return redirect('add_product')

    categories = Category.objects.all()
    return render(request, 'admin_panel/add_product.html', {'categories': categories})


@login_required
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            category_id = request.POST.get('category', '').strip()
            description = request.POST.get('description', '').strip()
            price = request.POST.get('price', '').strip()
            images = request.FILES.getlist('images')
            delete_images = request.POST.getlist('delete_images')
            primary_image_id = request.POST.get('primary_image')

            # Validatsiya: Bo'sh maydonlarni aniq tekshirish
            errors = []
            if not name:
                errors.append("Mahsulot nomi kiritilmagan!")
            if not category_id:
                errors.append("Kategoriya tanlanmagan!")
            if not description:
                errors.append("Tavsif kiritilmagan!")
            if not price:
                errors.append("Narx kiritilmagan!")

            if errors:
                for error in errors:
                    messages.error(request, error)
                logger.warning(f"Mahsulot #{pk} tahrirlashda maydonlar to'liq emas: {', '.join(errors)}")
                return redirect('edit_product', pk=pk)

            # Narxni tozalash va validatsiya qilish
            try:
                clean_price = ''.join(filter(str.isdigit, str(price)))
                if not clean_price:
                    messages.error(request, "Narx kiritilmagan yoki noto'g'ri formatda!")
                    logger.warning(f"Mahsulot #{pk} tahrirlashda narx kiritilmagan yoki noto'g'ri formatda: {price}")
                    return redirect('edit_product', pk=pk)

                price = Decimal(clean_price)
                if price <= 0:
                    messages.error(request, "Narx musbat son bo'lishi kerak!")
                    logger.warning(f"Mahsulot #{pk} tahrirlashda noto'g'ri narx qiymati: {price}")
                    return redirect('edit_product', pk=pk)
            except (InvalidOperation, ValueError) as e:
                messages.error(request, "Narx to'g'ri formatda kiritilmagan (faqat raqamlar va vergul ishlatiladi)!")
                logger.warning(f"Mahsulot #{pk} tahrirlashda noto'g'ri narx formati: {price}, xato: {e}")
                return redirect('edit_product', pk=pk)

            # Kategoriyani olish
            try:
                category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                messages.error(request, "Tanlangan kategoriya topilmadi!")
                logger.error(f"Mahsulot #{pk} tahrirlashda kategoriya topilmadi: ID {category_id}")
                return redirect('edit_product', pk=pk)

            # Mahsulot nomini tekshirish
            if Product.objects.filter(name=name).exclude(pk=pk).exists():
                messages.error(request, f"Mahsulot nomi '{name}' allaqachon mavjud! Iltimos, boshqa nom tanlang.")
                logger.warning(f"Mahsulot #{pk} tahrirlashda mahsulot nomi '{name}' allaqachon mavjud")
                return redirect('edit_product', pk=pk)

            # Mahsulotni yangilash
            product.name = name
            product.category = category
            product.description = description
            product.price = price
            product.save()

            # Rasmlarni o'chirish
            if delete_images:
                deleted_count = ProductImage.objects.filter(id__in=delete_images, product=product).delete()[0]
                logger.info(f"Mahsulot #{pk} uchun {deleted_count} ta rasm o'chirildi")

            # Yangi rasmlar qo'shish
            if images:
                for index, image in enumerate(images):
                    ProductImage.objects.create(
                        product=product,
                        image=image,
                        is_primary=(index == 0 and not product.images.filter(is_primary=True).exists())
                    )
                logger.info(f"Mahsulot #{pk} uchun {len(images)} ta yangi rasm qo'shildi")

            # Asosiy rasmni o'zgartirish
            if primary_image_id:
                ProductImage.objects.filter(product=product).update(is_primary=False)
                try:
                    ProductImage.objects.filter(id=primary_image_id, product=product).update(is_primary=True)
                    logger.info(f"Mahsulot #{pk} uchun asosiy rasm ID {primary_image_id} ga o'zgartirildi")
                except ProductImage.DoesNotExist:
                    logger.warning(f"Mahsulot #{pk} uchun asosiy rasm ID {primary_image_id} topilmadi")

            # Kamida bitta rasm borligini tekshirish
            if not product.images.exists():
                messages.error(request, "Kamida bitta rasm bo'lishi kerak!")
                logger.warning(f"Mahsulot #{pk} tahrirlashda rasm mavjud emas")
                return redirect('edit_product', pk=pk)

            messages.success(request, "Mahsulot muvaffaqiyatli yangilandi!")
            logger.info(f"Mahsulot #{pk} muvaffaqiyatli yangilandi")
            return redirect('admin_products')

        except Exception as e:
            logger.error(f"Mahsulot #{pk} tahrirlashda xato: {str(e)}", exc_info=True)
            messages.error(request, "Mahsulot tahrirlashda xato yuz berdi. Iltimos, qayta urinib ko'ring.")
            return redirect('edit_product', pk=pk)

    categories = Category.objects.all()
    return render(request, 'admin_panel/edit_product.html', {
        'product': product,
        'categories': categories
    })

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
        if Category.objects.filter(name=name).exists():
            messages.error(request, f"Kategoriya nomi '{name}' allaqachon mavjud! Iltimos, boshqa nom tanlang.")
            return redirect('add_category')
        base_slug = slugify(name)
        slug = base_slug
        counter = 1
        while Category.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
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
@csrf_exempt
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