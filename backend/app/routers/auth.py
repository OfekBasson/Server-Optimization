"""Two very different things live here:

- GET /users: a public list of lab members, used by the frontend to ask
  "who are you?" inline whenever someone books a server or creates a
  watch request. No session, no password - just picking a name. Nothing
  here identifies the browser as that person afterwards.
- POST /admin-login, /me, /logout: real (if lightweight) admin auth via
  a session cookie, gating the admin panel (routers/admin.py). Only users
  with is_admin=True and a password set (via routers/admin.py or
  scripts/seed_admin.py) can log in this way.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/users", response_model=list[schemas.UserSummary])
def list_selectable_users(db: Session = Depends(get_db)):
    return db.query(models.User).order_by(models.User.name).all()


@router.post("/admin-login", response_model=schemas.UserOut)
def admin_login(payload: schemas.AdminLoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.university_email == payload.username).first()
    if (
        not user
        or not user.is_admin
        or not user.password_hash
        or not verify_password(payload.password, user.password_hash)
    ):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    request.session["user_id"] = user.id
    return user


@router.get("/me", response_model=schemas.UserOut)
def me(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not signed in")

    user = db.get(models.User, user_id)
    if not user or not user.is_admin:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Not signed in")
    return user


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"status": "ok"}
