"""Maps a lab member's Linux account on a given server to their app User,
so the monitoring agent's per-process ownership can be attributed to a
person (idle vs. takeover detection, per-user analytics).

No login/admin check yet - this is meant to be called by whoever's setting
the lab up, from a trusted network. Add auth here before exposing it
publicly.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/os-usernames", tags=["os-usernames"])


@router.post("", response_model=schemas.OsUsernameOut)
def upsert_os_username(payload: schemas.OsUsernameCreate, db: Session = Depends(get_db)):
    server = db.query(models.Server).filter(models.Server.name == payload.server_name).first()
    if not server:
        raise HTTPException(status_code=404, detail=f"Unknown server '{payload.server_name}'")

    user = (
        db.query(models.User)
        .filter(models.User.university_email == payload.university_email)
        .first()
    )
    if not user:
        # Create a placeholder so mappings can be set up before someone's
        # first Microsoft login; the real name/account gets filled in once
        # they do log in (matched by this same email).
        display_name = payload.university_email.split("@")[0].replace(".", " ").title()
        user = models.User(name=display_name, university_email=payload.university_email)
        db.add(user)
        db.commit()
        db.refresh(user)

    mapping = (
        db.query(models.OsUsername)
        .filter(
            models.OsUsername.server_id == server.id,
            models.OsUsername.os_username == payload.os_username,
        )
        .first()
    )
    if mapping:
        mapping.user_id = user.id
    else:
        mapping = models.OsUsername(
            user_id=user.id, server_id=server.id, os_username=payload.os_username
        )
        db.add(mapping)
    db.commit()
    db.refresh(mapping)
    return mapping


@router.get("", response_model=list[schemas.OsUsernameOut])
def list_os_usernames(server_name: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.OsUsername)
    if server_name:
        server = db.query(models.Server).filter(models.Server.name == server_name).first()
        if not server:
            raise HTTPException(status_code=404, detail=f"Unknown server '{server_name}'")
        query = query.filter(models.OsUsername.server_id == server.id)
    return query.all()
