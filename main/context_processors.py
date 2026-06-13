
from .models import Cart, ContactMessage

def cart_count(request):
    count = 0
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.filter(user=request.user).order_by('-created_at').first()
            count = cart.item_count if cart else 0
        except Exception:
            count = 0
    else:
        session = getattr(request, 'session', None)
        if session and hasattr(session, 'session_key') and session.session_key:
            try:
                cart = Cart.objects.filter(session_key=session.session_key).order_by('-created_at').first()
                count = cart.item_count if cart else 0
            except Exception:
                count = 0
    return {'cart_count': count}


def unread_messages_count(request):
    count = 0
    if request.user.is_staff or request.user.is_superuser:
        try:
            count = ContactMessage.objects.filter(is_read=False).count()
        except Exception:
            count = 0
    return {'unread_messages_count': count}

