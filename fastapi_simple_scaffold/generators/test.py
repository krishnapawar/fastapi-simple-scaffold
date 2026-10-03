from pathlib import Path
from typing import Optional
from fastapi_simple_scaffold.utils import to_snake_case, to_pascal_case, pluralize, singularize


def generate_test(name: str, target_root: Optional[Path] = None) -> bool:
    """Generate an automated pytest test suite."""
    project_root = target_root or Path.cwd()
    singular = singularize(to_snake_case(name))
    plural = pluralize(singular)
    pascal_name = to_pascal_case(singular)

    tests_dir = project_root / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    test_file = tests_dir / f"test_{plural}.py"

    if test_file.exists():
        print(f"⚠️  Test file already exists: tests/test_{plural}.py")
        return False

    content = f'''import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_{plural}_unauthorized(client: AsyncClient):
    """Ensure {plural} listing requires authentication."""
    response = await client.get("/api/v1/{plural}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_{singular}_crud_flow(client: AsyncClient):
    # 1. Register & login user to get bearer token
    reg_payload = {{
        "email": "tester_{singular}@example.com",
        "full_name": "Test Runner",
        "password": "Password123"
    }}
    await client.post("/api/v1/auth/register", json=reg_payload)

    login_res = await client.post("/api/v1/auth/login", data={{
        "username": "tester_{singular}@example.com",
        "password": "Password123"
    }})
    token = login_res.json()["access_token"]
    headers = {{"Authorization": f"Bearer {{token}}"}}

    # 2. Create {singular}
    create_res = await client.post(
        "/api/v1/{plural}",
        json={{"name": "Initial {pascal_name}", "description": "Automated test description", "is_active": True}},
        headers=headers,
    )
    assert create_res.status_code == 201
    item_id = create_res.json()["data"]["id"]

    # 3. Read {singular}
    get_res = await client.get(f"/api/v1/{plural}/{{item_id}}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["data"]["name"] == "Initial {pascal_name}"

    # 4. Update {singular}
    put_res = await client.put(
        f"/api/v1/{plural}/{{item_id}}",
        json={{"name": "Updated {pascal_name}"}},
        headers=headers,
    )
    assert put_res.status_code == 200
    assert put_res.json()["data"]["name"] == "Updated {pascal_name}"

    # 5. Delete {singular}
    del_res = await client.delete(f"/api/v1/{plural}/{{item_id}}", headers=headers)
    assert del_res.status_code == 200
'''
    test_file.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"📄 Created test suite: tests/test_{plural}.py")
    return True
