---
name: enferno-dev
description: |
  Development skill for Enferno Flask framework. Use when implementing features, fixing bugs, or writing code for Enferno-based applications. This includes creating models, API endpoints, Vue.js frontend components, database operations, or any development task within the Enferno ecosystem. Triggers: creating blueprints, adding models, building APIs, Vue/Vuetify components, Celery tasks, database migrations.
---

# Enferno Development

Flask + Vue 3 + Vuetify 3 framework. No build step. SQLAlchemy 2.x patterns.

## Quick Reference

```bash
uv run flask run --port 5001      # Dev server (5001 on macOS)
uv run flask create-db            # Init database
uv run flask install              # Create admin user
uv run ruff format . && uv run ruff check --fix .  # Format + lint
```

## Blueprint Structure

```
enferno/
├── feature_name/
│   ├── views.py      # Routes and API endpoints
│   ├── models.py     # SQLAlchemy models
│   └── forms.py      # WTForms (if needed)
├── templates/
│   └── feature_name/ # Jinja templates
```

Register in `app.py`:
```python
from enferno.feature_name.views import bp as feature_bp
app.register_blueprint(feature_bp)
```

## Models

Always use `BaseMixin` and implement `to_dict()`/`from_dict()`:

```python
from enferno.extensions import db
from enferno.utils.base import BaseMixin

class Product(db.Model, BaseMixin):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Numeric(10, 2))
    active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "price": float(self.price), "active": self.active}

    @staticmethod
    def from_dict(data):
        return Product(name=data.get("name"), price=data.get("price"), active=data.get("active", True))
```

## API Endpoints

Standard CRUD pattern with pagination:

```python
from flask import Blueprint, request
from flask_security import roles_required, current_user
from enferno.extensions import db
from enferno.user.models import Activity

bp = Blueprint("products", __name__, url_prefix="/api")

@bp.get("/products")
@roles_required("admin")
def list_products():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 25, type=int)
    query = db.select(Product)
    pagination = db.paginate(query, page=page, per_page=per_page)
    return {"items": [p.to_dict() for p in pagination.items], "total": pagination.total, "perPage": per_page}

@bp.post("/product/")
@roles_required("admin")
def create_product():
    data = request.json
    product = Product.from_dict(data)
    product.save()
    Activity.register(current_user.id, "Product Create", product.to_dict())
    return {"item": product.to_dict()}

@bp.post("/product/<int:id>")
@roles_required("admin")
def update_product(id):
    product = db.get_or_404(Product, id)
    old = product.to_dict()
    product.name = request.json.get("name", product.name)
    product.price = request.json.get("price", product.price)
    product.save()
    Activity.register(current_user.id, "Product Update", {"old": old, "new": product.to_dict()})
    return {"item": product.to_dict()}

@bp.delete("/product/<int:id>")
@roles_required("admin")
def delete_product(id):
    product = db.get_or_404(Product, id)
    Activity.register(current_user.id, "Product Delete", product.to_dict())
    product.delete()
    return {"deleted": True}
```

## Vue 3 + Vuetify Frontend

Uses `${}` delimiters (not `{{}}`). Mount per-page Vue apps:

```html
{% extends "layout.html" %}
{% block content %}
<div id="app">
  <v-data-table-server
    :headers="headers"
    :items="items"
    :items-length="total"
    :loading="loading"
    @update:options="loadItems"
  ></v-data-table-server>
</div>
{% endblock %}

{% block js %}
<script>
const { createApp, ref, onMounted } = Vue;
const { createVuetify } = Vuetify;

createApp({
  delimiters: ['${', '}'],
  setup() {
    const items = ref([]);
    const total = ref(0);
    const loading = ref(false);
    const headers = ref([
      { title: 'Name', key: 'name' },
      { title: 'Price', key: 'price' },
      { title: 'Actions', key: 'actions', sortable: false }
    ]);

    async function loadItems({ page, itemsPerPage }) {
      loading.value = true;
      const res = await axios.get('/api/products', { params: { page, per_page: itemsPerPage } });
      items.value = res.data.items;
      total.value = res.data.total;
      loading.value = false;
    }

    return { items, total, loading, headers, loadItems };
  }
}).use(createVuetify(vuetifyConfig)).mount('#app');
</script>
{% endblock %}
```

## Database Queries (SQLAlchemy 2.x)

```python
# Select with filter
query = db.select(User).where(User.active == True)
users = db.session.execute(query).scalars().all()

# Get or 404
user = db.get_or_404(User, id)

# Paginate
pagination = db.paginate(query, page=1, per_page=25)

# Join
query = db.select(Order).join(User).where(User.id == user_id)
```

## Activity Logging

Always log admin actions:

```python
from enferno.user.models import Activity

Activity.register(current_user.id, "Action Name", {"relevant": "data"})
```

## Celery Tasks

Define in `enferno/tasks/views.py`:

```python
from enferno.extensions import celery

@celery.task
def process_order(order_id):
    # task logic
    pass
```

## Patterns Reference

For detailed patterns and examples, see [references/patterns.md](references/patterns.md).
