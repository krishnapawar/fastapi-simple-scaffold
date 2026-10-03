import sys
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from fastapi_simple_scaffold.utils import setup_terminal_encoding

setup_terminal_encoding()
console = Console()


from fastapi_simple_scaffold.doctor import run_doctor
from fastapi_simple_scaffold.generators.cron import generate_cron
from fastapi_simple_scaffold.generators.middleware import generate_middleware
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
from fastapi_simple_scaffold.route_list import list_routes

console = Console()


def run_interactive_menu():
    console.print()
    console.print(Panel.fit(
        "[bold cyan]🛠️  FastAPI Simple Scaffold - Interactive CLI Studio[/bold cyan]\n"
        "[dim]Rapidly build modular production-grade FastAPI applications[/dim]",
        border_style="cyan"
    ))

    menu_text = """[bold white]Select an action to perform:[/bold white]

  [bold green]1)[/bold green]  Create Project Structure (Scaffold Complete Backend)
  [bold green]2)[/bold green]  Scaffold Full Resource (Model + Module + Migration)
  [bold green]3)[/bold green]  Scaffold Layered Module (Router, Schemas, Service, Repo)
  [bold green]4)[/bold green]  Generate SQLAlchemy Model
  [bold green]5)[/bold green]  Generate APIRouter
  [bold green]6)[/bold green]  Generate Service Layer
  [bold green]7)[/bold green]  Generate FastAPI Middleware
  [bold green]8)[/bold green]  Generate Background Cron / Scheduled Job
  [bold green]9)[/bold green]  Generate HTML Email Notification & Mailer
  [bold green]10)[/bold green] Generate Database Seeder
  [bold green]11)[/bold green] Generate Pytest Test Suite
  [bold green]12)[/bold green] Scaffold Model Relationship / Foreign Key
  [bold green]13)[/bold green] View All Registered API Routes
  [bold green]14)[/bold green] Run System Diagnostics & Health Check (Doctor)
  [bold red]0)[/bold red]  Exit
"""
    console.print(menu_text)

    choice = Prompt.ask("[bold yellow]👉 Enter option (0-14)[/bold yellow]", default="1")

    if choice == "1":
        target = Prompt.ask("Enter project folder name (or press Enter for current directory)", default="")
        create_project_structure(target_dir=target if target else None)
    elif choice == "2":
        name = Prompt.ask("Enter Resource Name (e.g. Product, Order)")
        if name:
            generate_resource(name)
    elif choice == "3":
        name = Prompt.ask("Enter Module Name (e.g. Payment, Invoice)")
        if name:
            generate_module(name)
    elif choice == "4":
        name = Prompt.ask("Enter Model Name (e.g. Category)")
        if name:
            generate_model(name)
    elif choice == "5":
        name = Prompt.ask("Enter Router Name (e.g. Report)")
        if name:
            generate_router(name)
    elif choice == "6":
        name = Prompt.ask("Enter Service Name (e.g. PaymentGateway)")
        if name:
            generate_service(name)
    elif choice == "7":
        name = Prompt.ask("Enter Middleware Name (e.g. RateLimiter)")
        if name:
            generate_middleware(name)
    elif choice == "8":
        name = Prompt.ask("Enter Cron Job Name (e.g. DailyCleanup)")
        expr = Prompt.ask("Enter Cron Expression", default="0 0 * * *")
        if name:
            generate_cron(name, expr)
    elif choice == "9":
        name = Prompt.ask("Enter Notification Name (e.g. PasswordReset)")
        if name:
            generate_notification(name)
    elif choice == "10":
        name = Prompt.ask("Enter Seeder Model Name (e.g. Product)")
        if name:
            generate_seeder(name)
    elif choice == "11":
        name = Prompt.ask("Enter Test Suite Name (e.g. Product)")
        if name:
            generate_test(name)
    elif choice == "12":
        src = Prompt.ask("Enter Source Model (e.g. User)")
        tgt = Prompt.ask("Enter Target Model (e.g. Order)")
        rel = Prompt.ask("Enter Relationship Type", choices=["has_many", "belongs_to"], default="has_many")
        if src and tgt:
            generate_relation(src, tgt, rel)
    elif choice == "13":
        list_routes()
    elif choice == "14":
        run_doctor()
    elif choice == "0":
        console.print("[dim]Goodbye![/dim]")
        sys.exit(0)
    else:
        console.print("[red]Invalid selection.[/red]")
