# app/quality/router/view_router.py
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.dependencies import TokenData, get_current_manager
from app.quality.service.QualityService import QualityService

quality_view_router = APIRouter(
    prefix="/quality",
    tags=["quality-view"],
)

# Jinja cercherà dentro app/templates
templates = Jinja2Templates(directory="app/templates")


@quality_view_router.get("/documents", response_class=HTMLResponse)
async def view_quality_documents(
    request: Request,
    # ⚠ year arriva come stringa (può essere ""), la convertiamo noi a int o None
    tipodoc: Optional[str] = Query(default=None),
    numerodoc: Optional[str] = Query(default=None),
    year: Optional[str] = Query(default=None),
    codicecf: Optional[str] = Query(default=None),
    fornitore_search: Optional[str] = Query(default=None),
    articolo_search: Optional[str] = Query(default=None),
    service: QualityService = Depends(QualityService),
    current_user: TokenData = Depends(get_current_manager),
):
    """
    Pagina HTML per l'elenco dei documents qualità.
    Filtri:
      - tipodoc            (OC/ON/BA/CB/BC/BO)
      - numerodoc          (match parziale)
      - year               (esercizio, d.esanno)
      - codicecf           (codice cliente/fornitore)
      - fornitore_search   (ragione sociale in anagrafe)
      - articolo_search    (testo in righe documento)
    """
    # normalizza year: da stringa a int o None
    year_int: Optional[int]
    if year is None or str(year).strip() == "":
        year_int = None
    else:
        try:
            year_int = int(year)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Parametro 'year' deve essere un intero (es. 2025).",
            )

    try:
        rows = service.search_schede_lavoro(
            tipodoc=tipodoc.strip().upper() if tipodoc else None,
            numerodoc=numerodoc.strip() if numerodoc else None,
            year=year_int,
            codicecf=codicecf.strip() if codicecf else None,
            fornitore_search=fornitore_search.strip() if fornitore_search else None,
            articolo_search=articolo_search.strip() if articolo_search else None,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Errore nel caricamento documents qualità: {e}",
        )

    return templates.TemplateResponse(
        "quality/documenti_list.html",
        {
            "request": request,
            "user": current_user,
            "items": rows,
            "filters": {
                "tipodoc": tipodoc,
                "numerodoc": numerodoc,
                "year": year,  # stringa originale, così il campo input rimane valorizzato
                "codicecf": codicecf,
                "fornitore_search": fornitore_search,
                "articolo_search": articolo_search,
            },
        },
    )


@quality_view_router.get(
    "/documents/{tipodoc}/{esanno}/{numerodoc}",
    response_class=HTMLResponse,
)
async def view_quality_document_detail(
    request: Request,
    tipodoc: str,
    esanno: str,
    numerodoc: str,
    service: QualityService = Depends(QualityService),
    current_user: TokenData = Depends(get_current_manager),
):
    """
    Pagina HTML di dettaglio per un singolo document qualità.
    """
    try:
        data = service.get_scheda_lavoro(
            tipodoc=tipodoc,
            esanno=int(esanno),
            numerodoc=numerodoc,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Errore nel caricamento document qualità: {e}",
        )

    if not data or not data.get("header"):
        raise HTTPException(
            status_code=404,
            detail="Document qualità non trovato",
        )

    header = data["header"]
    righe = data["righe"]

    return templates.TemplateResponse(
        "quality/documenti_detail.html",
        {
            "request": request,
            "user": current_user,
            "header": header,
            "lines": righe,  # il template usa 'lines'
        },
    )


@quality_view_router.get("/articles-by-customer", response_class=HTMLResponse)
async def view_quality_articoli_cliente(
    request: Request,
    tipodoc: Optional[str] = Query(default=None),
    year: Optional[str] = Query(default=None),
    codicecf: Optional[str] = Query(default=None),
    cliente_search: Optional[str] = Query(default=None),
    articolo_search: Optional[str] = Query(default=None),
    offset: Optional[int] = Query(default=0),
    limit: Optional[int] = Query(default=50),
    service: QualityService = Depends(QualityService),
    current_user: TokenData = Depends(get_current_manager),
):
    """
    Pagina HTML per l'elenco degli articoli per anagrafica cliente.
    """
    year_int: Optional[int]
    if year is None or str(year).strip() == "":
        year_int = None
    else:
        try:
            year_int = int(year)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Parametro 'year' deve essere un intero (es. 2025).",
            )

    try:
        # pagina iniziale vuota: non effettuare query se non ci sono filtri
        if not any([
            tipodoc and tipodoc.strip(),
            year_int is not None,
            codicecf and codicecf.strip(),
            cliente_search and cliente_search.strip(),
            articolo_search and articolo_search.strip(),
        ]):
            rows = []
        else:
            # Se il cliente è valorizzato, mostra TUTTE le righe (no paginazione)
            eff_limit = 100000 if (codicecf and codicecf.strip()) else (limit or 50)
            eff_offset = 0 if (codicecf and codicecf.strip()) else (offset or 0)
            rows = service.search_articoli_per_cliente(
                tipodoc=tipodoc.strip().upper() if tipodoc else None,
                year=year_int,
                codicecf=codicecf.strip() if codicecf else None,
                cliente_search=cliente_search.strip() if cliente_search else None,
                articolo_search=articolo_search.strip() if articolo_search else None,
                limit=eff_limit,
                offset=eff_offset,
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Errore nel caricamento articoli per cliente: {e}",
        )

    return templates.TemplateResponse(
        "quality/articoli_per_cliente.html",
        {
            "request": request,
            "user": current_user,
            "items": rows,
            "filters": {
                "tipodoc": tipodoc,
                "year": year,
                "codicecf": codicecf,
                "cliente_search": cliente_search,
                "articolo_search": articolo_search,
                "limit": limit,
                "offset": offset,
            },
        },
    )
