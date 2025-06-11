from django.urls import path
from django.views.generic import RedirectView
from . import admin_views

urlpatterns = [
    path('login/', admin_views.AdminLoginView.as_view(), name='admin_login'),
    path('logout/', admin_views.AdminLogoutView.as_view(), name='admin_logout'),
    path('', admin_views.admin_dashboard, name='admin_dashboard'),
    path('products/', admin_views.admin_products, name='admin_products'),
    path('categories/', admin_views.admin_categories, name='admin_categories'),
    path('orders/', admin_views.admin_orders, name='admin_orders'),
    path('orders/status/<str:status>/', admin_views.orders_by_status, name='orders_by_status'),
    path('statistics/', admin_views.admin_statistics, name='admin_statistics'),
    path('product/add/', admin_views.add_product, name='add_product'),
    path('product/edit/<int:pk>/', admin_views.edit_product, name='edit_product'),
    path('product/delete/<int:pk>/', admin_views.delete_product, name='delete_product'),
    path('category/add/', admin_views.add_category, name='add_category'),
    path('category/edit/<int:pk>/', admin_views.edit_category, name='edit_category'),
    path('category/delete/<int:pk>/', admin_views.delete_category, name='delete_category'),
    path('order/edit-status/<int:pk>/', admin_views.edit_order_status, name='edit_order'),
    path('orders/delete/<int:order_id>/', admin_views.delete_order, name='delete_order'),
    path('order/update-status/<int:pk>/', admin_views.update_order_status, name='update_order_status'),
    path('.well-known/appspecific/com.chrome.devtools.json', RedirectView.as_view(url='/static/empty.json')),
    path('admin/statistics/export/', admin_views.admin_statistics_export, name='admin_statistics_export'),
]