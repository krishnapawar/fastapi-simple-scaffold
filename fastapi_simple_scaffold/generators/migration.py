import datetime
import subprocess
import sys
from pathlib import Path
from typing import Optional
from fastapi_simple_scaffold.utils import to_snake_case, pluralize, singularize


def generate_migration(migration_name: str, target_root: Optional[Path] = None) -> bool:
    """Generate an Alembic database migration (with autogenerate support)."""
    project_root = target_root or Path.cwd()
    clean_name = to_snake_case(migration_name)
    versions_dir = project_root / "alembic" / "versions"
    versions_dir.mkdir(parents=True, exist_ok=True)

    # 1. Try running alembic revision --autogenerate if alembic.ini exists
    ini_file = project_root / "alembic.ini"
    if ini_file.exists():
        try:
            res = subprocess.run(
                [sys.executable, "-m", "alembic", "revision", "--autogenerate", "-m", migration_name],
                cwd=str(project_root),
                capture_output=True,
                text=True,
                encoding="utf-8"
            )
            if res.returncode == 0:
                print(f"✅ Auto-generated Alembic migration from models: {migration_name}")
                return True
        except Exception:
            pass

    # 2. Fallback: Generate timestamped migration revision template file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    revision_id = f"rev_{timestamp[:12]}"
    filename = f"{timestamp}_{clean_name}.py"
    migration_file = versions_dir / filename

    table_name = pluralize(singularize(clean_name))

    content = f'''"""{migration_name}

Revision ID: {revision_id}
Revises: 
Create Date: {datetime.datetime.now().isoformat()}

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "{revision_id}"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Example migration operation:
    # op.create_table(
    #     "{table_name}",
    #     sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
    #     sa.Column("name", sa.String(255), nullable=False),
    #     sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    #     sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    # )
    pass


def downgrade() -> None:
    # op.drop_table("{table_name}")
    pass
'''

    migration_file.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"📄 Created migration revision: alembic/versions/{filename}")
    return True


def run_db_migrate(target_root: Optional[Path] = None) -> bool:
    """Apply all pending database migrations (alembic upgrade head)."""
    project_root = target_root or Path.cwd()
    ini_file = project_root / "alembic.ini"
    if not ini_file.exists():
        print("❌ alembic.ini not found. Are you inside a scaffolded project root?")
        return False

    try:
        print("🚀 Applying database migrations (alembic upgrade head)...")
        res = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=str(project_root),
            text=True,
        )
        if res.returncode == 0:
            print("✅ Database migrations applied successfully!")
            return True
        else:
            print("❌ Migration upgrade failed.")
            return False
    except Exception as e:
        print(f"❌ Failed to run migration upgrade: {str(e)}")
        return False

