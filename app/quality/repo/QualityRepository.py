# app/repo/QualityRepository.py
# MIT License (c) 2025 Riccardo Leonelli

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.db import DbManager, MySQLDb, QueryType
from app.quality.sql.quality_queries import QuerySqlQualityMYSQL


class QualityRepositoryMYSQL:
    """
    Repository di accesso dati per il modulo QUALITÀ.

    Usa il DB `fox_staging` (MySQLDb.FOX_STAGING) e incapsula la logica SQL per:
    - ricerca schede lavoro (solo testata)
    - dettaglio scheda lavoro (testata + righe)
    """

    def __init__(self, db_manager: Optional[DbManager] = None) -> None:
        # Evita di condividere la stessa istanza MySQLDb tra richieste concorrenti.
        # Se viene passato un DbManager esterno lo usiamo, altrimenti creiamo
        # un nuovo DbManager per ogni operazione tramite _new_db_manager().
        self._db_manager = db_manager

    def _new_db_manager(self) -> DbManager:
        # Crea una NUOVA istanza MySQLDb puntata al DB QUALITY ad ogni uso.
        from app.settings import get_settings
        settings = get_settings()
        return DbManager(db=MySQLDb(settings.QUALITY_MYSQL_DB))

    # ------------------------------------------------------------------ #
    # LISTA / RICERCA SCHEDE LAVORO
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
        Ritorna una lista di schede lavoro (solo testata).

        Parametri (tutti opzionali):
          - tipodoc: tipo documento (OC/ON/BA/CB/BC/BO)
          - numerodoc: match parziale su numero documento
          - year: esercizio (doctes.esanno)
          - codicecf: codice cliente/fornitore
          - fornitore_search: testo su anagrafe (DESCRIZION/SUPRAGSOC)
          - articolo_search: testo su righe doc / magart / qualità
        """
        sql = QuerySqlQualityMYSQL.search_schede_lavoro_sql()

        # Normalizzazione parametri
        tipodoc_val = (tipodoc or "").strip().upper() or None
        numerodoc_val = (numerodoc or "").strip() or None
        year_val = int(year) if year is not None else None
        codicecf_val = (codicecf or "").strip() or None
        fornitore_val = (fornitore_search or "").strip() or None
        articolo_val = (articolo_search or "").strip() or None

        # ⚠ QUI DEVE ESSERCI LO STESSO NUMERO DI PARAMETRI DEI %s NELLA SQL
        # Ordine (come definito in QuerySqlQualityMYSQL.search_schede_lavoro_sql):
        #
        #   1  tipodoc_filter
        #   2  tipodoc_filter
        #   3  numerodoc_filter
        #   4  numerodoc_filter
        #   5  esanno_filter
        #   6  esanno_filter
        #   7  codicecf_filter
        #   8  codicecf_filter
        #   9  fornitore_search
        #   10 fornitore_search
        #   11 fornitore_search
        #   12 articolo_search (IS NULL)
        #   13 articolo_search (codicearti)
        #   14 articolo_search (descrizion riga)
        #   15 articolo_search (magart.DESCRIZION)
        #   16 articolo_search (us2.passo)
        #   17 articolo_search (us2.fascia)
        #   18 limit
        #   19 offset
        params = [
            # tipodoc filter
            tipodoc_val,
            tipodoc_val,

            # numerodoc filter
            numerodoc_val,
            numerodoc_val,

            # year/esanno filter
            year_val,
            year_val,

            # codicecf filter
            codicecf_val,
            codicecf_val,

            # fornitore_search (DESCRIZION / SUPRAGSOC)
            fornitore_val,
            fornitore_val,
            fornitore_val,

            # articolo_search (righe documento / magart / qualità)
            articolo_val,  # IS NULL check
            articolo_val,  # r2.codicearti
            articolo_val,  # r2.descrizion
            articolo_val,  # ma2.DESCRIZION
            articolo_val,  # us2.passo
            articolo_val,  # us2.fascia

            # paginazione
            int(limit),
            int(offset),
        ]

        with (self._db_manager or self._new_db_manager()) as db:
            rows = db.execute_query(sql, params, query_type=QueryType.GET)  # type: ignore[arg-type]

        return rows or []

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
        Ritorna le righe documento (articoli) filtrate per anagrafica cliente.

        Parametri (tutti opzionali):
          - tipodoc: tipo documento (OC/ON/BA/CB/BC/BO)
          - year: esercizio (doctes.esanno)
          - codicecf: codice cliente/fornitore
          - cliente_search: testo su anagrafe (DESCRIZION/SUPRAGSOC)
          - articolo_search: testo su righe doc / magart / qualità
        """
        sql = QuerySqlQualityMYSQL.search_articoli_per_cliente_sql()

        # Normalizzazione parametri
        tipodoc_val = (tipodoc or "").strip().upper() or None
        year_val = int(year) if year is not None else None
        codicecf_val = (codicecf or "").strip() or None
        cliente_val = (cliente_search or "").strip() or None
        articolo_val = (articolo_search or "").strip() or None

        # Ordine parametri come definito in search_articoli_per_cliente_sql:
        #   1  tipodoc_filter
        #   2  tipodoc_filter
        #   3  esanno_filter
        #   4  esanno_filter
        #   5  codicecf_filter
        #   6  codicecf_filter
        #   7  cliente_search
        #   8  cliente_search
        #   9  cliente_search
        #   10 articolo_search (IS NULL)
        #   11 articolo_search (r.codicearti)
        #   12 articolo_search (r.descrizion)
        #   13 articolo_search (ma.DESCRIZION)
        #   14 articolo_search (us.passo/us.fascia)
        #   15 limit
        #   16 offset
        params = [
            tipodoc_val,
            tipodoc_val,
            year_val,
            year_val,
            codicecf_val,
            codicecf_val,
            cliente_val,
            cliente_val,
            cliente_val,
            articolo_val,
            articolo_val,
            articolo_val,
            articolo_val,
            articolo_val,
            articolo_val,
            int(limit),
            int(offset),
        ]

        with (self._db_manager or self._new_db_manager()) as db:
            rows = db.execute_query(sql, params, query_type=QueryType.GET)  # type: ignore[arg-type]

        return rows or []

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
        sql = QuerySqlQualityMYSQL.search_clienti_options_sql()
        q = (cliente_search or "").strip() or None
        params = [q, q, q, q, int(limit), int(offset)]
        with (self._db_manager or self._new_db_manager()) as db:
            rows = db.execute_query(sql, params, query_type=QueryType.GET)  # type: ignore[arg-type]
        return rows or []

    # ------------------------------------------------------------------ #
    # DETTAGLIO SCHEDA LAVORO
    # ------------------------------------------------------------------ #
    def get_scheda_lavoro(
        self,
        *,
        tipodoc: str,
        esanno: int,
        numerodoc: str,
    ) -> List[Dict[str, Any]]:
        """
        Ritorna il dettaglio COMPLETO di una scheda lavoro:

        - Ogni riga del risultato contiene:
          - tutti i campi di testata con prefisso `d_...`
          - tutti i campi di riga con prefisso `r_...`

        Sarà il `QualityService` a:
        - estrarre un unico header dalla prima riga
        - normalizzare le righe per il frontend.
        """
        if not tipodoc:
            raise ValueError("tipodoc è obbligatorio per get_scheda_lavoro")
        if not numerodoc:
            raise ValueError("numerodoc è obbligatorio per get_scheda_lavoro")

        sql = QuerySqlQualityMYSQL.get_scheda_lavoro_sql()
        params = [tipodoc, int(esanno), str(numerodoc)]

        with (self._db_manager or self._new_db_manager()) as db:
            rows = db.execute_query(sql, params, query_type=QueryType.GET)  # type: ignore[arg-type]

        return rows or []
