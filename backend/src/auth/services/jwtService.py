from globals.utils.logger import logger
from globals.config.config import (
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES,
    JWT_SECRET_KEY,
    JWT_ALGORITHM
)
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import uuid

from globals.exceptions.global_exceptions import (
    UnauthorizedError
)

class JWTService: 
    def __init__(self):
        logger.info("JWTService initialized successfully")

    @classmethod
    def create_access_token(cls, data: dict):
        try:
            to_encode = data.copy()
            to_encode["type"] = "access"
            to_encode.update({
                "exp":  datetime.now(timezone.utc) + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
                "iat": datetime.now(timezone.utc),
                "jti": str(uuid.uuid4())
            })
            encoded_jwt = jwt.encode(
                claims=to_encode,
                key=JWT_SECRET_KEY,
                algorithm=JWT_ALGORITHM
            )
            logger.info(f"Access token created successfully for {data.get('username')}")
            return encoded_jwt
        
        except Exception as e:
            logger.error(f"Error creating access token: {e}")
            raise e


    @classmethod
    def create_refresh_token(cls, data: dict):
        try:
            to_encode = data.copy()
            to_encode["type"] = "refresh"
            to_encode.update({
                "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_REFRESH_TOKEN_EXPIRE_MINUTES),
                "iat": datetime.now(timezone.utc),
                "jti": str(uuid.uuid4()),
                "sub": data.get("user_id")
            })
            encoded_jwt = jwt.encode(
                claims=to_encode, 
                key=JWT_SECRET_KEY, 
                algorithm=JWT_ALGORITHM
                )
            logger.info(f"Refresh token created successfully for {data.get('user_id')}")
            return encoded_jwt
        
        except Exception as e:
            logger.error(f"Error creating refresh token: {e}")
            raise e

    @classmethod
    def decode_token(cls, token: str):
        try:
            decoded_jwt = jwt.decode(
                token=token,
                key=JWT_SECRET_KEY,
                algorithms=[JWT_ALGORITHM]
            )

            exp = decoded_jwt.get("exp")
            if exp is not None:
                exp_datetime = datetime.fromtimestamp(exp, tz=timezone.utc)
                if exp_datetime < datetime.now(timezone.utc):
                    logger.error("Token has expired (manual check).")
                    raise UnauthorizedError(message="Token has expired.")
                
            return decoded_jwt
        
        except JWTError as e:
            logger.error(f"Error decoding token: {e}")
            raise UnauthorizedError(
                message="Invalid token or token has expired."
            )
        
        except Exception as e:
            logger.error(f"Unexpected error while decoding token: {e}")
            raise UnauthorizedError(
                message="Invalid token or token has expired."
            )
        
        
    @classmethod
    def verify_access_token(cls, token: str):
        try:
            decoded_jwt = cls.decode_token(token)
            if decoded_jwt.get("type") != "access":
                raise UnauthorizedError(
                    message="Invalid access token type."
                    )
            logger.info(f"Access token verified successfully for user: {decoded_jwt.get('username')}")
            return decoded_jwt
        
        except Exception as e:
            logger.error(f"Unexpected error during access token verification: {e}")
            raise 

    @classmethod
    def verify_refresh_token(cls, token: str):
        try:
            decoded_jwt = cls.decode_token(token)
            if decoded_jwt.get("type") != "refresh":
                raise UnauthorizedError(
                    message="Invalid refresh token type."
                )
            logger.info(f"Refresh token verified successfully for user: {decoded_jwt.get('sub')}")
            return decoded_jwt
        
        except Exception as e:
            logger.error(f"Unexpected error during refresh token verification: {e}")
            raise UnauthorizedError(
                message="Invalid refresh token."
            )