from app.models.user import User  # Импортируем только класс User
from app.models.task import Task  # Импортируем только класс Task
from fastapi import APIRouter, Depends, status, HTTPException
# Сессия БД
from sqlalchemy.orm import Session
# Функция подключения к БД
from app.backend.db import get_db
# Аннотации, Модели БД и Pydantic.
from typing import Annotated
from app.schemas import CreateUser, UpdateUser
from app.schemas import CreateTask, UpdateTask
# Функции работы с записями.
from sqlalchemy import insert, select, update, delete
# Функция создания slug-строки
from slugify import slugify

# Создаем роутер с префиксом '/user' и тегом 'user'
router_u = APIRouter(prefix='/user', tags=['user'])

# Создаем маршруты для User

# Маршрут для получения всех пользователей
@router_u.get('/')
async def all_users(db: Annotated[Session, Depends(get_db)]):
    users = db.scalars(select(User)).all()
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no users'
        )
    return users


# Маршрут для получения пользователя по ID
@router_u.get('/{user_id}')
async def user_by_id(user_id: int, db: Annotated[Session, Depends(get_db)]):
    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User was not found"
        )
    return user


# Маршрут для создания нового пользователя
@router_u.post('/create')
async def create_user(user: CreateUser, db: Annotated[Session, Depends(get_db)]):
    new_user = insert(User).values(
        username=user.username,
        firstname=user.firstname,
        lastname=user.lastname,
        age=user.age,
        slug=slugify(user.username)
    )
    db.execute(new_user)
    db.commit()
    return {'status_code': status.HTTP_201_CREATED, 'transaction': 'Successful'}


# Маршрут для обновления пользователя
@router_u.put('/update')
async def update_user(user: UpdateUser, user_id: int, db: Annotated[Session, Depends(get_db)]):
    upd_user = db.scalar(select(User).where(User.id == user_id))
    if upd_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User was not found"
        )
    db.execute(update(User).where(User.id == user_id).values(
        username=upd_user.username,  # так как в схеме обновления пользователей нет username то подставляем username
        # найденного пользователя upd_user
        firstname=user.firstname,
        lastname=user.lastname,
        age=user.age,
        slug=slugify(upd_user.username)))

    db.commit()

    return {'status_code': status.HTTP_200_OK, 'transaction': 'User update is successful!'}


# # Маршрут для удаления пользователя
# @router_u.delete('/delete')
# async def delete_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
#     del_user = db.scalar(select(User).where(User.id == user_id))
#     if del_user is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User was not found"
#         )
#     db.execute(delete(User).where(User.id == user_id))
#     db.commit()
#
#     return {'status_code': status.HTTP_200_OK, 'transaction': 'User deletion is successful!'}


# Маршрут для удаления пользователя вместе с его задачами
@router_u.delete('/delete')
async def delete_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    del_user = db.scalar(select(User).where(User.id == user_id))
    if del_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User was not found"
        )

    # Удаляем все задачи, связанные с этим пользователем
    tasks_deleted = db.execute(delete(Task).where(Task.user_id == user_id)).rowcount  # rowcount будет показывать,
    # сколько строк было удалено, значение запишется в tasks_deleted
    print(f"Deleted {tasks_deleted} tasks for user {user_id}")

    # Удаляем самого пользователя
    user_deleted = db.execute(delete(User).where(User.id == user_id)).rowcount
    print(f"Deleted {user_deleted} user with id {user_id}")

    db.commit()

    return {'status_code': status.HTTP_200_OK, 'transaction': 'User and his tasks deletion is successful!'}


# Маршрут для получения всех Task конкретного User по id
@router_u.get('/user_id/tasks')
async def tasks_by_user_id(user_id: int, db: Annotated[Session, Depends(get_db)]):
    tasks_user_id = db.scalars(select(Task).where(Task.user_id == user_id)).all()
    if not tasks_user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no tasks by user_id'
        )
    return tasks_user_id

# Создаем маршруты для Task

# Создаем роутер с префиксом '/task' и тегом 'task'
router_t = APIRouter(prefix='/task', tags=['task'])


# Маршрут для получения всех задач
@router_t.get('/')
async def all_tasks(db: Annotated[Session, Depends(get_db)]):
    tasks = db.scalars(select(Task)).all()
    if not tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no tasks'
        )
    return tasks


# Маршрут для получения задачи по ID
@router_t.get('/{task_id}')
async def task_by_id(task_id: int, db: Annotated[Session, Depends(get_db)]):
    task = db.scalar(select(Task).where(Task.id == task_id))
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task was not found"
        )
    return task


# Маршрут для создания новой задачи
@router_t.post('/create')
async def create_task(task: CreateTask, user_id: int, db: Annotated[Session, Depends(get_db)]):
    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User was not found"
        )

    new_task = insert(Task).values(
        title=task.title,
        content=task.content,
        priority=task.priority,
        #completed=task.completed,
        user_id=user_id,
        slug=slugify(task.title)
    )
    db.execute(new_task)
    db.commit()
    return {'status_code': status.HTTP_201_CREATED, 'transaction': 'Successful'}

# Маршрут для обновления задачи
@router_t.put('/update')
async def update_task(task: UpdateTask, task_id: int, db: Annotated[Session, Depends(get_db)]):
    upd_task = db.scalar(select(Task).where(Task.id == task_id))
    if upd_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task was not found"
        )
    db.execute(update(Task).where(Task.id == task_id).values(
        title=task.title,
        content=task.content,
        priority=task.priority,
        completed=upd_task.completed, # так как в схеме обновления задач нет completed то подставляем completed
        # задачи которую обновляем upd_task
        slug=slugify(task.title)))

    db.commit()

    return {'status_code': status.HTTP_200_OK, 'transaction': 'Task update is successful!'}


# Маршрут для удаления задачи
@router_t.delete('/delete')
async def delete_task(task_id: int, db: Annotated[Session, Depends(get_db)]):
    del_task = db.scalar(select(Task).where(Task.id == task_id))
    if del_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task was not found"
        )
    db.execute(delete(Task).where(Task.id == task_id))
    db.commit()

    return {'status_code': status.HTTP_200_OK, 'transaction': 'Task deletion is successful!'}