# Enferno Patterns Reference

Detailed patterns for common Enferno development tasks.

## Table of Contents

- [Full Blueprint Example](#full-blueprint-example)
- [Model Relationships](#model-relationships)
- [Form Handling](#form-handling)
- [File Uploads](#file-uploads)
- [Search and Filtering](#search-and-filtering)
- [Vue Components](#vue-components)
- [Dialog Patterns](#dialog-patterns)
- [Error Handling](#error-handling)

## Full Blueprint Example

Complete blueprint with models, views, and templates:

```python
# enferno/products/models.py
from enferno.extensions import db
from enferno.utils.base import BaseMixin
from datetime import datetime

class Category(db.Model, BaseMixin):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    products = db.relationship("Product", back_populates="category")

    def to_dict(self):
        return {"id": self.id, "name": self.name}

class Product(db.Model, BaseMixin):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    category = db.relationship("Category", back_populates="products")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": float(self.price) if self.price else None,
            "category": self.category.to_dict() if self.category else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "active": self.active
        }

    @staticmethod
    def from_dict(data):
        return Product(
            name=data.get("name"),
            description=data.get("description"),
            price=data.get("price"),
            category_id=data.get("category_id"),
            active=data.get("active", True)
        )
```

```python
# enferno/products/views.py
from flask import Blueprint, request, render_template
from flask_security import roles_required, current_user, login_required
from enferno.extensions import db
from enferno.user.models import Activity
from .models import Product, Category

bp = Blueprint("products", __name__)

# Page routes
@bp.get("/products/")
@login_required
def products_page():
    return render_template("products/index.html")

# API routes
@bp.get("/api/products")
@roles_required("admin")
def list_products():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 25, type=int)
    search = request.args.get("search", "")
    category_id = request.args.get("category_id", type=int)

    query = db.select(Product)
    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))
    if category_id:
        query = query.where(Product.category_id == category_id)

    pagination = db.paginate(query, page=page, per_page=per_page)
    return {
        "items": [p.to_dict() for p in pagination.items],
        "total": pagination.total,
        "perPage": per_page
    }

@bp.get("/api/categories")
@roles_required("admin")
def list_categories():
    query = db.select(Category)
    categories = db.session.execute(query).scalars().all()
    return {"items": [c.to_dict() for c in categories]}
```

## Model Relationships

### One-to-Many
```python
class Author(db.Model, BaseMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    books = db.relationship("Book", back_populates="author", lazy="dynamic")

class Book(db.Model, BaseMixin):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    author_id = db.Column(db.Integer, db.ForeignKey("author.id"))
    author = db.relationship("Author", back_populates="books")
```

### Many-to-Many
```python
product_tags = db.Table(
    "product_tags",
    db.Column("product_id", db.Integer, db.ForeignKey("products.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id"), primary_key=True)
)

class Product(db.Model, BaseMixin):
    id = db.Column(db.Integer, primary_key=True)
    tags = db.relationship("Tag", secondary=product_tags, backref="products")

class Tag(db.Model, BaseMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
```

## Form Handling

WTForms with Flask-Security:

```python
# enferno/products/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SelectField
from wtforms.validators import DataRequired, NumberRange

class ProductForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    price = DecimalField("Price", validators=[DataRequired(), NumberRange(min=0)])
    category_id = SelectField("Category", coerce=int)
```

## File Uploads

```python
import os
from werkzeug.utils import secure_filename
from flask import current_app

@bp.post("/api/product/<int:id>/image")
@roles_required("admin")
def upload_image(id):
    product = db.get_or_404(Product, id)
    file = request.files.get("image")
    if file:
        filename = secure_filename(file.filename)
        path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        file.save(path)
        product.image = filename
        product.save()
    return {"item": product.to_dict()}
```

## Search and Filtering

Advanced filtering pattern:

```python
@bp.get("/api/products")
@roles_required("admin")
def list_products():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 25, type=int)

    query = db.select(Product)

    # Text search
    if search := request.args.get("search"):
        query = query.where(
            db.or_(
                Product.name.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%")
            )
        )

    # Filter by category
    if category_id := request.args.get("category_id", type=int):
        query = query.where(Product.category_id == category_id)

    # Filter by price range
    if min_price := request.args.get("min_price", type=float):
        query = query.where(Product.price >= min_price)
    if max_price := request.args.get("max_price", type=float):
        query = query.where(Product.price <= max_price)

    # Filter by active status
    if active := request.args.get("active"):
        query = query.where(Product.active == (active.lower() == "true"))

    # Sorting
    sort_by = request.args.get("sort_by", "id")
    sort_order = request.args.get("sort_order", "asc")
    column = getattr(Product, sort_by, Product.id)
    query = query.order_by(column.desc() if sort_order == "desc" else column.asc())

    pagination = db.paginate(query, page=page, per_page=per_page)
    return {"items": [p.to_dict() for p in pagination.items], "total": pagination.total, "perPage": per_page}
```

## Vue Components

### Data Table with Actions
```html
<v-data-table-server
  :headers="headers"
  :items="items"
  :items-length="total"
  :loading="loading"
  @update:options="loadItems"
>
  <template v-slot:item.actions="{ item }">
    <v-btn icon size="small" @click="editItem(item)">
      <v-icon>mdi-pencil</v-icon>
    </v-btn>
    <v-btn icon size="small" color="error" @click="deleteItem(item)">
      <v-icon>mdi-delete</v-icon>
    </v-btn>
  </template>
</v-data-table-server>
```

### Form Dialog
```html
<v-dialog v-model="dialog" max-width="600">
  <v-card>
    <v-card-title>${ editMode ? 'Edit' : 'Create' } Product</v-card-title>
    <v-card-text>
      <v-text-field v-model="form.name" label="Name" required></v-text-field>
      <v-text-field v-model="form.price" label="Price" type="number"></v-text-field>
      <v-select v-model="form.category_id" :items="categories" item-title="name" item-value="id" label="Category"></v-select>
    </v-card-text>
    <v-card-actions>
      <v-spacer></v-spacer>
      <v-btn @click="dialog = false">Cancel</v-btn>
      <v-btn color="primary" @click="saveItem" :loading="saving">Save</v-btn>
    </v-card-actions>
  </v-card>
</v-dialog>
```

### Confirmation Dialog
```html
<v-dialog v-model="confirmDialog" max-width="400">
  <v-card>
    <v-card-title>Confirm Delete</v-card-title>
    <v-card-text>Are you sure you want to delete this item?</v-card-text>
    <v-card-actions>
      <v-spacer></v-spacer>
      <v-btn @click="confirmDialog = false">Cancel</v-btn>
      <v-btn color="error" @click="confirmDelete" :loading="deleting">Delete</v-btn>
    </v-card-actions>
  </v-card>
</v-dialog>
```

## Dialog Patterns

Complete Vue setup with CRUD dialogs:

```javascript
createApp({
  delimiters: ['${', '}'],
  setup() {
    const items = ref([]);
    const total = ref(0);
    const loading = ref(false);
    const dialog = ref(false);
    const confirmDialog = ref(false);
    const editMode = ref(false);
    const saving = ref(false);
    const deleting = ref(false);
    const selectedItem = ref(null);
    const form = ref({ name: '', price: 0, category_id: null });

    function openCreate() {
      editMode.value = false;
      form.value = { name: '', price: 0, category_id: null };
      dialog.value = true;
    }

    function editItem(item) {
      editMode.value = true;
      selectedItem.value = item;
      form.value = { ...item };
      dialog.value = true;
    }

    async function saveItem() {
      saving.value = true;
      const url = editMode.value ? `/api/product/${selectedItem.value.id}` : '/api/product/';
      await axios.post(url, form.value);
      dialog.value = false;
      saving.value = false;
      loadItems({ page: 1, itemsPerPage: 25 });
    }

    function deleteItem(item) {
      selectedItem.value = item;
      confirmDialog.value = true;
    }

    async function confirmDelete() {
      deleting.value = true;
      await axios.delete(`/api/product/${selectedItem.value.id}`);
      confirmDialog.value = false;
      deleting.value = false;
      loadItems({ page: 1, itemsPerPage: 25 });
    }

    return { items, total, loading, dialog, confirmDialog, editMode, saving, deleting, form, openCreate, editItem, saveItem, deleteItem, confirmDelete };
  }
}).use(createVuetify(vuetifyConfig)).mount('#app');
```

## Error Handling

API error responses:

```python
from flask import jsonify

@bp.errorhandler(400)
def bad_request(e):
    return jsonify({"error": str(e)}), 400

@bp.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Resource not found"}), 404

# In endpoints
@bp.post("/api/product/")
@roles_required("admin")
def create_product():
    data = request.json
    if not data.get("name"):
        return {"error": "Name is required"}, 400
    # ... rest of logic
```

Vue error handling:
```javascript
async function saveItem() {
  try {
    saving.value = true;
    await axios.post(url, form.value);
    dialog.value = false;
  } catch (error) {
    snackbar.value = { show: true, text: error.response?.data?.error || 'Save failed', color: 'error' };
  } finally {
    saving.value = false;
  }
}
```
