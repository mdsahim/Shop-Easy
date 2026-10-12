import uuid
from decimal import Decimal
from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    icon = models.CharField(max_length=50, default='bi-tag', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product_list_by_category', args=[self.slug])

    def get_image_url(self):
        if self.image:
            return self.image.url
        if self.image_url:
            return self.image_url
        return 'https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?auto=format&fit=crop&w=600&q=80'


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.5)
    reviews_count = models.PositiveIntegerField(default=12)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.slug])

    @property
    def is_in_stock(self):
        return self.stock > 0

    @property
    def discount_percentage(self):
        if self.old_price and self.old_price > self.price and self.old_price > 0:
            discount = ((self.old_price - self.price) / self.old_price) * 100
            return int(round(discount))
        return 0

    def get_image_url(self):
        if self.image:
            return self.image.url
        if self.image_url:
            return self.image_url
        return 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=600&q=80'


class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]

    order_number = models.CharField(max_length=32, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, help_text="PIN / Zip Code")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), blank=True)
    shipping_cost = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    payment_method = models.CharField(max_length=50, default='Cash on Delivery (COD)')
    payment_status = models.CharField(max_length=20, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.order_number} - {self.full_name}"

    @classmethod
    def generate_order_number(cls):
        date_str = timezone.now().strftime('%Y%m%d')
        random_code = uuid.uuid4().hex[:6].upper()
        return f"SE-{date_str}-{random_code}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
            # Ensure uniqueness
            while Order.objects.filter(order_number=self.order_number).exists():
                self.order_number = self.generate_order_number()
        if self.total_amount is None:
            self.total_amount = Decimal('0.00')
        super().save(*args, **kwargs)

    def update_total(self):
        """Recalculate and update total_amount based on associated items and shipping."""
        items_total = sum(item.get_cost() or Decimal('0.00') for item in self.items.all())
        self.total_amount = items_total + (self.shipping_cost or Decimal('0.00'))
        self.save(update_fields=['total_amount'])

    @property
    def items_count(self):
        return sum(item.quantity for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name='order_items')
    product_name = models.CharField(max_length=200, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity}x {self.product_name or (self.product.name if self.product else 'Item')} in #{self.order.order_number}"

    def clean(self):
        super().clean()
        # Automatically copy price and product_name from product if not specified
        if self.product:
            if self.price is None:
                self.price = self.product.price
            if not self.product_name:
                self.product_name = self.product.name

        # Validate required price: do not silently default to zero for genuine customer orders
        if self.price is None:
            raise ValidationError({
                'price': 'Price is required. Please enter a valid price or select a product to auto-populate.'
            })
        if self.price < 0:
            raise ValidationError({'price': 'Price cannot be negative.'})

        if self.quantity is None or self.quantity < 1:
            raise ValidationError({'quantity': 'Quantity must be at least 1.'})

    def save(self, *args, **kwargs):
        if self.product:
            if self.price is None:
                self.price = self.product.price
            if not self.product_name:
                self.product_name = self.product.name

        if self.price is None:
            raise ValidationError('Price is required. Please specify a price or select a product.')
        if self.price < 0:
            raise ValidationError('Price cannot be negative.')
        if self.quantity is None or self.quantity < 1:
            raise ValidationError('Quantity must be at least 1.')

        super().save(*args, **kwargs)

    def get_cost(self):
        """Safely compute line cost without raising TypeError when price or quantity is None."""
        if self.price is not None and self.quantity is not None:
            return self.price * self.quantity
        return None

    @property
    def item_total(self):
        """Calculated item total property for models, forms, and admin displays."""
        cost = self.get_cost()
        return cost if cost is not None else Decimal('0.00')
