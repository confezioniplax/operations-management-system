# app/sql/query/quality_queries.py
# MIT License (c) 2025 Riccardo Leonelli

from __future__ import annotations


class QuerySqlQualityMYSQL:
    """
    Query SQL per il modulo QUALITÀ che lavora sul DB fox_staging.

    Convenzioni IMPORTANTI sugli alias (usate dal QualityService):

    - Tutti i campi di TESTATA MUST hanno prefisso `d_`:
        d_tipodoc, d_esanno, d_numerodoc, d_datadoc,
        d_codicecf, d_cliente_nome, d_piva, d_cfisc,
        d_ddragsoc, d_ddindir, d_ddcap, d_ddlocal,
        d_totdoc, d_totimp, d_totmerce, d_totiva,
        d_oggetto, d_note_testa, d_username, d_timestamp_row

    - Tutti i campi di RIGA MUST hanno prefisso `r_`:
        r_numeroriga, r_codicearti, r_descrizione_articolo,
        r_descrizione_riga, r_unmisura, r_quantita, r_quantitare,
        r_sconti, r_prezzoun, r_prezzotot, r_aliiva,
        r_magpartenz, r_magarrivo, r_lotto, r_commessa,
        r_mezzo, r_tipolav, r_codcaumag,
        r_pass, r_fascia, r_componenti,
        r_note_riga, r_username, r_timestamp_row

    I tipi documento di interesse (schede lavoro):
        OC, ON, BA, CB, BC, BO
    """

    TIPI_DOC_LAVORO = ("OC", "ON", "BA", "CB", "BC", "BO")

    # ------------------------------------------------------------------ #
    # LISTA / RICERCA SCHEDE LAVORO (solo testata)
    # ------------------------------------------------------------------ #
    @staticmethod
    def search_schede_lavoro_sql() -> str:
        """
        Restituisce una lista di documenti (solo testata) filtrabile per:

        - tipodoc            -> opzionale (OC/ON/BA/CB/BC/BO). Se NULL: prende tutti TIPI_DOC_LAVORO
        - numerodoc          -> opzionale (LIKE, match parziale)
        - esercizio (year)   -> opzionale, mappato su d.esanno
        - codicecf           -> opzionale, codice cliente/fornitore
        - fornitore_search   -> opzionale, match su DESCRIZION / SUPRAGSOC (anagrafe)
        - articolo_search    -> opzionale, match su docrig/magart/u_scimp
                                (codice articolo, descrizione, passo, fascia, descrizione magazzino)

        Parametri (in QUESTO ordine):

            1  tipodoc_filter
            2  tipodoc_filter

            3  numerodoc_filter
            4  numerodoc_filter

            5  esanno_filter
            6  esanno_filter

            7  codicecf_filter
            8  codicecf_filter

            9  fornitore_search
            10 fornitore_search
            11 fornitore_search

            12 articolo_search
            13 articolo_search
            14 articolo_search
            15 articolo_search
            16 articolo_search

            17 limit
            18 offset
        """
        tipi_doc = ", ".join(f"'{t}'" for t in QuerySqlQualityMYSQL.TIPI_DOC_LAVORO)

        return f"""
        SELECT
            d.tipodoc                               AS d_tipodoc,
            d.esanno                                AS d_esanno,
            d.numerodoc                             AS d_numerodoc,
            d.datadoc                               AS d_datadoc,
            d.codicecf                              AS d_codicecf,
            COALESCE(a.SUPRAGSOC, a.DESCRIZION)     AS d_cliente_nome,
            a.PARTIVA                               AS d_piva,
            a.CODFISCALE                            AS d_cfisc,
            d.ddragsoc                              AS d_ddragsoc,
            d.ddindir                               AS d_ddindir,
            d.ddcap                                 AS d_ddcap,
            d.ddlocal                               AS d_ddlocal,
            d.totdoc                                AS d_totdoc,
            d.totimp                                AS d_totimp,
            d.totmerce                              AS d_totmerce,
            d.totiva                                AS d_totiva,
            d.oggetto                               AS d_oggetto,
            d.note                                  AS d_note_testa,
            d.username                              AS d_username,
            d.timestamp_row                         AS d_timestamp_row
        FROM doctes d
        LEFT JOIN anagrafe a
               ON a.CODICE = d.codicecf
        WHERE
            -- includiamo solo i tipi documento di interesse
            d.tipodoc IN ({tipi_doc})

            -- filtro per tipo doc opzionale (OC/ON/BA/CB/BC/BO)
            AND (%s IS NULL OR d.tipodoc = %s)

            -- filtro per NUMERO DOCUMENTO (parziale)
            AND (%s IS NULL OR d.numerodoc LIKE CONCAT('%%', %s, '%%'))

            -- filtro per ANNO / ESERCIZIO
            AND (%s IS NULL OR d.esanno = %s)

            -- filtro per CODICE CLIENTE / FORNITORE
            AND (%s IS NULL OR d.codicecf = %s)

            -- filtro per RAGIONE SOCIALE (anagrafe)
            AND (
                %s IS NULL
                OR a.DESCRIZION LIKE CONCAT('%%', %s, '%%')
                OR a.SUPRAGSOC  LIKE CONCAT('%%', %s, '%%')
            )

            -- filtro per ARTICOLO / TESTO RIGA DOCUMENTO
            AND (
                %s IS NULL
                OR EXISTS (
                    SELECT 1
                    FROM docrig r2
                    LEFT JOIN magart ma2
                           ON ma2.CODICE = r2.codicearti
                    LEFT JOIN u_scimp us2
                           ON us2.id_rigadoc = r2.id
                    WHERE r2.tipodoc   = d.tipodoc
                      AND r2.esanno    = d.esanno
                      AND r2.numerodoc = d.numerodoc
                      AND (
                          r2.codicearti LIKE CONCAT('%%', %s, '%%')
                          OR r2.descrizion LIKE CONCAT('%%', %s, '%%')
                          OR ma2.DESCRIZION LIKE CONCAT('%%', %s, '%%')
                          OR us2.passo  LIKE CONCAT('%%', %s, '%%')
                          OR us2.fascia LIKE CONCAT('%%', %s, '%%')
                      )
                )
            )

        ORDER BY d.datadoc DESC, d.numerodoc DESC
        LIMIT %s OFFSET %s
        """

    # ------------------------------------------------------------------ #
    # LISTA ARTICOLI PER ANAGRAFICA CLIENTE (righe documento)
    # ------------------------------------------------------------------ #
    @staticmethod
    def search_articoli_per_cliente_sql() -> str:
        """
        Restituisce l'elenco delle righe documento (articoli) filtrabile per:

        - tipodoc            -> opzionale (OC/ON/BA/CB/BC/BO)
        - esercizio (year)   -> opzionale, mappato su d.esanno
        - codicecf           -> opzionale, codice cliente/fornitore
        - cliente_search     -> opzionale, match su DESCRIZION / SUPRAGSOC (anagrafe)
        - articolo_search    -> opzionale, match su docrig/magart/u_scimp

        Parametri (in QUESTO ordine):

            1  tipodoc_filter
            2  tipodoc_filter

            3  esanno_filter
            4  esanno_filter

            5  codicecf_filter
            6  codicecf_filter

            7  cliente_search
            8  cliente_search
            9  cliente_search

            10 articolo_search
            11 articolo_search
            12 articolo_search
            13 articolo_search
            14 articolo_search

            15 limit
            16 offset
        """
        tipi_doc = ", ".join(f"'{t}'" for t in QuerySqlQualityMYSQL.TIPI_DOC_LAVORO)

        return f"""
        SELECT
            -- campi di testata minimi (prefisso d_)
            d.tipodoc                           AS d_tipodoc,
            d.esanno                            AS d_esanno,
            d.numerodoc                         AS d_numerodoc,
            d.datadoc                           AS d_datadoc,
            d.codicecf                          AS d_codicecf,
            COALESCE(a.SUPRAGSOC, a.DESCRIZION) AS d_cliente_nome,

            -- campi di riga (prefisso r_)
            r.numeroriga                        AS r_numeroriga,
            r.codicearti                        AS r_codicearti,
            ma.DESCRIZION                       AS r_descrizione_articolo,
            r.descrizion                        AS r_descrizione_riga,
            r.unmisura                          AS r_unmisura,
            r.quantita                          AS r_quantita,
            r.quantitare                        AS r_quantitare,
            COALESCE(us.passo,  ma.U_PASSO)     AS r_pass,
            COALESCE(us.fascia, ma.U_FASCIA)    AS r_fascia,
            CONCAT_WS(' / ',
                NULLIF(r.u_compon1, ''),
                NULLIF(r.u_compon2, ''),
                NULLIF(r.u_compon3, ''),
                NULLIF(r.u_compon4, '')
            )                                   AS r_componenti
        FROM doctes d
        JOIN docrig r
          ON r.tipodoc   = d.tipodoc
         AND r.esanno    = d.esanno
         AND r.numerodoc = d.numerodoc
        LEFT JOIN anagrafe a
               ON a.CODICE = d.codicecf
        LEFT JOIN magart ma
               ON ma.CODICE = r.codicearti
        LEFT JOIN u_scimp us
               ON us.id_rigadoc = r.id
        WHERE
            d.tipodoc IN ({tipi_doc})

            -- filtro per tipo doc opzionale
            AND (%s IS NULL OR d.tipodoc = %s)

            -- filtro per ANNO / ESERCIZIO
            AND (%s IS NULL OR d.esanno = %s)

            -- filtro per CODICE CLIENTE / FORNITORE
            AND (%s IS NULL OR d.codicecf = %s)

            -- filtro per RAGIONE SOCIALE (anagrafe)
            AND (
                %s IS NULL
                OR a.DESCRIZION LIKE CONCAT('%%', %s, '%%')
                OR a.SUPRAGSOC  LIKE CONCAT('%%', %s, '%%')
            )

            -- filtro per ARTICOLO / TESTO RIGA DOCUMENTO
            AND (
                %s IS NULL
                OR (
                    r.codicearti LIKE CONCAT('%%', %s, '%%')
                    OR r.descrizion LIKE CONCAT('%%', %s, '%%')
                    OR ma.DESCRIZION LIKE CONCAT('%%', %s, '%%')
                    OR us.passo  LIKE CONCAT('%%', %s, '%%')
                    OR us.fascia LIKE CONCAT('%%', %s, '%%')
                )
            )

            AND NOT (
                UPPER(r.codicearti) LIKE 'CONAI%%'
                OR UPPER(r.codicearti) LIKE 'BANCALE%%'
                OR UPPER(r.descrizion) LIKE '%CONAI%'
                OR UPPER(r.descrizion) LIKE '%BANCALE%'
                OR UPPER(ma.DESCRIZION) LIKE '%CONAI%'
                OR UPPER(ma.DESCRIZION) LIKE '%BANCALE%'
            )

            -- solo righe con codice articolo valorizzato
            AND r.codicearti IS NOT NULL
            AND r.codicearti <> ''

        ORDER BY d.datadoc DESC, d.numerodoc DESC, r.numeroriga ASC
        LIMIT %s OFFSET %s
        """

    # ------------------------------------------------------------------ #
    # OPZIONI CLIENTI (ragione sociale + codice) per tendina
    # ------------------------------------------------------------------ #
    @staticmethod
    def search_clienti_options_sql() -> str:
        """
        Restituisce le anagrafiche clienti/fornitori dalla tabella anagrafe,
        con filtro opzionale su ragione sociale/codice per ricerca dinamica.

        Parametri:
            1  search_text
            2  search_text
            3  search_text
            4  limit
            5  offset
        """
        return """
        SELECT
            a.CODICE                               AS codicecf,
            COALESCE(a.SUPRAGSOC, a.DESCRIZION)    AS cliente_nome
        FROM anagrafe a
        WHERE a.CODICE IS NOT NULL AND a.CODICE <> ''
          AND (
            %s IS NULL
            OR a.DESCRIZION LIKE CONCAT('%%', %s, '%%')
            OR a.SUPRAGSOC  LIKE CONCAT('%%', %s, '%%')
            OR a.CODICE     LIKE CONCAT('%%', %s, '%%')
          )
        ORDER BY cliente_nome ASC, a.CODICE ASC
        LIMIT %s OFFSET %s
        """

    # ------------------------------------------------------------------ #
    # DETTAGLIO SINGOLA SCHEDA LAVORO (testata + righe)
    # ------------------------------------------------------------------ #
    @staticmethod
    def get_scheda_lavoro_sql() -> str:
        """
        Dettaglio completo di una scheda lavoro (testata + righe).

        Chiave primaria logica:
            tipodoc + esanno + numerodoc

        Parametri (in questo ordine):
            1  tipodoc
            2  esanno
            3  numerodoc
        """
        return """
        SELECT
            -- ============================
            -- CAMPi TESTATA (prefisso d_)
            -- ============================
            d.tipodoc                           AS d_tipodoc,
            d.esanno                            AS d_esanno,
            d.numerodoc                         AS d_numerodoc,
            d.datadoc                           AS d_datadoc,
            d.codicecf                          AS d_codicecf,
            COALESCE(a.SUPRAGSOC, a.DESCRIZION) AS d_cliente_nome,
            a.PARTIVA                           AS d_piva,
            a.CODFISCALE                        AS d_cfisc,
            d.ddragsoc                          AS d_ddragsoc,
            d.ddindir                           AS d_ddindir,
            d.ddcap                             AS d_ddcap,
            d.ddlocal                           AS d_ddlocal,
            d.totdoc                            AS d_totdoc,
            d.totimp                            AS d_totimp,
            d.totmerce                          AS d_totmerce,
            d.totiva                            AS d_totiva,
            d.oggetto                           AS d_oggetto,
            d.note                              AS d_note_testa,
            d.username                          AS d_username,
            d.timestamp_row                     AS d_timestamp_row,

            -- ============================
            -- CAMPi RIGA (prefisso r_)
            -- ============================
            r.numeroriga                        AS r_numeroriga,
            r.codicearti                        AS r_codicearti,
            ma.DESCRIZION                       AS r_descrizione_articolo,
            r.descrizion                        AS r_descrizione_riga,
            r.unmisura                          AS r_unmisura,
            r.quantita                          AS r_quantita,
            r.quantitare                        AS r_quantitare,
            r.sconti                            AS r_sconti,
            r.prezzoun                          AS r_prezzoun,
            r.prezzotot                         AS r_prezzotot,
            r.aliiva                            AS r_aliiva,
            r.magpartenz                        AS r_magpartenz,
            r.magarrivo                         AS r_magarrivo,
            r.lotto                             AS r_lotto,
            r.commessa                          AS r_commessa,
            r.mezzo                             AS r_mezzo,
            r.tipolav                           AS r_tipolav,
            r.codcaumag                         AS r_codcaumag,
            r.note                              AS r_note_riga,
            r.username                          AS r_username,
            r.timestamp_row                     AS r_timestamp_row,

            -- ============================
            -- CAMPi QUALITÀ (prefisso r_)
            -- ============================
            COALESCE(us.passo,  ma.U_PASSO)     AS r_pass,
            COALESCE(us.fascia, ma.U_FASCIA)    AS r_fascia,
            CONCAT_WS(' / ',
                NULLIF(r.u_compon1, ''),
                NULLIF(r.u_compon2, ''),
                NULLIF(r.u_compon3, ''),
                NULLIF(r.u_compon4, '')
            )                                   AS r_componenti
        FROM doctes d
        JOIN docrig r
          ON r.tipodoc   = d.tipodoc
         AND r.esanno    = d.esanno
         AND r.numerodoc = d.numerodoc
        LEFT JOIN anagrafe a
               ON a.CODICE = d.codicecf
        LEFT JOIN magart ma
               ON ma.CODICE = r.codicearti
        LEFT JOIN u_scimp us
               ON us.id_rigadoc = r.id

        WHERE d.tipodoc   = %s
          AND d.esanno    = %s
          AND d.numerodoc = %s
          AND r.codicearti IS NOT NULL
          AND r.codicearti <> ''

        ORDER BY r.numeroriga ASC
        """
