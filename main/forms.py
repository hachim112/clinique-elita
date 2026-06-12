
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import (
    Appointment, Product, Category, Order, OrderItem,
    ContactMessage, AnimalProfile, Profile, CartItem
)
import datetime


class CustomUserCreationForm(UserCreationForm):
    """Custom registration form with additional fields."""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    phone = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            Profile.objects.create(
                user=user,
                phone=self.cleaned_data.get('phone', '')
            )
        return user


class AppointmentForm(forms.ModelForm):
    """Appointment booking form for registered users."""
    class Meta:
        model = Appointment
        fields = ['animal_name', 'animal_type', 'breed', 'age', 'reason', 'date', 'time']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'min': ''}),
            'time': forms.Select(),
            'reason': forms.Textarea(attrs={'rows': 4}),
        }


class GuestAppointmentForm(forms.ModelForm):
    """Appointment booking form for guests (no account required)."""
    class Meta:
        model = Appointment
        fields = [
            'guest_name', 'guest_phone', 'guest_email',
            'animal_name', 'animal_type', 'breed', 'age',
            'reason', 'date', 'time'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.Select(),
            'reason': forms.Textarea(attrs={'rows': 4}),
        }


class ProductForm(forms.ModelForm):
    """Admin product form."""
    rating = forms.DecimalField(
        max_digits=3,
        decimal_places=2,
        required=False,
        initial=0.0,
        widget=forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '5.00', 'class': 'form-control'})
    )

    class Meta:
        model = Product
        fields = [
            'name', 'description', 'price', 'stock', 'category',
            'image', 'rating', 'is_available', 'is_hidden'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating is None:
            return self._meta.model._meta.get_field('rating').default
        return rating


class CategoryForm(forms.ModelForm):
    """Admin category form."""
    slug = forms.CharField(max_length=100, required=False, help_text='Leave blank to auto-generate from name')

    class Meta:
        model = Category
        fields = ['name', 'slug', 'description', 'image', 'is_active']

    def clean_slug(self):
        from django.utils.text import slugify
        slug = self.cleaned_data.get('slug', '').strip()
        if not slug:
            slug = slugify(self.cleaned_data.get('name', ''))
        if not slug:
            slug = 'category'
        unique_slug = slug
        counter = 1
        while Category.objects.filter(slug=unique_slug).exclude(pk=self.instance.pk).exists():
            unique_slug = f"{slug}-{counter}"
            counter += 1
        return unique_slug


class ContactForm(forms.ModelForm):
    """Contact page form."""
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5}),
        }


class CheckoutForm(forms.Form):
    """Guest checkout form."""
    name = forms.CharField(max_length=100, label="Nom complet")
    phone = forms.CharField(max_length=20, label="Téléphone")
    wilaya = forms.ChoiceField(choices=Order.WILAYA_CHOICES, label="Wilaya")
    commune = forms.CharField(max_length=100, label="Commune")
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label="Adresse de livraison")
    delivery_type = forms.ChoiceField(
        choices=Order.DELIVERY_CHOICES,
        widget=forms.RadioSelect,
        label="Type de livraison",
        initial='home'
    )
    notes = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False, label="Notes (optionnel)")


class AnimalProfileForm(forms.ModelForm):
    """Pet profile form for registered users."""
    class Meta:
        model = AnimalProfile
        fields = [
            'name', 'species', 'breed', 'weight', 'age',
            'gender', 'vaccination_history', 'medical_notes'
        ]
        widgets = {
            'vaccination_history': forms.Textarea(attrs={'rows': 4}),
            'medical_notes': forms.Textarea(attrs={'rows': 4}),
        }


class AdminOrderStatusForm(forms.Form):
    """Admin order status update form."""
    status = forms.ChoiceField(choices=Order.STATUS_CHOICES)


class AdminAppointmentStatusForm(forms.Form):
    """Admin appointment status update form."""
    status = forms.ChoiceField(choices=Appointment.STATUS_CHOICES)
    notes = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
