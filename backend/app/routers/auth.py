"""Microsoft OIDC login (university/Outlook accounts).

Requires MS_CLIENT_ID / MS_CLIENT_SECRET / MS_TENANT_ID to be set (an app
registration in the university's Azure AD tenant); until then /login
returns 501 so the rest of the app still runs without it configured.
"""

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from .. import models
from ..config import settings
from ..database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])

oauth = OAuth()
if settings.ms_client_id:
    oauth.register(
        name="microsoft",
        client_id=settings.ms_client_id,
        client_secret=settings.ms_client_secret,
        server_metadata_url=(
            f"https://login.microsoftonline.com/{settings.ms_tenant_id}"
            "/v2.0/.well-known/openid-configuration"
        ),
        client_kwargs={"scope": "openid email profile"},
    )


@router.get("/login")
async def login(request: Request):
    if not settings.ms_client_id:
        raise HTTPException(status_code=501, detail="Microsoft OAuth is not configured yet")
    return await oauth.microsoft.authorize_redirect(request, settings.ms_redirect_uri)


@router.get("/callback")
async def callback(request: Request, db: Session = Depends(get_db)):
    if not settings.ms_client_id:
        raise HTTPException(status_code=501, detail="Microsoft OAuth is not configured yet")

    token = await oauth.microsoft.authorize_access_token(request)
    userinfo = token.get("userinfo") or {}
    email = userinfo.get("email") or userinfo.get("preferred_username")
    account_id = userinfo.get("sub")
    name = userinfo.get("name", email)

    if not email:
        raise HTTPException(status_code=400, detail="Microsoft account did not return an email")

    user = db.query(models.User).filter(models.User.university_email == email).first()
    if not user:
        user = models.User(name=name, university_email=email, microsoft_account_id=account_id)
        db.add(user)
    else:
        user.microsoft_account_id = account_id
    db.commit()
    db.refresh(user)

    # TODO: issue a real session/JWT for the frontend. For now redirect with
    # the user id as a placeholder so the booking UI can be wired up next.
    return RedirectResponse(url=f"/?user_id={user.id}")
