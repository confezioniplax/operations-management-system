# app/quality/service/QualityService.py
# MIT License (c) 2025 Riccardo Leonelli

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from app.quality.repo.QualityRepository import QualityRepositoryMYSQL


# Tipi documento che consideriamo "schede lavoro"
DEFAULT_TIPI_DOC: Sequence[str] = ("OC", "ON", "BA", "CB", "BC", "BO")


class QualityService:
    """
    Servizio applicativo per il modulo QUALITÀ.

    Responsabilità:
      - ricerca schede lavoro (lista)
      - dettaglio scheda lavoro (testata + righe)
      - normalizzazione dei dati grezzi del repository
    """

    def __init__(self, repo: Optional[QualityRepositoryMYSQL] = None) -> None:
        self._repo = repo or QualityRepositoryMYSQL()

    # ------------------------------------------------------------------ #
    # LISTA / RICERCA SCHEDA LAVORO - API interna "pulita"
    # ------------------------------------------------------------------ #
    def search_schede_lavoro(
        self,
        *,
        tipodoc: Optional[str] = None,
        numerodoc: Optional[str] = None,
        year: Optional[int] = None,
        codicecf: Optional[str] = None,
        fornitore_search: Optional[str] = None,
        articolo_search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Restituisce una lista di schede lavoro (solo testata) normalizzate.

        Parametri "puliti":
          - tipodoc: tipo documento (OC, ON, BA, CB, BC, BO)
          - numerodoc: numero doc (LIKE, parziale)
          - year: esercizio (mappato su d.esanno)
          - codicecf: codice cliente/fornitore
          - fornitore_search: filtro su DESCRIZION / SUPRAGSOC
          - articolo_search: filtro su righe doc / magart / qualità
        """
        # Traduzione parametri verso il repository
        raw_rows = self._repo.search_schede_lavoro(
            tipodoc=tipodoc,
            numerodoc=numerodoc,
            year=year,  # ✅ QUI prima avevamo esanno=year: era l'errore
            codicecf=codicecf,
            fornitore_search=fornitore_search,
            articolo_search=articolo_search,
            limit=limit,
            offset=offset,
        )

        out: List[Dict[str, Any]] = []

        # Filtro di sicurezza sui tipi documento (già filtrati in SQL)
        for row in raw_rows:
            header = self._extract_header(row)
            tip = str(header.get("tipodoc") or "").upper()
            if tip and tip not in DEFAULT_TIPI_DOC:
                continue
            out.append(header)

        return out

    # ------------------------------------------------------------------ #
    # LISTA ARTICOLI PER ANAGRAFICA CLIENTE (righe documento)
    # ------------------------------------------------------------------ #
    def search_articoli_per_cliente(
        self,
        *,
        tipodoc: Optional[str] = None,
        year: Optional[int] = None,
        codicecf: Optional[str] = None,
        cliente_search: Optional[str] = None,
        articolo_search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Restituisce righe documento (articoli) normalizzate, con informazioni
        minime di testata per risalire al documento.
        """
        raw_rows = self._repo.search_articoli_per_cliente(
            tipodoc=tipodoc,
            year=year,
            codicecf=codicecf,
            cliente_search=cliente_search,
            articolo_search=articolo_search,
            limit=limit,
            offset=offset,
        )

        out: List[Dict[str, Any]] = []
        for row in raw_rows:
            header = self._extract_header(row)
            tip = str(header.get("tipodoc") or "").upper()
            if tip and tip not in DEFAULT_TIPI_DOC:
                continue
            r = self._extract_row(row)
            # componiamo un item unendo alcuni campi di testata e riga
            item: Dict[str, Any] = {
                "tipodoc": header.get("tipodoc"),
                "esanno": header.get("esanno"),
                "numerodoc": header.get("numerodoc"),
                "datadoc": header.get("datadoc"),
                "codicecf": header.get("codicecf"),
                "cliente_nome": header.get("cliente_nome"),
                "numeroriga": r.get("numeroriga"),
                "codicearti": r.get("codicearti"),
                "descrizione_articolo": r.get("descrizione_articolo"),
                "descrizione_riga": r.get("descrizione_riga"),
                "unmisura": r.get("unmisura"),
                "quantita": r.get("quantita"),
                "quantitare": r.get("quantitare"),
                "pass": r.get("pass"),
                "fascia": r.get("fascia"),
                "componenti": r.get("componenti"),
            }
            out.append(item)

        return out

    # ------------------------------------------------------------------ #
    # OPZIONI CLIENTI (ragione sociale + codice) per tendina
    # ------------------------------------------------------------------ #
    def search_clienti_options(
        self,
        *,
        cliente_search: Optional[str] = None,
        limit: int = 200,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        rows = self._repo.search_clienti_options(
            cliente_search=cliente_search,
            limit=limit,
            offset=offset,
        )
        out: List[Dict[str, Any]] = []
        for r in rows:
            out.append({
                "codicecf": r.get("codicecf"),
                "cliente_nome": r.get("cliente_nome"),
            })
        return out

    # ------------------------------------------------------------------ #
    # WRAPPER compatibile con i vecchi router (se ancora usati da qualche parte)
    # ------------------------------------------------------------------ #
    def list_schede_lavoro(
        self,
        *,
        year: Optional[int] = None,
        codicecf: Optional[str] = None,
        cliente_search: Optional[str] = None,
        text_search: Optional[str] = None,
        tipi_doc: Optional[Sequence[str]] = None,  # oggi ignorato
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Wrapper per i router più vecchi.

        Mappa i parametri "esterni" usati dalla view verso search_schede_lavoro.

        Ad oggi:
          - `cliente_search` -> fornitore_search (ragione sociale)
          - `text_search`    -> articolo_search (righe documento)
          - `tipi_doc`       -> ignorato (i tipi sono già filtrati in SQL)
        """
        fornitore_search = cliente_search
        articolo_search = text_search

        return self.search_schede_lavoro(
            tipodoc=None,              # il filtro per singolo tipo lo gestiamo lato nuova view
            numerodoc=None,
            year=year,
            codicecf=codicecf,
            fornitore_search=fornitore_search,
            articolo_search=articolo_search,
            limit=limit,
            offset=offset,
        )

    # ------------------------------------------------------------------ #
    # DETTAGLIO SCHEDA LAVORO
    # ------------------------------------------------------------------ #
    def get_scheda_lavoro(
        self,
        *,
        tipodoc: str,
        esanno: int,
        numerodoc: str,
    ) -> Dict[str, Any]:
        """
        Dettaglio completo di una scheda lavoro.

        Ritorna:

            {
              "header": {...},   # campi testata senza prefisso d_
              "righe":  [...],   # lista di righe senza prefisso r_
            }
        """
        rows = self._repo.get_scheda_lavoro(
            tipodoc=tipodoc,
            esanno=esanno,
            numerodoc=numerodoc,
        )

        if not rows:
            return {"header": None, "righe": []}

        header = self._extract_header(rows[0])
        righe = [self._extract_row(r) for r in rows]

        return {
            "header": header,
            "righe": righe,
        }

    # ------------------------------------------------------------------ #
    # HELPERS DI NORMALIZZAZIONE
    # ------------------------------------------------------------------ #
    @staticmethod
    def _extract_header(row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estrae tutti i campi con prefisso `d_` da una riga
        del repository e li restituisce senza prefisso.
        """
        out: Dict[str, Any] = {}
        for key, value in row.items():
            if key.startswith("d_"):
                clean = key[2:]
                out[clean] = value
        return out

    @staticmethod
    def _extract_row(row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estrae tutti i campi con prefisso `r_` da una riga
        del repository e li restituisce senza prefisso.
        """
        out: Dict[str, Any] = {}
        for key, value in row.items():
            # usiamo SOLO prefisso r_
            if key.startswith("r_"):
                clean = key[2:]
                out[clean] = value
        return out
