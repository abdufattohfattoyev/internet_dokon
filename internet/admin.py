# shop/admin.py
from django.contrib import admin
from .models import Category, Product, Cart, CartItem, Order, OrderItem

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(CartItem)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'phone', 'region', 'city', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'region', 'created_at')
    search_fields = ('first_name', 'phone', 'address')
    readonly_fields = ('created_at', 'total_price')
    fieldsets = (
        ('Mijoz ma\'lumotlari', {
            'fields': ('first_name', 'phone')
        }),
        ('Yetkazib berish ma\'lumotlari', {
            'fields': ('region', 'city', 'address', 'notes')
        }),
        ('Buyurtma ma\'lumotlari', {
            'fields': ('status', 'total_price', 'created_at', 'admin_notes')
        }),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')
    search_fields = ('order__first_name', 'product__name')