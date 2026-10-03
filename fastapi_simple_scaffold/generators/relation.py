from pathlib import Path
from typing import Optional
from fastapi_simple_scaffold.utils import to_snake_case, to_pascal_case, pluralize, singularize


def generate_relation(
    source_model: str,
    target_model: str,
    relation_type: str = "has_many",
    target_root: Optional[Path] = None,
) -> bool:
    """Scaffold a relationship between two SQLAlchemy models."""
    project_root = target_root or Path.cwd()

    src_singular = singularize(to_snake_case(source_model))
    tgt_singular = singularize(to_snake_case(target_model))
    src_pascal = to_pascal_case(src_singular)
    tgt_pascal = to_pascal_case(tgt_singular)
    src_plural = pluralize(src_singular)
    tgt_plural = pluralize(tgt_singular)

    src_file = project_root / "app" / "models" / f"{src_singular}.py"
    tgt_file = project_root / "app" / "models" / f"{tgt_singular}.py"

    norm_rel = relation_type.lower().replace("-", "_")

    print(f"\n🔗 Scaffolding SQLAlchemy relation: {src_pascal} -> {norm_rel} -> {tgt_pascal}")

    if not src_file.exists():
        print(f"❌ Source model file not found: app/models/{src_singular}.py")
        return False
    if not tgt_file.exists():
        print(f"❌ Target model file not found: app/models/{tgt_singular}.py")
        return False

    src_code = src_file.read_text(encoding="utf-8")
    tgt_code = tgt_file.read_text(encoding="utf-8")

    # Ensure relationship and ForeignKey imports
    for file, code in [(src_file, src_code), (tgt_file, tgt_code)]:
        if "from sqlalchemy.orm import" in code and "relationship" not in code:
            code = code.replace("from sqlalchemy.orm import", "from sqlalchemy.orm import relationship, ")
            file.write_text(code, encoding="utf-8")

    src_code = src_file.read_text(encoding="utf-8")
    tgt_code = tgt_file.read_text(encoding="utf-8")

    if norm_rel in ["has_many", "hasmany"]:
        # Source hasMany Target (e.g. User has many Orders)
        # In Source: orders: Mapped[List["Order"]] = relationship("Order", back_populates="user")
        # In Target: user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
        #            user: Mapped["User"] = relationship("User", back_populates="orders")
        if "ForeignKey" not in tgt_code:
            tgt_code = tgt_code.replace("from sqlalchemy import", "from sqlalchemy import ForeignKey, ")

        if f'back_populates="{src_singular}"' not in tgt_code:
            tgt_lines = tgt_code.splitlines()
            insert_idx = len(tgt_lines) - 2
            for i, line in enumerate(tgt_lines):
                if "is_active" in line or "name" in line:
                    insert_idx = i + 1

            new_cols = [
                f'    {src_singular}_id: Mapped[int] = mapped_column(ForeignKey("{src_plural}.id"), nullable=False)',
                f'    {src_singular}: Mapped["{src_pascal}"] = relationship("{src_pascal}", back_populates="{tgt_plural}")',
            ]
            for c in reversed(new_cols):
                tgt_lines.insert(insert_idx, c)
            tgt_file.write_text("\n".join(tgt_lines) + "\n", encoding="utf-8")
            print(f"  ✅ Updated {tgt_pascal} with foreign key and relationship to {src_pascal}")

        if f'back_populates="{tgt_plural}"' not in src_code:
            src_lines = src_code.splitlines()
            if "from typing import List" not in src_code:
                src_lines.insert(0, "from typing import List")

            insert_idx = len(src_lines) - 2
            for i, line in enumerate(src_lines):
                if "is_active" in line or "name" in line:
                    insert_idx = i + 1

            src_lines.insert(
                insert_idx,
                f'    {tgt_plural}: Mapped[List["{tgt_pascal}"]] = relationship("{tgt_pascal}", back_populates="{src_singular}", cascade="all, delete-orphan")',
            )
            src_file.write_text("\n".join(src_lines) + "\n", encoding="utf-8")
            print(f"  ✅ Updated {src_pascal} with relationship to {tgt_pascal}")

    print("🎉 Relationship configuration complete!\n")
    return True
