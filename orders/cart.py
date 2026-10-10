from decimal import Decimal

from products.models import Product


class Cart:
    session_key = "cart"

    def __init__(self, request):
        self.session = request.session
        self.data = self.session.get(self.session_key, {})

    def add(self, product, quantity=1):
        quantity = max(int(quantity), 1)
        product_id = str(product.pk)
        current_quantity = int(self.data.get(product_id, 0))
        self.data[product_id] = min(current_quantity + quantity, product.stock)
        self._save()

    def set_quantity(self, product, quantity):
        quantity = int(quantity)
        product_id = str(product.pk)
        if quantity <= 0 or product.stock <= 0:
            self.data.pop(product_id, None)
        else:
            self.data[product_id] = min(quantity, product.stock)
        self._save()

    def remove(self, product):
        self.data.pop(str(product.pk), None)
        self._save()

    def items(self):
        product_ids = [int(product_id) for product_id in self.data]
        products = Product.objects.filter(
            id__in=product_ids,
            is_active=True,
            category__is_active=True,
            product_type=Product.ProductType.PHYSICAL,
        ).select_related("category")
        products_by_id = {str(product.pk): product for product in products}
        items = []
        stale_ids = []
        changed = False

        for product_id, raw_quantity in self.data.items():
            product = products_by_id.get(product_id)
            if product is None or product.stock <= 0:
                stale_ids.append(product_id)
                continue
            quantity = min(int(raw_quantity), product.stock)
            if quantity != int(raw_quantity):
                self.data[product_id] = quantity
                changed = True
            items.append(
                {
                    "product": product,
                    "quantity": quantity,
                    "subtotal": product.price * quantity,
                }
            )

        if stale_ids:
            for product_id in stale_ids:
                self.data.pop(product_id, None)
            changed = True
        if changed:
            self._save()
        return items

    def count(self):
        return sum(item["quantity"] for item in self.items())

    def total(self):
        return sum(
            (item["subtotal"] for item in self.items()),
            Decimal("0.00"),
        )

    def clear(self):
        self.data = {}
        self._save()

    def _save(self):
        self.session[self.session_key] = self.data
        self.session.modified = True
        self.session.save()
