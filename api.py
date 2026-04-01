from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from schemes import TodoCreate, TodoOut, TodoUpdate
from database import Base, get_db, engine
from models import Todo


Base.metadata.create_all(bind=engine)
api_router = APIRouter(prefix="/api/todos")

@api_router.post("/", response_model=TodoOut)
def create_todo(todo_in: TodoCreate, db = Depends(get_db)):
    todo = Todo(**todo_in.model_dump())
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo

@api_router.get("/", response_model=list[TodoOut])
def get_todos(db = Depends(get_db)):
    stmt = select(Todo)
    todos = db.scalars(stmt).all()
    return todos

@api_router.get("/{task_id}", response_model=TodoOut)
def get_todo(task_id: int, db = Depends(get_db)):
    stmt = select(Todo).where(Todo.id == task_id)
    todo = db.scalar(stmt)
    
    if not todo:
        raise HTTPException(status_code=404, detail=f"{task_id} - raqamli todo topilmadi...")
    return todo

@api_router.put("/{task_id}", response_model=TodoOut)
def update_todo(task_id: int, todo_in: TodoUpdate, db = Depends(get_db)):
    stmt = select(Todo).where(Todo.id == task_id)
    todo = db.scalar(stmt)

    if not todo:
        raise HTTPException(status_code=404, detail=f"{task_id} - raqamli todo topilmadi...")

    todo.name = todo_in.name
    todo.description = todo_in.description
    todo.is_completed = todo_in.is_completed

    db.add(todo)
    db.commit()
    db.refresh(todo)

    return todo

@api_router.delete("/{task_id}")
def delete_todo(task_id: int, db = Depends(get_db)):
    stmt = select(Todo).where(Todo.id == task_id)
    todo = db.scalar(stmt)

    if not todo:
        raise HTTPException(status_code=404, detail=f"{task_id} - raqamli todo topilmadi...")

    db.delete(todo)
    db.commit()

    return {"detail": f"{task_id} - raqamli todo o'chirildi..."}