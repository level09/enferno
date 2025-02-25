# Vue and Jinja Integration Patterns

## Vue Delimiters with Jinja
- When using Jinja templates, set Vue custom delimiters to `${ }` to avoid conflict with Jinja's `{{ }}` syntax
- Example: `delimiters: ["${", "}"]`

## Component Lifecycle
- Use the `mounted()` lifecycle hook for initial data loading
- Example:
```javascript
mounted() {
    this.refresh();
}
```

## State Management
- Follow Vue.js patterns for state management and reactivity
- Use Vue's reactivity system for data binding
- Keep component data in the `data()` function
- Example:
```javascript
data() {
    return {
        items: [],
        itemsLength: 0,
        // other reactive properties
    };
}
```

## API Calls
- Keep API calls in methods and use async/await or promises
- Use axios for HTTP requests
- Example:
```javascript
methods: {
    refresh() {
        axios.get('/api/endpoint').then(res => {
            this.items = res.data.items;
            this.itemsLength = res.data.total;
        });
    }
}
```

## Client-Side Implementation
- Write Vue code directly in client-side JavaScript without build tools
- Include Vue and Vuetify via CDN or local files 