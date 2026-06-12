
from .models import Cart, ContactMessage

def cart_count(request):
    count = 0
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            count = cart.item_count
        except Cart.DoesNotExist:
            count = 0
    else:
        session = getattr(request, 'session', None)
        if session and hasattr(session, 'session_key') and session.session_key:
            try:
                cart = Cart.objects.get(session_key=session.session_key)
                count = cart.item_count
            except Cart.DoesNotExist:
                count = 0
    return {'cart_count': count}

def unread_messages_count(request):
    count = 0
    if request.user.is_staff or request.user.is_superuser:
        count = ContactMessage.objects.filter(is_read=False).count()
    return {'unread_messages_count': count}
