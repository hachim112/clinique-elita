from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Profile, Appointment, Category, Product, Cart, CartItem,
    Order, OrderItem, ContactMessage, AnimalProfile
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone']
    readonly_fields = ['created_at']


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        'tracking_id', 'get_user_name', 'animal_type', 'date', 'time', 'status'
    ]
    list_filter = ['status', 'date', 'animal_type']
    search_fields = [
        'tracking_id', 'guest_name', 'guest_email', 'guest_phone',
        'user__username', 'user__email', 'animal_name'
    ]
    ordering = ['-date', '-time']
    readonly_fields = ['created_at']

    def get_user_name(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return obj.guest_name or '-'
    get_user_name.short_description = 'Patient'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at', 'image_thumb']
    list_filter = ['is_active']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}

    def image_thumb(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:44px;height:44px;border-radius:10px;object-fit:cover;box-shadow:var(--shadow);" />',
                obj.image.url
            )
        return format_html('<div style="width:44px;height:44px;border-radius:10px;background:var(--light-gray);display:flex;align-items:center;justify-content:center;font-size:1.1rem;">📁</div>')
    image_thumb.short_description = 'Image'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'price', 'stock',
        'rating', 'is_available', 'is_hidden', 'updated_at', 'image_thumb'
    ]
    list_filter = ['category', 'is_available', 'is_hidden']
    search_fields = ['name', 'description']
    ordering = ['-created_at']

    def image_thumb(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:48px;height:48px;border-radius:10px;object-fit:cover;box-shadow:var(--shadow);" />',
                obj.image.url
            )
        return format_html('<div style="width:48px;height:48px;border-radius:10px;background:var(--light-gray);display:flex;align-items:center;justify-content:center;font-size:1.4rem;">📦</div>')
    image_thumb.short_description = 'Image'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_user_or_session', 'item_count', 'total', 'updated_at']
    list_filter = ['created_at']
    readonly_fields = ['total', 'item_count']

    def get_user_or_session(self, obj):
        if obj.user:
            return obj.user.username
        return f"Session {obj.session_key[:8]}"
    get_user_or_session.short_description = 'User/Session'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'quantity', 'total_price']
    list_filter = ['cart']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'product_price', 'quantity', 'total_price']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_id', 'get_user_name', 'wilaya', 'status', 'total_price', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = [
        'order_id', 'guest_name', 'guest_email', 'guest_phone',
        'user__username', 'user__email', 'wilaya'
    ]
    inlines = [OrderItemInline]
    readonly_fields = ['order_id', 'total_price', 'created_at', 'updated_at']

    def get_user_name(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return obj.guest_name or 'Guest'
    get_user_name.short_description = 'Customer'


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['name', 'email', 'message']
    readonly_fields = ['name', 'email', 'message', 'created_at']


@admin.register(AnimalProfile)
class AnimalProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'species', 'breed', 'user', 'age', 'gender']
    list_filter = ['species', 'gender']
    search_fields = ['name', 'user__username', 'breed']
