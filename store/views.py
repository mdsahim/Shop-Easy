import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse, Http404

from store.models import Category, Product, Order, OrderItem
from store.cart import Cart
from store.forms import CheckoutForm, UserRegisterForm, UserLoginForm


def home(request):
    """Store homepage with banner, featured categories, and featured products."""
    featured_products = Product.objects.filter(is_active=True, is_featured=True)[:8]
    latest_products = Product.objects.filter(is_active=True)[:8]
    categories = Category.objects.all()[:6]

    context = {
        'featured_products': featured_products,
        'latest_products': latest_products,
        'categories': categories,
    }
    return render(request, 'store/home.html', context)


def product_list(request, category_slug=None):
    """
    Product catalog page with searching, category filtering, and sorting.
    """
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(is_active=True)

    # Filter by category slug in URL
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    # Search keyword
    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )

    # Optional category filter via query parameter
    cat_id = request.GET.get('category')
    if cat_id:
        products = products.filter(category__id=cat_id)

    # Filter by availability
    in_stock_only = request.GET.get('in_stock')
    if in_stock_only == '1':
        products = products.filter(stock__gt=0)

    # Sorting
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'rating':
        products = products.order_by('-rating', '-reviews_count')
    else:  # 'newest' default
        products = products.order_by('-created_at')

    # Pagination: 8 products per page
    paginator = Paginator(products, 8)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.get_page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.get_page(1)

    context = {
        'category': category,
        'categories': categories,
        'products': page_obj,
        'query': query,
        'sort_by': sort_by,
        'total_count': products.count(),
        'in_stock_only': in_stock_only,
    }
    return render(request, 'store/product_list.html', context)


def product_detail(request, slug):
    """Single product details view with related products."""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id)[:4]

    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'store/product_detail.html', context)


# ==========================================
# Shopping Cart Views
# ==========================================

def cart_detail(request):
    """View shopping cart contents, subtotals, and checkout CTA."""
    cart = Cart(request)
    context = {
        'cart': cart,
    }
    return render(request, 'store/cart.html', context)


def cart_add(request, product_id):
    """
    Add product to cart or increase quantity.
    Supports both traditional POST/GET and AJAX requests.
    """
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart = Cart(request)

    # Determine quantity
    quantity = 1
    override = False

    if request.method == 'POST':
        try:
            # Handle JSON payload if sent via fetch
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                quantity = int(data.get('quantity', 1))
                override = bool(data.get('override', False))
            else:
                quantity = int(request.POST.get('quantity', 1))
                override = bool(request.POST.get('override', False))
        except (ValueError, TypeError):
            quantity = 1

    success, message, new_qty = cart.add(product, quantity=quantity, override_quantity=override)

    # Handle AJAX response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
        return JsonResponse({
            'success': success,
            'message': message,
            'item_quantity': new_qty,
            'cart_count': len(cart),
            'subtotal': str(cart.get_subtotal()),
            'shipping': str(cart.get_shipping_cost()),
            'total': str(cart.get_total_price()),
        })

    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'cart_detail'
    return redirect(next_url)


def cart_update(request, product_id):
    """
    Update item quantity in cart (increment, decrement, or set exact value).
    """
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)

    action = request.POST.get('action')
    quantity_val = request.POST.get('quantity')

    current_qty = cart.cart.get(str(product.id), {}).get('quantity', 0)

    if action == 'increment':
        target_qty = current_qty + 1
    elif action == 'decrement':
        target_qty = current_qty - 1
    elif quantity_val is not None:
        try:
            target_qty = int(quantity_val)
        except ValueError:
            target_qty = current_qty
    else:
        target_qty = current_qty

    if target_qty <= 0:
        cart.remove(product)
        msg = f"Removed '{product.name}' from your cart."
        success = True
    else:
        success, msg, target_qty = cart.add(product, quantity=target_qty, override_quantity=True)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
        return JsonResponse({
            'success': success,
            'message': msg,
            'item_quantity': target_qty,
            'item_total': str(product.price * target_qty),
            'cart_count': len(cart),
            'subtotal': str(cart.get_subtotal()),
            'shipping': str(cart.get_shipping_cost()),
            'total': str(cart.get_total_price()),
        })

    if success:
        messages.success(request, msg)
    else:
        messages.error(request, msg)

    return redirect('cart_detail')


def cart_remove(request, product_id):
    """Remove a product completely from the cart."""
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    cart.remove(product)

    msg = f"'{product.name}' was removed from your cart."

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
        return JsonResponse({
            'success': True,
            'message': msg,
            'cart_count': len(cart),
            'subtotal': str(cart.get_subtotal()),
            'shipping': str(cart.get_shipping_cost()),
            'total': str(cart.get_total_price()),
        })

    messages.info(request, msg)
    return redirect('cart_detail')


def cart_clear(request):
    """Remove all items from the cart."""
    cart = Cart(request)
    cart.clear()
    messages.info(request, "Your shopping cart has been cleared.")
    return redirect('cart_detail')


# ==========================================
# Checkout and Order Processing Views
# ==========================================

def checkout(request):
    """
    Checkout page view. Validates cart, stock, and processes orders.
    """
    cart = Cart(request)

    # Prevent checkout if cart is empty
    if len(cart) == 0:
        messages.warning(request, "Your shopping cart is empty. Add products before checking out.")
        return redirect('product_list')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                # Use database transaction to maintain absolute consistency
                with transaction.atomic():
                    # 1. Lock and verify stock for all items
                    items_to_process = []
                    subtotal = Decimal('0.00')

                    for item in cart:
                        # Select product for update to lock the row and avoid race conditions
                        product = Product.objects.select_for_update().get(id=item['product'].id)
                        requested_qty = item['quantity']

                        if product.stock < requested_qty:
                            raise ValueError(
                                f"Insufficient stock for '{product.name}'. "
                                f"Only {product.stock} units available, but your cart has {requested_qty}."
                            )

                        items_to_process.append({
                            'product': product,
                            'quantity': requested_qty,
                            'price': product.price,  # Always use authoritative server price
                        })
                        subtotal += product.price * requested_qty

                    # 2. Compute shipping cost
                    shipping_cost = Decimal('0.00') if subtotal >= Decimal('50.00') else Decimal('5.00')
                    total_amount = subtotal + shipping_cost

                    # 3. Create the Order
                    order = form.save(commit=False)
                    if request.user.is_authenticated:
                        order.user = request.user
                    order.total_amount = total_amount
                    order.shipping_cost = shipping_cost
                    order.status = 'PENDING'
                    order.payment_method = 'Cash on Delivery (COD)'
                    order.payment_status = 'Pending'
                    order.save()

                    # 4. Create OrderItem records & reduce stock
                    for item_data in items_to_process:
                        prod = item_data['product']
                        qty = item_data['quantity']

                        OrderItem.objects.create(
                            order=order,
                            product=prod,
                            product_name=prod.name,
                            price=item_data['price'],
                            quantity=qty
                        )

                        # Decrement stock
                        prod.stock -= qty
                        prod.save()

                    # 5. Clear cart
                    cart.clear()

                    # Store recent order number in session for confirmation page access
                    request.session['recent_order'] = order.order_number

                    messages.success(request, f"Thank you! Your order #{order.order_number} has been placed successfully.")
                    return redirect('order_confirmation', order_number=order.order_number)

            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"An error occurred while processing your order: {str(e)}")
        else:
            messages.error(request, "Please correct the errors in the shipping details below.")
    else:
        # Pre-fill form if user is logged in
        initial_data = {}
        if request.user.is_authenticated:
            u = request.user
            initial_data = {
                'full_name': f"{u.first_name} {u.last_name}".strip() or u.username,
                'email': u.email,
            }
        form = CheckoutForm(initial=initial_data)

    context = {
        'form': form,
        'cart': cart,
    }
    return render(request, 'store/checkout.html', context)


def order_confirmation(request, order_number):
    """
    Displays confirmation for a successfully placed order.
    Protected to ensure guest or authenticated customer sees their own order.
    """
    order = get_object_or_404(Order, order_number=order_number)

    # Permission check: Allowed if user owns the order, is staff, or just placed it in this session
    recent_order = request.session.get('recent_order')
    if order.user:
        if request.user != order.user and not request.user.is_staff and recent_order != order.order_number:
            raise Http404("Order not found or permission denied.")
    else:
        # Guest order: allow if matches recent session order
        if recent_order != order.order_number and not request.user.is_staff:
            raise Http404("Order not found or permission denied.")

    context = {
        'order': order,
    }
    return render(request, 'store/order_confirmation.html', context)


@login_required
def order_history(request):
    """Displays order history for the authenticated customer."""
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product')
    context = {
        'orders': orders,
    }
    return render(request, 'store/order_history.html', context)


@login_required
def order_detail(request, order_number):
    """
    Displays full details of a specific past order.
    Customer can only view their own orders.
    """
    order = get_object_or_404(Order, order_number=order_number)
    if order.user != request.user and not request.user.is_staff:
        raise Http404("Order not found or access denied.")

    context = {
        'order': order,
    }
    return render(request, 'store/order_detail.html', context)


# ==========================================
# User Authentication Views
# ==========================================

def user_register(request):
    """Customer registration view."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            # Log the user in immediately
            login(request, user)
            messages.success(request, f"Welcome to ShopEasy, {user.first_name or user.username}! Your account has been created.")
            return redirect('home')
        else:
            messages.error(request, "Registration could not be completed. Please check the form errors below.")
    else:
        form = UserRegisterForm()

    return render(request, 'store/register.html', {'form': form})


def user_login(request):
    """Customer login view."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_page = request.GET.get('next') or request.POST.get('next') or 'home'
            return redirect(next_page)
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = UserLoginForm()

    return render(request, 'store/login.html', {'form': form})


def user_logout(request):
    """Customer logout view."""
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('home')


def contact(request):
    """Contact & support information page."""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        if name and email and message:
            messages.success(request, "Thank you for reaching out! Our support team will get back to you within 24 hours.")
            return redirect('contact')
        else:
            messages.error(request, "Please fill in all required fields.")

    return render(request, 'store/contact.html')
