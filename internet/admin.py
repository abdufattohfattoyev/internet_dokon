from django.contrib import admin
from .models import Category, Product, ProductImage, Cart, CartItem, Order, OrderItem

# Inline model for ProductImage
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1  # Bo'sh formada nechta rasm qo'shish mumkinligi
    fields = ('image', 'is_primary')
    readonly_fields = ('image',)  # Rasmni faqat ko'rish uchun, tahrirlash uchun view ishlatiladi
    can_delete = True  # Rasmlarni o'chirish imkoniyati

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('category', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]  # ProductImage modelini inline sifatida qo'shish

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'image', 'is_primary')
    list_filter = ('product', 'is_primary')
    search_fields = ('product__name',)

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'created_at')
    search_fields = ('session_key',)

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity')
    search_fields = ('product__name',)

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