import os
import json
from flask import Flask, render_template, request, redirect, url_for, abort
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Initialize Flask app
app = Flask(__name__)

# Load a lightweight pre-trained model for generating vector embeddings
# 'all-MiniLM-L6-v2' is fast and efficient for product descriptions
# This will download on first run (approx 80MB)
try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception as e:
    print(f"Error loading model: {e}")
    # Fallback for environment issues
    model = None

# Mock Database: Product Catalog
PRODUCTS = [
    {
        "id": "1",
        "name": "Titanium Professional Drill Set",
        "description": "21-piece high-speed titanium coated drill bit set. Perfect for wood, metal, and plastic. Includes heavy-duty carrying case.",
        "image": "https://images.unsplash.com/photo-1504148455328-c376907d081c?auto=format&fit=crop&q=80&w=300",
        "category": "Power Tools"
    },
    {
        "id": "2",
        "name": "Ergonomic Office Chair",
        "description": "High-back mesh chair with adjustable lumbar support and headrest. Breathable material for long working hours.",
        "image": "https://images.unsplash.com/photo-1505797149-43b00766a9d7?auto=format&fit=crop&q=80&w=300",
        "category": "Furniture"
    },
    {
        "id": "3",
        "name": "Smart Wireless Earbuds",
        "description": "Active noise canceling Bluetooth earbuds with 30-hour battery life. Water-resistant design for gym and outdoors.",
        "image": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?auto=format&fit=crop&q=80&w=300",
        "category": "Electronics"
    },
    {
        "id": "4",
        "name": "Concrete Mixing Tool",
        "description": "Electric hand-held mortar mixer with adjustable speed. Ideal for mixing thinset, grout, and concrete.",
        "image": "https://images.unsplash.com/photo-1581235720704-06d3acfcb36f?auto=format&fit=crop&q=80&w=300",
        "category": "Power Tools"
    },
    {
        "id": "5",
        "name": "Standing Desk Converter",
        "description": "Sit-to-stand height adjustable workstation. Converts any table into a standing desk. Spacious top for dual monitors.",
        "image": "https://images.unsplash.com/photo-1591123120675-6f7f1aae0e5b?auto=format&fit=crop&q=80&w=300",
        "category": "Furniture"
    },
    {
        "id": "6",
        "name": "Noise Canceling Headphones",
        "description": "Over-ear wireless headphones with premium audio and immersive sound. Built-in microphone for crystal clear calls.",
        "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&q=80&w=300",
        "category": "Electronics"
    },
    {
        "id": "7",
        "name": "Handheld Circular Saw",
        "description": "Compact circular saw with laser guide. Powerful motor for straight cuts through thick timber and plywood.",
        "image": "https://images.unsplash.com/photo-1530124560676-4ac8274f4b9c?auto=format&fit=crop&q=80&w=300",
        "category": "Power Tools"
    }
]

# Pre-calculate embeddings for all products on startup
print("Encoding product catalog into vectors...")
if model:
    for product in PRODUCTS:
        text_to_encode = f"{product['name']} {product['description']}"
        product['vector'] = model.encode(text_to_encode)

def get_recommendations(query_vector, exclude_id=None, top_k=3):
    """Computes cosine similarity between query and product vectors."""
    similarities = []
    for product in PRODUCTS:
        if exclude_id and product['id'] == exclude_id:
            continue
        
        sim = cosine_similarity(
            [query_vector], 
            [product['vector']]
        )[0][0]
        
        similarities.append({
            "product": product,
            "score": float(sim)
        })
    
    similarities.sort(key=lambda x: x['score'], reverse=True)
    return similarities[:top_k]

# --- HTML Templates ---
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VectorShop - AI Product Search</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .hero { background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%); color: white; padding: 4rem 0; }
        .card { border: none; border-radius: 12px; transition: transform 0.2s; height: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        .card:hover { transform: translateY(-5px); }
        .card-img-top { height: 200px; object-fit: cover; border-top-left-radius: 12px; border-top-right-radius: 12px; }
        .search-container { margin-top: -30px; }
        .badge-score { font-size: 0.8rem; background: #e0e7ff; color: #4338ca; }
        .product-meta { font-size: 0.85rem; color: #6b7280; }
    </style>
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand fw-bold" href="/">VectorShop</a>
        </div>
    </nav>
    {% block content %}{% endblock %}
    <footer class="py-4 mt-5 bg-white border-top text-center text-muted">
        <p>&copy; 2026 VectorShop - AI Semantic Search</p>
    </footer>
</body>
</html>
"""

INDEX_HTML = """
{% extends "layout" %}
{% block content %}
<div class="hero text-center">
    <div class="container">
        <h1 class="display-4 fw-bold">Semantic Product Discovery</h1>
        <p class="lead">Search using meaning, not just keywords.</p>
    </div>
</div>
<div class="container search-container">
    <div class="row justify-content-center">
        <div class="col-md-8">
            <div class="bg-white p-4 rounded-4 shadow-sm">
                <form action="/search" method="GET" class="d-flex gap-2">
                    <input type="text" name="q" class="form-control form-control-lg" placeholder="Try 'something to listen to music'..." required>
                    <button type="submit" class="btn btn-primary btn-lg">Search</button>
                </form>
            </div>
        </div>
    </div>
</div>
<div class="container mt-5">
    <h3>Explore Catalog</h3>
    <div class="row g-4 mt-2">
        {% for p in products %}
        <div class="col-md-3">
            <div class="card">
                <img src="{{ p.image }}" class="card-img-top">
                <div class="card-body">
                    <h5 class="h6 fw-bold">{{ p.name }}</h5>
                    <a href="/product/{{ p.id }}" class="btn btn-sm btn-outline-primary w-100">Details</a>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}
"""

RESULTS_HTML = """
{% extends "layout" %}
{% block content %}
<div class="container mt-5">
    <h2>Results for "{{ query }}"</h2>
    <div class="row g-4 mt-3">
        {% for item in results %}
        <div class="col-md-4">
            <div class="card d-flex flex-row overflow-hidden">
                <img src="{{ item.product.image }}" style="width: 100px; object-fit: cover;">
                <div class="card-body">
                    <h5 class="h6 fw-bold mb-0">{{ item.product.name }}</h5>
                    <span class="badge badge-score mb-2">{{ (item.score * 100)|round(1) }}% match</span>
                    <a href="/product/{{ item.product.id }}" class="btn btn-primary btn-sm d-block">View</a>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}
"""

DETAIL_HTML = """
{% extends "layout" %}
{% block content %}
<div class="container mt-5">
    <div class="row">
        <div class="col-md-6"><img src="{{ product.image }}" class="img-fluid rounded-4 shadow"></div>
        <div class="col-md-6">
            <h1 class="fw-bold">{{ product.name }}</h1>
            <p class="lead">{{ product.description }}</p>
        </div>
    </div>
    <h3 class="mt-5">Related Products</h3>
    <div class="row g-4 mt-2">
        {% for item in recs %}
        <div class="col-md-4">
            <div class="card">
                <img src="{{ item.product.image }}" class="card-img-top">
                <div class="card-body">
                    <h5 class="h6 fw-bold">{{ item.product.name }}</h5>
                    <p class="small text-success">{{ (item.score * 100)|round(0) }}% Related</p>
                    <a href="/product/{{ item.product.id }}" class="btn btn-sm btn-link">View</a>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}
"""

# Template Mock for single-file operation
class TemplateMock:
    def from_string(self, source, name):
        from jinja2 import Environment, FunctionLoader
        env = Environment(loader=FunctionLoader(lambda x: source if x == name else HTML_LAYOUT))
        return env.get_template(name)

st_tmpl = TemplateMock()

@app.route('/')
def index():
    return st_tmpl.from_string(INDEX_HTML, "index").render(products=PRODUCTS)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    query_vector = model.encode(query)
    results = get_recommendations(query_vector, top_k=6)
    return st_tmpl.from_string(RESULTS_HTML, "results").render(results=results, query=query)

@app.route('/product/<product_id>')
def detail(product_id):
    product = next((p for p in PRODUCTS if p['id'] == product_id), None)
    recommendations = get_recommendations(product['vector'], exclude_id=product['id'], top_k=3)
    return st_tmpl.from_string(DETAIL_HTML, "detail").render(product=product, recs=recommendations)

if __name__ == '__main__':
    print("🚀 Starting Vector Search Engine...")
    app.run(debug=True, port=5000)