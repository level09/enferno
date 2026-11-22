---
name: enferno-dev
description: |
  Development skill for the Enferno Flask framework. Use when implementing features, fixing bugs, or writing code in Enferno-based applications: blueprints, SQLAlchemy models and migrations, admin JSON APIs, Vue 3 + Vuetify pages without a build step, Flask-Security auth, Celery tasks, and dependency upgrades.
---

# Enferno Development

Flask 3 + SQLAlchemy 2.x + Vue 3 + Vuetify 4. No frontend build step. `uv` for everything.

## Quick Reference

```bash
uv run flask run --port 5001                      # Dev server (5001 on macOS)
uv run flask create-db                            # Create tables and stamp migrations
uv run flask install                              # Create admin user
uv run flask db migrate -m "msg"                  # Draft migration, review before upgrade
uv run flask db upgrade                           # Apply migrations
uv run pytest                                     # Routes, auth, admin API, migrations, setup.sh
uv run ruff check . && uv run ruff format .       # Lint + format
```

## Blueprint Structure

```
enferno/
├── feature_name/
│   ├── views.py      # Page routes and /api/ endpoints
│   ├── models.py     # SQLAlchemy models
│   └── forms.py      # WTForms (if needed)
└── templates/feature_name/
```

Register in `register_blueprints()` in `enferno/app.py`:

```python
from enferno.feature_name.views import bp as feature_bp

app.register_blueprint(feature_bp)
```

## Models

Use `BaseMixin` (`save()`/`delete()`) and implement `to_dict()`/`from_dict()`. After changing models, run `flask db migrate` and review the generated revision.

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
        return {"id": self.id, "name": self.name, "price": float(self.price or 0), "active": self.active}

    def from_dict(self, data):
        self.name = data.get("name", self.name)
        self.price = data.get("price", self.price)
        self.active = data.get("active", self.active)
        return self
```

## API Endpoints

Protect the whole blueprint in `before_request`. Payloads are `{"item": {...}}`; lists return `items`, `total`, `perPage`. Log admin actions with `Activity.register`, which commits: leave the change pending (`flush()` for a new row's id) so the change and its audit entry are saved together or not at all. Errors under `/api/` return `{"message": ...}` JSON from the app-level handler.

```python
from flask import Blueprint, render_template, request
from flask_security import auth_required, current_user, roles_required

from enferno.extensions import db
from enferno.user.models import Activity
from enferno.utils.tables import table_response

bp = Blueprint("products", __name__)


@bp.before_request
@auth_required("session")
@roles_required("admin")
def before_request():
    pass


@bp.get("/products/")
def products_page():
    return render_template("products/index.html")


@bp.get("/api/products")
def list_products():
    # Paging, ?sort_by= (only the columns named here) and ?q= search
    return table_response(
        db.select(Product).order_by(Product.id),
        sortable={"name": Product.name, "price": Product.price},
        searchable=(Product.name,),
    )


@bp.post("/api/product/")
def create_product():
    product = Product().from_dict(request.json.get("item", {}))
    db.session.add(product)
    db.session.flush()
    Activity.register(current_user.id, "Product Create", product.to_dict())
    return {"item": product.to_dict()}


@bp.post("/api/product/<int:id>")
def update_product(id):
    product = db.get_or_404(Product, id)
    old = product.to_dict()
    product.from_dict(request.json.get("item", {}))
    Activity.register(current_user.id, "Product Update", {"old": old, "new": product.to_dict()})
    return {"item": product.to_dict()}


@bp.delete("/api/product/<int:id>")
def delete_product(id):
    product = db.get_or_404(Product, id)
    data = product.to_dict()
    db.session.delete(product)
    Activity.register(current_user.id, "Product Delete", data)
    return {"deleted": True}
```

## Pages (Vue 3 + Vuetify)

`layout.html` owns `<v-app>`, the nav and the `#app` mount point. A page fills `{% block content %}` and mounts its app in `{% block js %}` with `layoutMixin` and `registerEnfernoComponents`, or the nav breaks. Vue expressions use `${ }`; `{{ }}` is Jinja.

Data tables use `crudMixin` (`static/js/crud.js`) on the page and `table_response()` (`enferno/utils/tables.py`) on the server. Together they give paging, sorting, search, a skeleton while loading, an edit dialog that works on a copy, saves that keep the dialog open on failure, and an in-app delete confirmation. `cms/roles.html` is the smallest complete example. `layoutMixin` also provides `notify(message)`, `await confirmAction(message)` and `formatDate(iso)` for any page.

```html
{% extends "layout.html" %}
{% block content %}
<v-card class="ma-2 mt-12 w-100">
  <v-card-text>
    <v-data-table-server :headers="headers" :items="items" :items-length="itemsLength"
                         :loading="loading" :search="search" @update:options="refresh">
      <template v-slot:top>
        <v-text-field v-model="search" placeholder="Search" prepend-inner-icon="ti-search"
                      density="compact" variant="outlined" hide-details clearable max-width="320"></v-text-field>
      </template>
      <template v-slot:loading><v-skeleton-loader type="table-row@5"></v-skeleton-loader></template>
      <template v-slot:item.actions="{ item }">
        <v-btn icon="ti-pencil" variant="text" aria-label="Edit" @click="editItem(item)"></v-btn>
        <v-btn icon="ti-trash" variant="text" aria-label="Delete" @click="deleteItem(item, item.name)"></v-btn>
      </template>
    </v-data-table-server>
  </v-card-text>
</v-card>

<v-dialog v-model="edialog" width="600">
  <v-card v-if="edialog" :title="eitem.id ? 'Edit Product' : 'Add Product'">
    <v-card-text><v-text-field label="Name" v-model="eitem.name"></v-text-field></v-card-text>
    <v-card-actions>
      <v-spacer></v-spacer>
      <v-btn :loading="saving" color="primary" variant="elevated" @click="saveItem">Save</v-btn>
    </v-card-actions>
  </v-card>
</v-dialog>
{% endblock %}

{% block js %}
<script>
const app = Vue.createApp({
  mixins: [layoutMixin, crudMixin({list: '/api/products', item: '/api/product/'})],
  delimiters: config.delimiters,
  data() {
    return {headers: [{title: 'Name', key: 'name'}, {title: 'Actions', key: 'actions', sortable: false}]};
  },
});
registerEnfernoComponents(app);
app.use(Vuetify.createVuetify(config.vuetifyConfig)).mount('#app');
</script>
{% endblock %}
```

Templates are parsed by the browser before Vue sees them: put `<tr>`/`<thead>` rows inside a `<template>` within `<v-table>`, or the parser moves them out. Pages without their own app (error pages) get a default mount from `layout.html`; a page that overrides `{% block js %}` must mount its own, because `#app` stays hidden (`v-cloak`) until Vue mounts.

The hard rules (Tabler icons, POST logout, CSRF, no state writes in computed, Vuetify 4 classes, cascade layers) live in `AGENTS.md`. `tests/test_conventions.py` enforces the ones a scan can check. Icon-only buttons also need an `aria-label`.

## Queries (SQLAlchemy 2.x)

```python
users = db.session.execute(db.select(User).where(User.active == True)).scalars().all()
user = db.get_or_404(User, id)
pagination = db.paginate(db.select(User), page=1, per_page=25)
orders = db.session.execute(db.select(Order).join(User).where(User.id == user_id)).scalars().all()
```

## Celery Tasks

Optional (`uv sync --extra full`). `enferno.tasks.celery` is `None` when Celery is not installed or configured.

```python
from enferno.tasks import celery


@celery.task
def process_order(order_id):
    ...
```

## Dependency Upgrades

`uv lock --upgrade && uv sync --extra dev --extra full`, then `uv run --with pip-audit pip-audit` and `uv run pytest`. Bump vendored JS by editing the pins in `vendor.sh` and running it. Read the Flask-Security changelog for changed defaults, and load an admin page in a real browser: a Vue upgrade once froze admin pages while every Python check passed.

## More Patterns

Relationships, forms, uploads, search/filtering, dialogs and error handling: [references/patterns.md](references/patterns.md).
