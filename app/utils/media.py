from fastapi import UploadFile, HTTPException
import filetype
from pathlib import Path

MEDIA_CONFIG = {
    "proof_image": {
        "max_bytes": 5 * 1024 * 1024,
        "allowed_extensions": [".jpg", ".jpeg", ".png"],
        "allowed_mimes": ["image/jpeg", "image/png"]
    }
}

async def validate_upload(file: UploadFile, config_type: str = "proof_image"):
    config = MEDIA_CONFIG.get(config_type)
    if not config:
        raise ValueError("Invalid config type")
        
    # 1. 확장자 검증
    ext = Path(file.filename).suffix.lower()
    if ext not in config["allowed_extensions"]:
        raise HTTPException(status_code=400, detail="허용되지 않는 확장자입니다.")
        
    # 2. MIME 타입 검증
    header = await file.read(2048)
    kind = filetype.guess(header)
    mime = kind.mime if kind else "application/octet-stream"
    if mime not in config["allowed_mimes"]:
        raise HTTPException(status_code=400, detail="허용되지 않는 파일 형식입니다.")
    await file.seek(0)
    
    # 3. 크기 검증
    content = await file.read()
    if len(content) > config["max_bytes"]:
        raise HTTPException(status_code=400, detail="파일 크기를 초과했습니다.")
    await file.seek(0)
    
    return content

async def upload_proof_image(file: UploadFile) -> str:
    # MOCK: 실제 환경에서는 Cloudinary 업로드 후 URL 반환
    await validate_upload(file, "proof_image")
    return f"https://mock.cloudinary.com/proofs/{file.filename}"
