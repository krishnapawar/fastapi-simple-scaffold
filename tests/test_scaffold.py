import shutil
import tempfile
from pathlib import Path
import pytest

from fastapi_simple_scaffold.utils import (
    to_snake_case,
    to_pascal_case,
    pluralize,
    singularize,
)
from fastapi_simple_scaffold.generators.project import create_project_structure
from fastapi_simple_scaffold.generators.model import generate_model
from fastapi_simple_scaffold.generators.module import generate_module
from fastapi_simple_scaffold.generators.resource import generate_resource
from fastapi_simple_scaffold.generators.router import generate_router
from fastapi_simple_scaffold.generators.service import generate_service
from fastapi_simple_scaffold.generators.middleware import generate_middleware
from fastapi_simple_scaffold.generators.migration import generate_migration
from fastapi_simple_scaffold.generators.seeder import generate_seeder
from fastapi_simple_scaffold.generators.cron import generate_cron
from fastapi_simple_scaffold.generators.notification import generate_notification
from fastapi_simple_scaffold.generators.relation import generate_relation
from fastapi_simple_scaffold.generators.test import generate_test
from fastapi_simple_scaffold.route_list import scan_routes_statically


@pytest.fixture
def temp_project():
    temp_dir = tempfile.mkdtemp()
    project_path = Path(temp_dir)
    # Generate base structure
    create_project_structure(target_dir=str(project_path))
    yield project_path
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_naming_utils():
    assert to_snake_case("UserProfile") == "user_profile"
    assert to_snake_case("userProfile") == "user_profile"
    assert to_snake_case("user-profile") == "user_profile"

    assert to_pascal_case("user_profile") == "UserProfile"
    assert to_pascal_case("user-profile") == "UserProfile"

    assert pluralize("product") == "products"
    assert pluralize("category") == "categories"
    assert singularize("products") == "product"
    assert singularize("categories") == "category"


def test_project_structure_generation(temp_project):
    assert (temp_project / "app" / "main.py").exists()
    assert (temp_project / "app" / "core" / "config.py").exists()
    assert (temp_project / "app" / "core" / "database.py").exists()
    assert (temp_project / "app" / "core" / "security.py").exists()
    assert (temp_project / "app" / "models" / "user.py").exists()
    assert (temp_project / "app" / "modules" / "auth" / "router.py").exists()
    assert (temp_project / "app" / "modules" / "users" / "router.py").exists()
    assert (temp_project / "requirements.txt").exists()
    assert (temp_project / ".env.example").exists()
    assert (temp_project / "run.py").exists()


def test_make_model(temp_project):
    success = generate_model("Product", target_root=temp_project)
    assert success is True
    model_file = temp_project / "app" / "models" / "product.py"
    assert model_file.exists()
    content = model_file.read_text(encoding="utf-8")
    assert "class Product(Base, TimestampMixin):" in content
    assert '__tablename__ = "products"' in content

    # Test registered in __init__.py
    init_content = (temp_project / "app" / "models" / "__init__.py").read_text(encoding="utf-8")
    assert "from app.models.product import Product" in init_content


def test_make_module(temp_project):
    success = generate_module("Product", target_root=temp_project)
    assert success is True
    mod_dir = temp_project / "app" / "modules" / "products"
    assert (mod_dir / "router.py").exists()
    assert (mod_dir / "schemas.py").exists()
    assert (mod_dir / "service.py").exists()
    assert (mod_dir / "repository.py").exists()

    # Check router registered in main.py
    main_content = (temp_project / "app" / "main.py").read_text(encoding="utf-8")
    assert "from app.modules.products.router import router as products_router" in main_content


def test_make_resource(temp_project):
    success = generate_resource("Order", target_root=temp_project)
    assert success is True
    assert (temp_project / "app" / "models" / "order.py").exists()
    assert (temp_project / "app" / "modules" / "orders" / "router.py").exists()

    # Check migration created
    versions = list((temp_project / "alembic" / "versions").glob("*create_orders_table.py"))
    assert len(versions) == 1


def test_make_router_service_middleware(temp_project):
    assert generate_router("Invoice", target_root=temp_project) is True
    assert (temp_project / "app" / "routers" / "invoices.py").exists()

    assert generate_service("PaymentGateway", target_root=temp_project) is True
    assert (temp_project / "app" / "services" / "payment_gateway_service.py").exists()

    assert generate_middleware("RateLimiter", target_root=temp_project) is True
    assert (temp_project / "app" / "middleware" / "rate_limiter.py").exists()


def test_make_cron_and_notification(temp_project):
    assert generate_cron("DailyCleanup", "0 0 * * *", target_root=temp_project) is True
    assert (temp_project / "app" / "jobs" / "daily_cleanup_job.py").exists()

    assert generate_notification("Welcome", target_root=temp_project) is True
    assert (temp_project / "app" / "notifications" / "welcome_service.py").exists()
    assert (temp_project / "app" / "notifications" / "templates" / "welcome.html").exists()


def test_make_relation(temp_project):
    generate_model("Customer", target_root=temp_project)
    generate_model("Invoice", target_root=temp_project)
    success = generate_relation("Customer", "Invoice", "has_many", target_root=temp_project)
    assert success is True

    cust_content = (temp_project / "app" / "models" / "customer.py").read_text(encoding="utf-8")
    inv_content = (temp_project / "app" / "models" / "invoice.py").read_text(encoding="utf-8")

    assert "invoices: Mapped[List[\"Invoice\"]]" in cust_content
    assert "customer_id: Mapped[int]" in inv_content


def test_make_test(temp_project):
    assert generate_test("Product", target_root=temp_project) is True
    assert (temp_project / "tests" / "test_products.py").exists()


def test_scan_routes_statically(temp_project):
    routes = scan_routes_statically(temp_project)
    paths = [r["path"] for r in routes]
    assert any("/auth" in p for p in paths)
    assert any("/users" in p for p in paths)
