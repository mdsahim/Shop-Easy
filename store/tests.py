from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from store.models import Category, Product, Order, OrderItem
from store.cart import Cart


class ShopEasyTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create Category
        self.category = Category.objects.create(
            name="Electronics",
            slug="electronics",
            description="Electronic devices and tech gear"
        )

        # Create Products
        self.product1 = Product.objects.create(
            category=self.category,
            name="Wireless Headphones",
            slug="wireless-headphones",
            description="Crisp acoustics and noise cancellation",
            price=Decimal('129.99'),
            old_price=Decimal('169.99'),
            stock=10,
            rating=Decimal('4.8'),
            reviews_count=20,
            is_featured=True,
            is_active=True
        )

        self.product_out_of_stock = Product.objects.create(
            category=self.category,
            name="Smart Watch Ultra",
            slug="smart-watch-ultra",
            description="Advanced fitness watch",
            price=Decimal('199.99'),
            stock=0,  # Out of stock
            is_active=True
        )

        # Create User
        self.user = User.objects.create_user(
            username='testbuyer',
            email='buyer@example.com',
            password='testpassword123',
            first_name='Alice',
            last_name='Smith'
        )

        self.other_user = User.objects.create_user(
            username='otherbuyer',
            email='other@example.com',
            password='testpassword123'
        )

    # 1. Product Listing & Filtering
    def test_product_list_view(self):
        response = self.client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Wireless Headphones")

    def test_product_list_category_filter(self):
        response = self.client.get(reverse('product_list_by_category', args=[self.category.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Wireless Headphones")

    def test_product_search(self):
        response = self.client.get(reverse('product_list') + '?q=Headphones')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Wireless Headphones")

        # Search for non-existent item
        response_empty = self.client.get(reverse('product_list') + '?q=NonExistentDevice123')
        self.assertEqual(response_empty.status_code, 200)
        self.assertContains(response_empty, "No matching products found")

    def test_product_sorting(self):
        Product.objects.create(
            category=self.category,
            name="Budget Cable",
            slug="budget-cable",
            description="Charging wire",
            price=Decimal('9.99'),
            stock=5,
            is_active=True
        )
        response_asc = self.client.get(reverse('product_list') + '?sort=price_asc')
        self.assertEqual(response_asc.status_code, 200)
        products = list(response_asc.context['products'])
        self.assertTrue(products[0].price <= products[-1].price)

    # 2. Product Detail View
    def test_product_detail_view(self):
        response = self.client.get(reverse('product_detail', args=[self.product1.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Wireless Headphones")
        self.assertContains(response, "129.99")
        self.assertContains(response, "In Stock")

    def test_product_detail_404(self):
        response = self.client.get(reverse('product_detail', args=['non-existent-slug']))
        self.assertEqual(response.status_code, 404)

    # 3. Shopping Cart Session Operations
    def test_add_to_cart(self):
        response = self.client.post(reverse('cart_add', args=[self.product1.id]), {'quantity': 2})
        self.assertEqual(response.status_code, 302)

        # Check cart in session
        cart_data = self.client.session.get('cart')
        self.assertIsNotNone(cart_data)
        self.assertEqual(cart_data[str(self.product1.id)]['quantity'], 2)

    def test_add_out_of_stock_to_cart(self):
        response = self.client.post(reverse('cart_add', args=[self.product_out_of_stock.id]), {'quantity': 1})
        self.assertEqual(response.status_code, 302)
        cart_data = self.client.session.get('cart', {})
        self.assertNotIn(str(self.product_out_of_stock.id), cart_data)

    def test_cart_quantity_capped_at_stock(self):
        # Product1 has stock of 10
        response = self.client.post(reverse('cart_add', args=[self.product1.id]), {'quantity': 15})
        self.assertEqual(response.status_code, 302)
        cart_data = self.client.session.get('cart')
        self.assertEqual(cart_data[str(self.product1.id)]['quantity'], 10)

    def test_update_and_remove_cart_item(self):
        # Add first
        self.client.post(reverse('cart_add', args=[self.product1.id]), {'quantity': 3})
        # Update
        self.client.post(reverse('cart_update', args=[self.product1.id]), {'quantity': 5})
        cart_data = self.client.session.get('cart')
        self.assertEqual(cart_data[str(self.product1.id)]['quantity'], 5)

        # Remove
        self.client.post(reverse('cart_remove', args=[self.product1.id]))
        cart_data = self.client.session.get('cart')
        self.assertNotIn(str(self.product1.id), cart_data)

    def test_cart_ajax_add(self):
        response = self.client.post(
            reverse('cart_add', args=[self.product1.id]),
            {'quantity': 1},
            headers={'x-requested-with': 'XMLHttpRequest'}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['cart_count'], 1)

    # 4. Checkout Validation & Stock Reduction
    def test_checkout_empty_cart_redirects(self):
        response = self.client.get(reverse('checkout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('product_list'))

    def test_successful_checkout_and_stock_reduction(self):
        # Add 2 headphones to cart
        self.client.post(reverse('cart_add', args=[self.product1.id]), {'quantity': 2})
        initial_stock = self.product1.stock  # 10

        checkout_data = {
            'full_name': 'Alice Smith',
            'email': 'alice@example.com',
            'phone': '+1 555-123-4567',
            'address': '456 Tech Park Way, Apt 3B',
            'city': 'San Jose',
            'state': 'CA',
            'postal_code': '95112',
            'payment_method': 'COD',
        }

        response = self.client.post(reverse('checkout'), checkout_data)
        self.assertEqual(response.status_code, 302)

        # Verify order exists in DB
        order = Order.objects.latest('created_at')
        self.assertEqual(order.full_name, 'Alice Smith')
        self.assertEqual(order.payment_method, 'Cash on Delivery (COD)')
        # Subtotal: 2 * 129.99 = 259.98 >= 50 so shipping is free
        self.assertEqual(order.total_amount, Decimal('259.98'))
        self.assertEqual(order.shipping_cost, Decimal('0.00'))

        # Verify OrderItem
        self.assertEqual(order.items.count(), 1)
        item = order.items.first()
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.price, Decimal('129.99'))

        # Verify product stock reduction
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.stock, initial_stock - 2)

        # Verify cart was cleared
        cart_data = self.client.session.get('cart', {})
        self.assertEqual(len(cart_data), 0)

    def test_checkout_fails_if_stock_depleted_before_submission(self):
        # User puts 5 in cart
        self.client.post(reverse('cart_add', args=[self.product1.id]), {'quantity': 5})

        # Another process depletes stock to 2
        self.product1.stock = 2
        self.product1.save()

        checkout_data = {
            'full_name': 'Alice Smith',
            'email': 'alice@example.com',
            'phone': '+1 555-123-4567',
            'address': '456 Tech Park Way, Apt 3B',
            'city': 'San Jose',
            'state': 'CA',
            'postal_code': '95112',
        }

        response = self.client.post(reverse('checkout'), checkout_data)
        self.assertEqual(response.status_code, 200)  # Re-renders checkout with error
        self.assertContains(response, "Insufficient stock")

        # No order created
        self.assertEqual(Order.objects.count(), 0)

    # 5. User Authentication & Order Permissions
    def test_user_registration_and_login(self):
        reg_data = {
            'username': 'newshopper',
            'first_name': 'New',
            'last_name': 'Shopper',
            'email': 'newshopper@example.com',
            'password': 'StrongPassword123!',
            'confirm_password': 'StrongPassword123!',
        }
        response = self.client.post(reverse('register'), reg_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newshopper').exists())

    def test_order_history_requires_login(self):
        # Anonymous user should be redirected to login
        response = self.client.get(reverse('order_history'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_user_cannot_view_other_users_order(self):
        # Create order for Alice
        order = Order.objects.create(
            user=self.user,
            full_name='Alice Smith',
            email='alice@example.com',
            phone='5551234567',
            address='123 Road',
            city='City',
            state='State',
            postal_code='12345',
            total_amount=Decimal('100.00'),
            shipping_cost=Decimal('0.00')
        )

        # Log in as other_user
        self.client.login(username='otherbuyer', password='testpassword123')
        response = self.client.get(reverse('order_detail', args=[order.order_number]))
        # Must return 404 to protect confidentiality
        self.assertEqual(response.status_code, 404)

        # Log in as the actual owner
        self.client.login(username='testbuyer', password='testpassword123')
        owner_response = self.client.get(reverse('order_detail', args=[order.order_number]))
        self.assertEqual(owner_response.status_code, 200)
        self.assertContains(owner_response, order.order_number)

    # 6. Admin Dashboard & OrderItem Safety Tests
    def test_admin_order_add_page_loads_without_error(self):
        superuser = User.objects.create_superuser(
            username='adminuser',
            email='adminuser@example.com',
            password='adminpassword123'
        )
        self.client.login(username='adminuser', password='adminpassword123')
        response = self.client.get('/admin/store/order/add/')
        self.assertEqual(response.status_code, 200)

    def test_admin_order_creation_with_price_auto_population(self):
        superuser = User.objects.create_superuser(
            username='adminuser2',
            email='adminuser2@example.com',
            password='adminpassword123'
        )
        self.client.login(username='adminuser2', password='adminpassword123')

        post_data = {
            'full_name': 'Admin Created Order',
            'email': 'adminorder@example.com',
            'phone': '1234567890',
            'address': '789 Commerce St',
            'city': 'Chicago',
            'state': 'IL',
            'postal_code': '60601',
            'status': 'PENDING',
            'payment_method': 'Cash on Delivery (COD)',
            'payment_status': 'Pending',
            'shipping_cost': '5.00',
            'items-TOTAL_FORMS': '1',
            'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '0',
            'items-MAX_NUM_FORMS': '1000',
            'items-0-product': str(self.product1.id),
            'items-0-product_name': '',  # Auto-populate
            'items-0-price': '',         # Auto-populate
            'items-0-quantity': '2',
        }
        response = self.client.post('/admin/store/order/add/', post_data)
        self.assertEqual(response.status_code, 302)

        created_order = Order.objects.latest('created_at')
        item = created_order.items.first()
        self.assertEqual(item.price, self.product1.price)
        self.assertEqual(item.product_name, self.product1.name)
        self.assertEqual(created_order.total_amount, (self.product1.price * 2) + Decimal('5.00'))

    def test_order_item_cost_and_display_safety_with_none(self):
        order = Order.objects.create(
            full_name='Test Safe',
            email='test@example.com',
            phone='1234567890',
            address='123 Test St',
            city='City',
            state='State',
            postal_code='12345'
        )
        empty_item = OrderItem(order=order)
        self.assertIsNone(empty_item.get_cost())
        self.assertEqual(empty_item.item_total, Decimal('0.00'))

        from store.admin import OrderItemInline
        from django.contrib.admin.sites import AdminSite
        inline = OrderItemInline(Order, AdminSite())
        self.assertEqual(inline.item_total(empty_item), '—')

    def test_order_item_validation_prevents_missing_price_without_product(self):
        from django.core.exceptions import ValidationError
        order = Order.objects.create(
            full_name='Test Invalid',
            email='test@example.com',
            phone='1234567890',
            address='123 Test St',
            city='City',
            state='State',
            postal_code='12345'
        )
        invalid_item = OrderItem(order=order, product=None, price=None, quantity=1)
        with self.assertRaises(ValidationError):
            invalid_item.clean()

