from sqlalchemy.orm import Session
#will need an instance of a session to talk to db 

class BaseRepository: 
    def __init__(self, session:Session) -> None:
        self.session = session
        