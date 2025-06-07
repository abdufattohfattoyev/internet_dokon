from django.core.validators import RegexValidator
from django.db import models
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Added unique=True
    slug = models.SlugField(unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Ensure slug is unique by appending a counter if necessary
            base_slug = self.slug
            counter = 1
            while Category.objects.filter(slug=self.slug).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, unique=True)  # Added unique=True
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Ensure slug is unique by appending a counter if necessary
            base_slug = self.slug
            counter = 1
            while Product.objects.filter(slug=self.slug).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Cart(models.Model):
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_total_price(self):
        return sum(item.get_total_price() for item in self.cartitem_set.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def get_total_price(self):
        return self.product.price * self.quantity

class Order(models.Model):
    STATUS_CHOICES = [
        ('kutilmoqda', 'Kutilmoqda'),
        ('boglandi', "Bog'landi"),
        ('bajarildi', "Bajarildi"),
        ('bekor_qilindi', 'Bekor qilindi'),
    ]

    # Customer information
    first_name = models.CharField(max_length=100, verbose_name="Ism")
    phone = models.CharField(
        max_length=13,
        verbose_name="Telefon raqam",
        validators=[
            RegexValidator(
                regex=r'^\+998\d{9}$',
                message="Telefon raqami +998 bilan boshlanishi va 9 ta raqamdan iborat bo'lishi kerak"
            )
        ]
    )

    # Delivery information
    REGION_CHOICES = [
        ('samarqand', 'Samarqand'),
    ]
    region = models.CharField(max_length=50, choices=REGION_CHOICES, verbose_name="Viloyat", default='samarqand')
    city = models.CharField(max_length=50, verbose_name="Shahar")
    address = models.TextField(blank=True, null=True, verbose_name="Manzil")  # Made optional
    notes = models.TextField(blank=True, null=True, verbose_name="Qo'shimcha manzil izohi")
    admin_notes = models.TextField(blank=True, null=True, verbose_name="Admin izohlari")

    # Order information
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='kutilmoqda')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Buyurtma #{self.id} - {self.first_name}"

    def get_status_color(self):
        colors = {
            'kutilmoqda': 'warning',
            'boglandi': 'info',
            'bekor_qilindi': 'danger',
        }
        return colors.get(self.status, 'secondary')

    def calculate_total(self):
        return sum(item.get_total_price() for item in self.orderitem_set.all())

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='order_items')
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def get_total_price(self):
        return self.quantity * self.price

    def __str__(self):
        return f"{self.quantity} x {self.product.name} - {self.get_total_price()} UZS"