"""No-password identification: pick your own name from the list of users
the admin has added. This is intentionally not real authentication -
appropriate for a tool on a trusted internal lab network, not for
anything exposed publicly. See routers/admin.py for adding users.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/users", response_model=list[schemas.UserSummary])
def list_selectable_users(db: Session = Depends(get_db)):
    return db.query(models.User).order_by(models.User.name).all()


@router.post("/select", response_model=schemas.UserOut)
def select_user(payload: schemas.SelectUserRequest, request: Request, db: Session = Depends(get_db)):
    user = db.get(models.User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="No such user")
    request.session["user_id"] = user.id
    return user


@router.get("/me", response_model=schemas.UserOut)
def me(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not signed in")

    user = db.get(models.User, user_id)
    if not user:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Not signed in")
    return user


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"status": "ok"}
