from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import role_checker
from enums import Roles
from models import Todo, User
from schemas.todo import TodoCreate, TodoOut, TodoUpdate

router = APIRouter(prefix="/todo")


async def get_todo_or_404(db: AsyncSession, todo_id: int) -> Todo:
    todo = await db.get(Todo, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail=f"{todo_id} - raqamli todo topilmadi...")
    return todo


@router.post("/", response_model=TodoOut)
async def create_todo(todo_in: TodoCreate, db: AsyncSession = Depends(get_db),
                      user: User = Depends(role_checker(Roles.ADMIN))):

    todo = Todo(**todo_in.model_dump(), user_id=user.id)
    db.add(todo)
    await db.commit()
    await db.refresh(todo)
    return todo


@router.get("/todos", response_model=list[TodoOut])
async def get_todos(db: AsyncSession = Depends(get_db)):
    return list(await db.scalars(select(Todo)))


@router.get("/{todo_id}", response_model=TodoOut)
async def get_todo(todo_id: int, db: AsyncSession = Depends(get_db)):
    return await get_todo_or_404(db, todo_id)


@router.put("/{todo_id}", response_model=TodoOut)
async def update_todo(
    todo_id: int,
    todo_in: TodoUpdate,
    db: AsyncSession = Depends(get_db),
):
    todo = await get_todo_or_404(db, todo_id)

    todo.name = todo_in.name
    todo.description = todo_in.description
    todo.is_completed = todo_in.is_completed

    await db.commit()
    await db.refresh(todo)
    return todo


@router.delete("/{todo_id}")
async def delete_todo(todo_id: int, db: AsyncSession = Depends(get_db)):
    todo = await get_todo_or_404(db, todo_id)

    await db.delete(todo)
    await db.commit()

    return {"detail": f"{todo_id} - raqamli todo o'chirildi..."}
