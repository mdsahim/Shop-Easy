from store.cart import Cart
from store.models import Category


def shop_context(request):
    """
    Makes the Cart instance, cart item count, and all product categories
    globally available across all templates.
    """
    cart = Cart(request)
    categories = Category.objects.all()
    return {
        'cart': cart,
        'cart_item_count': len(cart),
        'cart_subtotal': cart.get_subtotal(),
        'global_categories': categories,
    }
