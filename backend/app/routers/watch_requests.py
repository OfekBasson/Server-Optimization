from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/watch-requests", tags=["watch-requests"])


@router.post("", response_model=schemas.WatchRequestOut)
def create_watch_request(payload: schemas.WatchRequestCreate, db: Session = Depends(get_db)):
    watch = models.WatchRequest(**payload.model_dump())
    db.add(watch)
    db.commit()
    db.refresh(watch)
    return watch


@router.get("", response_model=list[schemas.WatchRequestOut])
def list_watch_requests(user_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(models.WatchRequest)
    if user_id is not None:
        query = query.filter(models.WatchRequest.user_id == user_id)
    return query.order_by(models.WatchRequest.created_at.desc()).all()


@router.post("/{watch_id}/cancel", response_model=schemas.WatchRequestOut)
def cancel_watch_request(watch_id: int, db: Session = Depends(get_db)):
    watch = db.get(models.WatchRequest, watch_id)
    if not watch:
        raise HTTPException(status_code=404, detail="Watch request not found")
    watch.status = models.WatchRequestStatus.expired
    db.commit()
    db.refresh(watch)
    return watch
