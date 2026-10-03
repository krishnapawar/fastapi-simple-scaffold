from pathlib import Path
from typing import Optional
from fastapi_simple_scaffold.utils import to_snake_case, to_pascal_case, singularize


def generate_service(name: str, target_root: Optional[Path] = None) -> bool:
    """Generate a standalone Service layer."""
    project_root = target_root or Path.cwd()
    singular = singularize(to_snake_case(name))
    pascal_name = to_pascal_case(singular)

    services_dir = project_root / "app" / "services"
    services_dir.mkdir(parents=True, exist_ok=True)
    service_file = services_dir / f"{singular}_service.py"

    if service_file.exists():
        print(f"⚠️  Service file already exists: app/services/{singular}_service.py")
        return False

    content = f'''from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.logger import logger


class {pascal_name}Service:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def execute(self, payload: dict):
        """Execute business logic for {pascal_name}."""
        logger.info(f"Executing {pascal_name}Service with payload: {{payload}}")
        # Add your business logic here
        return {{"status": "processed", "payload": payload}}
'''
    service_file.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"📄 Created service: app/services/{singular}_service.py")
    return True
