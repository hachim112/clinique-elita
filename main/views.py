
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Q, Value, BooleanField, Case, When
from django.http import JsonResponse, Http404
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, date, timedelta
import random
import string

from .models import (
    Profile, Appointment, Category, Product, Cart, CartItem,
    Order, OrderItem, ContactMessage, AnimalProfile, Testimonial
)
from .forms import (
    CustomUserCreationForm, AppointmentForm, GuestAppointmentForm,
    ProductForm, CategoryForm, ContactForm, CheckoutForm,
    AnimalProfileForm, AdminOrderStatusForm, AdminAppointmentStatusForm
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_or_create_cart(request):
    """Get or create cart for user or guest."""
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).order_by('-created_at').first()
        if not cart:
            cart = Cart.objects.create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        cart = Cart.objects.filter(session_key=request.session.session_key).order_by('-created_at').first()
        if not cart:
            cart = Cart.objects.create(session_key=request.session.session_key, user=None)
    return cart


def get_available_time_slots(selected_date):
    """Get available 30-minute time slots for a given date."""
    if selected_date.weekday() == 6:  # Sunday
        return []

    slots = []
    for hour in range(8, 17):
        for minute in [0, 30]:
            time_str = f"{hour:02d}:{minute:02d}"
            t = datetime.strptime(time_str, "%H:%M").time()
            slots.append(t)

    booked_times = list(
        Appointment.objects.filter(date=selected_date)
        .exclude(status__in=['denied', 'cancelled'])
        .values_list('time', flat=True)
    )
    available_slots = [t for t in slots if t not in booked_times]
    return available_slots


def generate_order_id():
    """Generate unique order ID."""
    while True:
        oid = f"ORD{random.randint(10000, 99999)}"
        if not Order.objects.filter(order_id=oid).exists():
            return oid


def generate_appointment_id():
    """Generate unique appointment tracking ID."""
    while True:
        apt_id = f"APT{random.randint(10000, 99999)}"
        if not Appointment.objects.filter(tracking_id=apt_id).exists():
            return apt_id


# ============================================================
# AUTHENTICATION VIEWS
# ============================================================

def register_view(request):
    """User registration."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Welcome to Clinique Elita! Your account has been created successfully.')
            return redirect('home')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomUserCreationForm()

    return render(request, 'register.html', {'form': form})


def login_view(request):
    """User login - handles both regular users and admin panel."""
    if request.user.is_authenticated:
        return redirect('home')

    is_admin_login = '/admin/' in request.GET.get('next', '') or '/panel/' in request.GET.get('next', '')

    if request.method == 'POST':
        identifier = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        if not identifier or not password:
            messages.error(request, 'Please provide both email/username and password.')
            return render(request, 'login.html')

        user_obj = None
        if '@' in identifier:
            user_obj = User.objects.filter(email=identifier).first()
        else:
            user_obj = User.objects.filter(username=identifier).first()

        if user_obj and user_obj.check_password(password):
            if user_obj.is_active:
                login(request, user_obj)
                next_url = request.GET.get('next', 'home')
                if user_obj.is_staff or user_obj.is_superuser:
                    if is_admin_login:
                        messages.success(request, f'Welcome to the admin panel, {user_obj.get_full_name() or user_obj.username}!')
                    else:
                        messages.success(request, f'Welcome back, {user_obj.get_full_name() or user_obj.username}!')
                    return redirect('admin_dashboard')
                messages.success(request, f'Welcome back, {user_obj.get_full_name() or user_obj.username}!')
                return redirect(next_url)
            else:
                messages.error(request, 'Your account is disabled.')
        elif user_obj and not user_obj.check_password(password):
            messages.error(request, 'Incorrect password. Please try again.')
        else:
            messages.error(request, 'No account found with this email or username.')

    context = {'is_admin_login': is_admin_login}
    return render(request, 'login.html', context)


def logout_view(request):
    """User logout."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


# ============================================================
# HOME & PAGES
# ============================================================

def home_view(request):
    """Homepage with hero, stats, services, testimonials."""
    categories = Category.objects.filter(is_active=True).annotate(
        product_count=Count('products', filter=Q(products__is_available=True, products__is_hidden=False))
    ).order_by('-product_count')[:6]
    new_threshold = timezone.now() - timedelta(days=7)
    products = Product.objects.filter(is_available=True, is_hidden=False).select_related('category').annotate(
        is_new=Case(
            When(created_at__gte=new_threshold, then=Value(True)),
            default=Value(False),
            output_field=BooleanField()
        )
    )[:8]

    testimonials = Testimonial.objects.filter(is_active=True).order_by('-created_at')[:6]

    context = {
        'categories': categories,
        'products': products,
        'testimonials': testimonials,
    }
    return render(request, 'home.html', context)


def services_view(request):
    """Services page."""
    return render(request, 'services.html')


def about_view(request):
    """About us page."""
    return render(request, 'about.html')


def contact_view(request):
    """Contact page with form."""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            ContactMessage.objects.create(
                name=form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                message=form.cleaned_data['message']
            )
            messages.success(request, 'Your message has been sent successfully!')
            return redirect('contact')
    else:
        form = ContactForm()

    return render(request, 'contact.html', {'form': form})


# ============================================================
# APPOINTMENT VIEWS
# ============================================================
    return d.weekday() == 6


def appointments_view(request):
    """Appointments overview - book or track."""
    if request.method == 'POST':
        if request.user.is_authenticated:
            form = AppointmentForm(request.POST)
            if form.is_valid():
                appt_date = form.cleaned_data['date']
                appt_time = form.cleaned_data['time']

                if is_sunday(appt_date):
                    messages.error(request, 'The clinic is closed on Sundays. Please choose another day.')
                    return redirect('appointments')

                if appt_date < timezone.now().date():
                    messages.error(request, 'Cannot book appointments in the past.')
                    return redirect('appointments')

                if Appointment.objects.filter(date=appt_date, time=appt_time).exclude(
                    status__in=['denied']
                ).exists():
                    messages.error(request, 'This time slot is already reserved. Please choose another one.')
                    return redirect('appointments')

                appointment = form.save(commit=False)
                appointment.user = request.user
                appointment.tracking_id = generate_appointment_id()
                appointment.save()
                messages.success(request, f'Appointment booked successfully! Your tracking ID: {appointment.tracking_id}')
                return redirect('appointments')
        else:
            form = GuestAppointmentForm(request.POST)
            if form.is_valid():
                appt_date = form.cleaned_data['date']
                appt_time = form.cleaned_data['time']

                if is_sunday(appt_date):
                    messages.error(request, 'The clinic is closed on Sundays. Please choose another day.')
                    return redirect('appointments')

                if appt_date < timezone.now().date():
                    messages.error(request, 'Cannot book appointments in the past.')
                    return redirect('appointments')

                if Appointment.objects.filter(date=appt_date, time=appt_time).exclude(
                    status__in=['denied']
                ).exists():
                    messages.error(request, 'This time slot is already reserved. Please choose another one.')
                    return redirect('appointments')

                appointment = form.save(commit=False)
                appointment.tracking_id = generate_appointment_id()
                appointment.save()
                if 'guest_appointment_ids' not in request.session:
                    request.session['guest_appointment_ids'] = []
                request.session['guest_appointment_ids'].append(appointment.id)
                request.session.modified = True
                messages.success(request, f'Appointment booked successfully! Your tracking ID: {appointment.tracking_id}')
                return redirect('appointments')

    if request.user.is_authenticated:
        form = AppointmentForm()
        my_appointments = Appointment.objects.filter(user=request.user)
    else:
        form = GuestAppointmentForm()
        guest_ids = request.session.get('guest_appointment_ids', [])
        my_appointments = Appointment.objects.filter(id__in=guest_ids)

    tomorrow = timezone.now().date() + timedelta(days=1)
    available_slots = get_available_time_slots(tomorrow)

    context = {
        'form': form,
        'my_appointments': my_appointments,
        'available_slots': available_slots,
        'tomorrow': tomorrow,
        'available_slots_json': [{'value': str(s), 'label': s.strftime('%H:%M')} for s in available_slots],
    }
    return render(request, 'appointments.html', context)


def track_appointment_view(request):
    """Track appointment by phone + appointment ID for guests."""
    appointment = None
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        apt_id = request.POST.get('appointment_id', '').strip()
        appointment = Appointment.objects.filter(guest_phone=phone, tracking_id=apt_id).first()
        if not appointment:
            messages.error(request, 'No appointment found with the provided details.')

    return render(request, 'track_appointment.html', {'appointment': appointment})


def cancel_appointment_view(request, appt_id):
    """Cancel a pending appointment."""
    if request.user.is_authenticated:
        appointment = get_object_or_404(Appointment, id=appt_id, user=request.user)
    else:
        appointment = get_object_or_404(Appointment, id=appt_id, status='pending')

    if appointment.status == 'pending':
        appointment.status = 'denied'
        appointment.save()
        messages.success(request, 'Appointment cancelled successfully.')
    else:
        messages.error(request, 'Cannot cancel this appointment.')

    if request.user.is_authenticated:
        return redirect('appointments')
    return redirect('track_appointment')


def get_available_slots_ajax(request):
    """AJAX endpoint to get available time slots for a given date."""
    date_str = request.GET.get('date', '')
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return JsonResponse({'slots': [], 'error': 'Invalid date'})

    if is_sunday(selected_date):
        return JsonResponse({'slots': [], 'error': 'Clinic closed on Sundays'})

    if selected_date < timezone.now().date():
        return JsonResponse({'slots': [], 'error': 'Cannot book past dates'})

    slots = get_available_time_slots(selected_date)
    slot_choices = [{'value': str(s), 'label': s.strftime('%H:%M')} for s in slots]

    return JsonResponse({'slots': slot_choices})


# ============================================================
# PET SHOP VIEWS
# ============================================================

def pet_shop_view(request):
    """Pet shop with search, filters, and sorting."""
    products = Product.objects.filter(is_available=True, is_hidden=False).select_related('category')

    category_id = request.GET.get('category', '')
    search_query = request.GET.get('q', '')
    sort_by = request.GET.get('sort', 'newest')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')

    if category_id:
        products = products.filter(category_id=category_id)

    if search_query:
        products = products.filter(Q(name__icontains=search_query) | Q(description__icontains=search_query))

    if min_price:
        products = products.filter(price__gte=float(min_price))
    if max_price:
        products = products.filter(price__lte=float(max_price))

    new_threshold = timezone.now() - timedelta(days=7)
    products = products.annotate(
        is_new=Case(
            When(created_at__gte=new_threshold, then=Value(True)),
            default=Value(False),
            output_field=BooleanField()
        )
    )

    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    else:
        products = products.order_by('-created_at')

    categories = Category.objects.filter(is_active=True).annotate(
        product_count=Count('products', filter=Q(products__is_available=True, products__is_hidden=False))
    ).order_by('name')
    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': category_id,
        'search_query': search_query,
        'sort_by': sort_by,
        'min_price': min_price,
        'max_price': max_price,
    }
    return render(request, 'shop.html', context)


def product_detail_view(request, product_id):
    """Single product detail page."""
    new_threshold = timezone.now() - timedelta(days=7)
    product = get_object_or_404(
        Product.objects.select_related('category').annotate(
            is_new=Case(
                When(created_at__gte=new_threshold, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        ),
        id=product_id, is_available=True, is_hidden=False
    )
    related = Product.objects.filter(
        category=product.category, is_available=True, is_hidden=False
    ).exclude(id=product.id).annotate(
        is_new=Case(
            When(created_at__gte=new_threshold, then=Value(True)),
            default=Value(False),
            output_field=BooleanField()
        )
    )[:4]

    context = {
        'product': product,
        'related': related,
        'wilaya_choices': Order.WILAYA_CHOICES,
    }
    return render(request, 'product_detail.html', context)


# ============================================================
# CART VIEWS
# ============================================================

@login_required
def cart_view(request):
    """Cart page - redirects to shop since cart is no longer used."""
    messages.info(request, 'The cart has been removed. Please use the Buy Now button to order products directly.')
    return redirect('shop')


def add_to_cart(request, product_id):
    """Redirect to product detail - cart removed."""
    messages.info(request, 'Please use the Buy Now button on the product page to place your order directly.')
    return redirect('product_detail', product_id=product_id)


def update_cart_item(request, item_id):
    """Redirect to shop - cart removed."""
    messages.info(request, 'The cart has been removed. Please use the Buy Now button to order products directly.')
    return redirect('shop')


def remove_from_cart(request, item_id):
    """Redirect to shop - cart removed."""
    messages.info(request, 'The cart has been removed. Please use the Buy Now button to order products directly.')
    return redirect('shop')


# ============================================================
# CHECKOUT & ORDERS
# ============================================================

def checkout_view(request):
    """Checkout page."""
    cart = get_or_create_cart(request)
    items = cart.items.select_related('product').all().filter(product__is_available=True)

    if not items.exists():
        messages.error(request, 'Votre panier est vide.')
        return redirect('shop')

    total = sum(item.product.price * item.quantity for item in items)

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = Order(
                user=request.user if request.user.is_authenticated else None,
                guest_name=form.cleaned_data['name'],
                guest_phone=form.cleaned_data['phone'],
                guest_email=request.user.email if request.user.is_authenticated else '',
                wilaya=form.cleaned_data['wilaya'],
                commune=form.cleaned_data['commune'],
                address=form.cleaned_data['address'],
                delivery_type=form.cleaned_data['delivery_type'],
                total_price=total,
                notes=form.cleaned_data.get('notes', ''),
                order_id=generate_order_id(),
            )
            order.save()

            for item in items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    product_name=item.product.name,
                    product_price=item.product.price,
                    quantity=item.quantity,
                )
                item.product.stock -= item.quantity
                item.product.save()

            cart.items.all().delete()
            messages.success(request, f'Commande {order.order_id} passée avec succès!')
            return redirect('order_tracking', order_id=order.id)

    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'name': request.user.get_full_name() or request.user.username,
                'phone': request.user.profile.phone if hasattr(request.user, 'profile') else '',
            }
        form = CheckoutForm(initial=initial_data)

    context = {
        'form': form,
        'items': items,
        'total': total,
    }
    return render(request, 'checkout.html', context)


@login_required
def my_orders_view(request):
    """User's order history."""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    paginator = Paginator(orders, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'my_orders.html', {'page_obj': page_obj})


def order_tracking_view(request, order_id):
    """Track order status."""
    order = get_object_or_404(Order, id=order_id)

    if request.user.is_authenticated and order.user and order.user != request.user:
        messages.error(request, 'Unauthorized.')
        return redirect('home')

    context = {'order': order}
    return render(request, 'order_tracking.html', context)


def direct_buy_view(request, product_id):
    """Direct buy: create order from product detail page without cart."""
    product = get_object_or_404(Product, id=product_id, is_available=True, is_hidden=False)

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        wilaya = request.POST.get('wilaya', '').strip()
        commune = request.POST.get('commune', '').strip()
        address = request.POST.get('address', '').strip()
        quantity = request.POST.get('quantity', '1')
        delivery_type = request.POST.get('delivery_type', 'home')

        errors = []
        if not first_name:
            errors.append('First name is required.')
        if not last_name:
            errors.append('Last name is required.')
        if not phone:
            errors.append('Phone number is required.')
        if not wilaya:
            errors.append('Wilaya is required.')
        if not commune:
            errors.append('Commune is required.')
        if not address:
            errors.append('Address is required.')
        if delivery_type not in ['home', 'desk']:
            delivery_type = 'home'

        errors = []
        if not first_name:
            errors.append('First name is required.')
        if not last_name:
            errors.append('Last name is required.')
        if not phone:
            errors.append('Phone number is required.')
        if not wilaya:
            errors.append('Wilaya is required.')
        if not commune:
            errors.append('Commune is required.')
        if not address:
            errors.append('Address is required.')

        try:
            quantity = int(quantity)
            if quantity < 1:
                errors.append('Quantity must be at least 1.')
            elif quantity > product.stock:
                errors.append(f'Only {product.stock} items available.')
        except ValueError:
            errors.append('Invalid quantity.')
            quantity = 1

        if errors:
            for error in errors:
                messages.error(request, error)
            context = {
                'product': product,
                'errors': errors,
                'data': request.POST,
                'wilaya_choices': Order.WILAYA_CHOICES,
            }
            return render(request, 'product_detail.html', context)

        full_name = f'{first_name} {last_name}'
        total = product.price * quantity

        order = Order(
            user=request.user if request.user.is_authenticated else None,
            guest_name=full_name,
            guest_phone=phone,
            guest_email=request.user.email if request.user.is_authenticated else '',
            wilaya=wilaya,
            commune=commune,
            address=address,
            delivery_type=delivery_type,
            total_price=total,
            order_id=generate_order_id(),
        )
        order.save()

        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            product_price=product.price,
            quantity=quantity,
        )

        product.stock -= quantity
        product.save()

        messages.success(request, f'Order {order.order_id} placed successfully! We will contact you soon.')
        return redirect('order_tracking', order_id=order.id)

    return redirect('product_detail', product_id=product.id)


# ============================================================
# ANIMAL PROFILES
# ============================================================

@login_required
def animal_profiles_view(request):
    """List user's animal profiles."""
    animals = AnimalProfile.objects.filter(user=request.user)

    if request.method == 'POST':
        form = AnimalProfileForm(request.POST)
        if form.is_valid():
            animal = form.save(commit=False)
            animal.user = request.user
            animal.save()
            messages.success(request, 'Animal profile created successfully!')
            return redirect('animal_profiles')
    else:
        form = AnimalProfileForm()

    return render(request, 'animal_profiles.html', {
        'animals': animals,
        'form': form,
    })


@login_required
def edit_animal_profile_view(request, animal_id):
    """Edit animal profile."""
    animal = get_object_or_404(AnimalProfile, id=animal_id, user=request.user)

    if request.method == 'POST':
        form = AnimalProfileForm(request.POST, instance=animal)
        if form.is_valid():
            form.save()
            messages.success(request, 'Animal profile updated successfully!')
            return redirect('animal_profiles')
    else:
        form = AnimalProfileForm(instance=animal)

    return render(request, 'edit_animal_profile.html', {
        'form': form,
        'animal': animal,
    })


@login_required
def delete_animal_profile_view(request, animal_id):
    """Delete animal profile."""
    animal = get_object_or_404(AnimalProfile, id=animal_id, user=request.user)
    animal.delete()
    messages.success(request, 'Animal profile deleted successfully.')
    return redirect('animal_profiles')


# ============================================================
# PROFILE VIEW
# ============================================================

@login_required
def profile_view(request):
    """User profile page."""
    from .models import Order, AnimalProfile
    orders_count = Order.objects.filter(user=request.user).count()
    appointments_count = Appointment.objects.filter(user=request.user).count()
    animals_count = AnimalProfile.objects.filter(user=request.user).count()
    return render(request, 'profile.html', {
        'user': request.user,
        'orders_count': orders_count,
        'appointments_count': appointments_count,
        'animals_count': animals_count,
    })


# ============================================================
# ADMIN DASHBOARD VIEWS
# ============================================================

def is_admin(user):
    return user.is_staff or user.is_superuser


@user_passes_test(is_admin)
def admin_dashboard_view(request):
    """Admin dashboard with statistics and charts."""
    total_appointments = Appointment.objects.count()
    pending_appointments = Appointment.objects.filter(status='pending').count()
    accepted_appointments = Appointment.objects.filter(status='accepted').count()
    total_products = Product.objects.filter(is_hidden=False).count()
    out_of_stock = Product.objects.filter(stock=0, is_hidden=False).count()
    total_orders = Order.objects.count()

    today_sales = Order.objects.filter(
        created_at__date=timezone.now().date()
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0

    month_ago = timezone.now() - timedelta(days=30)
    monthly_sales = Order.objects.filter(
        created_at__gte=month_ago
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0

    now = timezone.now()
    monthly_labels = []
    monthly_data = []
    for i in range(11, -1, -1):
        m = now - timedelta(days=30 * i)
        month_start = m.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if i > 0:
            month_end = (now - timedelta(days=30 * (i - 1))).replace(day=1)
        else:
            month_end = now
        sales = Order.objects.filter(
            created_at__gte=month_start,
            created_at__lt=month_end
        ).aggregate(Sum('total_price'))['total_price__sum'] or 0
        monthly_labels.append(month_start.strftime('%b %Y'))
        monthly_data.append(float(sales))

    recent_orders = Order.objects.order_by('-created_at')[:5]

    context = {
        'total_appointments': total_appointments,
        'pending_appointments': pending_appointments,
        'accepted_appointments': accepted_appointments,
        'total_products': total_products,
        'out_of_stock': out_of_stock,
        'total_orders': total_orders,
        'today_sales': today_sales,
        'monthly_sales': monthly_sales,
        'monthly_labels': monthly_labels,
        'monthly_data': monthly_data,
        'recent_orders': recent_orders,
        'appointment_stats': {
            'pending': Appointment.objects.filter(status='pending').count(),
            'accepted': Appointment.objects.filter(status='accepted').count(),
            'completed': Appointment.objects.filter(status='completed').count(),
            'denied': Appointment.objects.filter(status='denied').count(),
        },
    }
    return render(request, 'admin/admin_dashboard.html', context)


@user_passes_test(is_admin)
def admin_appointments_view(request):
    """Admin appointments management."""
    appointments = Appointment.objects.all().order_by('-date', '-time')

    status_filter = request.GET.get('status', '')
    if status_filter:
        appointments = appointments.filter(status=status_filter)

    paginator = Paginator(appointments, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    if request.method == 'POST':
        appt_id = request.POST.get('appointment_id')
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')

        appointment = get_object_or_404(Appointment, id=appt_id)

        if action == 'accept':
            appointment.status = 'accepted'
            appointment.notes = notes
            appointment.save()
            messages.success(request, 'Appointment accepted.')
        elif action == 'deny':
            appointment.status = 'denied'
            appointment.notes = notes
            appointment.save()
            messages.success(request, 'Appointment denied.')
        elif action == 'complete':
            appointment.status = 'completed'
            appointment.notes = notes
            appointment.save()
            messages.success(request, 'Appointment marked as completed.')
        elif action == 'edit':
            new_date = request.POST.get('new_date')
            new_time = request.POST.get('new_time')
            if new_date and new_time:
                conflict = Appointment.objects.filter(
                    date=new_date, time=new_time
                ).exclude(id=appointment.id).exclude(status__in=['denied']).exists()
                if conflict:
                    messages.error(request, 'This time slot is already taken.')
                else:
                    appointment.date = new_date
                    appointment.time = new_time
                    appointment.save()
                    messages.success(request, 'Appointment rescheduled.')

        return redirect('admin_appointments')

    return render(request, 'admin/admin_appointments.html', {
        'page_obj': page_obj,
        'status_filter': status_filter,
    })


@user_passes_test(is_admin)
def admin_products_view(request):
    """Admin product management."""
    products = Product.objects.all().order_by('-created_at')

    category_filter = request.GET.get('category', '')
    if category_filter:
        products = products.filter(category_id=category_filter)

    stock_filter = request.GET.get('stock', '')
    if stock_filter == 'out':
        products = products.filter(stock=0)
    elif stock_filter == 'low':
        products = products.filter(stock__gt=0, stock__lt=5)
    elif stock_filter == 'good':
        products = products.filter(stock__gte=5)

    search_query = request.GET.get('q', '')
    if search_query:
        products = products.filter(name__icontains=search_query)

    paginator = Paginator(products, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    categories = Category.objects.all()

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Product added successfully!')
                return redirect('admin_products')
            except Exception as e:
                messages.error(request, f'Error adding product: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = ProductForm()

    return render(request, 'admin/admin_products.html', {
        'page_obj': page_obj,
        'categories': categories,
        'category_filter': category_filter,
        'stock_filter': stock_filter,
        'search_query': search_query,
        'form': form,
    })


@user_passes_test(is_admin)
def admin_edit_product_view(request, product_id):
    """Edit product."""
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.all()

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('admin_products')
    else:
        form = ProductForm(instance=product)

    return render(request, 'admin/admin_edit_product.html', {
        'form': form,
        'product': product,
        'categories': categories,
    })


@user_passes_test(is_admin)
def admin_delete_product_view(request, product_id):
    """Delete product."""
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    messages.success(request, 'Product deleted successfully.')
    return redirect('admin_products')


@user_passes_test(is_admin)
def admin_toggle_product_view(request, product_id):
    """Toggle product visibility."""
    product = get_object_or_404(Product, id=product_id)
    product.is_hidden = not product.is_hidden
    product.save()
    status = 'hidden' if product.is_hidden else 'visible'
    messages.success(request, f'Product is now {status}.')
    return redirect('admin_products')


@user_passes_test(is_admin)
def admin_products_bulk_delete_view(request):
    """Delete multiple products at once."""
    if request.method == 'POST':
        product_ids = request.POST.get('product_ids', '')
        if product_ids:
            ids_list = [id.strip() for id in product_ids.split(',') if id.strip().isdigit()]
            deleted_count = Product.objects.filter(id__in=ids_list).delete()[0]
            messages.success(request, f'{deleted_count} product(s) deleted successfully.')
    return redirect('admin_products')


@user_passes_test(is_admin)
def admin_orders_view(request):
    """Admin order management."""
    orders = Order.objects.all().order_by('-created_at')

    status_filter = request.GET.get('status', '')
    if status_filter:
        orders = orders.filter(status=status_filter)

    search_query = request.GET.get('q', '')
    if search_query:
        orders = orders.filter(
            Q(order_id__icontains=search_query) |
            Q(guest_name__icontains=search_query) |
            Q(guest_phone__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(wilaya__icontains=search_query)
        )

    paginator = Paginator(orders, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    if request.method == 'POST':
        order_id_post = request.POST.get('order_id')
        action = request.POST.get('action')
        order = get_object_or_404(Order, id=order_id_post)

        status_map = {
            'confirm': 'confirmed',
            'ship': 'shipping',
            'deliver': 'delivered',
            'cancel': 'cancelled',
        }
        if action in status_map:
            order.status = status_map[action]
            order.save()
            messages.success(request, f'Order status updated to {order.get_status_display()}.')

        return redirect('admin_orders')

    return render(request, 'admin/admin_orders.html', {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
    })


@user_passes_test(is_admin)
def admin_order_details_ajax(request, order_id):
    """AJAX endpoint to get order details for modal."""
    from django.template.loader import render_to_string
    order = get_object_or_404(Order, id=order_id)
    
    html = render_to_string('admin/order_details_modal.html', {'order': order})
    return JsonResponse({'success': True, 'html': html})


@user_passes_test(is_admin)
def admin_categories_view(request):
    """Admin category management."""
    categories = Category.objects.all().order_by('name').annotate(
        product_count=Count('products')
    )

    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Category added successfully!')
                return redirect('admin_categories')
            except Exception as e:
                messages.error(request, f'Error adding category: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CategoryForm()

    return render(request, 'admin/admin_categories.html', {
        'categories': categories,
        'form': form,
    })


@user_passes_test(is_admin)
def admin_edit_category_view(request, category_id):
    """Edit category."""
    category = get_object_or_404(Category, id=category_id)

    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('admin_categories')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CategoryForm(instance=category)

    return render(request, 'admin/admin_edit_category.html', {
        'form': form,
        'category': category,
    })


@user_passes_test(is_admin)
def admin_delete_category_view(request, category_id):
    """Delete category."""
    category = get_object_or_404(Category, id=category_id)
    category.delete()
    messages.success(request, 'Category deleted successfully.')
    return redirect('admin_categories')


@user_passes_test(is_admin)
def admin_customers_view(request):
    """Admin customer management."""
    users = User.objects.filter(is_staff=False).order_by('-date_joined')
    search_query = request.GET.get('q', '')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    total_customers = users.count()
    total_guests = Order.objects.filter(user=None).count()

    context = {
        'users': users,
        'total_customers': total_customers,
        'total_guests': total_guests,
        'search_query': search_query,
    }
    return render(request, 'admin/admin_customers.html', context)


@user_passes_test(is_admin)
def admin_customer_detail_view(request, user_id):
    """Admin customer detail with appointments and orders."""
    user = get_object_or_404(User, id=user_id)
    appointments = Appointment.objects.filter(user=user).order_by('-date', '-time')[:20]
    orders = Order.objects.filter(user=user).order_by('-created_at')[:20]
    total_appointments = Appointment.objects.filter(user=user).count()
    total_orders = Order.objects.filter(user=user).count()
    total_spent = Order.objects.filter(user=user).aggregate(Sum('total_price'))['total_price__sum'] or 0

    context = {
        'customer': user,
        'appointments': appointments,
        'orders': orders,
        'total_appointments': total_appointments,
        'total_orders': total_orders,
        'total_spent': total_spent,
    }
    return render(request, 'admin/admin_customer_detail.html', context)


@user_passes_test(is_admin)
def admin_contact_messages_view(request):
    """Admin contact messages."""
    messages_list = ContactMessage.objects.all().order_by('-created_at')
    paginator = Paginator(messages_list, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    if request.method == 'POST':
        msg_id = request.POST.get('msg_id')
        action = request.POST.get('action')
        msg = get_object_or_404(ContactMessage, id=msg_id)

        if action == 'mark_read':
            msg.is_read = True
            msg.save()
            messages.success(request, 'Message marked as read.')
        elif action == 'delete':
            msg.delete()
            messages.success(request, 'Message deleted.')
        elif action == 'share_testimonial':
            testimonial, created = Testimonial.objects.get_or_create(
                name=msg.name,
                message=msg.message,
                defaults={
                    'is_from_message': True,
                    'original_message': msg,
                    'role': '',
                    'is_active': True,
                }
            )
            if created:
                messages.success(request, 'Message shared to Testimonials!')
            else:
                messages.info(request, 'This message is already in Testimonials.')

        return redirect('admin_contact_messages')

    return render(request, 'admin/admin_contact_messages.html', {'page_obj': page_obj})


@user_passes_test(is_admin)
def admin_testimonials_view(request):
    """Admin testimonials management."""
    testimonials = Testimonial.objects.all().order_by('-created_at')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        role = request.POST.get('role', '').strip()
        message = request.POST.get('message', '').strip()
        is_active = request.POST.get('is_active') == 'on'

        if name and message:
            Testimonial.objects.create(
                name=name,
                role=role,
                message=message,
                is_active=is_active,
            )
            messages.success(request, 'Testimonial added successfully!')
            return redirect('admin_testimonials')
        else:
            messages.error(request, 'Name and message are required.')

    context = {
        'testimonials': testimonials,
    }
    return render(request, 'admin/admin_testimonials.html', context)


@user_passes_test(is_admin)
def admin_delete_testimonial_view(request, testimonial_id):
    """Delete testimonial."""
    testimonial = get_object_or_404(Testimonial, id=testimonial_id)
    testimonial.delete()
    messages.success(request, 'Testimonial deleted successfully.')
    return redirect('admin_testimonials')


@user_passes_test(is_admin)
def admin_toggle_testimonial_view(request, testimonial_id):
    """Toggle testimonial visibility."""
    testimonial = get_object_or_404(Testimonial, id=testimonial_id)
    testimonial.is_active = not testimonial.is_active
    testimonial.save()
    status = 'visible' if testimonial.is_active else 'hidden'
    messages.success(request, f'Testimonial is now {status}.')
    return redirect('admin_testimonials')


@user_passes_test(is_admin)
def admin_profile_view(request):
    """Admin profile settings page."""
    user = request.user
    profile = getattr(user, 'profile', None)

    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()

        if profile:
            profile.phone = request.POST.get('phone', '')
            profile.address = request.POST.get('address', '')
            profile.save()

        old_password = request.POST.get('old_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if new_password:
            if not old_password:
                messages.error(request, 'Please enter your current password to change it.')
                return redirect('admin_profile')
            if not user.check_password(old_password):
                messages.error(request, 'Current password is incorrect.')
                return redirect('admin_profile')
            if new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
                return redirect('admin_profile')
            user.set_password(new_password)
            user.save()
            messages.success(request, 'Password updated successfully! Please log in again with your new password.')
            return redirect('login')

        messages.success(request, 'Profile updated successfully!')
        return redirect('admin_profile')

    return render(request, 'admin/admin_profile.html', {
        'user': user,
        'profile': profile,
    })


@user_passes_test(is_admin)
def admin_sessions_view(request):
    """Admin sessions management - view user statistics."""
    from django.contrib.auth.models import User
    total_users = User.objects.count()
    total_staff = User.objects.filter(is_staff=True).count()
    superusers = User.objects.filter(is_superuser=True).count()
    active_today = User.objects.filter(last_login__date=timezone.now().date()).count()
    week_ago = timezone.now() - timedelta(days=7)
    active_week = User.objects.filter(last_login__gte=week_ago).count()
    staff_users = User.objects.filter(is_staff=True).order_by('-date_joined')

    context = {
        'total_users': total_users,
        'total_staff': total_staff,
        'superusers': superusers,
        'active_today': active_today,
        'active_week': active_week,
        'staff_users': staff_users,
    }
    return render(request, 'admin/admin_sessions.html', context)


# ============================================================
# AJAX VIEWS
# ============================================================

def search_products_ajax(request):
    """AJAX search suggestions for products."""
    query = request.GET.get('q', '')
    products = []
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query),
            is_available=True,
            is_hidden=False
        )[:8]
        products = [{'id': p.id, 'name': p.name, 'price': str(p.price)} for p in products]
    return JsonResponse({'products': products})


def add_to_cart_ajax(request, product_id):
    """AJAX add to cart - redirects to product page since cart is removed."""
    return JsonResponse({
        'success': False,
        'message': 'Cart removed. Please use the Buy Now button on the product page.',
        'redirect': True,
    })


def get_communes_ajax(request, wilaya_code):
    """AJAX endpoint to get communes for a given wilaya code."""
    import json
    import os
    from django.conf import settings

    json_path = os.path.join(settings.BASE_DIR, 'main', 'static', 'data', 'algeria_communes.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            communes_map = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return JsonResponse({'communes': []})

    communes = communes_map.get(str(wilaya_code), [])
    return JsonResponse({'communes': communes})
