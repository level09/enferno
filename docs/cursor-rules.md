# Cursor Rules

## Overview

Enferno has transitioned from template-based AI code generation to a more flexible and powerful approach using Cursor Rules. This modern approach leverages AI-powered IDEs to provide context-aware assistance and code generation.

## What Are Cursor Rules?

Cursor Rules are documentation-as-code specifications that provide guidance to AI assistants in modern IDEs like Cursor. They contain structured information about:

- Code patterns and conventions
- Framework-specific best practices
- Integration techniques
- Component usage examples
- UI/UX standards

## Benefits Over Template-Based Generation

The previous OpenAI code generation approach had several limitations:

1. **Fixed Templates**: Generated code was constrained by pre-defined templates
2. **Limited Context**: Generation happened in isolation from your codebase
3. **API Dependency**: Required external API keys and service availability
4. **Limited Scope**: Only supported specific predefined generation patterns

The Cursor Rules approach offers significant improvements:

1. **Contextual Awareness**: AI assistants understand your entire codebase
2. **Flexible Generation**: Not limited to predefined templates or commands
3. **No External Dependencies**: Works within your development environment
4. **Broader Coverage**: Assists with any development task, not just code scaffolding
5. **Learning Integration**: Rules evolve with your codebase and team knowledge

## Available Rules

Enferno includes rules for key aspects of development:

- **Vue-Jinja Patterns**: Guidance for integrating Vue.js with Flask Jinja templates
- **UI Components**: Standards for Vuetify components and usage
- **Python Standards**: Flask patterns and backend conventions
- **API Design**: RESTful API design patterns

## Using Cursor Rules

To use Cursor Rules with compatible IDEs:

1. Explore the `cursor/rules` directory to see available rules
2. When working in a supported IDE like Cursor, the AI assistant will automatically leverage these rules
3. Ask the assistant for help with specific aspects of Enferno development
4. Reference rule categories in your questions for more targeted assistance

Example prompts:
- "Help me create a data table for users following our UI component patterns"
- "Show me how to integrate Vue with a Jinja template for a product listing page"
- "Generate a RESTful API endpoint for order management following our standards"

## Creating Your Own Rules

As your project evolves, you can extend the rules:

1. Create new markdown files in the `cursor/rules` directory
2. Follow the established format for rule documentation
3. Organize rules by domain area or feature
4. Include concrete examples and best practices
5. Reference existing code patterns when possible

## Future Development

The Cursor Rules approach will continue to evolve with:

- Additional domain-specific rule sets
- More comprehensive examples
- Integration with testing and validation
- Extended documentation coverage

For questions or contributions to the rule set, please refer to our contribution guidelines. 