from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.point_log import PointLog

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "level": user.level,
        "total_points": user.total_points,
        "role": user.role
    }

@router.get("/me/points")
async def get_my_points(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    user_id = user.id
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
        
    logs_result = await db.execute(select(PointLog).where(PointLog.user_id == user_id).order_by(desc(PointLog.created_at)).limit(10))
    logs = logs_result.scalars().all()
    
    return {
        "total_points": user.total_points,
        "level": user.level,
        "logs": [{"id": l.id, "amount": l.amount, "reason": l.reason, "created_at": l.created_at} for l in logs]
    }

@router.get("/ranking")
async def get_ranking(db: AsyncSession = Depends(get_db)):
    # In reality, this might use Redis for caching. Using simple DB order for now.
    result = await db.execute(select(User).order_by(desc(User.total_points)).limit(50))
    users = result.scalars().all()
    
    return {
        "ranking": [{"id": u.id, "username": u.username, "total_points": u.total_points, "level": u.level} for u in users]
    }
