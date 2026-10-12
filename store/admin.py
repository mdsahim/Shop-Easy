from django.contrib import admin
from store.models import Category, Product, Order, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'product_count', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products Count'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'old_price', 'stock', 'rating', 'is_featured', 'is_active')
    list_filter = ('category', 'is_featured', 'is_active', 'created_at')
    list_editable = ('price', 'stock', 'is_featured', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_per_page = 20


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = ('product', 'product_name', 'price', 'quantity', 'item_total')
    readonly_fields = ('item_total',)

    @admin.display(description='Total')
    def item_total(self, obj):
        if obj is None or obj.price is None or obj.quantity is None:
            return '—'
        cost = obj.get_cost()
        if cost is None:
            return '—'
        return f"${cost:.2f}"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'full_name', 'email', 'phone', 'total_amount', 'status', 'payment_status', 'created_at')
    list_filter = ('status', 'payment_status', 'created_at')
    search_fields = ('order_number', 'full_name', 'email', 'phone', 'city', 'postal_code')
    list_editable = ('status', 'payment_status')
    inlines = [OrderItemInline]
    readonly_fields = ('order_number', 'created_at', 'updated_at', 'total_amount')
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'total_amount', 'shipping_cost', 'created_at', 'updated_at')
        }),
        ('Customer Delivery Details', {
            'fields': ('full_name', 'email', 'phone', 'address', 'city', 'state', 'postal_code')
        }),
        ('Payment Details', {
            'fields': ('payment_method', 'payment_status')
        }),
    )

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        order = form.instance
        order.update_total()


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'product_name', 'price', 'quantity', 'item_total')
    list_filter = ('order__status', 'order__created_at')
    search_fields = ('product_name', 'order__order_number')
    readonly_fields = ('item_total',)

    @admin.display(description='Total')
    def item_total(self, obj):
        if obj is None or obj.price is None or obj.quantity is None:
            return '—'
        cost = obj.get_cost()
        if cost is None:
            return '—'
        return f"${cost:.2f}"
