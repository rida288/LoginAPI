from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.db.schema.user import UserOutput
from app.service.userService import UserService
from app.util.protectRoute import get_current_admin

adminRouter = APIRouter()

@adminRouter.get("/users", response_model=List[UserOutput])
def get_all_users(
    session: Session = Depends(get_db),
    admin_user: UserOutput = Depends(get_current_admin)
):
    try:
        return UserService(session=session).get_all_users()
    except Exception as e:
        print(e)
        raise e

@adminRouter.get("/users/pending", response_model=List[UserOutput])
def get_pending_users(
    session: Session = Depends(get_db),
    admin_user: UserOutput = Depends(get_current_admin)
):
    try:
        return UserService(session=session).get_pending_users()
    except Exception as e:
        print(e)
        raise e

@adminRouter.put("/users/{user_id}/approve", response_model=UserOutput)
def approve_user(
    user_id: int,
    session: Session = Depends(get_db),
    admin_user: UserOutput = Depends(get_current_admin)
):
    try:
        return UserService(session=session).approve_user(user_id=user_id)
    except Exception as e:
        print(e)
        raise e

@adminRouter.put("/users/{user_id}/suspend", response_model=UserOutput)
def suspend_user(
    user_id: int,
    session: Session = Depends(get_db),
    admin_user: UserOutput = Depends(get_current_admin)
):
    try:
        return UserService(session=session).suspend_user(user_id=user_id)
    except Exception as e:
        print(e)
        raise e
