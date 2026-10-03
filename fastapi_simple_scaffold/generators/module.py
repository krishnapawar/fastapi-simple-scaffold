import os
from pathlib import Path
from typing import Optional
from fastapi_simple_scaffold.utils import to_snake_case, to_pascal_case, pluralize, singularize


def generate_module(module_name: str, target_root: Optional[Path] = None) -> bool:
    """Generate a complete layered module: router, schemas, service, repository."""
    project_root = target_root or Path.cwd()

    singular = singularize(to_snake_case(module_name))
    plural = pluralize(singular)
    pascal_name = to_pascal_case(singular)
    plural_pascal = to_pascal_case(plural)

    module_dir = project_root / "app" / "modules" / plural
    module_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n🚀 Scaffolding layered module: [bold green]{pascal_name}[/bold green] -> app/modules/{plural}/\n")

    # 1. __init__.py
    init_file = module_dir / "__init__.py"
    if not init_file.exists():
        with open(init_file, "w", encoding="utf-8") as f:
            f.write(f'from app.modules.{plural}.router import router\n\n__all__ = ["router"]\n')

    # 2. schemas.py
    schemas_file = module_dir / "schemas.py"
    if not schemas_file.exists():
        with open(schemas_file, "w", encoding="utf-8") as f:
            f.write(f'''from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class {pascal_name}Base(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Name of the {singular}")
    description: Optional[str] = Field(None, max_length=1000)
    is_active: bool = Field(True, description="Active status")


class {pascal_name}Create({pascal_name}Base):
    pass


class {pascal_name}Update(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class {pascal_name}Response({pascal_name}Base):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class {pascal_name}ListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    items: List[{pascal_name}Response]
''')
        print(f"  📄 Created: app/modules/{plural}/schemas.py")
    else:
        print(f"  ⚠️ Skipped: app/modules/{plural}/schemas.py (already exists)")

    # 3. repository.py
    repo_file = module_dir / "repository.py"
    if not repo_file.exists():
        with open(repo_file, "w", encoding="utf-8") as f:
            f.write(f'''from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.{singular} import {pascal_name}


class {pascal_name}Repository:
    @staticmethod
    async def get_by_id(db: AsyncSession, item_id: int) -> Optional[{pascal_name}]:
        stmt = select({pascal_name}).where({pascal_name}.id == item_id)
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[{pascal_name}], int]:
        query = select({pascal_name})
        count_query = select(func.count({pascal_name}.id))

        if search:
            query = query.where({pascal_name}.name.ilike(f"%{{search}}%"))
            count_query = count_query.where({pascal_name}.name.ilike(f"%{{search}}%"))

        if is_active is not None:
            query = query.where({pascal_name}.is_active == is_active)
            count_query = count_query.where({pascal_name}.is_active == is_active)

        total_res = await db.execute(count_query)
        total = total_res.scalar() or 0

        query = query.order_by({pascal_name}.id.desc()).offset(skip).limit(limit)
        items_res = await db.execute(query)
        items = list(items_res.scalars().all())

        return items, total

    @staticmethod
    async def create(db: AsyncSession, data: dict) -> {pascal_name}:
        item = {pascal_name}(**data)
        db.add(item)
        await db.flush()
        await db.refresh(item)
        return item

    @staticmethod
    async def update(db: AsyncSession, item: {pascal_name}, data: dict) -> {pascal_name}:
        for key, value in data.items():
            if value is not None:
                setattr(item, key, value)
        await db.flush()
        await db.refresh(item)
        return item

    @staticmethod
    async def delete(db: AsyncSession, item: {pascal_name}) -> None:
        await db.delete(item)
        await db.flush()
''')
        print(f"  📄 Created: app/modules/{plural}/repository.py")
    else:
        print(f"  ⚠️ Skipped: app/modules/{plural}/repository.py (already exists)")

    # 4. service.py
    service_file = module_dir / "service.py"
    if not service_file.exists():
        with open(service_file, "w", encoding="utf-8") as f:
            f.write(f'''from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.{plural}.repository import {pascal_name}Repository
from app.modules.{plural}.schemas import {pascal_name}Create, {pascal_name}Update


class {pascal_name}Service:
    @staticmethod
    async def get_all(db: AsyncSession, skip: int = 0, limit: int = 20, search: Optional[str] = None):
        return await {pascal_name}Repository.get_all(db, skip=skip, limit=limit, search=search)

    @staticmethod
    async def get_by_id(db: AsyncSession, item_id: int):
        item = await {pascal_name}Repository.get_by_id(db, item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{pascal_name} with id {{item_id}} not found"
            )
        return item

    @staticmethod
    async def create(db: AsyncSession, data: {pascal_name}Create):
        return await {pascal_name}Repository.create(db, data.model_dump())

    @staticmethod
    async def update(db: AsyncSession, item_id: int, data: {pascal_name}Update):
        item = await {pascal_name}Service.get_by_id(db, item_id)
        return await {pascal_name}Repository.update(db, item, data.model_dump(exclude_unset=True))

    @staticmethod
    async def delete(db: AsyncSession, item_id: int):
        item = await {pascal_name}Service.get_by_id(db, item_id)
        await {pascal_name}Repository.delete(db, item)
        return True
''')
        print(f"  📄 Created: app/modules/{plural}/service.py")
    else:
        print(f"  ⚠️ Skipped: app/modules/{plural}/service.py (already exists)")

    # 5. router.py
    router_file = module_dir / "router.py"
    if not router_file.exists():
        with open(router_file, "w", encoding="utf-8") as f:
            f.write(f'''from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.modules.{plural}.schemas import {pascal_name}Create, {pascal_name}Update, {pascal_name}Response
from app.modules.{plural}.service import {pascal_name}Service
from app.utils.response import success_response

router = APIRouter(prefix="/{plural}", tags=["{plural_pascal}"])


@router.get("", summary="List all {plural}")
async def list_{plural}(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve paginated list of {plural}."""
    items, total = await {pascal_name}Service.get_all(db, skip=skip, limit=limit, search=search)
    return success_response(
        data={{
            "total": total,
            "skip": skip,
            "limit": limit,
            "items": [{pascal_name}Response.model_validate(item) for item in items],
        }},
        message="{plural_pascal} retrieved successfully",
    )


@router.get("/{{item_id}}", summary="Get {singular} by ID")
async def get_{singular}(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single {singular} by its primary ID."""
    item = await {pascal_name}Service.get_by_id(db, item_id)
    return success_response(
        data={pascal_name}Response.model_validate(item),
        message="{pascal_name} found",
    )


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create new {singular}")
async def create_{singular}(
    data: {pascal_name}Create,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new {singular}."""
    item = await {pascal_name}Service.create(db, data)
    return success_response(
        data={pascal_name}Response.model_validate(item),
        message="{pascal_name} created successfully",
        status_code=status.HTTP_201_CREATED,
    )


@router.put("/{{item_id}}", summary="Update {singular}")
async def update_{singular}(
    item_id: int,
    data: {pascal_name}Update,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing {singular}."""
    item = await {pascal_name}Service.update(db, item_id, data)
    return success_response(
        data={pascal_name}Response.model_validate(item),
        message="{pascal_name} updated successfully",
    )


@router.delete("/{{item_id}}", summary="Delete {singular}")
async def delete_{singular}(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a {singular} by ID."""
    await {pascal_name}Service.delete(db, item_id)
    return success_response(data=None, message="{pascal_name} deleted successfully")
''')
        print(f"  📄 Created: app/modules/{plural}/router.py")
    else:
        print(f"  ⚠️ Skipped: app/modules/{plural}/router.py (already exists)")

    # 6. Auto-register in app/main.py
    main_file = project_root / "app" / "main.py"
    if main_file.exists():
        content = main_file.read_text(encoding="utf-8")
        import_stmt = f"from app.modules.{plural}.router import router as {plural}_router"
        include_stmt = f"app.include_router({plural}_router, prefix=settings.API_V1_PREFIX)"

        if import_stmt not in content:
            lines = content.splitlines()
            # find last router import
            insert_idx = -1
            for i, line in enumerate(lines):
                if "import router as" in line:
                    insert_idx = i + 1

            if insert_idx != -1:
                lines.insert(insert_idx, import_stmt)
            else:
                lines.insert(5, import_stmt)

            # find where routers are included
            inc_idx = -1
            for i, line in enumerate(lines):
                if "app.include_router" in line:
                    inc_idx = i + 1

            if inc_idx != -1:
                lines.insert(inc_idx, include_stmt)
            else:
                lines.append(include_stmt)

            main_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
            print(f"  🔗 Auto-registered router in app/main.py")

    return True
