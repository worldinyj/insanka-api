import sys
import os

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.room import Room
from app.models.post import Post, Comment, PostLike
from app.models.vote import Vote, VoteOption, VoteCast
from app.models.point_log import PointLog

# Mock magic library since libmagic is not installed on the system
import sys
from unittest.mock import MagicMock
sys.modules['magic'] = MagicMock()

from app.main import app

async def seed_db(session: AsyncSession):
    # 1. Create Admin
    admin = User(username="admin", email="admin@test.com", hashed_pw="admin12345!", role="admin", status="approved")
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    
    # 2. Create Room
    room = Room(name="Main Room", slug="main", description="Test Room")
    session.add(room)
    await session.commit()
    await session.refresh(room)
    
    return admin, room

async def teardown(session: AsyncSession, admin_id: int, room_id: int):
    # Delete everything related
    await session.execute(delete(PointLog).where(PointLog.user_id == admin_id))
    await session.execute(delete(VoteCast).where(VoteCast.user_id == admin_id))
    await session.execute(delete(VoteOption))
    await session.execute(delete(Vote))
    await session.execute(delete(Comment).where(Comment.author_id == admin_id))
    await session.execute(delete(PostLike).where(PostLike.user_id == admin_id))
    await session.execute(delete(Post).where(Post.author_id == admin_id))
    await session.execute(delete(Room).where(Room.id == room_id))
    await session.execute(delete(User).where(User.id == admin_id))
    await session.commit()

async def run_scenario():
    async with AsyncSessionLocal() as session:
        admin, room = await seed_db(session)
        print(f"[Seed] Created Admin User ID: {admin.id}, Room Slug: {room.slug}")

        try:
            # Need asgi_lifespan if we have startup events, but for simple testing this works
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                # Mock token for Depends(oauth2_scheme)
                headers = {"Authorization": "Bearer fake-token"}
                
                # 1. Create Post
                print("\n[Scenario] 1. Creating a Post...")
                response = await client.post(
                    "/api/v1/rooms/main/posts", 
                    json={"title": "Hello World", "content": "This is a test post."},
                    headers=headers
                )
                assert response.status_code == 200, f"Failed to create post: {response.text}"
                post_id = response.json()["id"]
                print(f"✅ Post created with ID: {post_id}")
                
                # 2. Create Comment
                print("\n[Scenario] 2. Creating a Comment...")
                response = await client.post(
                    f"/api/v1/posts/{post_id}/comments",
                    json={"content": "This is a test comment."},
                    headers=headers
                )
                assert response.status_code == 200, f"Failed to create comment: {response.text}"
                print("✅ Comment created.")
                
                # 3. Create Vote
                print("\n[Scenario] 3. Creating a Vote...")
                response = await client.post(
                    "/api/v1/rooms/main/votes",
                    json={
                        "title": "What's the best stock?",
                        "options": [{"text": "TSLA"}, {"text": "AAPL"}],
                        "is_multiple": False
                    },
                    headers=headers
                )
                assert response.status_code == 200, f"Failed to create vote: {response.text}"
                vote_id = response.json()["id"]
                print(f"✅ Vote created with ID: {vote_id}")
                
                # Get vote options
                response = await client.get(f"/api/v1/votes/{vote_id}/results")
                options = response.json()["results"]
                option_id = options[0]["id"]
                
                # 4. Cast Vote
                print("\n[Scenario] 4. Casting a Vote...")
                response = await client.post(
                    f"/api/v1/votes/{vote_id}/cast",
                    json=[option_id],
                    headers=headers
                )
                assert response.status_code == 200, f"Failed to cast vote: {response.text}"
                print("✅ Vote casted.")
                
                # 5. Check Points
                print("\n[Scenario] 5. Checking Points and Ranking...")
                response = await client.get("/api/v1/users/me/points", headers=headers)
                assert response.status_code == 200, f"Failed to get points: {response.text}"
                points_data = response.json()
                print(f"✅ Current Points: {points_data['total_points']}")
                assert points_data['total_points'] > 0, "Points should be greater than 0"
                
                response = await client.get("/api/v1/users/ranking", headers=headers)
                assert response.status_code == 200, f"Failed to get ranking: {response.text}"
                ranking_data = response.json()["ranking"]
                print(f"✅ Top Ranker: {ranking_data[0]['username']} with {ranking_data[0]['total_points']} points")
                
                print("\n🎉 ALL SCENARIOS PASSED SUCCESSFULLY!")
                
        except Exception as e:
            print(f"\n❌ SCENARIO FAILED: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print("\n[Teardown] Cleaning up sample data...")
            await teardown(session, admin.id, room.id)
            print("✅ Teardown complete.")

if __name__ == "__main__":
    asyncio.run(run_scenario())
