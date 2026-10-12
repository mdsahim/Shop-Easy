from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils.text import slugify
from store.models import Category, Product


class Command(BaseCommand):
    help = 'Populates the database with categories, requested sample products, and demo users.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Initializing sample data for ShopEasy..."))

        # 1. Create superuser if it doesn't exist
        admin_user, created_admin = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@shopeasy.com',
                'first_name': 'ShopEasy',
                'last_name': 'Admin',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created_admin:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created superuser 'admin' with password 'admin123'."))
        else:
            self.stdout.write("Superuser 'admin' already exists.")

        # 2. Create demo customer
        demo_user, created_user = User.objects.get_or_create(
            username='customer',
            defaults={
                'email': 'john.doe@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
            }
        )
        if created_user:
            demo_user.set_password('customer123')
            demo_user.save()
            self.stdout.write(self.style.SUCCESS("Created demo customer 'customer' with password 'customer123'."))

        # 3. Categories data
        categories_data = [
            {
                'name': 'Audio & Headphones',
                'description': 'Premium noise-cancelling headphones, wireless earphones, and studio audio gear.',
                'icon': 'bi-headphones',
                'image_url': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=600&q=80',
            },
            {
                'name': 'Wearables & Smart Watches',
                'description': 'Advanced fitness trackers, smart watches with health metrics, and wearable tech.',
                'icon': 'bi-smartwatch',
                'image_url': 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=600&q=80',
            },
            {
                'name': 'Laptops & Computers',
                'description': 'High-performance laptops, ultrabooks, and workstations for productivity and creators.',
                'icon': 'bi-laptop',
                'image_url': 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=600&q=80',
            },
            {
                'name': 'Computer Accessories',
                'description': 'Ergonomic keyboards, precision mice, monitors, and modern desk workspace accessories.',
                'icon': 'bi-keyboard',
                'image_url': 'https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=600&q=80',
            },
            {
                'name': 'Smartphones & Gadgets',
                'description': 'Flagship mobile phones, 5G smartphones, and versatile everyday electronic devices.',
                'icon': 'bi-phone',
                'image_url': 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=600&q=80',
            },
        ]

        cat_objs = {}
        for c_data in categories_data:
            slug = slugify(c_data['name'])
            cat, _ = Category.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': c_data['name'],
                    'description': c_data['description'],
                    'icon': c_data['icon'],
                    'image_url': c_data['image_url'],
                }
            )
            cat_objs[c_data['name']] = cat

        self.stdout.write(self.style.SUCCESS(f"Loaded {len(cat_objs)} categories."))

        # 4. Products data (specifically including all requested items)
        products_data = [
            {
                'name': 'Wireless Headphones',
                'category': cat_objs['Audio & Headphones'],
                'price': Decimal('129.99'),
                'old_price': Decimal('169.99'),
                'stock': 25,
                'rating': Decimal('4.8'),
                'reviews_count': 142,
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=700&q=80',
                'description': 'Experience crisp acoustic clarity with our premier Wireless Over-Ear Headphones. Features hybrid active noise cancellation (ANC), 40-hour extended battery life, ultra-plush memory foam earcups, and crystal-clear microphone calling with Bluetooth 5.3 multi-point pairing.'
            },
            {
                'name': 'Smart Watch',
                'category': cat_objs['Wearables & Smart Watches'],
                'price': Decimal('199.99'),
                'old_price': Decimal('249.99'),
                'stock': 18,
                'rating': Decimal('4.7'),
                'reviews_count': 98,
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=700&q=80',
                'description': 'Elevate your daily lifestyle with the ShopEasy Smart Watch. Equipped with an AMOLED always-on display, all-day heart rate & SpO2 monitoring, built-in GPS, sleep quality analytics, and IP68 waterproof rating. Works seamlessly with iOS and Android.'
            },
            {
                'name': 'Laptop',
                'category': cat_objs['Laptops & Computers'],
                'price': Decimal('899.99'),
                'old_price': Decimal('999.99'),
                'stock': 12,
                'rating': Decimal('4.9'),
                'reviews_count': 76,
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=700&q=80',
                'description': 'Ultra-thin, featherweight aluminum body engineered for modern creators and professionals. Features a vivid 15.6-inch 2K IPS screen, high-speed multi-core processor, 16GB DDR5 RAM, 512GB NVMe SSD, and 12-hour all-day battery life with rapid USB-C charging.'
            },
            {
                'name': 'Mechanical Keyboard',
                'category': cat_objs['Computer Accessories'],
                'price': Decimal('89.99'),
                'old_price': Decimal('119.99'),
                'stock': 30,
                'rating': Decimal('4.6'),
                'reviews_count': 115,
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=700&q=80',
                'description': 'Custom hot-swappable mechanical keyboard built with lubed linear switches, premium double-shot PBT keycaps, per-key RGB backlighting, sound-dampening silicone foam, and versatile triple-mode connection (Bluetooth, 2.4GHz wireless, USB-C).'
            },
            {
                'name': 'Gaming Mouse',
                'category': cat_objs['Computer Accessories'],
                'price': Decimal('49.99'),
                'old_price': Decimal('69.99'),
                'stock': 40,
                'rating': Decimal('4.7'),
                'reviews_count': 89,
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?auto=format&fit=crop&w=700&q=80',
                'description': 'Ultra-lightweight ergonomic gaming mouse featuring a precision 26,000 DPI optical sensor, optical switches rated for 90 million clicks, PTFE glide feet, and customizable RGB zones with programmable macro buttons.'
            },
            {
                'name': 'Smartphone',
                'category': cat_objs['Smartphones & Gadgets'],
                'price': Decimal('699.99'),
                'old_price': Decimal('799.99'),
                'stock': 15,
                'rating': Decimal('4.8'),
                'reviews_count': 160,
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=700&q=80',
                'description': 'Flagship 5G smartphone boasting a 6.7-inch 120Hz LTPO display, 50MP triple studio camera system with optical image stabilization, 5000mAh battery with 65W fast charging, and edge-to-edge Corning Gorilla Glass Armor.'
            },
            {
                'name': 'Bluetooth Speaker',
                'category': cat_objs['Audio & Headphones'],
                'price': Decimal('59.99'),
                'old_price': Decimal('79.99'),
                'stock': 35,
                'rating': Decimal('4.5'),
                'reviews_count': 64,
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1545454675-3531b543be5d?auto=format&fit=crop&w=700&q=80',
                'description': 'Portable rugged wireless speaker delivering 360-degree punchy stereo sound with deep bass radiators. IP67 waterproof and dustproof design, 24-hour playtime, and party-boost wireless daisy-chain capability for indoor and outdoor adventures.'
            },
            {
                'name': 'Laptop Stand',
                'category': cat_objs['Computer Accessories'],
                'price': Decimal('29.99'),
                'old_price': Decimal('39.99'),
                'stock': 50,
                'rating': Decimal('4.6'),
                'reviews_count': 78,
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?auto=format&fit=crop&w=700&q=80',
                'description': 'Ergonomic aluminum laptop riser designed for optimum heat dissipation and posture alignment. Adjustable 6-angle height settings, non-slip silicone pads, and foldable travel pouch included. Compatible with laptops 10 to 17 inches.'
            },
            {
                'name': 'Noise-Cancelling Wireless Earbuds',
                'category': cat_objs['Audio & Headphones'],
                'price': Decimal('79.99'),
                'old_price': Decimal('99.99'),
                'stock': 28,
                'rating': Decimal('4.7'),
                'reviews_count': 53,
                'is_featured': False,
                'image_url': 'https://images.unsplash.com/photo-1590658268037-6bf12165a8df?auto=format&fit=crop&w=700&q=80',
                'description': 'True wireless earbuds with transparency mode, quad-mic beamforming audio, wireless charging case, and water resistance for fitness workouts.'
            },
            {
                'name': '4K Ultra HD IPS Monitor',
                'category': cat_objs['Computer Accessories'],
                'price': Decimal('349.99'),
                'old_price': Decimal('429.99'),
                'stock': 10,
                'rating': Decimal('4.9'),
                'reviews_count': 41,
                'is_featured': False,
                'image_url': 'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?auto=format&fit=crop&w=700&q=80',
                'description': '27-inch 4K UHD color-calibrated display with 99% sRGB color gamut, USB-C 65W power delivery, HDR400 support, and tilt/swivel ergonomic stand.'
            },
        ]

        for p_data in products_data:
            slug = slugify(p_data['name'])
            Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'category': p_data['category'],
                    'name': p_data['name'],
                    'description': p_data['description'],
                    'price': p_data['price'],
                    'old_price': p_data['old_price'],
                    'stock': p_data['stock'],
                    'rating': p_data['rating'],
                    'reviews_count': p_data['reviews_count'],
                    'is_featured': p_data['is_featured'],
                    'image_url': p_data['image_url'],
                    'is_active': True,
                }
            )

        self.stdout.write(self.style.SUCCESS(f"Successfully loaded {len(products_data)} sample products!"))
