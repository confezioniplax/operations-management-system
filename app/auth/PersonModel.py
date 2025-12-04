"""
 MIT License
 
 Copyright (c) 2024 Riccardo Leonelli
"""

from app.auth.Person import Person
from app.auth.PersonRepository import PersonRepository


class PersonModel:
    def __init__(self, dal: PersonRepository | None = None) -> None:
        self.dal = dal or PersonRepository()

    def get_user_info_auth(self, username: str) -> Person | None:
        return self.dal.get_user_info_auth(username)
  
    def get_encrypted_password(self, password: str) -> str:
        return self.dal.get_encrypted_password(password)

    def check_password(self, stored_password: str, password: str) -> bool:
        return self.dal.check_password(
            stored_password=stored_password,
            password=password,
        )
