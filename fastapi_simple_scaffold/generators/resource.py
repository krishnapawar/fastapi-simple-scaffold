from pathlib import Path
from typing import Optional
from fastapi_simple_scaffold.generators.model import generate_model
from fastapi_simple_scaffold.generators.module import generate_module
from fastapi_simple_scaffold.generators.migration import generate_migration
from fastapi_simple_scaffold.utils import to_snake_case, pluralize, singularize, to_pascal_case


def generate_resource(resource_name: str, target_root: Optional[Path] = None) -> bool:
    """Generate complete resource stack: Model + Module (CRUD) + Migration."""
    project_root = target_root or Path.cwd()
    singular = singularize(to_snake_case(resource_name))
    plural = pluralize(singular)
    pascal_name = to_pascal_case(singular)

    print(f"\n⚡ [bold cyan]Scaffolding Full Resource Stack: {pascal_name}[/bold cyan]\n")

    # 1. Model
    print("1️⃣ Generating SQLAlchemy Model...")
    generate_model(singular, project_root)

    # 2. Module
    print("\n2️⃣ Generating Layered Feature Module (Router, Schemas, Service, Repository)...")
    generate_module(singular, project_root)

    # 3. Migration
    print("\n3️⃣ Generating Database Migration...")
    generate_migration(f"create_{plural}_table", project_root)

    print(f"\n🎉 [bold green]Resource {pascal_name} successfully scaffolded![/bold green]\n")
    return True
