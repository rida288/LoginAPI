import jwt
from decouple import config 
import time 

JWT_SECRET = config("JWT_SECRET")
JWT_ALGORITHM = config("JWT_ALGORITHM")

class AuthHandler(object):
    @staticmethod 
    def sign_jwt(user_id:int, role:str) -> str:
        payload = {
            "user_id":user_id, 
            "role": role,
            "expires":time.time()+900
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return token 
    
    @staticmethod
    def decode_jwt(token:str) -> dict:
        try:
            decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return decoded_token if decoded_token["expires"] >= time.time() else None
        except:
            print("Unable to decode token")
            return None