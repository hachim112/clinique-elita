import os
from io import BytesIO
from PIL import Image as PILImage
from django.core.files.uploadedfile import SimpleUploadedFile

os.environ['DJANGO_SETTINGS_MODULE'] = 'clinique_elita.settings'
os.environ['DEBUG'] = 'True'
import django
django.setup()

from django.conf import settings
settings.DEBUG = True
settings.ALLOWED_HOSTS.append('testserver')

from django.test import Client
from django.contrib.auth.models import User
from main.models import Product, Category

user = User.objects.filter(is_staff=True, is_superuser=True).first()
c = Client()
c.force_login(user)

cat = Category.objects.first()

# Add product with image
img = BytesIO()
PILImage.new('RGB', (100, 100), color='red').save(img, 'JPEG')
img.seek(0)
uploaded_img = SimpleUploadedFile('prod.jpg', img.read(), content_type='image/jpeg')

resp = c.post('/panel/products/', {
    'name': 'Image Test Product',
    'description': 'Test',
    'price': '10.00',
    'stock': '5',
    'category': str(cat.id),
    'rating': '4.5',
    'is_available': 'on',
    'image': uploaded_img,
})
print(f"Add product: {resp.status_code}")

# Add category with image
img2 = BytesIO()
PILImage.new('RGB', (100, 100), color='blue').save(img2, 'JPEG')
img2.seek(0)
uploaded_img2 = SimpleUploadedFile('cat.jpg', img2.read(), content_type='image/jpeg')

resp2 = c.post('/panel/categories/', {
    'name': 'Image Test Cat',
    'slug': 'image-test-cat',
    'description': 'Test',
    'is_active': 'on',
    'image': uploaded_img2,
})
print(f"Add category: {resp2.status_code}")

# Get pages
resp3 = c.get('/panel/products/')
print(f"Products page: {resp3.status_code}")
content = resp3.content.decode()
if 'prod.jpg' in content:
    print("Product image reference found in products page")
else:
    print("WARNING: Product image NOT found in products page")
    # Show a snippet around media
    idx = content.find('products/')
    if idx >= 0:
        print("Snippet:", content[max(0,idx-50):idx+100])

resp4 = c.get('/panel/categories/')
print(f"Categories page: {resp4.status_code}")
content4 = resp4.content.decode()
if 'cat.jpg' in content4:
    print("Category image reference found in categories page")
else:
    print("WARNING: Category image NOT found in categories page")

# Home page
resp5 = c.get('/')
print(f"Home page: {resp5.status_code}")
content5 = resp5.content.decode()
if 'cat.jpg' in content5 or 'prod.jpg' in content5:
    print("Images found on home page")
else:
    print("Images NOT found on home page (might be none active)")

# Clean up
Product.objects.filter(name='Image Test Product').delete()
Category.objects.filter(name='Image Test Cat').delete()
