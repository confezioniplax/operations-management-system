# app/quality/router/api_router.py
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
import traceback

from app.dependencies import TokenData, get_current_manager
from app.quality.service.QualityService import QualityService

quality_api_router = APIRouter(
    prefix="/api/quality",
    tags=["quality-api"],
)


@quality_api_router.get("/documents")
def api_list_documents(
    year: Optional[int] = Query(
        default=None,
        description="Anno documento (d.esanno)",
    ),
    codicecf: Optional[str] = Query(
        default=None,
        description="Codice cliente (d.codicecf)",
    ),
    cliente_search: Optional[str] = Query(
        default=None,
        description="Filtro testuale su ragione sociale / cliente",
    ),
    text_search: Optional[str] = Query(
        default=None,
        description="LIKE su descrizione riga / pass / fascia / componenti (da implementare nel repo)",
    ),
    tipi_doc: Optional[List[str]] = Query(
        default=None,
        alias="tipi_doc",
        description="Lista tipi documento (OC, ON, BA, CB, BC, BO, ...)",
    ),
    service: QualityService = Depends(QualityService),
    current_user: TokenData = Depends(get_current_manager),
):
    """
    REST API per l'elenco dei documents qualità (OC/ON/BA/CB/BC/BO).
    """
    try:
        rows = service.list_schede_lavoro(
            year=year,
            codicecf=codicecf,
            cliente_search=cliente_search,
            text_search=text_search,
            tipi_doc=tuple(tipi_doc) if tipi_doc else None,
        )
        return JSONResponse(status_code=200, content={"items": rows})
    except Exception as e:
        print("[api_list_documents]", str(e))
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Errore nel caricamento documents: {e}",
        )


@quality_api_router.get("/documents/{tipodoc}/{esanno}/{numerodoc}")
def api_get_document(
    tipodoc: str,
    esanno: str,
    numerodoc: str,
    service: QualityService = Depends(QualityService),
    current_user: TokenData = Depends(get_current_manager),
):
    """
    REST API per il dettaglio di un singolo document qualità.
    """
    try:
        data = service.get_scheda_lavoro(
            tipodoc=tipodoc,
            esanno=int(esanno),
            numerodoc=numerodoc,
        )
        if not data or not data.get("header"):
            raise HTTPException(
                status_code=404,
                detail="Document qualità non trovato",
            )

        return JSONResponse(status_code=200, content=data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Errore nel caricamento document qualità: {e}",
        )


@quality_api_router.get("/customers")
def api_list_customers(
    search: Optional[str] = Query(default=None, description="Filtro su ragione sociale/codice"),
    limit: Optional[int] = Query(default=200),
    offset: Optional[int] = Query(default=0),
    service: QualityService = Depends(QualityService),
    current_user: TokenData = Depends(get_current_manager),
):
    try:
        rows = service.search_clienti_options(
            cliente_search=search,
            limit=limit or 200,
            offset=offset or 0,
        )
        return JSONResponse(status_code=200, content={"items": rows})
    except Exception as e:
        print("[api_list_customers]", str(e))
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Errore nel caricamento clienti: {e}")
