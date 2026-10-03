import sys
from rich.console import Console
from rich.panel import Panel

from fastapi_simple_scaffold.utils import setup_terminal_encoding
setup_terminal_encoding()

from fastapi_simple_scaffold.doctor import run_doctor

from fastapi_simple_scaffold.generators.cron import generate_cron
from fastapi_simple_scaffold.generators.middleware import generate_middleware
from fastapi_simple_scaffold.generators.migration import generate_migration, run_db_migrate
from fastapi_simple_scaffold.generators.model import generate_model

from fastapi_simple_scaffold.generators.module import generate_module
from fastapi_simple_scaffold.generators.notification import generate_notification
from fastapi_simple_scaffold.generators.project import create_project_structure
from fastapi_simple_scaffold.generators.relation import generate_relation
from fastapi_simple_scaffold.generators.resource import generate_resource
from fastapi_simple_scaffold.generators.router import generate_router
from fastapi_simple_scaffold.generators.seeder import generate_seeder
from fastapi_simple_scaffold.generators.service import generate_service
from fastapi_simple_scaffold.generators.test import generate_test
from fastapi_simple_scaffold.interactive import run_interactive_menu
from fastapi_simple_scaffold.route_list import list_routes

console = Console()

COMMANDS_DOC = {
    "structure": "Generate complete modular FastAPI project structure",
    "init": "Generate complete modular FastAPI project structure",
    "new": "Generate complete modular FastAPI project structure",
    "create": "Generate complete modular FastAPI project structure",
    "make:resource": "Scaffold full resource stack (Model + Migration + Module)",
    "make:module": "Scaffold layered feature module (Router, Schemas, Service, Repo)",
    "make:model": "Generate a new SQLAlchemy 2.0 mapped model",
    "make:router": "Generate a new APIRouter file",
    "make:controller": "Generate a new APIRouter file",
    "make:service": "Generate a new Service class",
    "make:middleware": "Generate a new FastAPI middleware",
    "make:migration": "Generate an Alembic database migration file",
    "make:seeder": "Generate a database seeder script",
    "make:notification": "Generate an HTML email notification service",
    "make:email": "Generate an HTML email notification service",
    "make:cron": "Generate a background scheduled cron job",
    "make:job": "Generate a background scheduled cron job",
    "make:relation": "Scaffold SQLAlchemy relationship between two models",
    "make:test": "Generate a pytest test suite file",
    "db:migrate": "Apply pending Alembic database migrations (alembic upgrade head)",
    "db:upgrade": "Apply pending Alembic database migrations (alembic upgrade head)",
    "route:list": "Display formatted table of all registered API endpoints",

    "routes": "Display formatted table of all registered API endpoints",
    "doctor": "Run system health check & diagnostics",
}


def print_help():
    console.print()
    console.print(Panel.fit(
        "[bold cyan]🛠️  FastAPI Simple Scaffold CLI Tool[/bold cyan]\n"
        "[dim]Rapidly build modular production-ready FastAPI REST APIs[/dim]",
        border_style="cyan"
    ))
    console.print("[bold white]Usage:[/bold white] [green]fastapi-scaffold[/green] [yellow][command|project-name][/yellow] [cyan][options][/cyan]\n")
    console.print("[bold magenta]Available Commands:[/bold magenta]")
    console.print("═" * 76)
    for cmd, desc in COMMANDS_DOC.items():
        console.print(f"  [bold green]{cmd:<18}[/bold green] [white]{desc}[/white]")
    console.print("═" * 76)
    console.print("\n[bold magenta]Examples:[/bold magenta]")
    console.print("  [dim]# Launch interactive dashboard:[/dim]")
    console.print("  [cyan]fastapi-scaffold[/cyan]")
    console.print("  [dim]# Generate project in new directory:[/dim]")
    console.print("  [cyan]fastapi-scaffold my-api[/cyan]")
    console.print("  [dim]# Scaffold full resource stack:[/dim]")
    console.print("  [cyan]fastapi-scaffold make:resource Product[/cyan]")
    console.print("  [dim]# Scaffold relationships:[/dim]")
    console.print("  [cyan]fastapi-scaffold make:relation User Order has_many[/cyan]")
    console.print("  [dim]# List registered endpoints:[/dim]")
    console.print("  [cyan]fastapi-scaffold route:list[/cyan]")
    console.print("  [dim]# Environment health check:[/dim]")
    console.print("  [cyan]fastapi-scaffold doctor[/cyan]\n")


def main():
    args = sys.argv[1:]

    # 1. No arguments -> Launch Interactive Menu
    if not args:
        run_interactive_menu()
        return

    cmd = args[0]
    extra = args[1:]

    if cmd in ["--help", "-h", "help"]:
        print_help()
        return

    # Check flags
    force = "--force" in extra or "-f" in extra
    clean_extra = [a for a in extra if not a.startswith("-")]

    # Dispatch commands
    if cmd in ["structure", "init", "new", "create"]:
        target = clean_extra[0] if clean_extra else None
        create_project_structure(target_dir=target, force=force)

    elif cmd == "make:resource":
        if not clean_extra:
            console.print("[bold red]❌ Please provide a resource name.[/bold red] Example: [cyan]fastapi-scaffold make:resource Product[/cyan]")
            sys.exit(1)
        generate_resource(clean_extra[0])

    elif cmd == "make:module":
        if not clean_extra:
            console.print("[bold red]❌ Please provide a module name.[/bold red] Example: [cyan]fastapi-scaffold make:module Payment[/cyan]")
            sys.exit(1)
        generate_module(clean_extra[0])

    elif cmd == "make:model":
        if not clean_extra:
            console.print("[bold red]❌ Please provide a model name.[/bold red] Example: [cyan]fastapi-scaffold make:model Category[/cyan]")
            sys.exit(1)
        generate_model(clean_extra[0])

    elif cmd in ["make:router", "make:controller"]:
        if not clean_extra:
            console.print("[bold red]❌ Please provide a router name.[/bold red] Example: [cyan]fastapi-scaffold make:router Invoice[/cyan]")
            sys.exit(1)
        generate_router(clean_extra[0])

    elif cmd == "make:service":
        if not clean_extra:
            console.print("[bold red]❌ Please provide a service name.[/bold red] Example: [cyan]fastapi-scaffold make:service Analytics[/cyan]")
            sys.exit(1)
        generate_service(clean_extra[0])

    elif cmd == "make:middleware":
        if not clean_extra:
            console.print("[bold red]❌ Please provide a middleware name.[/bold red] Example: [cyan]fastapi-scaffold make:middleware RateLimiter[/cyan]")
            sys.exit(1)
        generate_middleware(clean_extra[0])

    elif cmd in ["make:migration", "model:migration"]:
        name = clean_extra[0] if clean_extra else "auto_migration"
        generate_migration(name)

    elif cmd in ["db:migrate", "db:upgrade"]:
        run_db_migrate()


    elif cmd in ["make:seeder", "make:seed"]:
        if not clean_extra:
            console.print("[bold red]❌ Please provide a seeder model name.[/bold red] Example: [cyan]fastapi-scaffold make:seeder Product[/cyan]")
            sys.exit(1)
        generate_seeder(clean_extra[0])

    elif cmd in ["make:notification", "make:email"]:
        if not clean_extra:
            console.print("[bold red]❌ Please provide a notification name.[/bold red] Example: [cyan]fastapi-scaffold make:notification Welcome[/cyan]")
            sys.exit(1)
        generate_notification(clean_extra[0])

    elif cmd in ["make:cron", "make:job", "make:schedule"]:
        if not clean_extra:
            console.print("[bold red]❌ Please provide a job name.[/bold red] Example: [cyan]fastapi-scaffold make:cron DailyReport '0 0 * * *'[/cyan]")
            sys.exit(1)
        name = clean_extra[0]
        expr = clean_extra[1] if len(clean_extra) > 1 else "0 0 * * *"
        generate_cron(name, expr)

    elif cmd in ["make:relation", "make:association"]:
        if len(clean_extra) < 2:
            console.print("[bold red]❌ Please provide source and target models.[/bold red] Example: [cyan]fastapi-scaffold make:relation User Order has_many[/cyan]")
            sys.exit(1)
        src = clean_extra[0]
        tgt = clean_extra[1]
        rel_type = clean_extra[2] if len(clean_extra) > 2 else "has_many"
        generate_relation(src, tgt, rel_type)

    elif cmd == "make:test":
        if not clean_extra:
            console.print("[bold red]❌ Please provide a test suite name.[/bold red] Example: [cyan]fastapi-scaffold make:test Product[/cyan]")
            sys.exit(1)
        generate_test(clean_extra[0])

    elif cmd in ["route:list", "routes"]:
        list_routes()

    elif cmd in ["doctor", "cli:doctor"]:
        run_doctor()

    else:
        # If not recognized and doesn't start with "-", treat as project folder name
        if not cmd.startswith("-"):
            create_project_structure(target_dir=cmd, force=force)
        else:
            console.print(f"[bold red]❌ Unknown command:[/bold red] '{cmd}'\n")
            print_help()
            sys.exit(1)


if __name__ == "__main__":
    main()
