from .cart import Cart


def cart_summary(request):
    cart = Cart(request)
    items = cart.items()
    return {
        "cart_count": sum(item["quantity"] for item in items),
        "cart_items": items,
        "cart_total": sum((item["subtotal"] for item in items), 0),
    }
