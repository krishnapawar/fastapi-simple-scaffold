from pathlib import Path
from typing import Optional
from fastapi_simple_scaffold.utils import to_snake_case, to_pascal_case


def generate_notification(name: str, target_root: Optional[Path] = None) -> bool:
    """Generate an HTML email notification service & template."""
    project_root = target_root or Path.cwd()
    snake_name = to_snake_case(name)
    pascal_name = to_pascal_case(snake_name)

    templates_dir = project_root / "app" / "notifications" / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)
    template_file = templates_dir / f"{snake_name}.html"

    if not template_file.exists():
        template_file.write_text(f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{pascal_name} Notification</title>
</head>
<body style="font-family: Arial, sans-serif; background-color: #f8fafc; padding: 25px;">
    <div style="max-width: 600px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
        <h2 style="color: #0f172a; margin-top: 0;">{pascal_name} Alert</h2>
        <p>Hello {{{{ user_name }}}},</p>
        <p>{{{{ message }}}}</p>
        <div style="margin: 20px 0; padding: 15px; background: #f1f5f9; border-left: 4px solid #3b82f6; border-radius: 4px;">
            <p style="margin: 0; font-size: 14px; color: #334155;">{{{{ details }}}}</p>
        </div>
        <p style="color: #94a3b8; font-size: 13px;">Sent by {{{{ app_name }}}}.</p>
    </div>
</body>
</html>
''', encoding="utf-8")
        print(f"📄 Created template: app/notifications/templates/{snake_name}.html")

    service_file = project_root / "app" / "notifications" / f"{snake_name}_service.py"
    if not service_file.exists():
        service_file.write_text(f'''from fastapi import BackgroundTasks
from app.core.config import settings
from app.notifications.email_service import render_template, send_email_sync


def send_{snake_name}_notification(
    background_tasks: BackgroundTasks,
    recipient: str,
    user_name: str,
    message: str,
    details: str = "",
):
    """Enqueue {pascal_name} notification email via BackgroundTasks."""
    content = render_template(
        "{snake_name}.html",
        {{
            "app_name": settings.APP_NAME,
            "user_name": user_name,
            "message": message,
            "details": details,
        }}
    )
    background_tasks.add_task(
        send_email_sync,
        recipient=recipient,
        subject=f"[{{settings.APP_NAME}}] {pascal_name} Notification",
        html_content=content
    )
''', encoding="utf-8")
        print(f"📄 Created notification service: app/notifications/{snake_name}_service.py")


    return True
