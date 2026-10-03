from pathlib import Path
from typing import Optional
from fastapi_simple_scaffold.utils import to_snake_case, to_pascal_case, pluralize, singularize


def generate_router(name: str, target_root: Optional[Path] = None) -> bool:
    """Generate standalone APIRouter file."""
    project_root = target_root or Path.cwd()
    singular = singularize(to_snake_case(name))
    plural = pluralize(singular)
    pascal_name = to_pascal_case(singular)

    router_dir = project_root / "app" / "routers"
    router_dir.mkdir(parents=True, exist_ok=True)
    router_file = router_dir / f"{plural}.py"

    if router_file.exists():
        print(f"⚠️  Router already exists: app/routers/{plural}.py")
        return False

    content = f'''from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.utils.response import success_response

router = APIRouter(prefix="/{plural}", tags=["{to_pascal_case(plural)}"])


@router.get("", summary="Get all {plural}")
async def list_{plural}(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return success_response(data=[], message="{plural} retrieved successfully")


@router.get("/{{item_id}}", summary="Get {singular} by ID")
async def get_{singular}(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return success_response(data={{"id": item_id}}, message="{singular} found")
'''
    router_file.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"📄 Created router: app/routers/{plural}.py")
    return True
