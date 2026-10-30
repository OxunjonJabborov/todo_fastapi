from pathlib import Path
import security
import shutil

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm

from config import UPLOAD_FOLDER
from dependencies import get_current_user, role_checker
from email_service import send_welcome_email
from enums import Roles
from models import User
from database import get_db
from schemas.users import Token, UserCreate, UserOut

router = APIRouter(prefix='/users')


@router.post("/user", response_model=UserOut)
async def create_user(bg_tasks: BackgroundTasks, user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    if await db.scalar(select(User).where(User.username == user_in.username)):
        raise HTTPException(status_code=400, detail="Bunday foydalanuvchi allaqachon mavjud...")

    if await db.scalar(select(User).where(User.email == user_in.email)):
        raise HTTPException(status_code=400, detail="Bu email bilan foydalanuvchi allaqachon mavjud...")

    user_dict = user_in.model_dump()
    hashed_password = security.get_password_hash(user_dict.pop("password"))

    user = User(**user_dict, hashed_password=hashed_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    bg_tasks.add_task(send_welcome_email, user.email)
    return user


@router.post('/upload_avatar/', response_model=UserOut)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    file_extension = Path(file.filename or "").suffix.lstrip(".").lower()
    if not file_extension:
        raise HTTPException(status_code=400, detail="Avatar fayl turi topilmadi...")

    file_name = f"{current_user.id}_avatar.{file_extension}"
    with open(Path(UPLOAD_FOLDER) / file_name, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    current_user.user_avatar = f"/static/{file_name}"
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.post('/login', response_model=Token)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.username == form.username))
    if not user:
        raise HTTPException(status_code=400, detail="Bunday foydalanuvchi mavjud emas...")

    if not security.verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Noto'g'ri username yoki parol kiritidi...")

    access_token = security.create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/users", response_model=list[UserOut])
async def get_users(db: AsyncSession = Depends(get_db)):
    return list(await db.scalars(select(User)))


@router.get("/admin-only")
async def admin_panel(user: User = Depends(role_checker(Roles.ADMIN))):
    return {"msg": "Admin kirildi"}


@router.get("/user-or-admin")
async def user_or_admin_panel(user: User = Depends(role_checker(Roles.ADMIN, Roles.USER))):
    return {"msg": f"{user.username} kirildi"}


@router.put("/update_role/{user_id}")
async def update_user_role(
    user_id: int,
    new_role: Roles,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(role_checker(Roles.ADMIN)),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi...")

    user.role = new_role.value
    await db.commit()
    await db.refresh(user)
    return {"msg": f"{user.username} ning roli {new_role.value} ga o'zgartirildi"}
