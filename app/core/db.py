# app/core/db.py
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Sequence

import mysql.connector
from mysql.connector import MySQLConnection

from app.settings import get_settings


class QueryType(str, Enum):
    """
    Tipologia di query gestite dal wrapper DB.

    - SELECT / GET  -> SELECT (ritorna righe)
    - INSERT        -> inserimento
    - UPDATE        -> update
    - DELETE        -> delete
    - SCRIPT        -> script multi-statement
    """

    SELECT = "SELECT"
    GET = "GET"          # alias logico di SELECT (compatibilità con vecchi repo)
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    SCRIPT = "SCRIPT"


class MySQLDb:
    """
    Wrapper minimale per la connessione MySQL.

    Supporta:
    - DB principale (da settings.API_MYSQL_DB)
    - DB secondari (es. QUALITY / fox_staging) tramite db_name

    Esempi:

        # DB principale
        with DbManager(MySQLDb()) as db:
            ...

        # DB fox_staging (QUALITY, compatibilità col vecchio codice)
        with DbManager(MySQLDb.FOX_STAGING) as db:
            ...
    """

    def __init__(self, db_name: Optional[str] = None) -> None:
        # se None, usa settings.API_MYSQL_DB
        self._db_name = db_name
        self._conn: Optional[MySQLConnection] = None

    # ---------------- Connessione ----------------
    def connect(self) -> None:
        if self._conn is not None and self._conn.is_connected():
            return

        settings = get_settings()

        # DB principale
        if self._db_name is None:
            host = settings.API_MYSQL_HOSTNAME
            port = settings.API_MYSQL_PORT
            user = settings.API_MYSQL_USERNAME
            password = settings.API_MYSQL_PASSWORD
            db_to_use = settings.API_MYSQL_DB

        # DB QUALITY (fox_staging) con eventuali override dedicati
        elif self._db_name == settings.QUALITY_MYSQL_DB:
            host = settings.QUALITY_MYSQL_HOSTNAME or settings.API_MYSQL_HOSTNAME
            port = settings.QUALITY_MYSQL_PORT or settings.API_MYSQL_PORT
            user = settings.QUALITY_MYSQL_USERNAME or settings.API_MYSQL_USERNAME
            password = settings.QUALITY_MYSQL_PASSWORD or settings.API_MYSQL_PASSWORD
            db_to_use = settings.QUALITY_MYSQL_DB

        # Altro DB nominato: usa stesso host/utente del principale, nome diverso
        else:
            host = settings.API_MYSQL_HOSTNAME
            port = settings.API_MYSQL_PORT
            user = settings.API_MYSQL_USERNAME
            password = settings.API_MYSQL_PASSWORD
            db_to_use = self._db_name

        self._conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=db_to_use,
            autocommit=False,
        )

    def close(self) -> None:
        if self._conn is not None and self._conn.is_connected():
            self._conn.close()
        self._conn = None

    # ------------- API di basso livello: execute(...) -------------
    def execute(
        self,
        *,
        query_type: QueryType,
        sql: str,
        params: Optional[Sequence[Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Esegue una singola query / script.

        - SELECT / GET -> ritorna list[dict]
        - INSERT / UPDATE / DELETE -> commit e ritorna []
        - SCRIPT -> esegue anche statement multipli (multi=True), ritorna []
        """
        if self._conn is None or not self._conn.is_connected():
            raise RuntimeError(
                "Connessione MySQL non inizializzata. "
                "Chiama connect() prima di usare execute()."
            )

        cursor = self._conn.cursor(dictionary=True)

        try:
            if query_type is QueryType.SCRIPT:
                # Esecuzione multi-statement (es. script .sql)
                for _ in cursor.execute(sql, params or None, multi=True):
                    pass
                self._conn.commit()
                return []

            # Tutto il resto: SELECT/GET/INSERT/UPDATE/DELETE
            cursor.execute(sql, params or None)

            if query_type in (QueryType.SELECT, QueryType.GET):
                rows = cursor.fetchall()
                return list(rows)

            # INSERT / UPDATE / DELETE
            self._conn.commit()
            return []

        except Exception:
            self._conn.rollback()
            raise
        finally:
            cursor.close()

    # ------------- API "vecchia": execute_query(...) -------------
    def execute_query(
        self,
        query: str,
        params: Optional[Sequence[Any]] = None,
        fetchall: bool = True,
        *,
        query_type: QueryType = QueryType.SELECT,
    ) -> List[Dict[str, Any]]:
        """
        Adapter compatibile con il codice che hai già:

            db.execute_query(
                query,
                params,
                query_type=QueryType.SELECT
            )

        Comportamento:

        - Se query_type in (SELECT, GET):
            - se fetchall=True  -> ritorna tutte le righe
            - se fetchall=False -> ritorna solo la prima riga come lista con 1 elem.
        - Se query_type in (INSERT, UPDATE, DELETE, SCRIPT):
            - esegue la query/script
            - commit
            - ritorna []
        """
        # SELECT / GET
        if query_type in (QueryType.SELECT, QueryType.GET):
            rows = self.execute(
                query_type=query_type,
                sql=query,
                params=params,
            )
            if not fetchall and rows:
                return [rows[0]]
            return rows

        # INSERT / UPDATE / DELETE / SCRIPT
        self.execute(
            query_type=query_type,
            sql=query,
            params=params,
        )
        return []


class DbManager:
    """
    Context manager per gestire apertura/chiusura connessione.

    Uso previsto:

        from app.core.db import DbManager, MySQLDb, QueryType

        with DbManager(MySQLDb()) as db:
            rows = db.execute_query(
                "SELECT ...",
                params=[...],
                query_type=QueryType.SELECT,
            )
    """

    def __init__(self, db: MySQLDb) -> None:
        self._db = db

    def __enter__(self) -> MySQLDb:
        self._db.connect()
        return self._db

    def __exit__(self, exc_type, exc, tb) -> None:
        self._db.close()


# ============================================================
#  COMPATIBILITÀ LEGACY: MySQLDb.FOX_STAGING (QUALITY)
# ============================================================
_settings = get_settings()
MySQLDb.FOX_STAGING = MySQLDb(db_name=_settings.QUALITY_MYSQL_DB)
