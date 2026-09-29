---
name: enferno-dev
description: |
  Development skill for the Enferno Flask framework. Use when implementing features, fixing bugs, or writing code in Enferno-based applications: blueprints, SQLAlchemy models and migrations, admin JSON APIs, Vue 3 + Vuetify pages without a build step, Flask-Security auth, Celery tasks, and dependency upgrades.
---

# Enferno Development

Flask 3 + SQLAlchemy 2.x + Vue 3 + Vuetify 3. No frontend build step. `uv` for everything.

## Quick Reference

```bash
uv run flask run --port 5001                      # Dev server (5001 on macOS)
uv run flask create-db                            # Create tables and stamp migrations
uv run flask install                              # Create admin user
uv run flask db migrate -m "msg"                  # Draft migration, review before upgrade
uv run flask db upgrade                           # Apply migrations
uv run python checks.py                           # Boot, DB, routes, login/logout smoke checks
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

Protect the whole blueprint in `before_request`. Payloads are `{"item": {...}}`; lists return `items`, `total`, `perPage`. Log admin actions with `Activity.register`.

```python
from flask import Blueprint, render_template, request
from flask_security import auth_required, current_user, roles_required

from enferno.extensions import db
from enferno.user.models import Activity

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
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 25, type=int)
    pagination = db.paginate(db.select(Product), page=page, per_page=per_page)
    return {"items": [p.to_dict() for p in pagination.items], "total": pagination.total, "perPage": pagination.per_page}


@bp.post("/api/product/")
def create_product():
    product = Product().from_dict(request.json.get("item", {}))
    db.session.add(product)
    db.session.commit()
    Activity.register(current_user.id, "Product Create", product.to_dict())
    return {"item": product.to_dict()}


@bp.post("/api/product/<int:id>")
def update_product(id):
    product = db.get_or_404(Product, id)
    old = product.to_dict()
    product.from_dict(request.json.get("item", {}))
    db.session.commit()
    Activity.register(current_user.id, "Product Update", {"old": old, "new": product.to_dict()})
    return {"item": product.to_dict()}


@bp.delete("/api/product/<int:id>")
def delete_product(id):
    product = db.get_or_404(Product, id)
    Activity.register(current_user.id, "Product Delete", product.to_dict())
    db.session.delete(product)
    db.session.commit()
    return {"deleted": True}
```

## Pages (Vue 3 + Vuetify)

`layout.html` owns `<v-app>`, the nav and the `#app` mount point. A page fills `{% block content %}` and mounts its app in `{% block js %}` with `layoutMixin` and `registerEnfernoComponents`, or the nav breaks. Vue expressions use `${ }`; `{{ }}` is Jinja.

```html
{% extends "layout.html" %}
{% block content %}
<v-card class="ma-2 mt-12 w-100">
  <v-card-text>
    <v-data-table-server :headers="headers" :items="items" :items-length="total"
                         :loading="loading" @update:options="loadItems">
      <template v-slot:item.actions="{ item }">
        <v-btn icon="ti-pencil" variant="text" @click="editItem(item)"></v-btn>
      </template>
    </v-data-table-server>
  </v-card-text>
</v-card>
{% endblock %}

{% block js %}
<script type="application/json" id="categories-data">{{ categories|tojson|safe }}</script>
<script>
const { createApp } = Vue;
const vuetify = Vuetify.createVuetify(config.vuetifyConfig);

const app = createApp({
  mixins: [layoutMixin],
  delimiters: config.delimiters,
  data() {
    return {
      items: [], total: 0, loading: false,
      categories: JSON.parse(document.querySelector('#categories-data').textContent),
      headers: [
        { title: 'Name', key: 'name' },
        { title: 'Actions', key: 'actions', sortable: false },
      ],
    };
  },
  methods: {
    async loadItems({ page, itemsPerPage }) {
      this.loading = true;
      const res = await axios.get('/api/products', { params: { page, per_page: itemsPerPage } });
      this.items = res.data.items;
      this.total = res.data.total;
      this.loading = false;
    },
    editItem(item) { /* open dialog */ },
  },
});

registerEnfernoComponents(app);
app.use(vuetify).mount('#app');
</script>
{% endblock %}
```

Rules:
- Icons are Tabler only: `ti-*` names (`icon="ti-pencil"`, `<i class="ti ti-user">`). Never `mdi-*`; it renders blank.
- Logout is POST-only: `<form method="post" action="/logout"><v-btn type="submit">Logout</v-btn></form>`, never `href="/logout"`.
- Pass server data through a `<script type="application/json">` tag and `|tojson`, never by interpolating into JS.
- Never mutate reactive state inside a computed property. It loops forever on Vue 3.5.

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

`uv lock --upgrade && uv sync --extra dev --extra full`, then `uv run --with pip-audit pip-audit` and `uv run python checks.py`. Read the Flask-Security changelog for changed defaults, and load an admin page in a real browser: a Vue upgrade once froze admin pages while every Python check passed.

## More Patterns

Relationships, forms, uploads, search/filtering, dialogs and error handling: [references/patterns.md](references/patterns.md).
