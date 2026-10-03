import ast
import re
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from fastapi_simple_scaffold.utils import setup_terminal_encoding

setup_terminal_encoding()
console = Console()



def scan_main_py_mounts(main_file: Path):
    """Inspect app/main.py to map router names to mount prefixes and extract root routes."""
    mount_map = {}
    main_routes = []

    if not main_file.exists():
        return mount_map, main_routes

    try:
        tree = ast.parse(main_file.read_text(encoding="utf-8"))
    except Exception:
        return mount_map, main_routes

    api_prefix = "/api/v1"
    # Find settings.API_V1_PREFIX or API_V1_PREFIX default
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            # app.include_router(router, prefix=...)
            if isinstance(func, ast.Attribute) and func.attr == "include_router":
                router_name = ""
                if node.args and isinstance(node.args[0], ast.Name):
                    router_name = node.args[0].id

                prefix_val = api_prefix
                for kw in node.keywords:
                    if kw.arg == "prefix":
                        if isinstance(kw.value, ast.Constant):
                            prefix_val = str(kw.value.value)
                        elif isinstance(kw.value, ast.Attribute) and kw.value.attr == "API_V1_PREFIX":
                            prefix_val = api_prefix

                if router_name:
                    mount_map[router_name] = prefix_val

    # Also extract root routes defined on app in main.py (@app.get(...))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call):
                    func = decorator.func
                    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id == "app":
                        method = func.attr.upper()
                        if method in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                            subpath = ""
                            summary = ""
                            tag = "Health / App"
                            if decorator.args and isinstance(decorator.args[0], ast.Constant):
                                subpath = str(decorator.args[0].value)

                            for kw in decorator.keywords:
                                if kw.arg == "summary" and isinstance(kw.value, ast.Constant):
                                    summary = str(kw.value.value)
                                elif kw.arg == "tags" and isinstance(kw.value, ast.List):
                                    if kw.value.elts and isinstance(kw.value.elts[0], ast.Constant):
                                        tag = str(kw.value.elts[0].value)

                            if not summary:
                                doc = ast.get_docstring(node)
                                summary = doc.split("\n")[0].strip() if doc else node.name.replace("_", " ").capitalize()

                            main_routes.append({
                                "method": method,
                                "path": subpath or "/",
                                "summary": summary or "-",
                                "module": tag
                            })

    return mount_map, main_routes


def extract_file_routes(file_path: Path, default_module: str, base_mount: str = "/api/v1"):
    """Parse a router file using AST for 100% reliable endpoint detection."""
    routes = []
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except Exception:
        return routes

    # 1. Determine router prefix from APIRouter(prefix="/...")
    router_prefix = ""
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            func = node.value.func
            is_router = (isinstance(func, ast.Name) and func.id == "APIRouter") or (
                isinstance(func, ast.Attribute) and func.attr == "APIRouter"
            )
            if is_router:
                for kw in node.value.keywords:
                    if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                        router_prefix = str(kw.value.value)

    if not router_prefix:
        router_prefix = f"/{default_module}"

    # 2. Extract decorated functions
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call):
                    func = decorator.func
                    if isinstance(func, ast.Attribute) and func.attr.lower() in [
                        "get", "post", "put", "delete", "patch", "api_route"
                    ]:
                        method = func.attr.upper()
                        subpath = ""
                        summary = ""
                        module_tag = default_module

                        if decorator.args and isinstance(decorator.args[0], ast.Constant):
                            subpath = str(decorator.args[0].value)

                        for kw in decorator.keywords:
                            if kw.arg == "path" and isinstance(kw.value, ast.Constant):
                                subpath = str(kw.value.value)
                            elif kw.arg == "summary" and isinstance(kw.value, ast.Constant):
                                summary = str(kw.value.value)
                            elif kw.arg == "tags" and isinstance(kw.value, ast.List):
                                if kw.value.elts and isinstance(kw.value.elts[0], ast.Constant):
                                    module_tag = str(kw.value.elts[0].value)

                        if not summary:
                            doc = ast.get_docstring(node)
                            summary = doc.split("\n")[0].strip() if doc else node.name.replace("_", " ").capitalize()

                        # Normalize path
                        full_path = f"{base_mount}{router_prefix}{subpath}".replace("//", "/")
                        routes.append({
                            "method": method,
                            "path": full_path,
                            "summary": summary or "-",
                            "module": module_tag,
                        })
    return routes


def scan_routes_statically(project_root: Path):
    """Scan project route files using AST for zero-dependency endpoint listing."""
    routes = []
    main_file = project_root / "app" / "main.py"
    mount_map, main_routes = scan_main_py_mounts(main_file)

    # Add root routes from main.py
    routes.extend(main_routes)

    # Modules
    modules_dir = project_root / "app" / "modules"
    if modules_dir.exists():
        for d in sorted(modules_dir.iterdir()):
            if d.is_dir():
                rf = d / "router.py"
                if rf.exists():
                    routes.extend(extract_file_routes(rf, default_module=d.name, base_mount="/api/v1"))

    # Routers
    routers_dir = project_root / "app" / "routers"
    if routers_dir.exists():
        for rf in sorted(routers_dir.glob("*.py")):
            routes.extend(extract_file_routes(rf, default_module=rf.stem, base_mount="/api/v1"))

    return routes


def list_routes():
    console.print()
    console.print(Panel.fit("[bold green]🗺️  FastAPI Simple Scaffold - Registered API Endpoints[/bold green]", border_style="green"))

    project_root = Path.cwd()
    routes = []

    # Attempt dynamic inspection first if app is importable
    sys.path.insert(0, str(project_root))
    try:
        from app.main import app
        for route in app.routes:
            if hasattr(route, "methods"):
                for m in route.methods:
                    if m in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                        # Exclude automatic openapi/docs internal routes or tag them
                        is_docs = route.path in ["/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"]
                        tag = getattr(route, "tags", None)
                        module_tag = tag[0] if (tag and len(tag) > 0) else ("Docs" if is_docs else "App")
                        summary = getattr(route, "summary", None) or getattr(route, "name", "-")

                        routes.append({
                            "method": m,
                            "path": route.path,
                            "summary": summary,
                            "module": module_tag,
                        })
    except Exception:
        # Fallback to AST static parser
        routes = scan_routes_statically(project_root)

    if not routes:
        console.print("[yellow]No route endpoints found or not currently inside a scaffolded project root.[/yellow]\n")
        return

    # Deduplicate routes preserving order
    seen = set()
    unique_routes = []
    for r in routes:
        key = (r["method"], r["path"])
        if key not in seen:
            seen.add(key)
            unique_routes.append(r)

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Method", width=9, justify="center")
    table.add_column("Endpoint Path", style="bold white", min_width=24)
    table.add_column("Module / Tag", style="dim cyan", min_width=14)
    table.add_column("Summary / Description", style="dim", min_width=20)

    method_colors = {
        "GET": "green",
        "POST": "blue",
        "PUT": "yellow",
        "DELETE": "red",
        "PATCH": "magenta",
    }

    for r in unique_routes:
        m = r["method"]
        color = method_colors.get(m, "white")
        table.add_row(
            f"[{color}]{m}[/{color}]",
            r["path"],
            str(r.get("module", "-")),
            str(r.get("summary", "-")),
        )

    console.print(table)
    console.print(f"\n[dim]Total Endpoints: {len(unique_routes)}[/dim]\n")

