from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.vote import Vote, VoteOption, VoteCast
from pydantic import BaseModel
from typing import List

router = APIRouter(tags=["votes"])

class OptionCreate(BaseModel):
    text: str

class VoteCreate(BaseModel):
    title: str
    options: List[OptionCreate]
    is_multiple: bool = False

@router.post("/rooms/{slug}/votes")
async def create_vote(
    slug: str,
    vote_in: VoteCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # Skip room resolving for brevity in mock
    room_id = 1 # MOCK
    
    new_vote = Vote(
        room_id=room_id,
        creator_id=user.id,
        title=vote_in.title,
        is_multiple=vote_in.is_multiple
    )
    db.add(new_vote)
    await db.commit()
    await db.refresh(new_vote)
    
    for opt in vote_in.options:
        db.add(VoteOption(vote_id=new_vote.id, text=opt.text))
        
    await db.commit()
    return {"id": new_vote.id, "title": new_vote.title}

@router.post("/votes/{vote_id}/cast")
async def cast_vote(
    vote_id: int,
    option_ids: List[int],
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    user_id = user.id
    
    vote = (await db.execute(select(Vote).where(Vote.id == vote_id))).scalar_one_or_none()
    if not vote:
        raise HTTPException(404, "Vote not found")
        
    if not vote.is_multiple and len(option_ids) > 1:
        raise HTTPException(400, "This vote does not allow multiple options")
        
    try:
        for opt_id in option_ids:
            # Here we would also verify if opt_id belongs to vote_id
            db.add(VoteCast(vote_id=vote_id, user_id=user_id, option_id=opt_id))
            
            # Simple increment, in production should use atomic update
            # e.g., update(VoteOption).where(id==opt_id).values(vote_count=VoteOption.vote_count + 1)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(400, "Already voted")
        
    return {"message": "Vote cast successfully"}

@router.get("/votes/{vote_id}/results")
async def get_results(vote_id: int, db: AsyncSession = Depends(get_db)):
    options = (await db.execute(select(VoteOption).where(VoteOption.vote_id == vote_id))).scalars().all()
    total = sum([o.vote_count for o in options])
    
    return {
        "vote_id": vote_id,
        "total_votes": total,
        "results": [{"id": o.id, "text": o.text, "count": o.vote_count} for o in options]
    }
