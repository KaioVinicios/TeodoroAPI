# Development Guidelines

This document describes the development standards, architecture, and workflow conventions for this project.

The goal is to ensure **consistency, maintainability, and scalability** across the codebase.

---

# 1. Project Overview

This project is a **Django REST API** designed to expose backend services through HTTP/HTTPS endpoints.

The system follows a **modular architecture**, where each domain responsibility is encapsulated within a Django app.

---

# 2. Project Structure

The project is organized as follows:

setup/ # Main Django project configuration
settings.py # Global project settings
urls.py # Root URL configuration
asgi.py # ASGI configuration
wsgi.py # WSGI configuration

apps/ # Contains all project applications
authentication/ # Authentication app
solicitations/ # Solicitations app
… # Other apps

requirements.txt # Project dependencies
manage.py # Django management script

---

# 3. The `setup` Project

The `setup` directory represents the **core Django project configuration**.

It contains the global configuration used across all applications.

Important files include:

### `settings.py`

This file contains the **main configuration for the entire project**, including:

- Installed applications
- Middleware
- Database configuration
- Authentication settings
- Django REST Framework settings
- Environment variables
- Third-party integrations

All global configurations must be centralized here.

---

# 4. Applications (`apps/`)

All domain logic must be implemented inside applications located in:

./apps
Each application must represent a **specific domain responsibility**.

Examples:

### `authentication`

Responsible for:

- User authentication
- Login and logout processes
- Token management
- Authentication validation

This app **must not contain unrelated business logic**.

---

### `solicitations`

Responsible for:

- Handling solicitations made by users
- Managing solicitation data
- Processing solicitation-related workflows

This app **must not handle authentication logic**.

---

# 5. Separation of Responsibilities

Each app must follow **clear responsibility boundaries**.

Rules:

- Apps must represent **business domains**
- Avoid coupling between apps
- Communication between apps must be done through **services or well-defined interfaces**

Example:

authentication -> handles authentication
solicitations -> handles solicitation processes

---

# 6. Service Layer

Each application must include a **service layer**.

Structure example:

apps/
authentication/
services/
authentication_service.py
token_service.py

Services are responsible for **business logic that is independent of Django's internal framework**.

### Service Rules

Services must:

- Contain **pure Python business logic**
- Avoid direct dependency on views
- Be reusable across multiple parts of the system
- Encapsulate complex operations

Services **should not contain Django-specific code when possible**.

Example:

apps/
solicitations/
services/
create_solicitation.py
validate_solicitation.py

Views should act primarily as **HTTP interface layers**, delegating business logic to services.

---

# 7. Language Standard

All development must be done in **English**.

This includes:

- Variable names
- Function names
- Class names
- Comments
- Commit messages
- Documentation

Example:

Correct:
create_solicitation()

Incorrect:
criar_solicitacao()

Using English ensures **international readability and professional standards**.

---

# 8. Code Formatting

Before making any commit, the code **must be formatted using Black**.

Run:

black .

This ensures consistent formatting across the entire codebase.

Do not commit unformatted code.

---

# 9. Dependency Management

Whenever a new Python package is installed, the dependency list must be updated.

After installing a package, run:

pip freeze > requirements.txt

This ensures that all project dependencies remain synchronized.

---

# 10. Commit Practices

Before committing changes, ensure the following steps are executed:

### 1. Format the code

black .

### 2. Update dependencies (if applicable)

pip freeze > requirements.txt

### 3. Verify application integrity

Ensure:

- No debug code remains
- No unused imports exist
- No temporary test code is committed

### 4. Use Conventional Commits Pattern

Always use Conventional Commits Pattern -> https://www.conventionalcommits.org/en/v1.0.0/

Structure:

commit_type(scope): short description

Example:

feat(authentication): create TokenBlackListView 

---

# 11. General Development Principles

Follow these principles during development:

### Keep apps focused

Each app must have **a single clear responsibility**.

### Prefer services over fat views

Views should remain **thin and focused on request/response handling**.

### Avoid business logic in serializers

Serializers should handle **data validation and transformation only**.

### Write readable code

Prioritize:

- Clear naming
- Small functions
- Explicit logic

---

# 12. Future Improvements

This guideline may evolve as the project grows.

Possible future additions:

- Testing guidelines
- CI/CD practices
- API versioning standards
- Security practices
