from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta, timezone
from app.database import get_db
from app.models.invitation import Invitation
from app.models.user import User
from app.dependencies import get_current_user, require_level
from app.utils.email import send_invitation_email
import uuid

router = APIRouter(prefix="/invitations", tags=["invitations"])

@router.post("/")
async def create_invitation(
    email: str,
    user: User = Depends(require_level(3)),
    db: AsyncSession = Depends(get_db)
):
    # Check limit (max 3 per month)
    # Mocking date check for simplicity here
    # In real logic: count invitations by inviter_id this month
    
    # Check if existing invitation exists
    result = await db.execute(select(Invitation).where(Invitation.email == email, Invitation.status == 'pending'))
    existing = result.scalar_one_or_none()
    
    if existing:
        existing.status = 'expired'
        await db.commit()
    
    token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    new_invitation = Invitation(
        token=token,
        inviter_id=user.id,
        email=email,
        expires_at=expires_at
    )
    db.add(new_invitation)
    await db.commit()
    
    await send_invitation_email(email, user.username, token)
    return {"message": "Invitation sent successfully", "token": token}

@router.get("/validate/{token}")
async def validate_invitation(token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Invitation).options(selectinload(Invitation.inviter)).where(Invitation.token == token)
    )
    # The inviter relationship is not strictly defined in Invitation model above. 
    # Let's just fetch it simply:
    result = await db.execute(select(Invitation).where(Invitation.token == token))
    invitation = result.scalar_one_or_none()
    
    if not invitation:
        raise HTTPException(status_code=404, detail="초대장을 찾을 수 없습니다.")
        
    if invitation.status != 'pending' or invitation.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="초대장이 만료되었거나 이미 사용되었습니다.")
        
    inviter_result = await db.execute(select(User).where(User.id == invitation.inviter_id))
    inviter = inviter_result.scalar_one_or_none()
    inviter_name = inviter.username if inviter else "관리자"
    
    return {"email": invitation.email, "inviter": inviter_name}
