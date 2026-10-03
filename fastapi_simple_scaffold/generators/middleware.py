from pathlib import Path
from typing import Optional
from fastapi_simple_scaffold.utils import to_snake_case, to_pascal_case


def generate_middleware(name: str, target_root: Optional[Path] = None) -> bool:
    """Generate a custom FastAPI Starlette middleware."""
    project_root = target_root or Path.cwd()
    snake_name = to_snake_case(name)
    pascal_name = to_pascal_case(snake_name)

    if not pascal_name.endswith("Middleware"):
        class_name = f"{pascal_name}Middleware"
    else:
        class_name = pascal_name

    middleware_dir = project_root / "app" / "middleware"
    middleware_dir.mkdir(parents=True, exist_ok=True)
    file_path = middleware_dir / f"{snake_name}.py"

    if file_path.exists():
        print(f"⚠️  Middleware file already exists: app/middleware/{snake_name}.py")
        return False

    content = f'''from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.utils.logger import logger


class {class_name}(BaseHTTPMiddleware):
    """Custom middleware for {pascal_name}."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Pre-request processing
        logger.debug(f"[{class_name}] Request path: {{request.url.path}}")

        response = await call_next(request)

        # Post-request processing
        return response
'''
    file_path.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"📄 Created middleware: app/middleware/{snake_name}.py")
    return True
