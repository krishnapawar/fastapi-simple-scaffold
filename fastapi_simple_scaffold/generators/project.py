import os
from pathlib import Path
from typing import Dict, Optional

def create_project_structure(
    target_dir: Optional[str] = None,
    force: bool = False,
    project_name: Optional[str] = None
) -> Dict[str, int]:
    """
    Generate a complete, modern, production-ready modular FastAPI backend project.
    """
    if target_dir:
        project_root = Path.cwd() / target_dir
        app_name = project_name or Path(target_dir).name
    else:
        project_root = Path.cwd()
        app_name = project_name or project_root.name

    stats = {"created": 0, "skipped": 0, "overwritten": 0}

    def write_file(rel_path: str, content: str) -> None:
        file_path = project_root / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if file_path.exists():
            if not force:
                print(f"  [yellow]Skipped (exists):[/yellow] {rel_path}")
                stats["skipped"] += 1
                return
            else:
                print(f"  [blue]Overwritten:[/blue] {rel_path}")
                stats["overwritten"] += 1
        else:
            print(f"  [green]Created:[/green] {rel_path}")
            stats["created"] += 1

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")

    # 1. Base directories
    directories = [
        "app/core",
        "app/models",
        "app/modules/auth",
        "app/modules/users",
        "app/middleware",
        "app/notifications/templates",
        "app/jobs",
        "app/utils",
        "app/database/seeders",
        "alembic/versions",
        "logs",
        "uploads",
        "tests",
    ]

    for d in directories:
        (project_root / d).mkdir(parents=True, exist_ok=True)

    # Empty tracking files
    write_file("logs/.gitkeep", "")
    write_file("uploads/.gitkeep", "")
    write_file("alembic/versions/.gitkeep", "")

    # __init__.py files
    for init_path in [
        "app/__init__.py",
        "app/core/__init__.py",
        "app/models/__init__.py",
        "app/modules/__init__.py",
        "app/modules/auth/__init__.py",
        "app/modules/users/__init__.py",
        "app/middleware/__init__.py",
        "app/notifications/__init__.py",
        "app/jobs/__init__.py",
        "app/utils/__init__.py",
        "app/database/__init__.py",
        "app/database/seeders/__init__.py",
        "tests/__init__.py",
    ]:
        write_file(init_path, "")

    # 2. Config & Core
    write_file(
        "app/core/config.py",
        f'''from functools import lru_cache
from typing import List, Union
from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "{app_name}"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    API_V1_PREFIX: str = "/api/v1"

    # Database: Default SQLite async for 0-config local dev. PostgreSQL / MySQL fully supported.
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"
    DB_ECHO: bool = False

    # Security & JWT
    SECRET_KEY: str = "super-secret-key-change-this-in-production-1234567890"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000", "*"]

    # Email / SMTP
    SMTP_HOST: str = "smtp.mailtrap.io"
    SMTP_PORT: int = 2525
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: str = "noreply@example.com"
    EMAILS_FROM_NAME: str = "{app_name}"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
'''
    )

    write_file(
        "app/core/database.py",
        '''from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Create async database engine
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    future=True,
    connect_args=connect_args,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection for async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
'''
    )

    write_file(
        "app/core/security.py",
        '''from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union
import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    from app.modules.users.repository import UserRepository
    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token credentials",
        )

    user = await UserRepository.get_by_id(db, int(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or account is deactivated",
        )
    return user
'''
    )

    write_file(
        "app/core/events.py",
        '''from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import engine, Base
from app.utils.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB schema tables
    logger.info("🚀 Starting up application services...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database tables verified/synchronized.")

    yield

    # Shutdown
    logger.info("🛑 Shutting down application services...")
    await engine.dispose()
    logger.info("👋 Database connection closed.")
'''
    )

    # 3. Models
    write_file(
        "app/models/base.py",
        '''from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class TimestampMixin:
    """Reusable timestamp mixin for SQLAlchemy models."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
'''
    )

    write_file(
        "app/models/user.py",
        '''from sqlalchemy import String, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.base import TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="user", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
'''
    )

    write_file(
        "app/models/__init__.py",
        '''from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.user import User

__all__ = ["Base", "TimestampMixin", "User"]
'''
    )

    # 4. Modules: Auth
    write_file(
        "app/modules/auth/schemas.py",
        '''from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    role: str
    is_active: bool

    class Config:
        from_attributes = True
'''
    )

    write_file(
        "app/modules/auth/repository.py",
        '''from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User


class AuthRepository:
    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def create_user(db: AsyncSession, user_data: dict) -> User:
        user = User(**user_data)
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user
'''
    )

    write_file(
        "app/modules/auth/service.py",
        '''from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import RegisterRequest, LoginRequest, TokenResponse


class AuthService:
    @staticmethod
    async def register(db: AsyncSession, data: RegisterRequest):
        existing = await AuthRepository.get_by_email(db, data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists"
            )

        user_dict = {
            "email": data.email,
            "full_name": data.full_name,
            "hashed_password": get_password_hash(data.password),
            "role": "user",
            "is_active": True,
        }
        user = await AuthRepository.create_user(db, user_dict)
        return user

    @staticmethod
    async def authenticate(db: AsyncSession, data: LoginRequest) -> TokenResponse:
        user = await AuthRepository.get_by_email(db, data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive. Please contact support.",
            )

        payload = {"sub": str(user.id), "email": user.email, "role": user.role}
        access_token = create_access_token(payload)
        refresh_token = create_refresh_token(payload)

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    @staticmethod
    async def refresh_token(refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

        user_id = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role")

        new_payload = {"sub": user_id, "email": email, "role": role}
        return TokenResponse(
            access_token=create_access_token(new_payload),
            refresh_token=create_refresh_token(new_payload),
        )
'''
    )

    write_file(
        "app/modules/auth/router.py",
        '''from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.modules.auth.schemas import RegisterRequest, LoginRequest, TokenResponse, RefreshTokenRequest, UserOut
from app.modules.auth.service import AuthService
from app.utils.response import success_response

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    user = await AuthService.register(db, data)
    return success_response(
        data=UserOut.model_validate(user),
        message="User account registered successfully"
    )


@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """OAuth2 compatible token login, retrieve access and refresh tokens."""
    data = LoginRequest(email=form_data.username, password=form_data.password)
    return await AuthService.authenticate(db, data)


@router.post("/login/json")
async def login_json(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """JSON body login endpoint."""
    tokens = await AuthService.authenticate(db, data)
    return success_response(data=tokens.model_dump(), message="Logged in successfully")


@router.post("/refresh")
async def refresh_token(data: RefreshTokenRequest):
    """Refresh expired access token using valid refresh token."""
    tokens = await AuthService.refresh_token(data.refresh_token)
    return success_response(data=tokens.model_dump(), message="Token refreshed successfully")


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get authenticated user profile."""
    return success_response(
        data=UserOut.model_validate(current_user),
        message="User profile retrieved"
    )
'''
    )

    # 5. Modules: Users
    write_file(
        "app/modules/users/schemas.py",
        '''from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=6)
    role: str = "user"
    is_active: bool = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6)


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    total: int
    items: List[UserResponse]
'''
    )

    write_file(
        "app/modules/users/repository.py",
        '''from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User


class UserRepository:
    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[User], int]:
        query = select(User)
        count_query = select(func.count(User.id))

        if search:
            query = query.where(User.full_name.ilike(f"%{search}%") | User.email.ilike(f"%{search}%"))
            count_query = count_query.where(User.full_name.ilike(f"%{search}%") | User.email.ilike(f"%{search}%"))

        if is_active is not None:
            query = query.where(User.is_active == is_active)
            count_query = count_query.where(User.is_active == is_active)

        total_res = await db.execute(count_query)
        total = total_res.scalar() or 0

        query = query.order_by(User.id.desc()).offset(skip).limit(limit)
        items_res = await db.execute(query)
        items = list(items_res.scalars().all())

        return items, total

    @staticmethod
    async def create(db: AsyncSession, data: dict) -> User:
        user = User(**data)
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    @staticmethod
    async def update(db: AsyncSession, user: User, data: dict) -> User:
        for key, value in data.items():
            if value is not None:
                setattr(user, key, value)
        await db.flush()
        await db.refresh(user)
        return user

    @staticmethod
    async def delete(db: AsyncSession, user: User) -> None:
        await db.delete(user)
        await db.flush()
'''
    )

    write_file(
        "app/modules/users/service.py",
        '''from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_password_hash
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate, UserUpdate


class UserService:
    @staticmethod
    async def get_users(db: AsyncSession, skip: int = 0, limit: int = 20, search: Optional[str] = None):
        return await UserRepository.get_all(db, skip=skip, limit=limit, search=search)

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int):
        user = await UserRepository.get_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    @staticmethod
    async def create_user(db: AsyncSession, data: UserCreate):
        user_dict = data.model_dump()
        user_dict["hashed_password"] = get_password_hash(user_dict.pop("password"))
        return await UserRepository.create(db, user_dict)

    @staticmethod
    async def update_user(db: AsyncSession, user_id: int, data: UserUpdate):
        user = await UserService.get_user_by_id(db, user_id)
        update_data = data.model_dump(exclude_unset=True)
        if "password" in update_data and update_data["password"]:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        elif "password" in update_data:
            update_data.pop("password")
        return await UserRepository.update(db, user, update_data)

    @staticmethod
    async def delete_user(db: AsyncSession, user_id: int):
        user = await UserService.get_user_by_id(db, user_id)
        await UserRepository.delete(db, user)
        return True
'''
    )

    write_file(
        "app/modules/users/router.py",
        '''from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.modules.users.schemas import UserCreate, UserUpdate, UserResponse
from app.modules.users.service import UserService
from app.utils.response import success_response

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("")
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List users with pagination and search."""
    items, total = await UserService.get_users(db, skip=skip, limit=limit, search=search)
    return success_response(
        data={
            "total": total,
            "skip": skip,
            "limit": limit,
            "items": [UserResponse.model_validate(u) for u in items],
        },
        message="Users retrieved successfully",
    )


@router.get("/{user_id}")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get single user by ID."""
    user = await UserService.get_user_by_id(db, user_id)
    return success_response(
        data=UserResponse.model_validate(user),
        message="User found",
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new user (admin operation)."""
    user = await UserService.create_user(db, data)
    return success_response(
        data=UserResponse.model_validate(user),
        message="User created successfully",
    )


@router.put("/{user_id}")
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update user by ID."""
    user = await UserService.update_user(db, user_id, data)
    return success_response(
        data=UserResponse.model_validate(user),
        message="User updated successfully",
    )


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete user by ID."""
    await UserService.delete_user(db, user_id)
    return success_response(data=None, message="User deleted successfully")
'''
    )

    # 6. Middleware
    write_file(
        "app/middleware/timing.py",
        '''import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class ProcessTimeMiddleware(BaseHTTPMiddleware):
    """Adds X-Process-Time response header measuring execution duration in milliseconds."""
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = (time.perf_counter() - start_time) * 1000
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
        return response
'''
    )

    write_file(
        "app/middleware/error_handler.py",
        '''from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.utils.logger import logger


def register_error_handlers(app: FastAPI):
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "status_code": exc.status_code,
                "message": exc.detail,
                "data": None,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "status_code": 422,
                "message": "Validation Error",
                "errors": exc.errors(),
                "data": None,
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "status_code": 500,
                "message": "Internal Server Error",
                "data": None,
            },
        )
'''
    )

    write_file(
        "app/middleware/cors.py",
        '''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings


def setup_cors(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
'''
    )

    # 7. Utils
    write_file(
        "app/utils/response.py",
        '''from typing import Any, Optional
from fastapi.responses import JSONResponse


def success_response(data: Any = None, message: str = "Success", status_code: int = 200) -> dict:
    """Standard unified JSON API response envelope."""
    return {
        "success": True,
        "status_code": status_code,
        "message": message,
        "data": data,
    }


def error_response(message: str = "Error", status_code: int = 400, errors: Any = None) -> JSONResponse:
    """Standard unified error response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "status_code": status_code,
            "message": message,
            "errors": errors,
            "data": None,
        },
    )
'''
    )

    write_file(
        "app/utils/logger.py",
        '''import logging
import sys

logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)s : %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
handler.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(handler)
'''
    )

    # 8. Notifications
    write_file(
        "app/notifications/templates/welcome.html",
        '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Welcome to {{ app_name }}</title>
</head>
<body style="font-family: Arial, sans-serif; background-color: #f4f4f7; padding: 20px;">
    <div style="max-width: 600px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 8px;">
        <h2 style="color: #2563eb;">Welcome aboard, {{ user_name }}! 🚀</h2>
        <p>Thank you for joining <strong>{{ app_name }}</strong>. Your account has been successfully created.</p>
        <p>If you have any questions or need help getting started, simply reply to this email.</p>
        <br>
        <p style="color: #64748b; font-size: 14px;">Best regards,<br>The {{ app_name }} Team</p>
    </div>
</body>
</html>
'''
    )

    write_file(
        "app/notifications/email_service.py",
        '''import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from jinja2 import Template
from fastapi import BackgroundTasks
from app.core.config import settings
from app.utils.logger import logger

TEMPLATES_DIR = Path(__file__).parent / "templates"


def render_template(template_name: str, context: dict) -> str:
    template_path = TEMPLATES_DIR / template_name
    if not template_path.exists():
        return ""
    with open(template_path, "r", encoding="utf-8") as f:
        template = Template(f.read())
    return template.render(**context)


def send_email_sync(recipient: str, subject: str, html_content: str):
    """Synchronous email dispatch using standard smtplib."""
    if not settings.SMTP_USER or not settings.SMTP_HOST:
        logger.info(f"[Email Mock] To: {recipient} | Subject: {subject}")
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
        msg["To"] = recipient
        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAILS_FROM_EMAIL, recipient, msg.as_string())

        logger.info(f"✅ Email successfully sent to {recipient}")
    except Exception as e:
        logger.error(f"❌ Failed to send email to {recipient}: {str(e)}")


def send_welcome_email(background_tasks: BackgroundTasks, recipient: str, user_name: str):
    """Enqueue welcome email dispatch via FastAPI BackgroundTasks."""
    content = render_template(
        "welcome.html",
        {"app_name": settings.APP_NAME, "user_name": user_name}
    )
    background_tasks.add_task(
        send_email_sync,
        recipient=recipient,
        subject=f"Welcome to {settings.APP_NAME}!",
        html_content=content
    )
'''
    )

    # 9. Jobs
    write_file(
        "app/jobs/scheduler.py",
        '''import asyncio
from datetime import datetime
from app.utils.logger import logger


async def sample_cron_job():
    """Example background recurring task."""
    logger.info(f"⏰ [Cron Worker] Running periodic task at {datetime.now().isoformat()}")


async def start_background_jobs():
    """Run background jobs in asyncio loop if needed."""
    logger.info("🕒 Background jobs scheduler initialized.")
'''
    )

    # 10. Database Seeders
    write_file(
        "app/database/seeders/user_seeder.py",
        '''import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.utils.logger import logger


async def seed_users():
    async with AsyncSessionLocal() as session:
        # Check if admin exists
        stmt = select(User).where(User.email == "admin@example.com")
        res = await session.execute(stmt)
        admin = res.scalars().first()

        if not admin:
            admin = User(
                email="admin@example.com",
                full_name="Super Administrator",
                hashed_password=get_password_hash("Admin@123456"),
                role="admin",
                is_active=True,
            )
            session.add(admin)
            await session.commit()
            logger.info("✅ Seeded default admin: admin@example.com (Password: Admin@123456)")
        else:
            logger.info("ℹ️ Default admin already exists. Skipping seeder.")


if __name__ == "__main__":
    asyncio.run(seed_users())
'''
    )

    # 11. Main FastAPI Application
    write_file(
        "app/main.py",
        '''from fastapi import FastAPI
from app.core.config import settings
from app.core.events import lifespan
from app.middleware.cors import setup_cors
from app.middleware.timing import ProcessTimeMiddleware
from app.middleware.error_handler import register_error_handlers
from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as users_router

app = FastAPI(
    title=settings.APP_NAME,
    description="Modular FastAPI REST API scaffolded with fastapi-simple-scaffold",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 1. Setup Middlewares
setup_cors(app)
app.add_middleware(ProcessTimeMiddleware)
register_error_handlers(app)

# 2. Register Feature Routers
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(users_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}
'''
    )

    # 12. Alembic
    write_file(
        "alembic.ini",
        '''# Alembic Configuration File
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
'''
    )

    write_file(
        "alembic/script.py.mako",
        '''"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
'''
    )

    write_file(
        "alembic/env.py",
        '''import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from app.core.config import settings
from app.core.database import Base
# Import all models here so Alembic can autogenerate migrations
from app.models import *

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = settings.DATABASE_URL
    connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''
    )

    # 13. Tests
    write_file(
        "tests/conftest.py",
        '''import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
'''
    )

    write_file(
        "tests/test_auth.py",
        '''import pytest

@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_register_and_login(client):
    # Register
    reg_payload = {
        "email": "testuser@example.com",
        "full_name": "Test User",
        "password": "SecretPassword123"
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    assert reg_res.json()["data"]["email"] == "testuser@example.com"

    # Login
    login_res = await client.post("/api/v1/auth/login", data={
        "username": "testuser@example.com",
        "password": "SecretPassword123"
    })
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # Me
    me_res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["data"]["email"] == "testuser@example.com"
'''
    )

    write_file(
        "tests/test_users.py",
        '''import pytest

@pytest.mark.asyncio
async def test_user_endpoints_require_auth(client):
    response = await client.get("/api/v1/users")
    assert response.status_code == 401
'''
    )

    # 14. Requirements & Config files
    write_file(
        "requirements.txt",
        '''fastapi>=0.110.0
uvicorn[standard]>=0.28.0
pydantic>=2.6.0
pydantic-settings>=2.2.0
email-validator>=2.1.0
sqlalchemy>=2.0.28
aiosqlite>=0.20.0
asyncpg>=0.29.0
alembic>=1.13.1
pyjwt>=2.8.0
passlib[bcrypt]>=1.7.4
bcrypt>=4.0.1
python-dotenv>=1.0.1
jinja2>=3.1.3
python-multipart>=0.0.9
httpx>=0.27.0
pytest>=8.1.0
pytest-asyncio>=0.23.5
'''
    )

    write_file(
        ".env.example",
        f'''# Application
APP_NAME="{app_name}"
APP_ENV=development
DEBUG=True
PORT=8000
HOST=0.0.0.0
API_V1_PREFIX=/api/v1

# Database Configuration
# Default: Async SQLite (No external DB required for local dev)
DATABASE_URL=sqlite+aiosqlite:///./app.db
# PostgreSQL Example:
# DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/my_database
DB_ECHO=False

# JWT Security
SECRET_KEY=change-this-to-a-very-long-and-secure-random-secret-key-in-prod
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS (Comma separated or json array)
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000","*"]

# SMTP Mail Configuration
SMTP_HOST=smtp.mailtrap.io
SMTP_PORT=2525
SMTP_USER=
SMTP_PASSWORD=
EMAILS_FROM_EMAIL=noreply@example.com
EMAILS_FROM_NAME="{app_name}"
'''
    )

    write_file(
        ".env",
        f'''# Application
APP_NAME="{app_name}"
APP_ENV=development
DEBUG=True
PORT=8000
HOST=0.0.0.0
API_V1_PREFIX=/api/v1

# Database
DATABASE_URL=sqlite+aiosqlite:///./app.db
DB_ECHO=False

# JWT Security
SECRET_KEY=dev-secret-key-fastapi-scaffold-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000","*"]

# SMTP Mail
SMTP_HOST=smtp.mailtrap.io
SMTP_PORT=2525
SMTP_USER=
SMTP_PASSWORD=
EMAILS_FROM_EMAIL=noreply@example.com
EMAILS_FROM_NAME="{app_name}"
'''
    )

    write_file(
        ".gitignore",
        '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Database
*.db
*.sqlite
*.sqlite3

# Environment
.env

# Logs
logs/*
!logs/.gitkeep
*.log

# Uploads
uploads/*
!uploads/.gitkeep

# IDEs
.vscode/
.idea/
*.swp
*.swo

# Testing & Coverage
.pytest_cache/
.coverage
htmlcov/
'''
    )

    write_file(
        "run.py",
        '''import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
'''
    )

    write_file(
        "README.md",
        f'''# 🚀 {app_name}

> Production-ready Modular FastAPI Backend REST API generated with `fastapi-simple-scaffold`.

---

## ⚡ Quick Start

### 1. Create and Activate Virtual Environment

```bash
# Windows
python -m venv venv
venv\\Scripts\\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Seed Database (Optional Superadmin)

```bash
python -m app.database.seeders.user_seeder
```
*Creates default admin: `admin@example.com` / `Admin@123456`*

### 4. Run Development Server

```bash
python run.py
```
*or via uvicorn directly:*
```bash
uvicorn app.main:app --reload --port 8000
```

---

## 📖 Interactive API Documentation

Once the server is running, open:
- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🛠️ CLI Scaffolding & Code Generation

Use `fastapi-scaffold` (or `fscaffold`) inside this directory to generate code components:

```bash
# Interactive CLI Dashboard Studio
fastapi-scaffold

# Generate a complete resource stack (Model + Migration + Module)
fastapi-scaffold make:resource Product

# Generate a layered feature module (Router, Service, Repository, Schemas)
fastapi-scaffold make:module Payment

# Generate a new SQLAlchemy model
fastapi-scaffold make:model Order

# Generate a standalone APIRouter
fastapi-scaffold make:router Invoice

# Generate a Service layer
fastapi-scaffold make:service Analytics

# Generate a Middleware
fastapi-scaffold make:middleware RateLimiter

# Generate an Alembic migration
fastapi-scaffold make:migration create_orders_table

# Generate a Database Seeder
fastapi-scaffold make:seeder Order

# Scaffold Model Relationships
fastapi-scaffold make:relation User Order has_many

# View all registered endpoints
fastapi-scaffold route:list

# Run system health checks
fastapi-scaffold doctor
```

---

## 🧪 Running Automated Tests

```bash
pytest -v
```

---

## 📂 Architecture Overview

```text
app/
├── core/             # Settings, DB Engine, Security, Lifespan events
├── models/           # SQLAlchemy 2.0 mapped models
├── modules/          # Layered feature modules (Auth, Users, etc.)
│   └── [module]/
│       ├── router.py     # HTTP routes & endpoint definitions
│       ├── schemas.py    # Pydantic request/response schemas
│       ├── service.py    # Business logic
│       └── repository.py # Database queries & ORM operations
├── middleware/       # Error handling, timing, CORS
├── notifications/    # HTML email templates & mailer services
├── jobs/             # Scheduled tasks & background workers
├── utils/            # Standard response helpers, structured logger
├── database/         # Seeders & DB initializers
└── main.py           # FastAPI entrypoint
```

---

## 📄 License
MIT License.
'''
    )

    return stats
