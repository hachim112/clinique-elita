import os
import django
import requests
from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image as PILImage

os.environ['DJANGO_SETTINGS_MODULE'] = 'clinique_elita.settings'
django.setup()

from main.models import Category, Product

# Reliable image URLs from various CDN sources
IMAGE_URLS = {
    'cat_alimentation': 'https://images.pexels.com/photos/8434635/pexels-photo-8434635.jpeg',
    'cat_jouets': 'https://images.pexels.com/photos/125637/pexels-photo-125637.jpeg',
    'cat_habitat': 'https://images.pexels.com/photos/2558605/pexels-photo-2558605.jpeg',
    'cat_hygiene': 'https://images.pexels.com/photos/5737454/pexels-photo-5737454.jpeg',
    'prod_croquettes': 'https://images.pexels.com/photos/34952079/pexels-photo-34952079.jpeg',
    'prod_patee': 'https://images.pexels.com/photos/16112165/pexels-photo-16112165.jpeg',
    'prod_graines': 'https://images.pexels.com/photos/162940/pexels-photo-162940.jpeg',
    'prod_jouet_chien': 'https://images.pexels.com/photos/125637/pexels-photo-125637.jpeg',
    'prod_arbre_chat': 'https://images.pexels.com/photos/2558605/pexels-photo-2558605.jpeg',
    'prod_balancoire': 'https://images.pexels.com/photos/162940/pexels-photo-162940.jpeg',
    'prod_panier': 'https://images.pexels.com/photos/125637/pexels-photo-125637.jpeg',
    'prod_bac_litiere': 'https://images.pexels.com/photos/2065208/pexels-photo-2065208.jpeg',
    'prod_cage': 'https://images.pexels.com/photos/162940/pexels-photo-162940.jpeg',
    'prod_shampoing': 'https://images.pexels.com/photos/5737454/pexels-photo-5737454.jpeg',
    'prod_antiparasitaire': 'https://images.pexels.com/photos/5737428/pexels-photo-5737428.jpeg',
    'prod_brosse': 'https://images.pexels.com/photos/5737454/pexels-photo-5737454.jpeg',
}

def download_image(url, name):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; Django/4.2)'}
        resp = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
        print(f"  {name}: HTTP {resp.status_code}, content-type: {resp.headers.get('content-type', 'unknown')}, size: {len(resp.content)} bytes")
        if resp.status_code == 200 and len(resp.content) > 5000:
            img = PILImage.open(BytesIO(resp.content))
            if img.mode in ('RGBA', 'LA'):
                img = img.convert('RGB')
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            return ContentFile(buffer.getvalue()), f'{name}.jpg'
        else:
            print(f"    -> Skipped (too small or wrong status)")
    except Exception as e:
        print(f"  {name}: ERROR - {e}")
    return None, f'{name}.jpg'

# Clean up old example data
Category.objects.filter(name__in=['Alimentation', 'Jouets et Accessoires', 'Habitat et Équipement', 'Hygiène et Soins']).delete()

# Download images
print("Downloading images...")
downloaded = {}
for key, url in IMAGE_URLS.items():
    content, fname = download_image(url, key)
    if content:
        downloaded[key] = content
    else:
        downloaded[key] = None

# Create categories
print("\nCreating categories...")
cat1 = Category.objects.create(
    name='Alimentation', slug='alimentation',
    description='Alimentation pour chiens, chats et oiseaux - croquettes, pâtée et graines',
    is_active=True,
)
if downloaded['cat_alimentation']:
    cat1.image.save('alimentation.jpg', downloaded['cat_alimentation'], save=True)
print(f"  Alimentation: image={'yes' if cat1.image else 'no'}")

cat2 = Category.objects.create(
    name='Jouets et Accessoires', slug='jouets-accessoires',
    description='Jouets et accessoires pour le bonheur de vos animaux',
    is_active=True,
)
if downloaded['cat_jouets']:
    cat2.image.save('jouets.jpg', downloaded['cat_jouets'], save=True)
print(f"  Jouets: image={'yes' if cat2.image else 'no'}")

cat3 = Category.objects.create(
    name='Habitat et Équipement', slug='habitat-equipement',
    description="Équipements et accessoires pour l'habitat de vos animaux",
    is_active=True,
)
if downloaded['cat_habitat']:
    cat3.image.save('habitat.jpg', downloaded['cat_habitat'], save=True)
print(f"  Habitat: image={'yes' if cat3.image else 'no'}")

cat4 = Category.objects.create(
    name='Hygiène et Soins', slug='hygiene-soins',
    description="Produits d'hygiène et de soins pour vos animaux de compagnie",
    is_active=True,
)
if downloaded['cat_hygiene']:
    cat4.image.save('hygiene.jpg', downloaded['cat_hygiene'], save=True)
print(f"  Hygiène: image={'yes' if cat4.image else 'no'}")

# Create products
print("\nCreating products...")
products = [
    (cat1, 'Croquettes pour chien', 'Croquettes premium pour chien - sac 10kg', 4500, 25, 'prod_croquettes'),
    (cat1, 'Pâtée pour chat', 'Pâtée gourmande pour chat - lot de 12 boîtes', 1200, 40, 'prod_patee'),
    (cat1, 'Graines pour oiseaux', 'Mélange de graines pour oiseaux - sachet 1kg', 800, 30, 'prod_graines'),
    (cat2, 'Jouet à mâcher pour chien', 'Jouet résistant pour chien - caoutchouc naturel', 950, 20, 'prod_jouet_chien'),
    (cat2, 'Arbre à chat', 'Arbre à chat avec griffoirs - hauteur 120cm', 6500, 8, 'prod_arbre_chat'),
    (cat2, 'Balançoire pour oiseaux', 'Balançoire colorée pour oiseaux - perchoir', 600, 15, 'prod_balancoire'),
    (cat3, 'Panier pour chien', 'Panier confortable pour chien - taille L', 2800, 12, 'prod_panier'),
    (cat3, 'Bac à litière pour chat', 'Bac à litière fermé avec filtre - couleur grise', 3200, 10, 'prod_bac_litiere'),
    (cat3, 'Cage pour oiseaux', 'Cage spacieuse pour oiseaux - 60x40x50cm', 5500, 6, 'prod_cage'),
    (cat4, 'Shampoing pour animaux', 'Shampoing doux pour chiens et chats - 250ml', 1100, 18, 'prod_shampoing'),
    (cat4, 'Traitement antiparasitaire', 'Traitement antipuces et tiques - pipettes', 1800, 22, 'prod_antiparasitaire'),
    (cat4, 'Brosse de toilettage', 'Brosse professionnelle pour chiens et chats', 750, 35, 'prod_brosse'),
]

for cat, name, desc, price, stock, img_key in products:
    p = Product.objects.create(
        name=name, description=desc, price=price, stock=stock,
        category=cat, is_available=True, rating=4.5,
    )
    if downloaded.get(img_key):
        p.image.save(f'{img_key}.jpg', downloaded[img_key], save=True)
    print(f"  {p.name} ({cat.name}): image={'yes' if p.image else 'no'}")

print("\n=== Summary ===")
print(f"Categories: {Category.objects.count()}")
for c in Category.objects.all().order_by('name'):
    print(f"  - {c.name}: {c.products.count()} products, image={'yes' if c.image else 'no'}")
print(f"Products: {Product.objects.count()}")
