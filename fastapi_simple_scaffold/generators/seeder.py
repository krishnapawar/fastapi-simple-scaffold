from pathlib import Path
from typing import Optional
from fastapi_simple_scaffold.utils import to_snake_case, to_pascal_case, pluralize, singularize


def generate_seeder(name: str, target_root: Optional[Path] = None) -> bool:
    """Generate a database seeder script."""
    project_root = target_root or Path.cwd()
    singular = singularize(to_snake_case(name))
    plural = pluralize(singular)
    pascal_name = to_pascal_case(singular)

    seeders_dir = project_root / "app" / "database" / "seeders"
    seeders_dir.mkdir(parents=True, exist_ok=True)
    seeder_file = seeders_dir / f"{singular}_seeder.py"

    if seeder_file.exists():
        print(f"⚠️  Seeder file already exists: app/database/seeders/{singular}_seeder.py")
        return False

    content = f'''import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.{singular} import {pascal_name}
from app.utils.logger import logger


async def seed_{plural}():
    async with AsyncSessionLocal() as session:
        # Check if dummy record exists
        stmt = select({pascal_name}).limit(1)
        res = await session.execute(stmt)
        item = res.scalars().first()

        if not item:
            sample = {pascal_name}(
                name="Sample {pascal_name}",
                description="Seeded initial data record",
                is_active=True,
            )
            session.add(sample)
            await session.commit()
            logger.info("✅ Seeded initial {pascal_name} record")
        else:
            logger.info("ℹ️ {pascal_name} records already present. Skipping.")


if __name__ == "__main__":
    asyncio.run(seed_{plural}())
'''
    seeder_file.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"📄 Created seeder: app/database/seeders/{singular}_seeder.py")
    return True
