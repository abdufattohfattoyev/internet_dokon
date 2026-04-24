from .models import Cart, Category

def cart(request):
    cart_count = 0
    session_key = request.session.session_key
    if session_key:
        cart, _ = Cart.objects.get_or_create(session_key=session_key)
        cart_count = cart.cartitem_set.count()
    return {
        'cart_count': cart_count,
        'all_categories': Category.objects.all(),
    }