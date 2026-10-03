import os
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from fastapi_simple_scaffold.utils import setup_terminal_encoding

setup_terminal_encoding()
console = Console()



def run_doctor():
    console.print()
    console.print(Panel.fit("[bold cyan]🩺 FastAPI Simple Scaffold - System Health Doctor[/bold cyan]", border_style="cyan"))

    project_root = Path.cwd()
    issues = 0

    table = Table(title="Diagnostic Checks", show_header=True, header_style="bold magenta")
    table.add_column("Category", style="cyan", width=18)
    table.add_column("Component", style="white", width=26)
    table.add_column("Status", width=12)
    table.add_column("Details", style="dim")

    # 1. Python Version
    py_ver = sys.version.split()[0]
    if sys.version_info >= (3, 10):
        table.add_row("Environment", "Python Version", "[green]PASS[/green]", f"v{py_ver} (Supported >= 3.10)")
    else:
        table.add_row("Environment", "Python Version", "[red]FAIL[/red]", f"v{py_ver} (Recommend 3.10+)")
        issues += 1

    # 2. Virtual Environment
    in_venv = sys.prefix != sys.base_prefix or "VIRTUAL_ENV" in os.environ
    if in_venv:
        table.add_row("Environment", "Virtualenv", "[green]PASS[/green]", "Active")
    else:
        table.add_row("Environment", "Virtualenv", "[yellow]WARN[/yellow]", "No active virtual environment detected")

    # 3. .env Configuration
    env_file = project_root / ".env"
    if env_file.exists():
        content = env_file.read_text(encoding="utf-8")
        req_keys = ["DATABASE_URL", "SECRET_KEY", "PORT"]
        missing = [k for k in req_keys if f"{k}=" not in content]
        if not missing:
            table.add_row("Configuration", ".env File", "[green]PASS[/green]", "Present with required keys")
        else:
            table.add_row("Configuration", ".env File", "[yellow]WARN[/yellow]", f"Missing keys: {', '.join(missing)}")
            issues += 1
    else:
        table.add_row("Configuration", ".env File", "[red]FAIL[/red]", "Missing .env file (copy from .env.example)")
        issues += 1

    # 4. Folder Structure
    required_dirs = [
        "app/core",
        "app/models",
        "app/modules",
        "app/middleware",
        "app/utils",
        "tests",
    ]
    missing_dirs = [d for d in required_dirs if not (project_root / d).is_dir()]
    if not missing_dirs:
        table.add_row("Structure", "Core Directories", "[green]PASS[/green]", "All required directories present")
    else:
        table.add_row("Structure", "Core Directories", "[yellow]WARN[/yellow]", f"Missing: {', '.join(missing_dirs)}")
        issues += 1

    # 5. Core Dependencies Installed
    packages = ["fastapi", "uvicorn", "sqlalchemy", "pydantic", "alembic"]
    for pkg in packages:
        try:
            __import__(pkg)
            table.add_row("Dependency", pkg, "[green]PASS[/green]", "Installed")
        except ImportError:
            table.add_row("Dependency", pkg, "[yellow]WARN[/yellow]", "Not installed in current environment")

    console.print(table)
    console.print()

    if issues == 0:
        console.print("[bold green]✨ All checks passed! Your FastAPI project environment is in top shape.[/bold green]\n")
    else:
        console.print(f"[bold yellow]⚠️  Found {issues} warning/issue(s). Review recommendations above.[/bold yellow]\n")

    return issues
