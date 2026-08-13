from fastapi import APIRouter , Depends 
from app.db.schema.user import UserInCreate, UserInLogin, UserWithToken, UserOutput
from app.core.database import get_db
from sqlalchemy.orm import Session
from app.service.userService import UserService
from app.util.protectRoute import security
from app.db.repository.tokenRepo import TokenRepository
from fastapi.security import HTTPAuthorizationCredentials

authRouter = APIRouter()

@authRouter.post("/login", status_code=200, response_model=UserWithToken)
def login(loginDetails: UserInLogin, session:Session=Depends(get_db)):
    try:
        return UserService(session=session).login(login_details=loginDetails)
    except Exception as e:
        print(e)
        raise e 

@authRouter.post("/signup", status_code=201, response_model=UserOutput)
def signup(signupDetails: UserInCreate, session:Session=Depends(get_db)):
    try: 
        return UserService(session=session).signup(user_details=signupDetails)
    except Exception as e:
        print(e)
        raise e

@authRouter.post("/logout", status_code=200)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_db)
):
    try:
        token = credentials.credentials
        TokenRepository(session=session).add_to_blacklist(token=token)
        return {"message": "Successfully logged out"}
    except Exception as e:
        print(e)
        raise e
