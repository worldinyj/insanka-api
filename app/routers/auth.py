from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.invitation import Invitation
from app.models.membership_proof import MembershipProof
from app.utils.media import upload_proof_image
from datetime import datetime, timezone

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    # TODO: Implement login logic
    return {"access_token": "fake-token", "token_type": "bearer"}

@router.post("/invitations/{token}/signup")
async def signup(
    token: str,
    username: str = Form(...),
    password: str = Form(...),
    proof_image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Invitation).where(Invitation.token == token))
    invitation = result.scalar_one_or_none()
    
    if not invitation or invitation.status != 'pending' or invitation.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="유효하지 않은 초대 링크입니다.")
        
    # Check username
    existing_user = await db.execute(select(User).where(User.username == username))
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="이미 사용중인 닉네임입니다.")
        
    # Upload proof
    image_url = await upload_proof_image(proof_image)
    
    # Create user
    new_user = User(
        email=invitation.email,
        username=username,
        hashed_pw="mock-hashed-pw", # Mock password hashing for now
        invited_by=invitation.inviter_id
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Create proof
    proof = MembershipProof(
        user_id=new_user.id,
        image_url=image_url
    )
    db.add(proof)
    
    # Update invitation
    invitation.status = 'accepted'
    
    await db.commit()
    return {"message": "가입 신청이 완료되었습니다. 관리자 승인을 기다려주세요."}

@router.post("/refresh")
async def refresh_token():
    # TODO: Implement token refresh
    return {"message": "Refresh endpoint"}

@router.post("/logout")
async def logout():
    # TODO: Implement logout
    return {"message": "Logged out"}
