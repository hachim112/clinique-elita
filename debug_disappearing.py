import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'clinique_elita.settings'
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from main.models import Category, Product

user = User.objects.filter(is_staff=True, is_superuser=True).first()
c = Client()
c.force_login(user)

# Test adding category
print("=== Testing Category Addition ===")
resp = c.post('/panel/categories/', {
    'name': 'Test Cat Debug',
    'slug': 'test-cat-debug',
    'description': 'Debug test category',
    'is_active': 'on',
})
print(f"Status: {resp.status_code}")
print(f"Redirect: {resp.url if hasattr(resp, 'url') else 'N/A'}")

cat = Category.objects.filter(name='Test Cat Debug').first()
if cat:
    print(f"Category exists: {cat.name}")
    print(f"Category active: {cat.is_active}")
else:
    print("ERROR: Category NOT created!")

# Test adding product
print("\n=== Testing Product Addition ===")
cat2 = Category.objects.first()
resp2 = c.post('/panel/products/', {
    'name': 'Test Prod Debug',
    'description': 'Debug test product',
    'price': '1000.00',
    'stock': '10',
    'category': str(cat2.id),
    'rating': '4.5',
    'is_available': 'on',
})
print(f"Status: {resp2.status_code}")
print(f"Redirect: {resp2.url if hasattr(resp2, 'url') else 'N/A'}")

prod = Product.objects.filter(name='Test Prod Debug').first()
if prod:
    print(f"Product exists: {prod.name}")
    print(f"Product active: {prod.is_available}")
    print(f"Product stock: {prod.stock}")
else:
    print("ERROR: Product NOT created!")

# Check if items persisted in DB
all_cats = Category.objects.all()
print(f"\nTotal categories: {all_cats.count()}")
print(f"Category names: {[c.name for c in all_cats]}")

all_prods = Product.objects.all()
print(f"Total products: {all_prods.count()}")
print(f"Product names: {[p.name for p in all_prods]}")

# Clean up
if cat:
    cat.delete()
if prod:
    prod.delete()
print("\nCleaned up test data")
