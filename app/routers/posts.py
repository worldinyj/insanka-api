from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database import get_db
from app.models.post import Post, Comment, PostLike
from app.models.room import Room
from app.models.user import User
from app.dependencies import get_current_user
from app.services.point_service import award_points, POINTS_POST, POINTS_COMMENT, POINTS_LIKE_RECEIVED
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(tags=["posts"])

class PostCreate(BaseModel):
    title: str
    content: str

class CommentCreate(BaseModel):
    content: str
    parent_id: Optional[int] = None

@router.get("/rooms/{slug}/posts")
async def get_posts(
    slug: str,
    cursor: int = Query(None, description="Last post ID for cursor pagination"),
    limit: int = Query(20, le=50),
    db: AsyncSession = Depends(get_db)
):
    room = (await db.execute(select(Room).where(Room.slug == slug))).scalar_one_or_none()
    if not room:
        raise HTTPException(404, "Room not found")
        
    query = select(Post).where(Post.room_id == room.id)
    if cursor:
        query = query.where(Post.id < cursor)
        
    query = query.order_by(desc(Post.id)).limit(limit)
    result = await db.execute(query)
    posts = result.scalars().all()
    
    return {"posts": [{"id": p.id, "title": p.title, "created_at": p.created_at} for p in posts]}

@router.post("/rooms/{slug}/posts")
async def create_post(
    slug: str,
    post_in: PostCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    room = (await db.execute(select(Room).where(Room.slug == slug))).scalar_one_or_none()
    if not room:
        raise HTTPException(404, "Room not found")
        
    new_post = Post(
        room_id=room.id,
        author_id=user.id,
        title=post_in.title,
        content=post_in.content
    )
    db.add(new_post)
    await award_points(db, 1, POINTS_POST, "post_created", target_id=new_post.id)
    await db.commit()
    await db.refresh(new_post)
    return {"id": new_post.id, "title": new_post.title}

@router.get("/posts/{post_id}")
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    post = (await db.execute(select(Post).where(Post.id == post_id))).scalar_one_or_none()
    if not post:
        raise HTTPException(404, "Post not found")
        
    comments = (await db.execute(select(Comment).where(Comment.post_id == post_id))).scalars().all()
    
    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "comments": [{"id": c.id, "content": c.content, "parent_id": c.parent_id} for c in comments]
    }

@router.post("/posts/{post_id}/comments")
async def create_comment(
    post_id: int,
    comment_in: CommentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    new_comment = Comment(
        post_id=post_id,
        author_id=user.id,
        content=comment_in.content,
        parent_id=comment_in.parent_id
    )
    db.add(new_comment)
    await award_points(db, 1, POINTS_COMMENT, "comment_created", target_id=new_comment.id)
    await db.commit()
    return {"id": new_comment.id}

@router.post("/posts/{post_id}/like")
async def toggle_like(
    post_id: int, 
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    existing = (await db.execute(select(PostLike).where(PostLike.post_id == post_id, PostLike.user_id == user.id))).scalar_one_or_none()
    if existing:
        await db.delete(existing)
        action = "unliked"
    else:
        db.add(PostLike(post_id=post_id, user_id=user.id))
        
        # Award point to author
        post = (await db.execute(select(Post).where(Post.id == post_id))).scalar_one_or_none()
        if post:
            await award_points(db, post.author_id, POINTS_LIKE_RECEIVED, "like_received", target_id=post_id)
            
        action = "liked"
    await db.commit()
    return {"status": action}
