from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    # TODO: Proper JWT token verification. For now, mock authenticated user 1.
    user = (await db.execute(select(User).where(User.id == 1))).scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user

async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin required")
    return user

def require_level(min_level: int):
    async def checker(user: User = Depends(get_current_user)):
        if user.level < min_level:
            raise HTTPException(status_code=403, detail=f"레벨 {min_level} 이상 필요")
        return user
    return checker
