from .base import BaseRepository
from app.db.models.token import TokenBlacklist

class TokenRepository(BaseRepository):
    def add_to_blacklist(self, token: str):
        blacklisted_token = TokenBlacklist(token=token)
        self.session.add(instance=blacklisted_token)
        self.session.commit()
        return blacklisted_token
        
    def is_token_blacklisted(self, token: str) -> bool:
        blacklisted_token = self.session.query(TokenBlacklist).filter_by(token=token).first()
        return bool(blacklisted_token)
