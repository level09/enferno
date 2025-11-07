# AGENTS.md

This file provides comprehensive architectural patterns and coding standards for AI agents working with the Enferno framework.

## Framework Overview

**Enferno** is a Flask-based web framework optimized for rapid development with modern tooling:

- **Backend**: Flask 3.x with Blueprint organization
- **Frontend**: Vue 3 + Vuetify (no build step required)
- **Database**: SQLAlchemy 2.x with modern statement-based queries
- **Auth**: Flask-Security-Too with 2FA, WebAuthn, OAuth support
- **Tasks**: Celery + Redis for background processing
- **Package Manager**: uv for fast dependency management

## Project Structure

```
enferno/
├── enferno/                # Main application package
│   ├── app.py             # Application factory (create_app)
│   ├── settings.py        # Environment-based configuration
│   ├── extensions.py      # Flask extensions initialization
│   ├── commands.py        # Custom Flask CLI commands
│   ├── public/            # Public routes (no auth)
│   │   ├── views.py
│   │   ├── models.py
│   │   └── templates/
│   ├── user/              # Authentication & user management
│   │   ├── views.py
│   │   ├── models.py
│   │   ├── forms.py
│   │   └── templates/
│   ├── portal/            # Protected dashboard/admin
│   │   ├── views.py
│   │   └── templates/
│   ├── services/          # Business logic layer
│   ├── tasks/             # Celery task definitions
│   ├── utils/             # Utility functions
│   ├── static/            # CSS, JS, images
│   │   ├── css/
│   │   ├── js/
│   │   └── img/
│   └── templates/         # Global Jinja2 templates
├── docs/                  # Documentation
├── nginx/                 # Nginx configuration
├── instance/              # Instance-specific files (gitignored)
├── pyproject.toml         # Dependencies and project metadata
├── uv.lock               # Lock file for reproducible installs
├── .env                   # Environment variables (gitignored)
├── .env-sample            # Environment template
├── setup.sh              # Setup script
├── run.py                # Application entry point
├── Dockerfile            # Docker configuration
└── docker-compose.yml    # Docker Compose orchestration
```

## Development Commands

### Setup & Installation
```bash
./setup.sh                    # Create virtual environment, install dependencies, generate .env
uv sync --extra dev           # Install dependencies with dev tools
uv sync --extra wsgi          # For Unix deployments that need uWSGI
```

### Database Management
```bash
uv run flask create-db               # Initialize database tables
uv run flask install                 # Create admin user with secure password
uv run flask reset -e <email/username> -p <password>  # Reset user password
uv run flask add-role -e <email> -r <role>  # Add role to user
```

### Development Server
```bash
uv run flask run                     # Default http://localhost:5000
uv run flask run --port 5001         # Use 5001 locally if 5000 is busy (macOS)
```

### Code Quality
```bash
uv run ruff check .                  # Lint code with ruff
uv run ruff format .                 # Format code with ruff
uv run ruff check --fix .            # Auto-fix linting issues
uv run pre-commit install            # Install pre-commit hooks
```

### Docker Development
```bash
docker compose up --build            # Full stack with Redis, PostgreSQL, Nginx
```

### Internationalization
```bash
uv run flask i18n extract            # Extract translatable strings
uv run flask i18n init <lang>        # Initialize new language
uv run flask i18n update             # Update translations
uv run flask i18n compile            # Compile translations
```

## Flask Architecture Patterns

### Application Factory Pattern

The app is created using the factory pattern in `enferno/app.py`:

```python
from flask import Flask
from enferno.settings import Config
from enferno.extensions import db, cache, mail, session

def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    register_blueprints(app)
    register_extensions(app)
    register_errorhandlers(app)
    register_commands(app)

    return app
```

### Extension Initialization

Extensions are initialized in `enferno/extensions.py`:

```python
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class BaseModel(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=BaseModel)
cache = Cache()
mail = Mail()
session = Session()

# Import initialized extensions anywhere:
from enferno.extensions import db, cache, mail
```

### Blueprint Organization

Features are organized into blueprints by functional area:

#### 1. Public Blueprint (`enferno/public/`)
Routes accessible without authentication:

```python
from flask import Blueprint, render_template

public = Blueprint('public', __name__)

@public.route('/')
def index():
    return render_template('public/index.html')
```

#### 2. User Blueprint (`enferno/user/`)
Authentication and user account management:

```python
from flask import Blueprint
from flask_security import auth_required

bp_user = Blueprint('user', __name__)

@bp_user.route('/profile')
@auth_required()
def profile():
    return render_template('user/profile.html')
```

#### 3. Portal Blueprint (`enferno/portal/`)
Protected routes requiring authentication. Uses `before_request` to protect all routes:

```python
from flask import Blueprint
from flask_security import auth_required

portal = Blueprint('portal', __name__)

# Protect all routes in this blueprint
@portal.before_request
@auth_required()
def before_request():
    pass

@portal.route('/dashboard')
def dashboard():
    return render_template('portal/dashboard.html')
```

### Creating New Blueprints

1. Create directory: `enferno/feature_name/`
2. Add files: `views.py`, `models.py`, optionally `forms.py`
3. Create templates: `templates/feature_name/`
4. Register in `app.py`:

```python
from enferno.feature_name.views import feature_bp
app.register_blueprint(feature_bp)
```

## Database Patterns (SQLAlchemy 2.x)

### Model Definition

Models inherit from `db.Model` which uses a custom `BaseModel` with `DeclarativeBase`:

```python
from enferno.extensions import db
from datetime import datetime

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Relationships
    user = db.relationship('User', backref='posts')

    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'created_at': self.created_at.isoformat()
        }

    def from_dict(self, data):
        """Update model attributes from dictionary"""
        self.title = data.get('title', self.title)
        self.content = data.get('content', self.content)
        return self
```

### Modern Query Patterns (SQLAlchemy 2.x)

Use statement-based queries with `db.select()`, `db.update()`, `db.delete()`:

```python
from enferno.extensions import db
from enferno.user.models import User

# Select all
stmt = db.select(User)
users = db.session.scalars(stmt).all()

# Select with filtering
stmt = db.select(User).where(User.active == True)
active_users = db.session.scalars(stmt).all()

# Select single item
stmt = db.select(User).where(User.id == user_id)
user = db.session.scalar(stmt)

# Or use session.get for primary key lookup
user = db.session.get(User, user_id)

# Ordering and limiting
stmt = (
    db.select(Post)
    .order_by(Post.created_at.desc())
    .limit(10)
)
recent_posts = db.session.scalars(stmt).all()

# Joins
stmt = (
    db.select(Post)
    .join(Post.user)
    .where(User.active == True)
)
posts = db.session.scalars(stmt).all()

# Update
stmt = db.update(User).where(User.id == user_id).values(active=False)
db.session.execute(stmt)
db.session.commit()

# Delete
stmt = db.delete(Post).where(Post.id == post_id)
db.session.execute(stmt)
db.session.commit()
```

### CRUD Operations

```python
# Create
post = Post(title='New Post', content='Content here')
db.session.add(post)
db.session.commit()

# Read
post = db.session.get(Post, 1)

# Update
post.title = 'Updated Title'
db.session.commit()

# Delete
db.session.delete(post)
db.session.commit()
```

## API Development Standards

### RESTful Endpoint Patterns

- **Collections**: `/api/resource` (GET for list, POST for create)
- **Items**: `/api/resource/<id>` (GET for retrieve, POST for update, DELETE for remove)
- **JSON responses** with consistent structure
- **Proper HTTP status codes**: 200 (success), 400 (bad request), 404 (not found), 500 (error)

### API Response Patterns

```python
from flask import Blueprint, jsonify, request
from enferno.extensions import db
from enferno.user.models import User

api = Blueprint('api', __name__)

# List with pagination
@api.route('/api/users')
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)

    stmt = db.select(User).offset((page-1) * per_page).limit(per_page)
    users = db.session.scalars(stmt).all()
    total = db.session.scalar(db.select(db.func.count(User.id)))

    return jsonify({
        'items': [user.to_dict() for user in users],
        'total': total,
        'page': page,
        'per_page': per_page
    })

# Update with error handling
@api.route('/api/users/<int:user_id>', methods=['POST'])
def update_user(user_id):
    try:
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()
        user.from_dict(data)
        db.session.commit()

        return jsonify({
            'message': 'User updated successfully',
            'data': user.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Delete
@api.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        db.session.delete(user)
        db.session.commit()

        return jsonify({'message': 'User deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
```

## Security Patterns

### Authentication & Authorization

Flask-Security provides comprehensive auth with decorators:

```python
from flask_security import auth_required, roles_required, current_user

# Require authentication
@app.route('/protected')
@auth_required()
def protected_route():
    return render_template('protected.html')

# Require specific role
@app.route('/admin')
@auth_required()
@roles_required('admin')
def admin_route():
    return render_template('admin.html')

# Access current user
@app.route('/profile')
@auth_required()
def profile():
    user_name = current_user.name
    return render_template('profile.html', user=current_user)
```

### Input Validation with WTForms

```python
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, validators

class PostForm(FlaskForm):
    title = StringField('Title', [
        validators.DataRequired(),
        validators.Length(min=3, max=255)
    ])
    content = TextAreaField('Content', [
        validators.DataRequired(),
        validators.Length(min=10)
    ])
```

### CSRF Protection

CSRF is automatically enabled via Flask-WTF. For AJAX requests include the token:

```javascript
// Include CSRF token in AJAX requests
const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

axios.post('/api/endpoint', data, {
    headers: {
        'X-CSRFToken': csrfToken
    }
});
```

## Frontend Architecture (Vue 3 + Vuetify)

### No Build Step Philosophy

- Vue 3 and Vuetify loaded from local static files (`enferno/static/`)
- Components defined using `Vue.defineComponent` with template strings
- Per-page Vue instances (not SPA architecture)
- Global configuration in `enferno/static/js/config.js`

### CRITICAL: Custom Vue Delimiters

**IMPORTANT**: Enferno uses `${` and `}` for Vue expressions to avoid conflicts with Jinja's `{{ }}`:

```javascript
// In config.js
const config = {
    delimiters: ['${', '}'],
    // ... other config
};
```

```html
<!-- CORRECT: Vue expressions with custom delimiters -->
<v-card-title>${ user.name }</v-card-title>
<v-list-item v-for="item in items" :key="item.id">
    ${ item.title }
</v-list-item>

<!-- CORRECT: Jinja expressions (server-side) -->
{% if current_user.is_authenticated %}
    <v-btn href="/logout">Logout</v-btn>
{% endif %}

<!-- WRONG: Never use {{ }} for Vue expressions -->
<v-card-title>{{ user.name }}</v-card-title>
```

### Base Template Structure

All pages extend `layout.html` which provides Vue/Vuetify setup:

```html
<!DOCTYPE html>
<html>
<head>
    <link href="/static/css/vuetify.min.css" rel="stylesheet">
    <link href="/static/mdi/css/materialdesignicons.min.css" rel="stylesheet">
    {% block head %}{% endblock %}
</head>
<body>
    <div id="app">
        {% block content %}{% endblock %}
    </div>

    <script src="/static/js/vue.min.js"></script>
    <script src="/static/js/vuetify.min.js"></script>
    <script src="/static/js/config.js"></script>
    {% block js %}{% endblock %}
</body>
</html>
```

### Vue App Initialization Pattern

Every page that uses Vue must follow this pattern:

```html
{% extends 'layout.html' %}

{% block content %}
<v-app>
    <v-main>
        <v-container>
            <h1>${ pageTitle }</h1>
            <!-- Vue content here -->
        </v-container>
    </v-main>
</v-app>
{% endblock %}

{% block js %}
<script>
const {createApp} = Vue;
const {createVuetify} = Vuetify;
const vuetify = createVuetify(config.vuetifyConfig);

const app = createApp({
    data() {
        return {
            config: config,
            menu: config.menu,
            drawer: true,  // false for public pages
            pageTitle: 'My Page',
            items: []
        };
    },
    delimiters: config.delimiters,  // REQUIRED: Uses ${ }
    methods: {
        async loadData() {
            const response = await axios.get('/api/items');
            this.items = response.data.items;
        }
    },
    mounted() {
        this.loadData();
    }
});

app.use(vuetify).mount('#app');
</script>
{% endblock %}
```

### Passing Server Data to Vue

Use JSON script tags to safely pass data from Jinja to Vue:

```html
<!-- In template -->
<script type="application/json" id="server-data">
    {{ data|tojson|safe }}
</script>

<script>
// In Vue app initialization
const serverData = JSON.parse(
    document.getElementById('server-data').textContent
);

const app = createApp({
    data() {
        return {
            items: serverData.items || [],
            config: config
        };
    }
});
</script>
```

### Common Vue Patterns

#### Data Table with Pagination

```javascript
const app = createApp({
    data() {
        return {
            items: [],
            itemsLength: 0,
            loading: false,
            search: '',
            options: {
                page: 1,
                itemsPerPage: 25,
                sortBy: []
            },
            headers: [
                { title: 'ID', value: 'id', sortable: true },
                { title: 'Name', value: 'name', sortable: true },
                { title: 'Email', value: 'email', sortable: false },
                { title: 'Actions', value: 'actions', sortable: false }
            ]
        };
    },
    methods: {
        refresh(options) {
            if (options) {
                this.options = {...this.options, ...options};
            }
            this.loadItems();
        },

        async loadItems() {
            this.loading = true;
            try {
                const params = new URLSearchParams({
                    page: this.options.page,
                    per_page: this.options.itemsPerPage,
                    search: this.search
                });

                const response = await axios.get(`/api/items?${params}`);
                this.items = response.data.items;
                this.itemsLength = response.data.total;
            } catch (error) {
                console.error('Error loading data:', error);
                this.showSnack('Failed to load data');
            } finally {
                this.loading = false;
            }
        },

        showSnack(message, color = 'success') {
            this.snackMessage = message;
            this.snackColor = color;
            this.snackBar = true;
        }
    },
    mounted() {
        this.loadItems();
    }
});
```

#### Edit Dialog Pattern

```javascript
data() {
    return {
        edialog: false,
        eitem: {
            id: null,
            name: '',
            email: '',
            active: true
        },
        defaultItem: {
            id: null,
            name: '',
            email: '',
            active: true
        }
    };
},
methods: {
    editItem(item) {
        this.eitem = Object.assign({}, item);
        this.edialog = true;
    },

    newItem() {
        this.eitem = Object.assign({}, this.defaultItem);
        this.edialog = true;
    },

    async saveItem() {
        const endpoint = this.eitem.id ?
            `/api/items/${this.eitem.id}` :
            '/api/items';

        try {
            const response = await axios.post(endpoint, {item: this.eitem});
            this.showSnack(response.data.message || 'Saved successfully');
            this.edialog = false;
            this.refresh();
        } catch (error) {
            this.showSnack(error.response?.data?.error || 'Save failed', 'error');
        }
    },

    closeDialog() {
        this.edialog = false;
        this.eitem = Object.assign({}, this.defaultItem);
    }
}
```

### Vuetify Component Examples

```html
<!-- Data Table -->
<v-data-table
    :items="items"
    :headers="headers"
    :loading="loading"
    :items-length="itemsLength"
    :search="search"
    v-model:options="options"
    @update:options="refresh"
    class="elevation-1">

    <template v-slot:top>
        <v-toolbar flat>
            <v-toolbar-title>Users</v-toolbar-title>
            <v-spacer></v-spacer>
            <v-text-field
                v-model="search"
                append-icon="mdi-magnify"
                label="Search"
                single-line
                hide-details>
            </v-text-field>
            <v-btn color="primary" class="ml-2" @click="newItem">
                Add New
            </v-btn>
        </v-toolbar>
    </template>

    <template v-slot:item.actions="{ item }">
        <v-btn icon="mdi-pencil" size="small" @click="editItem(item)"></v-btn>
        <v-btn icon="mdi-delete" size="small" color="error" @click="deleteItem(item)"></v-btn>
    </template>
</v-data-table>

<!-- Edit Dialog -->
<v-dialog v-model="edialog" max-width="500px">
    <v-card>
        <v-card-title>
            <span>${ eitem.id ? 'Edit' : 'New' } Item</span>
        </v-card-title>

        <v-card-text>
            <v-text-field
                v-model="eitem.name"
                label="Name"
                required>
            </v-text-field>
            <v-text-field
                v-model="eitem.email"
                label="Email"
                type="email">
            </v-text-field>
            <v-switch
                v-model="eitem.active"
                label="Active">
            </v-switch>
        </v-card-text>

        <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn variant="text" @click="closeDialog">Cancel</v-btn>
            <v-btn color="primary" @click="saveItem">Save</v-btn>
        </v-card-actions>
    </v-card>
</v-dialog>

<!-- Snackbar for notifications -->
<v-snackbar v-model="snackBar" :color="snackColor" timeout="3000">
    ${ snackMessage }
    <template v-slot:actions>
        <v-btn variant="text" @click="snackBar = false">Close</v-btn>
    </template>
</v-snackbar>
```

### Button & Card Patterns

```html
<!-- Buttons -->
<v-btn color="primary" variant="elevated" prepend-icon="mdi-plus" @click="newItem">
    Add New
</v-btn>
<v-btn variant="text" @click="closeDialog">Cancel</v-btn>
<v-btn icon="mdi-pencil" size="small" @click="editItem(item)"></v-btn>
<v-btn color="error" variant="outlined" prepend-icon="mdi-delete">Delete</v-btn>

<!-- Card Layout -->
<v-card class="ma-2">
    <v-card-title class="d-flex justify-space-between align-center">
        <span>Card Title</span>
        <v-btn icon="mdi-refresh" @click="refresh"></v-btn>
    </v-card-title>

    <v-card-text>
        <!-- Main content -->
    </v-card-text>

    <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn variant="text">Cancel</v-btn>
        <v-btn color="primary">Save</v-btn>
    </v-card-actions>
</v-card>
```

### Template-Level Auth Checks

```html
<!-- Jinja auth checks (server-side) -->
{% if current_user.is_authenticated %}
    <v-btn href="/dashboard">Dashboard</v-btn>
{% else %}
    <v-btn href="/login">Login</v-btn>
{% endif %}

{% if current_user.has_role('admin') %}
    <v-btn href="/admin">Admin Panel</v-btn>
{% endif %}
```

## Background Tasks (Celery)

### Task Definition

Tasks are defined in `enferno/tasks/`:

```python
from enferno.tasks import celery
from enferno.extensions import db, mail

@celery.task
def send_welcome_email(user_id):
    from enferno.user.models import User
    from flask_mail import Message

    user = db.session.get(User, user_id)
    if not user:
        return False

    msg = Message(
        subject='Welcome!',
        recipients=[user.email],
        body=f'Welcome {user.name}!'
    )
    mail.send(msg)
    return True
```

### Calling Tasks

```python
from enferno.tasks import send_welcome_email

# Call asynchronously
send_welcome_email.delay(user.id)

# Call with ETA
from datetime import datetime, timedelta
send_welcome_email.apply_async(
    args=[user.id],
    eta=datetime.now() + timedelta(hours=1)
)
```

### Running Celery Worker

```bash
celery -A enferno.tasks worker --loglevel=info
```

## Docker Deployment

### Modern Dockerfile with uv

```dockerfile
# Build stage
FROM python:3.12-slim AS builder
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Install dependencies using uv (with optional wsgi extra)
COPY pyproject.toml uv.lock ./
RUN uv sync --extra wsgi --frozen

# Runtime stage
FROM python:3.12-slim
WORKDIR /app

# Copy virtual environment from build stage
COPY --from=builder /app/.venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user and ensure permissions
RUN useradd -m -u 1000 enferno && \
    chown -R enferno:enferno /app /opt/venv

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libexpat1 \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY --chown=enferno:enferno . .

# Switch to non-root user
USER enferno

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/ || exit 1

EXPOSE 5000
CMD ["uwsgi", "--ini", "uwsgi.ini"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:5000"
    environment:
      - FLASK_ENV=production
      - SQLALCHEMY_DATABASE_URI=postgresql://enferno:${DB_PASSWORD}@postgres/enferno
      - REDIS_SESSION=redis://:${REDIS_PASSWORD}@redis:6379/1
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: enferno
      POSTGRES_USER: enferno
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx:/etc/nginx/conf.d
    depends_on:
      - web

volumes:
  postgres_data:
  redis_data:
```

## Error Handling

### Exception Management

```python
from flask import jsonify
from sqlalchemy.exc import IntegrityError

try:
    db.session.commit()
except IntegrityError:
    db.session.rollback()
    return jsonify({'error': 'Data integrity violation'}), 400
except Exception as e:
    db.session.rollback()
    current_app.logger.error(f'Unexpected error: {str(e)}')
    return jsonify({'error': 'Internal server error'}), 500
```

### Logging

```python
from flask import current_app

# Use Flask's logger
current_app.logger.info('User login successful')
current_app.logger.error(f'Failed login attempt: {email}')
current_app.logger.debug(f'Processing request: {request.url}')
```

## Configuration Management

### Environment-Based Config

Configuration in `enferno/settings.py`:

```python
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    DEBUG = False
```

### Environment Variables

Use `.env` file for local development (never commit):

```bash
SECRET_KEY=your-secret-key-here
SQLALCHEMY_DATABASE_URI=sqlite:///enferno.sqlite3
FLASK_ENV=development

# Mail settings
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Security
SECURITY_PASSWORD_SALT=your-salt-here
SECURITY_TOTP_SECRETS=secret1,secret2

# Optional: OAuth
GOOGLE_AUTH_ENABLED=True
GOOGLE_OAUTH_CLIENT_ID=your-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
```

## Code Style Standards

### Python Conventions
- Python 3.11+ required
- 4-space indentation
- 88-character line length (Ruff default)
- Double quotes for strings
- Imports ordered by Ruff/isort

### Naming Conventions
- Modules/functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_CASE`
- Private attributes: `_leading_underscore`

### Import Organization
```python
# Standard library
import os
from datetime import datetime

# Third-party
from flask import Blueprint, jsonify
from flask_security import auth_required

# Local application
from enferno.extensions import db
from enferno.user.models import User
```

## Development Philosophy

Write code that's minimal, rock-solid, and production-ready. Focus on:

- **Simplicity First** - Fewest moving parts possible
- **Production Ready** - Code should work reliably in real use
- **Clear Purpose** - Every line solves one problem well
- **No Over-Engineering** - Avoid premature abstraction
- **Ship Fast** - Functional out-of-the-box with sensible defaults

## Verification Checklist

Before committing:
1. **Lint & Format**: `uv run ruff check --fix .` then `uv run ruff format .`
2. **Test Locally**: `uv run flask create-db && uv run flask install && uv run flask run`
3. **Smoke Test**: Visit `/`, `/login`, dashboard; verify no errors
4. **Pre-commit**: Run `uv run pre-commit run -a`

## Commit Guidelines

- Use imperative present tense: "Add feature" not "Added feature"
- Keep messages concise and descriptive
- Never mention AI/Claude in commits
- Never use `git add .` or `git add -A` - add files selectively
- Format: `Add Stripe webhook handler` or `Fix user login validation`

## Key Principles

1. **Blueprint Organization** - Features organized by functional area
2. **Modern SQLAlchemy** - Statement-based queries (`db.select()`, not legacy `.query`)
3. **Custom Vue Delimiters** - Always use `${}` for Vue expressions
4. **No Build Step** - Direct JavaScript without compilation
5. **Security First** - Use Flask-Security decorators, validate all inputs
6. **Consistent API** - RESTful patterns with standard JSON responses
7. **Environment Config** - Use `.env` files, never hardcode secrets
8. **Modern Tooling** - Use `uv` for package management, Ruff for linting

This architecture ensures clean separation of concerns, maintainable code, and rapid development velocity.
