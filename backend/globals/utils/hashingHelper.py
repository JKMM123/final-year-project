from passlib.context import CryptContext



class HashingHelper:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    @staticmethod
    def generate_hash(password: str) -> str:
        return HashingHelper.pwd_context.hash(password)

    @staticmethod
    def verify_hash(plain_password: str, hashed_password: str) -> bool:
        return HashingHelper.pwd_context.verify(plain_password, hashed_password)