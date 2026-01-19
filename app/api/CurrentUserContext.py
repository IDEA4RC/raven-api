from dataclasses import dataclass
from typing import Dict, Any
from app.models.user import User

@dataclass
class CurrentUserContext:
    user: User
    access_token: str
    claims: Dict[str, Any]
