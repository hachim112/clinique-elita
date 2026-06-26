
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile - {self.user.get_full_name() or self.user.username}"


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('denied', 'Denied'),
        ('completed', 'Completed'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='appointments')
    guest_name = models.CharField(max_length=100, blank=True)
    guest_phone = models.CharField(max_length=20, blank=True)
    guest_email = models.EmailField(blank=True)
    animal_name = models.CharField(max_length=100)
    animal_type = models.CharField(max_length=50, choices=[
        ('dog', 'Dog'),
        ('cat', 'Cat'),
        ('bird', 'Bird'),
        ('rabbit', 'Rabbit'),
        ('exotic', 'Exotic Animal'),
        ('other', 'Other'),
    ])
    breed = models.CharField(max_length=100, blank=True)
    age = models.CharField(max_length=50, blank=True)
    reason = models.TextField()
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    tracking_id = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['date', 'time']
        ordering = ['-date', '-time']

    def __str__(self):
        name = self.user.get_full_name() if self.user else self.guest_name
        return f"Appointment - {name} - {self.date} {self.time}"


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True, help_text='Use Cloudinary or S3 for production on Vercel')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    image = models.ImageField(upload_to='products/', blank=True, null=True, help_text='Use Cloudinary or S3 for production on Vercel')
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    is_available = models.BooleanField(default=True)
    is_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='carts')
    session_key = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.user:
            return f"Cart - {self.user.username}"
        return f"Cart - Session {self.session_key[:8]}"

    @property
    def total(self):
        return sum(item.total_price for item in self.items.all())

    @property
    def item_count(self):
        return self.items.aggregate(total=Sum('quantity'))['total'] or 0


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ['cart', 'product']

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    @property
    def total_price(self):
        return self.product.price * self.quantity


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('confirmed', 'Confirmée'),
        ('shipping', 'En livraison'),
        ('delivered', 'Livrée'),
        ('cancelled', 'Annulée'),
    ]
    DELIVERY_CHOICES = [
        ('home', 'Livraison à domicile'),
        ('desk', 'Récupération au bureau / clinique'),
    ]
    WILAYA_CHOICES = [
        ('Adrar', 'Adrar'), ('Chlef', 'Chlef'), ('Laghouat', 'Laghouat'),
        ('Oum El Bouaghi', 'Oum El Bouaghi'), ('Batna', 'Batna'),
        ('Béjaïa', 'Béjaïa'), ('Biskra', 'Biskra'), ('Béchar', 'Béchar'),
        ('Blida', 'Blida'), ('Bouira', 'Bouira'), ('Tamanrasset', 'Tamanrasset'),
        ('Tébessa', 'Tébessa'), ('Tlemcen', 'Tlemcen'), ('Tiaret', 'Tiaret'),
        ('Tizi Ouzou', 'Tizi Ouzou'), ('Alger', 'Alger'), ('Djelfa', 'Djelfa'),
        ('Jijel', 'Jijel'), ('Sétif', 'Sétif'), ('Saïda', 'Saïda'),
        ('Skikda', 'Skikda'), ('Sidi Bel Abbès', 'Sidi Bel Abbès'),
        ('Annaba', 'Annaba'), ('Guelma', 'Guelma'), ('Constantine', 'Constantine'),
        ('Médéa', 'Médéa'), ('Mostaganem', 'Mostaganem'), ('M\'Sila', 'M\'Sila'),
        ('Mascara', 'Mascara'), ('Ouargla', 'Ouargla'), ('Oran', 'Oran'),
        ('El Bayadh', 'El Bayadh'), ('Illizi', 'Illizi'), ('Bordj Bou Arréridj', 'Bordj Bou Arréridj'),
        ('Boumerdès', 'Boumerdès'), ('El Tarf', 'El Tarf'), ('Tindouf', 'Tindouf'),
        ('Tissemsilt', 'Tissemsilt'), ('El Oued', 'El Oued'), ('Khenchela', 'Khenchela'),
        ('Souk Ahras', 'Souk Ahras'), ('Tipaza', 'Tipaza'), ('Mila', 'Mila'),
        ('Aïn Defla', 'Aïn Defla'), ('Naâma', 'Naâma'), ('Aïn Témouchent', 'Aïn Témouchent'),
        ('Ghardaïa', 'Ghardaïa'), ('Relizane', 'Relizane'),
        ('Timimoun', 'Timimoun'), ('Bordj Badji Mokhtar', 'Bordj Badji Mokhtar'),
        ('Ouled Djellal', 'Ouled Djellal'), ('Béni Abbès', 'Béni Abbès'),
        ('Ain Salah', 'Ain Salah'), ('Ain Guezzam', 'Ain Guezzam'),
        ('Touggourt', 'Touggourt'), ('Djanet', 'Djanet'),
        ('El M\'Ghair', 'El M\'Ghair'), ('Ménaca', 'Ménaca'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='orders')
    order_id = models.CharField(max_length=20, unique=True)
    guest_name = models.CharField(max_length=100, blank=True)
    guest_phone = models.CharField(max_length=20, blank=True)
    guest_email = models.EmailField(blank=True)
    wilaya = models.CharField(max_length=50, choices=WILAYA_CHOICES)
    commune = models.CharField(max_length=100)
    address = models.TextField()
    delivery_type = models.CharField(max_length=10, choices=DELIVERY_CHOICES, default='home')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, default='Cash On Delivery')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_id}"

    @property
    def item_count(self):
        return self.items.aggregate(total=Sum('quantity'))['total'] or 0


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=200)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"

    @property
    def total_price(self):
        return self.product_price * self.quantity


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Message from {self.name}"


class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100, blank=True)
    message = models.TextField()
    is_active = models.BooleanField(default=True)
    is_from_message = models.BooleanField(default=False)
    original_message = models.ForeignKey(ContactMessage, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Testimonial - {self.name}"


class AnimalProfile(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='animals')
    name = models.CharField(max_length=100)
    species = models.CharField(max_length=50, choices=[
        ('dog', 'Dog'),
        ('cat', 'Cat'),
        ('bird', 'Bird'),
        ('rabbit', 'Rabbit'),
        ('exotic', 'Exotic Animal'),
        ('other', 'Other'),
    ])
    breed = models.CharField(max_length=100, blank=True)
    weight = models.CharField(max_length=50, blank=True)
    age = models.CharField(max_length=50, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    vaccination_history = models.TextField(blank=True)
    medical_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Animal Profiles'

    def __str__(self):
        return f"{self.name} ({self.user.get_full_name()})"
