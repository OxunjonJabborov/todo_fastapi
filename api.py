import asyncio
import shutil

from email_service import send_welcome_email

import security
import jwt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession as Session
from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

from schemas import TodoCreate, TodoOut, TodoUpdate, Token, UserOut, UserCreate
from database import get_db
from models import Todo, User


api_router = APIRouter(prefix="/api")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token yaroqsiz yoki muddati tugagan",
    )
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        user_id: int | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception
    
    user = await db.scalar(select(User).where(User.id == int(user_id)))
    
    if user is None:
        raise credentials_exception
    return user

@api_router.post("/users", response_model=UserOut)
async def create_user(bg_tasks: BackgroundTasks,user_in: UserCreate, db: Session = Depends(get_db)):
    user = await db.scalar(select(User).where(User.username == user_in.username))
    if user:
        raise HTTPException(status_code=400, detail="Bunday foydalanuvchi allaqachon mavjud...")

    user = await db.scalar(select(User).where(User.email == user_in.email))
    if user:
        raise HTTPException(status_code=400, detail="Bu email bilan foydalanuvchi allaqachon mavjud...")

    user_dict = user_in.model_dump()
    hashed_password = security.get_password_hash(user_dict.pop("password"))

    user = User(**user_dict, hashed_password=hashed_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    bg_tasks.add_task(send_welcome_email, f"{user.email}")
    return user

@api_router.post('/users/upload_avatar/')
async def upload_avatar(file: UploadFile = File(...), current_user: UserOut = Depends(get_current_user), db: Session = Depends(get_db)):
    from main import UPLOAD_FOLDER
    file_extension = file.filename.split(".")[-1]
    file_location = f"{UPLOAD_FOLDER}/{current_user.id}_avatar.{file_extension}"
    static_location = f"/static/{current_user.id}_avatar.{file_extension}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    
    current_user.user_avatar = static_location
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user

@api_router.post('/users/login', response_model=Token)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = await db.scalar(select(User).where(User.username == form.username))
    if not user:
        raise HTTPException(status_code=400, detail="Bunday foydalanuvchi mavjud emas...")
    
    if not security.verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Noto'g'ri username yoki parol kiritidi...")
    
    access_token = security.create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.post("/todos", response_model=TodoOut)
async def create_todo(todo_in: TodoCreate, db: Session = Depends(get_db), user: UserOut = Depends(get_current_user)):
    
    todo = Todo(**todo_in.model_dump(), user_id=user.id)
    db.add(todo)
    await db.commit()
    await db.refresh(todo)
    return todo

@api_router.get("/users/me", response_model=UserOut)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user

@api_router.get("/users", response_model=list[UserOut])
async def get_users(db: Session = Depends(get_db)):
    stmt = select(User)
    result = await db.scalars(stmt)
    users = list(result)
    return users

@api_router.get("/todos", response_model=list[TodoOut])
async def get_todos(db: Session = Depends(get_db)):
    stmt = select(Todo)
    result = await db.scalars(stmt)
    todos = list(result)
    return todos

@api_router.get("/todos/{task_id}", response_model=TodoOut)
async def get_todo(task_id: int, db = Depends(get_db)):
    stmt = select(Todo).where(Todo.id == task_id)
    todo = await db.scalar(stmt)

    if not todo:
        raise HTTPException(status_code=404, detail=f"{task_id} - raqamli todo topilmadi...")
    return todo

@api_router.put("/todos/{task_id}", response_model=TodoOut)
async def update_todo(task_id: int, todo_in: TodoUpdate, db = Depends(get_db)):
    stmt = select(Todo).where(Todo.id == task_id)
    todo = await db.scalar(stmt)

    if not todo:
        raise HTTPException(status_code=404, detail=f"{task_id} - raqamli todo topilmadi...")

    todo.name = todo_in.name
    todo.description = todo_in.description
    todo.is_completed = todo_in.is_completed

    db.add(todo)
    await db.commit()
    await db.refresh(todo)

    return todo

@api_router.delete("/todos/{task_id}")
async def delete_todo(task_id: int, db = Depends(get_db)):
    stmt = select(Todo).where(Todo.id == task_id)
    todo = await db.scalar(stmt)

    if not todo:
        raise HTTPException(status_code=404, detail=f"{task_id} - raqamli todo topilmadi...")

    db.delete(todo)
    await db.commit()

    return {"detail": f"{task_id} - raqamli todo o'chirildi..."}