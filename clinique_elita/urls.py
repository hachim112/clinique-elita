import os
from django.contrib import admin
from django.urls import path, re_path
from django.shortcuts import redirect
from django.conf.urls.static import static
from django.conf import settings
from django.views.static import serve as static_serve
from main import views

# Override Django admin login to redirect to our shared login page
from django.contrib.admin import AdminSite
_original_login = AdminSite.login
def _patched_login(self, request, extra_context=None):
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return _original_login(self, request, extra_context)
    return redirect('/login/?next=/panel/')
AdminSite.login = _patched_login

urlpatterns = [
    path('', views.home_view, name='home'),
    path('home/', views.home_view, name='home_page'),
    path('services/', views.services_view, name='services'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('appointments/', views.appointments_view, name='appointments'),
    path('appointments/cancel/<int:appt_id>/', views.cancel_appointment_view, name='cancel_appointment'),
    path('appointments/track/', views.track_appointment_view, name='track_appointment'),
    path('ajax/available-slots/', views.get_available_slots_ajax, name='get_available_slots_ajax'),
    path('ajax/communes/<str:wilaya_code>/', views.get_communes_ajax, name='get_communes_ajax'),
    path('shop/', views.pet_shop_view, name='shop'),
    path('pet-shop/', views.pet_shop_view, name='pet_shop'),
    path('product/<int:product_id>/', views.product_detail_view, name='product_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('ajax/add-to-cart/<int:product_id>/', views.add_to_cart_ajax, name='add_to_cart_ajax'),
    path('buy/<int:product_id>/', views.direct_buy_view, name='direct_buy'),
    path('ajax/search-products/', views.search_products_ajax, name='search_products_ajax'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('orders/', views.my_orders_view, name='my_orders'),
    path('order/<int:order_id>/track/', views.order_tracking_view, name='order_tracking'),
    path('animals/', views.animal_profiles_view, name='animal_profiles'),
    path('animals/edit/<int:animal_id>/', views.edit_animal_profile_view, name='edit_animal_profile'),
    path('animals/delete/<int:animal_id>/', views.delete_animal_profile_view, name='delete_animal_profile'),
    path('panel/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-panel/', views.admin_dashboard_view, name='admin_panel'),
    path('admin/panel/', views.admin_dashboard_view, name='admin_panel_from_admin'),
    path('panel/appointments/', views.admin_appointments_view, name='admin_appointments'),
    path('panel/products/', views.admin_products_view, name='admin_products'),
    path('panel/products/edit/<int:product_id>/', views.admin_edit_product_view, name='admin_edit_product'),
    path('panel/products/delete/<int:product_id>/', views.admin_delete_product_view, name='admin_delete_product'),
    path('panel/products/bulk-delete/', views.admin_products_bulk_delete_view, name='admin_products_bulk_delete'),
    path('panel/products/toggle/<int:product_id>/', views.admin_toggle_product_view, name='admin_toggle_product'),
    path('panel/orders/', views.admin_orders_view, name='admin_orders'),
    path('panel/orders/<int:order_id>/details/', views.admin_order_details_ajax, name='admin_order_details_ajax'),
    path('panel/categories/', views.admin_categories_view, name='admin_categories'),
    path('panel/categories/edit/<int:category_id>/', views.admin_edit_category_view, name='admin_edit_category'),
    path('panel/categories/delete/<int:category_id>/', views.admin_delete_category_view, name='admin_delete_category'),
    path('panel/customers/', views.admin_customers_view, name='admin_customers'),
    path('panel/customers/<int:user_id>/', views.admin_customer_detail_view, name='admin_customer_detail'),
    path('panel/messages/', views.admin_contact_messages_view, name='admin_contact_messages'),
    path('panel/testimonials/', views.admin_testimonials_view, name='admin_testimonials'),
    path('panel/testimonials/delete/<int:testimonial_id>/', views.admin_delete_testimonial_view, name='admin_delete_testimonial'),
    path('panel/testimonials/toggle/<int:testimonial_id>/', views.admin_toggle_testimonial_view, name='admin_toggle_testimonial'),
    path('panel/profile/', views.admin_profile_view, name='admin_profile'),
    path('panel/sessions/', views.admin_sessions_view, name='admin_sessions'),
    path('admin/', admin.site.urls),
]

urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', static_serve, {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG or os.environ.get('VERCEL'):
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
