# 🚀 fastapi-simple-scaffold

> **Modular FastAPI, SQLAlchemy 2.0 & Alembic REST API Scaffolding & CLI Code Generator**

`fastapi-simple-scaffold` is a powerful CLI tool and code generator that scaffolds production-ready, modular FastAPI backend projects and component stacks (modules, models, routers, services, middleware, migrations, seeders, relationships, cron jobs, background tasks, email notifications, and pytest suites) in seconds.

---

## ⚡ Step 1: Setup Virtual Environment & Install CLI

Create and activate a virtual environment, then install `fastapi-simple-scaffold`:

```bash
# Windows (PowerShell / Command Prompt)
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Install CLI Generator
pip install fastapi-simple-scaffold
```

> 💡 **Note:** Once installed, you can use `fastapi-scaffold` (or shortcut `fscaffold`). If running in a global environment without PATH configured, use `python -m fastapi_simple_scaffold.cli [command]` as fallback.

---

## 🚀 Step 2: Create a New FastAPI Project

Generate a complete modular backend project:

```bash
# Create project structure in a new directory:
fastapi-scaffold my-api

# Or initialize structure inside current working directory:
cd my-api
fastapi-scaffold structure
```

---

## 🏁 Step 3: Install Project Dependencies & Run Server

Navigate into your newly scaffolded project directory, install its dependencies, and start the development server:

```bash
cd my-api
pip install -r requirements.txt
python run.py
```

Your API with Swagger UI is live at: **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)** 🎉

---

## 🛠️ Step 4: Generator Commands (Scaffold Components On-the-Fly)

Once inside your project directory (`cd my-api`), use generator commands to build resources, modules, models, and services:

```bash
# Launch interactive CLI Dashboard Studio
fastapi-scaffold

# Scaffold a full resource stack (Model + Migration + Module)
fastapi-scaffold make:resource Product

# Generate a layered feature module (Router, Schemas, Service, Repository)
fastapi-scaffold make:module Payment

# Generate a SQLAlchemy 2.0 mapped model
fastapi-scaffold make:model Order

# Generate a standalone APIRouter
fastapi-scaffold make:router Invoice

# Generate a Service business logic layer
fastapi-scaffold make:service Analytics

# Generate custom FastAPI / Starlette middleware
fastapi-scaffold make:middleware RateLimiter

# Generate a timestamped Alembic database migration
fastapi-scaffold make:migration create_orders_table

# Apply pending database migrations
fastapi-scaffold db:migrate

# Generate a database seeder script
fastapi-scaffold make:seeder Product

# Scaffold foreign key relationship between models
fastapi-scaffold make:relation User Order has_many

# Generate an HTML email notification service & template
fastapi-scaffold make:notification WelcomeEmail

# Generate a scheduled cron / background worker job
fastapi-scaffold make:cron DailyReport "0 0 * * *"

# Generate an automated pytest test suite
fastapi-scaffold make:test Product

# Display formatted table of all registered API endpoints
fastapi-scaffold route:list

# Run system health diagnostics
fastapi-scaffold doctor
```

---

## 📋 Command Reference Table

| Command | Shortcut / Alias | Description |
|---|---|---|
| `fastapi-scaffold` | `fscaffold` | Interactive CLI studio dashboard |
| `fastapi-scaffold [dir]` | `fastapi-scaffold init [dir]` | Generate complete backend project structure |
| `make:resource <Name>` | `make:resource Product` | Full resource stack (`Model` + `Module` + `Migration`) |
| `make:module <Name>` | `make:module Payment` | Layered feature module (`Router`, `Schemas`, `Service`, `Repository`) |
| `make:model <Name>` | `make:model Vehicle` | Generates SQLAlchemy 2.0 mapped model |
| `make:router <Name>` | `make:controller <Name>` | Generates a standalone APIRouter |
| `make:service <Name>` | `make:service Payment` | Generates a service class |
| `make:middleware <Name>` | `make:middleware Auth` | Generates custom Starlette/FastAPI middleware |
| `make:migration <Name>` | `make:migration add_orders` | Generates timestamped Alembic migration revision |
| `db:migrate` | `db:upgrade` | Applies all pending Alembic database migrations |
| `make:seeder <Name>` | `make:seed <Name>` | Generates database seeder script |
| `make:relation <Src> <Tgt>` | `make:association User Order` | Scaffolds model foreign key relationship |
| `make:notification <Name>` | `make:email <Name>` | Generates email notification service and HTML template |
| `make:cron <Name> [expr]` | `make:job <Name>` | Generates scheduled background worker job |
| `make:test <Name>` | `make:test Auth` | Generates automated pytest test suite |
| `route:list` | `routes` | Displays formatted table of all registered endpoints |
| `doctor` | `cli:doctor` | Performs health check on env, DB, and dependencies |

---

## 📂 Project Structure Generated

Running `fastapi-scaffold my-api` creates a clean, modular layout:

```text
my-api/
├── app/
│   ├── core/               # Settings (Pydantic), DB Engine, Security, Lifespan
│   ├── models/             # SQLAlchemy 2.0 mapped models
│   ├── modules/            # Domain feature modules (Auth, Users, etc.)
│   │   └── [feature]/
│   │       ├── router.py       # API endpoints & dependency injection
│   │       ├── schemas.py      # Pydantic v2 schemas
│   │       ├── service.py      # Business logic
│   │       └── repository.py   # SQLAlchemy database queries
│   ├── middleware/         # CORS, Timing, Error Handlers
│   ├── notifications/      # HTML email templates & mailer services
│   ├── jobs/               # Background tasks & cron scheduler
│   ├── utils/              # Standard JSON response envelope & logger
│   ├── database/           # Seeders & DB initializers
│   └── main.py             # FastAPI entrypoint with OpenAPI docs
├── alembic/                # Alembic database migrations
├── tests/                  # Automated integration & unit tests
├── .env.example            # Environment configuration template
├── .env                    # Active local environment
├── requirements.txt        # Production dependencies
├── run.py                  # Dev server runner
└── README.md
```

---

## 📄 License

MIT License - Developed with ❤️ by **Krishna Pawar**.
