from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.auth.LoginRouter import router as login_router

# Router QUALITY (gli altri moduli per ora sono vuoti)
from app.quality.router.api_router import quality_api_router
from app.quality.router.view_router import quality_view_router

# ============================
# APP SETUP
# ============================

app = FastAPI(
    title="Operations Management System",
    description="Operations Management System - Quality / Maintenance / Scheduling",
    version="0.1.0",
)

# Templates Jinja2
templates = Jinja2Templates(directory="app/templates")

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# CORS (per ora aperto, lo stringerai quando avrai il frontend definitivo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # se vuoi limitarlo, qui metti la lista degli host
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================
# ROUTES BASE
# ============================

@app.get("/")
async def root():
    """
    Endpoint base minimale.
    Non dipende da template così l'app parte anche se non hai ancora creato gli HTML.
    """
    return {"app": "operations-management-system", "status": "ok"}


@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# ============================
# ERROR HANDLING
# ============================

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """
    Gestione centralizzata delle HTTPException.
    Per ora:
      - 401 → (placeholder) redirect a /login (lo potrai implementare dopo)
      - 403 → redirect alla root
      - resto → testo semplice
    """
    if exc.status_code == 401:
        return RedirectResponse(url="/login")
    if exc.status_code == 403:
        return RedirectResponse(url="/")
    return PlainTextResponse(str(exc.detail), status_code=exc.status_code)


# ============================
# INCLUDE ROUTER MODULO QUALITY
# ============================

app.include_router(quality_api_router)
app.include_router(quality_view_router)
app.include_router(login_router)
