from products.views import product_list


def home(request):
    return product_list(request)
