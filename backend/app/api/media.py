from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from .deps import get_db
from .. import schemas
from ..models import (
    Game, User, Task, Assignment, Media, FreeMedia, AssignmentStatus, MediaType,
)
from ..config import settings
from ..services import views
from ..services.storage import upload_file_to_r2

router = APIRouter()


@router.post("/u/{user_id}/assignments/{assignment_id}/upload",
             response_model=schemas.PresignOut)
async def upload_proxy(user_id: str, assignment_id: int,
                       file: UploadFile = File(...),
                       db: Session = Depends(get_db)):
    a = db.get(Assignment, assignment_id)
    if not a or a.user_id != user_id:
        raise HTTPException(404, "Assignment not found")
    data, content_type = await _read_media(file)
    public_url = upload_file_to_r2(file.filename or "upload", content_type, data)
    return schemas.PresignOut(upload_url="", public_url=public_url)


@router.post("/u/{user_id}/assignments/{assignment_id}/complete",
             response_model=schemas.AssignmentOut)
def complete_task(user_id: str, assignment_id: int,
                  payload: schemas.CompleteTaskIn, db: Session = Depends(get_db)):
    a = db.get(Assignment, assignment_id)
    if not a or a.user_id != user_id:
        raise HTTPException(404, "Assignment not found")
    if not payload.files:
        raise HTTPException(400, "Upload at least one photo or video")

    db.query(Media).filter(Media.assignment_id == assignment_id).delete()
    for f in payload.files:
        db.add(Media(assignment_id=assignment_id, file_url=f.public_url,
                     media_type=f.media_type))

    now = datetime.utcnow()
    # replacing proof of an already-completed task must not move the finish time
    if a.status != AssignmentStatus.completed:
        a.status = AssignmentStatus.completed
        a.completed_at = now
    db.flush()

    _recalc_user_completion(db, user_id, now)

    if a.pair_id:
        partner = (
            db.query(Assignment)
            .filter(Assignment.pair_id == a.pair_id, Assignment.id != a.id)
            .first()
        )
        if partner and partner.status != AssignmentStatus.completed:
            partner.status = AssignmentStatus.completed
            partner.completed_at = now
            db.flush()
            _recalc_user_completion(db, partner.user_id, now)

    db.commit()
    db.refresh(a)

    return views.assignment_out(db, db.get(Game, db.get(User, user_id).game_id), a)


async def _read_media(file: UploadFile) -> tuple[bytes, str]:
    """Only photos/videos, capped at MAX_UPLOAD_MB."""
    content_type = file.content_type or "application/octet-stream"
    if not content_type.startswith(("image/", "video/")):
        raise HTTPException(400, "Only photos and videos are allowed")
    limit = settings.MAX_UPLOAD_MB * 1024 * 1024
    data = await file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(413, f"File is too large (max {settings.MAX_UPLOAD_MB} MB)")
    return data, content_type


def _recalc_user_completion(db: Session, user_id: str, now: datetime):
    user = db.get(User, user_id)
    rows = db.query(Assignment).filter(Assignment.user_id == user_id).all()
    if rows and all(r.status == AssignmentStatus.completed for r in rows):
        user.completed_at = max(r.completed_at for r in rows)
    else:
        user.completed_at = None


@router.get("/download")
async def download_proxy(url: str):
    """Proxy download to force Content-Disposition: attachment for cross-origin files."""
    import httpx
    from fastapi.responses import StreamingResponse
    import urllib.parse
    base = settings.R2_PUBLIC_BASE_URL.rstrip("/") + "/"
    if not url.startswith(base):
        raise HTTPException(400, "Only game media can be downloaded")
    path = urllib.parse.urlparse(url).path
    filename = (path.split("/")[-1] or "download").replace('"', "")
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(url, timeout=60)
        except httpx.HTTPError:
            raise HTTPException(502, "Storage is unavailable")
        if r.status_code != 200:
            raise HTTPException(404, "File not found")
        content_type = r.headers.get("content-type", "application/octet-stream")
        return StreamingResponse(
            iter([r.content]),
            media_type=content_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )


@router.post("/u/{user_id}/free-upload", response_model=schemas.PresignOut)
async def free_upload(user_id: str,
                      file: UploadFile = File(...),
                      db: Session = Depends(get_db)):
    """Upload media without a task — appears in slideshow with just player name."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Player not found")
    data, content_type = await _read_media(file)
    public_url = upload_file_to_r2(file.filename or "upload", content_type, data)
    media_type = MediaType.video if (content_type or "").startswith("video") else MediaType.image
    db.add(FreeMedia(user_id=user_id, file_url=public_url, media_type=media_type))
    db.commit()
    return schemas.PresignOut(upload_url="", public_url=public_url)
