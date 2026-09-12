"""Admin-only user management: add lab members, promote/demote admins.

Guarded by require_admin below (the signed-in session user must have
is_admin=True) - not real auth, just gated on top of the no-password
picker in routers/auth.py. The very first admin can't be created through
this API (nothing to gate on yet) - bootstrap one with
scripts/seed_admin.py.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/admin", tags=["admin"])


def require_admin(request: Request, db: Session = Depends(get_db)) -> models.User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not signed in")
    user = db.get(models.User, user_id)
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    return user


@router.get("/users", response_model=list[schemas.UserOut])
def list_users(db: Session = Depends(get_db), _admin: models.User = Depends(require_admin)):
    return db.query(models.User).order_by(models.User.name).all()


@router.post("/users", response_model=schemas.UserOut)
def create_user(
    payload: schemas.UserCreate,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(require_admin),
):
    existing = db.query(models.User).filter(models.User.university_email == payload.university_email).first()
    if existing:
        raise HTTPException(status_code=409, detail="A user with that email already exists")

    user = models.User(**payload.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}", response_model=schemas.UserOut)
def update_user(
    user_id: int,
    payload: schemas.UserUpdate,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(require_admin),
):
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="No such user")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user
