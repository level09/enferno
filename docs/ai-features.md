# AI Features

Enferno includes AI-powered code generation tools that help you quickly scaffold common application components using natural language.

## Configuration

1. Get an API key from [OpenAI](https://platform.openai.com/)
2. Add it to your `.env` file:
```bash
OPENAI_API_KEY=your_api_key
```

## Available Commands

### Generate Model

Create database models with relationships and validation:

```bash
flask generate-model --class_name User --fields "name:string, email:string:unique, age:integer, created_at:datetime"
```

Supported field types:
- string
- integer
- float
- decimal
- boolean
- datetime
- date
- text
- json
- array
- relationship

Example with relationships:
```bash
flask generate-model --class_name Order --fields "number:string:unique, customer:relationship(User), items:relationship(Product, many=True)"
```

### Generate API

Create RESTful APIs with CRUD operations:

```bash
flask generate-api --class_name Product --fields "name, description:text, price:decimal, stock:integer"
```

Features:
- CRUD endpoints
- Input validation
- Error handling
- Authentication requirements
- Rate limiting
- API documentation

### Generate Dashboard

Create admin dashboards with data management:

```bash
flask generate-dashboard --class_name Order --fields "order_number, customer_name, total:decimal, status:string"
```

Features:
- Data listing with pagination
- Search and filtering
- Create/Edit forms
- Delete confirmation
- Export functionality
- Access control

## Customization

### Model Generation Options

```bash
flask generate-model --help
Options:
  --class_name TEXT     Name of the model class  [required]
  --fields TEXT         Field definitions  [required]
  --table_name TEXT     Custom table name
  --timestamps          Add created_at/updated_at fields
  --soft-delete        Add soft delete capability
```

### API Generation Options

```bash
flask generate-api --help
Options:
  --class_name TEXT     Name of the model class  [required]
  --fields TEXT         Field definitions  [required]
  --prefix TEXT         URL prefix for the API
  --auth               Require authentication
  --roles TEXT         Required roles (comma-separated)
```

### Dashboard Generation Options

```bash
flask generate-dashboard --help
Options:
  --class_name TEXT     Name of the model class  [required]
  --fields TEXT         Field definitions  [required]
  --title TEXT          Dashboard title
  --icon TEXT           Material Design icon name
  --roles TEXT         Required roles (comma-separated)
```

## Examples

### Complete User Management

```bash
# Generate User model
flask generate-model --class_name User --fields "username:string:unique, email:string:unique, password:string, active:boolean" --timestamps

# Generate User API
flask generate-api --class_name User --auth --roles "admin"

# Generate User Dashboard
flask generate-dashboard --class_name User --title "User Management" --icon "mdi-account"
```

### E-commerce Product Catalog

```bash
# Generate Category model
flask generate-model --class_name Category --fields "name:string, description:text"

# Generate Product model
flask generate-model --class_name Product --fields "name:string, description:text, price:decimal, category:relationship(Category)" --timestamps

# Generate APIs
flask generate-api --class_name Category
flask generate-api --class_name Product

# Generate Dashboards
flask generate-dashboard --class_name Category --title "Categories"
flask generate-dashboard --class_name Product --title "Products"
```

## Best Practices

1. Review and customize generated code
2. Add proper validation and error handling
3. Implement proper access control
4. Add tests for generated components
5. Keep OpenAI API key secure
6. Monitor API usage and costs 