from app.db.repository.userRepo import UserRepository
from app.db.schema.user import UserInCreate, UserInLogin, UserOutput, UserWithToken
from app.core.security.hashHelper import HashHelper
from app.core.security.authHandler import AuthHandler
from sqlalchemy.orm import Session
from fastapi import HTTPException

class UserService:
    def __init__(self, session:Session):
        self.__userRepository = UserRepository(session=session)
        
    def signup(self, user_details:UserInCreate) -> UserOutput:
        if self.__userRepository.user_exists_by_email(email=user_details.email):
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        hashed_password = HashHelper.get_password_hash(plain_password=user_details.password)
        user_details.password = hashed_password
        return self.__userRepository.create_user(user_data=user_details)
    
    def login(self, login_details:UserInLogin) -> UserWithToken:
        if not self.__userRepository.user_exists_by_email(email=login_details.email):
            raise HTTPException(status_code=400, detail="User with this email does not exist")
        
        user = self.__userRepository.get_user_by_email(email=login_details.email)
        
        if not user.is_approved:
            raise HTTPException(status_code=403, detail="Account pending admin approval")
            
        if HashHelper.verify_password(plain_password=login_details.password, hashed_password=user.password):
            token = AuthHandler.sign_jwt(user_id=user.id)
            if token:
                return UserWithToken(token=token)
            raise HTTPException(status_code=500, detail="Error generating token")
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    def get_user_by_id(self, user_id:int):
        user = self.__userRepository.get_user_by_id(user_id=user_id)
        if not user:
            raise HTTPException(status_code=400, detail="User not found")
        return user
        
    def get_all_users(self):
        return self.__userRepository.get_all_users()
        
    def get_pending_users(self):
        return self.__userRepository.get_pending_users()
        
    def approve_user(self, user_id: int):
        user = self.__userRepository.approve_user(user_id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
        
    def suspend_user(self, user_id: int):
        user = self.__userRepository.suspend_user(user_id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
        
        