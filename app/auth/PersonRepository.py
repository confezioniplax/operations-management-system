"""
 MIT License
 
 Copyright (c) 2024 Riccardo Leonelli
"""

from __future__ import annotations

from app.auth.Person import Person
from app.core.db import DbManager, MySQLDb, QueryType
from app.auth.AuthenticationService import AuthenticationService
from app.auth.QueryUserAuth import SqlUserAuth


class PersonRepository:
    def __init__(self) -> None:
        # Usa il DbManager della nuova app
        self.db = DbManager(MySQLDb())

    def get_user_info_auth(self, username: str) -> Person | None:
        """
        Ritorna i dati dell'utente (Person) a partire dall'email/username.
        Usa la query definita in SqlUserAuth.get_user_info_auth().
        """
        sql = SqlUserAuth.get_user_info_auth()

        with self.db as db:
            result = db.execute_query(
                sql,
                (username,),
                fetchall=True,
                query_type=QueryType.GET,
            )

        if result:
            return Person(**result[0])
        return None

    def get_encrypted_password(self, password: str) -> str:
        """
        Restituisce l'hash della password usando le stesse regole del login.
        """
        hashed_pw = AuthenticationService.hash_password(password=password)
        return hashed_pw

    def check_password(self, stored_password: str, password: str) -> bool:
        """
        Confronta password in chiaro con hash salvato a DB.
        """
        return AuthenticationService.check_password(
            stored_hash=stored_password,
            provided_password=password,
        )
