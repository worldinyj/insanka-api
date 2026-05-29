import logging

logger = logging.getLogger(__name__)

async def send_invitation_email(email: str, inviter_username: str, token: str):
    # Mocking SMTP
    # invite_url = f"{settings.FRONTEND_URL}/invite/{token}"
    invite_url = f"http://localhost:8000/invite/{token}"
    logger.info(f"MOCK EMAIL SENT to {email}: {inviter_username}님이 초대했습니다. 링크: {invite_url}")

async def send_approval_email(email: str):
    logger.info(f"MOCK EMAIL SENT to {email}: 가입이 승인되었습니다.")

async def send_rejection_email(email: str, reason: str):
    logger.info(f"MOCK EMAIL SENT to {email}: 가입이 거절되었습니다. 사유: {reason}")
