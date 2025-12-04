"""
 MIT License
 
 Copyright (c) 2024 Riccardo Leonelli
"""

import datetime
from pydantic import BaseModel


class Person(BaseModel):
    employee_id: int | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    hire_date: datetime.date | None = None
    end_date: str | None = None
    user_password: str | None = None
    role: str | None = None
