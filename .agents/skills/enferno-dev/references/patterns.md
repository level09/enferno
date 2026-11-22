# Enferno Patterns Reference

Detailed patterns for common Enferno development tasks.

## Table of Contents

- [Full Blueprint Example](#full-blueprint-example)
- [Model Relationships](#model-relationships)
- [Form Handling](#form-handling)
- [File Uploads](#file-uploads)
- [Search and Filtering](#search-and-filtering)
- [Data Tables and Dialogs](#data-tables-and-dialogs)
- [Error Handling](#error-handling)

## Full Blueprint Example

Complete blueprint with models, views, and templates:

```python
# enferno/products/models.py
from datetime import datetime

from enferno.extensions import db
from enferno.utils.base import BaseMixin

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
    created_at = db.Column(db.DateTime, default=datetime.now)
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

    def from_dict(self, data):
        self.name = data.get("name", self.name)
        self.description = data.get("description", self.description)
        self.price = data.get("price", self.price)
        self.category_id = data.get("category_id", self.category_id)
        self.active = data.get("active", self.active)
        return self
```

```python
# enferno/products/views.py
from flask import Blueprint, request, render_template
from flask_security import auth_required, current_user, roles_required
from enferno.extensions import db
from enferno.user.models import Activity
from enferno.utils.tables import table_response
from .models import Product, Category

bp = Blueprint("products", __name__)

# Protect all routes in this blueprint
@bp.before_request
@auth_required("session")
@roles_required("admin")
def before_request():
    pass

# Page routes
@bp.get("/products/")
def products_page():
    return render_template("products/index.html")

# API routes
@bp.get("/api/products")
def list_products():
    query = db.select(Product).order_by(Product.id)
    if category_id := request.args.get("category_id", type=int):
        query = query.where(Product.category_id == category_id)
    return table_response(
        query, sortable={"name": Product.name}, searchable=(Product.name,)
    )

@bp.get("/api/categories")
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

`table_response()` in `enferno/utils/tables.py` handles paging, `?sort_by=`/`?sort_desc=` for whitelisted columns and `?q=` across searchable columns. Apply any extra filters to the query first:

```python
@bp.get("/api/products")
def list_products():
    query = db.select(Product).order_by(Product.id)
    if category_id := request.args.get("category_id", type=int):
        query = query.where(Product.category_id == category_id)
    return table_response(
        query,
        sortable={"name": Product.name, "price": Product.price},
        searchable=(Product.name, Product.description),
    )
```

On the page, extra filters are ordinary data that `refresh()` sends: override it or add them to the URL. `serialize=` takes the whole page of rows when `to_dict()` is not enough (see `api_activities` in `enferno/user/views.py`).

## Data Tables and Dialogs

Use `crudMixin` from `static/js/crud.js`; the full example is in `SKILL.md` and `cms/roles.html`. It owns `items`, `loading`, `search`, `options`, `eitem`, `edialog` and `saving`, and `refresh`, `createItem`, `editItem`, `saveItem` and `deleteItem(row, label)`. Pass `newItem` for the defaults a new record starts with. Confirm destructive actions with `await this.confirmAction(message)` and report results with `this.notify(message)`, both from `layoutMixin`; never `window.confirm()`.

## Error Handling

The app-level handler in `enferno/app.py` turns every HTTP error under `/api/` into `{"message": ...}` JSON, including CSRF failures. Endpoints return the same shape for validation errors:

```python
@bp.post("/api/product/")
def create_product():
    data = request.json.get("item", {})
    if not data.get("name"):
        return {"message": "Name is required"}, 400
    # ... rest of logic
```

In Vue, show `err.response?.data?.message` with a fallback, as `saveItem()` in `static/js/crud.js` does.
