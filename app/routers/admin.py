from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.membership_proof import MembershipProof
from app.dependencies import require_admin
from app.utils.email import send_approval_email, send_rejection_email
from app.services.point_service import award_points, POINTS_SIGNUP
from datetime import datetime, timezone

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/pending-members")
async def get_pending_members(db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    result = await db.execute(
        select(MembershipProof, User)
        .join(User, MembershipProof.user_id == User.id)
        .where(MembershipProof.status == 'pending')
        .order_by(MembershipProof.created_at.desc())
    )
    rows = result.all()
    
    proofs_data = []
    for p, u in rows:
        proofs_data.append({
            "id": p.id,
            "user_id": u.id,
            "username": u.username,
            "email": u.email,
            "image_url": p.image_url,
            "created_at": p.created_at
        })
        
    return {"pending_count": len(proofs_data), "proofs": proofs_data}

@router.patch("/members/{user_id}/approve")
async def approve_member(user_id: int, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
        
    proof_result = await db.execute(select(MembershipProof).where(MembershipProof.user_id == user_id))
    proof = proof_result.scalar_one_or_none()
    
    if proof:
        proof.status = 'approved'
        proof.reviewer_id = admin.id
        proof.reviewed_at = datetime.now(timezone.utc)
        
    user.status = 'approved'
    user.approved_at = datetime.now(timezone.utc)
    
    await award_points(db, user.id, POINTS_SIGNUP, "signup_approved")
    
    await db.commit()
    await send_approval_email(user.email)
    
    return {"message": "승인되었습니다."}

@router.patch("/members/{user_id}/reject")
async def reject_member(user_id: int, reason: str, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
        
    proof_result = await db.execute(select(MembershipProof).where(MembershipProof.user_id == user_id))
    proof = proof_result.scalar_one_or_none()
    
    if proof:
        proof.status = 'rejected'
        proof.reviewer_id = admin.id
        proof.review_note = reason
        proof.reviewed_at = datetime.now(timezone.utc)
        
    user.status = 'rejected'
    
    await db.commit()
    await send_rejection_email(user.email, reason)
    
    return {"message": "거절되었습니다."}
