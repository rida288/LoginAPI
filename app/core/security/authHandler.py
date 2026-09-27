import jwt
from decouple import config 
import time 

JWT_SECRET = config("JWT_SECRET")
JWT_ALGORITHM = config("JWT_ALGORITHM")

class AuthHandler(object):
    @staticmethod 
    def sign_jwt(user_id:int, role:str) -> str:
        payload = {
            "user_id": user_id,
            "role": role,
            "expires": time.time() + 604800  # 7 days
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return token 
    
    @staticmethod
    def decode_jwt(token: str) -> dict:
        try:
            decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return decoded_token if decoded_token.get("expires", 0) >= time.time() else None
        except Exception as e:
            print(f"Unable to decode token: {e}")
            return None