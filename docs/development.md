# Development Guidelines

This guide covers best practices and conventions for developing with Enferno.

## Project Structure

```
enferno/
├── app/
│   ├── templates/      # Jinja2 templates
│   ├── static/        # Static files (JS, CSS, images)
│   ├── user/          # User management module
│   ├── public/        # Public views
│   └── portal/        # Admin portal
├── docs/             # Documentation
└── requirements.txt  # Python dependencies
```

## Code Style

### Python

- Follow PEP 8 style guide
- Keep functions focused and small
- Use meaningful variable names
- Add docstrings for important functions

Example:
```python
def get_user_orders(user_id, status=None):
    """Get orders for a specific user."""
    query = Order.query.filter_by(user_id=user_id)
    if status:
        query = query.filter_by(status=status)
    return query.all()
```

### Vue.js

- Keep components small and focused
- Follow Vue.js Options API pattern
- Use Vuetify components for UI consistency

Example:
```html
<template>
  <v-data-table
    :headers="headers"
    :items="items"
    :loading="loading"
    @update:options="loadItems"
  >
    <template v-slot:item.actions="{ item }">
      <v-btn icon="mdi-pencil" @click="editItem(item)"></v-btn>
    </template>
  </v-data-table>
</template>

<script>
{
  data() {
    return {
      loading: false,
      items: [],
      headers: [
        { title: 'Name', key: 'name' },
        { title: 'Actions', key: 'actions' }
      ]
    }
  },
  methods: {
    loadItems() {
      this.loading = true
      axios.get('/api/items')
        .then(response => {
          this.items = response.data
        })
        .finally(() => {
          this.loading = false
        })
    }
  }
}
</script>
```

## Frontend Development

### Vue.js Integration

Enferno uses Vue.js directly in templates without build tools. Standard template structure:

```html
{% extends 'layout.html' %}
{% block content %}
<v-app id="app">
    <!-- Snackbar for notifications -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color">
        ${ snackbar.message }
        <template v-slot:actions>
            <v-btn icon="mdi-close" @click="snackbar.show = false"></v-btn>
        </template>
    </v-snackbar>

    <!-- Your content here -->
</v-app>
{% endblock %}

{% block js %}
<script>
const { createApp } = Vue
const { createVuetify } = Vuetify
const vuetify = createVuetify()

const app = createApp({
    delimiters: ['${', '}'],  // Avoid conflict with Jinja2
    data() {
        return {
            snackbar: {
                show: false,
                message: '',
                color: 'success'
            },
            loading: false,
            items: [],
            edialog: false,
            eitem: {}
        }
    },
    methods: {
        showMessage(message, color = 'success') {
            this.snackbar.message = message
            this.snackbar.color = color
            this.snackbar.show = true
        },
        loadItems() {
            this.loading = true
            axios.get('/api/items')
                .then(response => {
                    this.items = response.data.items
                })
                .catch(error => {
                    this.showMessage(error.response?.data?.message || 'Error', 'error')
                })
                .finally(() => {
                    this.loading = false
                })
        }
    },
    mounted() {
        this.loadItems()
    }
}).use(vuetify).mount('#app')
</script>
{% endblock %}
```

### Common UI Patterns

1. **Data Tables**:
```html
<v-data-table
    :headers="headers"
    :items="items"
    :loading="loading"
    @update:options="loadItems"
>
    <template v-slot:item.actions="{ item }">
        <v-btn icon="mdi-pencil" @click="editItem(item)"></v-btn>
    </template>
</v-data-table>

<script>
{
    data() {
        return {
            headers: [
                { title: 'Name', key: 'name' },
                { title: 'Actions', key: 'actions', sortable: false }
            ]
        }
    }
}
</script>
```

2. **Edit Dialog Forms**:
```html
<v-dialog v-model="edialog" width="500">
    <v-card>
        <v-card-title>Edit Item</v-card-title>
        <v-card-text>
            <v-text-field v-model="eitem.name" label="Name"></v-text-field>
        </v-card-text>
        <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn @click="edialog = false">Cancel</v-btn>
            <v-btn color="primary" @click="saveItem">Save</v-btn>
        </v-card-actions>
    </v-card>
</v-dialog>
```

3. **Navigation Drawer**:
```html
<v-navigation-drawer v-model="drawer">
    <v-list>
        <v-list-item to="/dashboard">
            <template v-slot:prepend>
                <v-icon>mdi-view-dashboard</v-icon>
            </template>
            <v-list-item-title>Dashboard</v-list-item-title>
        </v-list-item>
    </v-list>
</v-navigation-drawer>
```

### API Integration

```javascript
methods: {
    saveItem() {
        axios.post('/api/items', this.eitem)
            .then(response => {
                this.showMessage('Item saved successfully')
                this.edialog = false
                this.loadItems()
            })
            .catch(error => {
                this.showMessage(error.response?.data?.message || 'Error saving item', 'error')
            })
    },
    editItem(item) {
        this.eitem = {...item}  // Clone to avoid direct mutation
        this.edialog = true
    }
}
```

### Required Assets

Include in your base template:
```html
<!-- CSS -->
<link href="/static/css/vuetify.min.css" rel="stylesheet">
<link href="/static/mdi/css/materialdesignicons.min.css" rel="stylesheet">

<!-- JavaScript -->
<script src="/static/js/vue.min.js"></script>
<script src="/static/js/vuetify.min.js"></script>
<script src="/static/js/axios.min.js"></script>
```

## Backend Development

### Environment Configuration

Key environment variables (.env):
```bash
# Core
FLASK_APP=run.py
FLASK_DEBUG=1  # 0 in production
SECRET_KEY=your_secret_key

# Database (choose one)
SQLALCHEMY_DATABASE_URI=sqlite:///enferno.sqlite3
# Or for PostgreSQL:
# SQLALCHEMY_DATABASE_URI=postgresql://username:password@localhost/dbname

# Redis & Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Email Settings (optional)
MAIL_SERVER=smtp.example.com
MAIL_PORT=465
MAIL_USE_SSL=True
MAIL_USERNAME=your_email
MAIL_PASSWORD=your_password
SECURITY_EMAIL_SENDER=noreply@example.com

# OAuth (optional)
GOOGLE_AUTH_ENABLED=true
GOOGLE_OAUTH_CLIENT_ID=your_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret

GITHUB_AUTH_ENABLED=true
GITHUB_OAUTH_CLIENT_ID=your_client_id
GITHUB_OAUTH_CLIENT_SECRET=your_client_secret

# AI Features (optional)
OPENAI_API_KEY=your_openai_key

# Security Settings
SECURITY_PASSWORD_SALT=your_secure_salt
SECURITY_TOTP_SECRETS=your_totp_secrets
```

### OAuth Setup

#### Google OAuth Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google+ API
4. Configure OAuth consent screen
5. Create OAuth 2.0 credentials
6. Add authorized redirect URI: `http://your-domain/login/google/authorized`

#### GitHub OAuth Setup
1. Go to GitHub Settings > Developer Settings > OAuth Apps
2. Create New OAuth App
3. Set Homepage URL to your domain
4. Set Authorization callback URL: `http://your-domain/login/github/authorized`

### AI Code Generation

Generate boilerplate code using natural language:

```bash
# Generate a model
flask generate-model --class_name User --fields "name:string, email:string:unique"

# Generate an API
flask generate-api --class_name Product --fields "name, price:decimal"

# Generate a dashboard
flask generate-dashboard --class_name Order --fields "order_number, total:decimal"
```

### Python Code Style

- Follow PEP 8
- Keep functions focused and small
- Use meaningful variable names
- Add docstrings for important functions

Example:
```python
def get_user_orders(user_id, status=None):
    """Get orders for a specific user."""
    query = Order.query.filter_by(user_id=user_id)
    if status:
        query = query.filter_by(status=status)
    return query.all()
```

### Database Models

Use SQLAlchemy for models:

```python
class Product(BaseModel):
    """Product model."""
    __tablename__ = 'products'
    
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Decimal(10, 2), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    
    category = db.relationship('Category', backref='products')
```

### API Endpoints

```python
@bp.route('/api/products', methods=['GET'])
@login_required
def get_products():
    """Get list of products."""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    
    products = Product.query.paginate(page=page, per_page=per_page)
    return jsonify({
        'items': [p.to_dict() for p in products.items],
        'total': products.total
    })
```

### Error Handling

Backend:
```python
@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    return jsonify({
        'error': 'Not found',
        'message': str(error)
    }), 404
```

Frontend:
```javascript
axios.get('/api/endpoint')
    .then(response => {
        // Handle success
    })
    .catch(error => {
        this.showMessage(error.response?.data?.message || 'Error', 'error')
    })
```

### Security Features

- Two-factor authentication (2FA)
- WebAuthn support
- OAuth integration
- Password policies
- Session protection
- CSRF protection
- Secure cookie settings
- Rate limiting
- XSS protection

```python
@roles_required('admin')
def admin_view():
    """Admin only view."""
    pass

@roles_accepted('admin', 'manager')
def manager_view():
    """View for admins and managers."""
    pass
```

## Performance

1. Use proper database indexes
2. Implement caching where appropriate
3. Optimize database queries
4. Use lazy loading for components
5. Implement proper pagination
6. Use background tasks for heavy operations 