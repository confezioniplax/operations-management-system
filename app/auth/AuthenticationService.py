import bcrypt


class AuthenticationService:
    @staticmethod
    def hash_password(password: str) -> str:
        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode("utf-8")

    @staticmethod
    def check_password(stored_hash: str, provided_password: str) -> bool:
        return bcrypt.checkpw(
            provided_password.encode("utf-8"),
            stored_hash.encode("utf-8"),
        )
