from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession as Session

from database import get_db
from dependencies import role_checker
from enums import Roles
from models import Todo, User
from schemas.todo import TodoCreate, TodoOut, TodoUpdate

api_router = APIRouter(prefix="/todo")


@api_router.post("/todo", response_model=TodoOut)
async def create_todo(todo_in: TodoCreate, db: Session = Depends(get_db),
                      user: User = Depends(role_checker(Roles.ADMIN))):

    todo = Todo(**todo_in.model_dump(), user_id=user.id)
    db.add(todo)
    await db.commit()
    await db.refresh(todo)
    return todo


@api_router.get("/todos", response_model=list[TodoOut])
async def get_todos(db: Session = Depends(get_db)):
    stmt = select(Todo)
    result = await db.scalars(stmt)
    todos = list(result)
    return todos


@api_router.get("/{task_id}", response_model=TodoOut)
async def get_todo(task_id: int, db: Session = Depends(get_db)):
    stmt = select(Todo).where(Todo.id == task_id)
    todo = await db.scalar(stmt)

    if not todo:
        raise HTTPException(status_code=404, detail=f"{task_id} - raqamli todo topilmadi...")
    return todo


@api_router.put("/{task_id}", response_model=TodoOut)
async def update_todo(
    task_id: int,
    todo_in: TodoUpdate,
    db: Session = Depends(get_db),
):
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


@api_router.delete("/{task_id}")
async def delete_todo(task_id: int, db: Session = Depends(get_db)):
    stmt = select(Todo).where(Todo.id == task_id)
    todo = await db.scalar(stmt)

    if not todo:
        raise HTTPException(status_code=404, detail=f"{task_id} - raqamli todo topilmadi...")

    await db.delete(todo)
    await db.commit()

    return {"detail": f"{task_id} - raqamli todo o'chirildi..."}
