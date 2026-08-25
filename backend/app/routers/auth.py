from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User
from ..schemas import LoginRequest, RegisterRequest, TokenResponse, UserOut
from ..security import create_access_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_response(user: User) -> TokenResponse:
    return TokenResponse(access_token=create_access_token(user.id), user=UserOut.model_validate(user))


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    username = payload.username.strip()
    if not username:
        raise HTTPException(status_code=422, detail="用户名不能为空")
    existing = (await db.execute(select(User).where(User.username == username))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="用户名已被占用")
    user = User(username=username, password_hash=hash_password(payload.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _token_response(user)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    username = payload.username.strip()
    user = (await db.execute(select(User).where(User.username == username))).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return _token_response(user)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user
