from pathlib import Path
from typing import Optional
from fastapi_simple_scaffold.utils import to_snake_case, to_pascal_case


def generate_cron(name: str, expression: str = "0 0 * * *", target_root: Optional[Path] = None) -> bool:
    """Generate a scheduled background worker job."""
    project_root = target_root or Path.cwd()
    snake_name = to_snake_case(name)
    pascal_name = to_pascal_case(snake_name)

    jobs_dir = project_root / "app" / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    job_file = jobs_dir / f"{snake_name}_job.py"

    if job_file.exists():
        print(f"⚠️  Job file already exists: app/jobs/{snake_name}_job.py")
        return False

    content = f'''import asyncio
from datetime import datetime
from app.utils.logger import logger

CRON_EXPRESSION = "{expression}"


async def run_{snake_name}_job():
    """Scheduled task for {pascal_name} (Cron: {expression})."""
    logger.info(f"⚡ [{pascal_name}Job] Executing scheduled task at {{datetime.now().isoformat()}}")
    try:
        # TODO: Implement your job logic here
        await asyncio.sleep(0.1)
        logger.info(f"✅ [{pascal_name}Job] Completed successfully.")
    except Exception as e:
        logger.error(f"❌ [{pascal_name}Job] Failed: {{str(e)}}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(run_{snake_name}_job())
'''
    job_file.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"📄 Created cron job: app/jobs/{snake_name}_job.py [Schedule: {expression}]")
    return True
