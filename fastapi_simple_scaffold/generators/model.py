from pathlib import Path
from typing import Optional
from fastapi_simple_scaffold.utils import to_snake_case, to_pascal_case, pluralize, singularize


def generate_model(model_name: str, target_root: Optional[Path] = None) -> bool:
    """Generate a new SQLAlchemy 2.0 mapped model."""
    project_root = target_root or Path.cwd()

    singular = singularize(to_snake_case(model_name))
    plural = pluralize(singular)
    pascal_name = to_pascal_case(singular)
    table_name = plural

    models_dir = project_root / "app" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    model_file = models_dir / f"{singular}.py"
    if model_file.exists():
        print(f"⚠️  Model file already exists: app/models/{singular}.py")
        return False

    content = f'''from sqlalchemy import String, Boolean, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.base import TimestampMixin


class {pascal_name}(Base, TimestampMixin):
    __tablename__ = "{table_name}"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<{pascal_name}(id={{self.id}}, name='{{self.name}}')>"
'''

    model_file.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"📄 Created model: app/models/{singular}.py")

    # Update app/models/__init__.py
    init_file = models_dir / "__init__.py"
    if init_file.exists():
        init_content = init_file.read_text(encoding="utf-8")
        import_stmt = f"from app.models.{singular} import {pascal_name}"
        if import_stmt not in init_content:
            lines = init_content.splitlines()
            lines.insert(len(lines) - 2 if len(lines) > 2 else len(lines), import_stmt)
            if "__all__" in init_content:
                # Update __all__ list
                idx = -1
                for i, l in enumerate(lines):
                    if "__all__" in l and "]" in l:
                        lines[i] = l.replace("]", f', "{pascal_name}"]')
                        break
            init_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
            print(f"🔗 Registered {pascal_name} in app/models/__init__.py")

    return True
