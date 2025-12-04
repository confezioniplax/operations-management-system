"""
 MIT License
 
 Copyright (c) 2024 Riccardo Leonelli
"""

from __future__ import annotations

from datetime import timedelta
import logging

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.PersonModel import PersonModel
from app.auth.Person import Person
from app.dependencies import create_access_token

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/token",
    tags=["login"],
)


@router.post("/")
def get_auth_token(
    response: Response,
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    user_model = PersonModel()
    user: Person | None = user_model.get_user_info_auth(form_data.username)

    # Utente non trovato
    if not user:
        return JSONResponse(
            status_code=401,
            content="user_not_found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Password sbagliata
    if not user_model.check_password(
        stored_password=user.user_password,
        password=form_data.password,
    ):
        return JSONResponse(
            status_code=401,
            content="username_password_error",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # JWT
    access_token_expires = timedelta(minutes=480)

    # ATTENZIONE: meglio usare model_dump() invece di __dict__ per Pydantic
    payload = user.model_dump()
    access_token = create_access_token(
        payload,
        expires_delta=access_token_expires,
    )

    # Costruisco io la JSONResponse e ci appiccico il cookie
    resp = JSONResponse(
        status_code=200,
        content={
            "access_token": access_token,
            "token_type": "bearer",
            "userdata": payload,
        },
    )

    resp.set_cookie(
        key="access_token",
        value=access_token,
        expires=int(access_token_expires.total_seconds()),
        httponly=True,
        samesite="lax",
    )

    return resp
