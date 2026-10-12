from decimal import Decimal
from django.conf import settings
from store.models import Product


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False):
        """
        Add a product to the cart or update its quantity.
        Respects available stock. Returns a tuple (success, message, current_qty).
        """
        product_id = str(product.id)
        if product.stock <= 0:
            return False, f"Sorry, '{product.name}' is out of stock.", 0

        current_qty = self.cart.get(product_id, {}).get('quantity', 0)

        if override_quantity:
            target_qty = quantity
        else:
            target_qty = current_qty + quantity

        if target_qty > product.stock:
            # Cap at available stock
            target_qty = product.stock
            self.cart[product_id] = {
                'quantity': target_qty,
                'price': str(product.price),
            }
            self.save()
            return True, f"Quantity capped to maximum available stock ({product.stock}).", target_qty

        if target_qty <= 0:
            self.remove(product)
            return True, f"'{product.name}' removed from cart.", 0

        self.cart[product_id] = {
            'quantity': target_qty,
            'price': str(product.price),
        }
        self.save()
        return True, f"Added {product.name} to cart.", target_qty

    def remove(self, product):
        """Remove a product from the cart."""
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def clear(self):
        """Clear the cart from session."""
        if settings.CART_SESSION_ID in self.session:
            del self.session[settings.CART_SESSION_ID]
            self.save()

    def save(self):
        """Mark session as modified to ensure it gets saved."""
        self.session.modified = True

    def __iter__(self):
        """
        Iterate over the items in the cart and retrieve the products from the database.
        """
        product_ids = list(self.cart.keys())
        products = Product.objects.filter(id__in=product_ids)
        product_map = {str(p.id): p for p in products}

        # Clean up any products that no longer exist
        missing_ids = [pid for pid in product_ids if pid not in product_map]
        for pid in missing_ids:
            del self.cart[pid]
        if missing_ids:
            self.save()

        for product_id, item in list(self.cart.items()):
            product = product_map.get(product_id)
            if not product:
                continue

            # Ensure cart price is accurate from current product price
            unit_price = product.price
            quantity = item['quantity']

            total_price = unit_price * quantity

            yield {
                'product': product,
                'price': unit_price,
                'quantity': quantity,
                'total_price': total_price,
                'max_stock': product.stock,
            }

    def __len__(self):
        """Count all items in the cart."""
        return sum(item['quantity'] for item in self.cart.values())

    def get_subtotal(self):
        """Calculate cart subtotal using latest database prices."""
        product_ids = list(self.cart.keys())
        products = Product.objects.filter(id__in=product_ids)
        product_map = {str(p.id): p for p in products}

        total = Decimal('0.00')
        for product_id, item in self.cart.items():
            product = product_map.get(product_id)
            if product:
                total += product.price * item['quantity']
        return total

    def get_shipping_cost(self):
        """Free shipping for orders $50 or more, else $5.00 flat (free if cart empty)."""
        subtotal = self.get_subtotal()
        if subtotal == Decimal('0.00'):
            return Decimal('0.00')
        if subtotal >= Decimal('50.00'):
            return Decimal('0.00')
        return Decimal('5.00')

    def get_total_price(self):
        """Total = subtotal + shipping cost."""
        return self.get_subtotal() + self.get_shipping_cost()

    def get_item_count(self):
        return sum(item['quantity'] for item in self.cart.values())
