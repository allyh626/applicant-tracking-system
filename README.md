# applicant-tracking-system

An internal applicant tracking system for hiring staff, built with Django,
Tailwind CSS + DaisyUI (via django-tailwind-cli) and HTMX. Every page requires
login; staff accounts are created by an administrator in the Django admin.

## Setup

```sh
uv sync                                   # install dependencies into .venv
uv run python manage.py migrate           # create the SQLite database
uv run python manage.py createsuperuser   # your admin account
```

## Run the dev server

```sh
uv run python manage.py tailwind runserver
```

This builds the Tailwind/DaisyUI stylesheet (`assets/css/tailwind.css`, not
committed), watches templates for class changes, and starts Django at
http://127.0.0.1:8000. The first run downloads the Tailwind CLI binary into
`.django_tailwind_cli/`.

## Tests and linting

```sh
uv run pytest
uv run ruff check .
uv run ruff format --check .
```
