from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.models.point_log import PointLog

# Constants
POINTS_SIGNUP = 10
POINTS_POST = 5
POINTS_COMMENT = 2
POINTS_LIKE_RECEIVED = 1

LEVEL_THRESHOLDS = {
    1: 0,
    2: 100,
    3: 500,
    4: 2000,
    5: 10000 # Honorary
}

async def calculate_level(total_points: int) -> int:
    new_level = 1
    for level, threshold in sorted(LEVEL_THRESHOLDS.items()):
        if total_points >= threshold:
            new_level = level
        else:
            break
    return new_level

async def award_points(db: AsyncSession, user_id: int, amount: int, reason: str, target_id: int = None):
    # 1. Fetch user
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        return
        
    # 2. Update points
    user.total_points += amount
    if user.total_points < 0:
        user.total_points = 0
        
    # 3. Calculate new level
    new_level = await calculate_level(user.total_points)
    if new_level != user.level:
        user.level = new_level
        # In a real app, you might want to trigger a notification here
        
    # 4. Create log
    log = PointLog(user_id=user_id, amount=amount, reason=reason, target_id=target_id)
    db.add(log)
    
    # Let caller commit to maintain transaction scope
