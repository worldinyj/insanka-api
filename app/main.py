from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI(title="Insanka API", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    from app.database import AsyncSessionLocal
    from app.models.user import User
    from app.utils.security import get_password_hash
    from sqlalchemy import select
    from datetime import datetime, timezone
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == "nsc.imp.atom@gmail.com"))
        admin_user = result.scalar_one_or_none()
        
        if not admin_user:
            hashed_pw = get_password_hash("admin12345!")
            new_admin = User(
                email="nsc.imp.atom@gmail.com",
                username="총괄관리자",
                hashed_pw=hashed_pw,
                role="admin",
                status="approved",
                level=5,
                total_points=99999,
                approved_at=datetime.now(timezone.utc)
            )
            session.add(new_admin)
            await session.commit()


# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import auth, invitations, admin, pages, posts, votes, users
app.include_router(auth.router, prefix="/api/v1")
app.include_router(invitations.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(posts.router, prefix="/api/v1")
app.include_router(votes.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(pages.router)

from fastapi.responses import RedirectResponse

@app.get("/")
async def root():
    # 접속 시 JSON이 아닌 실제 웹 화면(로그인 페이지)으로 리다이렉트
    return RedirectResponse(url="/login")
