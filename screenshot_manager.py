from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

from database import ROOT, init_db, insert_screenshot_record


SCREENSHOT_DIR = ROOT / "uploads" / "screenshots"
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
DEFAULT_STATUS = "uploaded"


def ensure_screenshot_dir() -> Path:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    return SCREENSHOT_DIR


def is_allowed_image(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def build_screenshot_filename(original_name: str, now: datetime | None = None) -> str:
    suffix = Path(original_name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("Only PNG, JPG, JPEG, and WEBP screenshots are supported.")
    timestamp = (now or datetime.now()).strftime("%Y%m%d_%H%M%S")
    return f"screenshot_{timestamp}_{uuid4().hex[:8]}{suffix}"


def save_uploaded_screenshot(
    file_obj: BinaryIO,
    original_name: str,
    screenshot_type: str,
    db_path: str | Path | None = None,
) -> dict:
    init_db(db_path)
    upload_dir = ensure_screenshot_dir()
    filename = build_screenshot_filename(original_name)
    target_path = upload_dir / filename
    content = file_obj.read()
    if not content:
        raise ValueError("Uploaded screenshot is empty.")
    target_path.write_bytes(content)
    upload_time = datetime.now().isoformat(timespec="seconds")
    screenshot_id = insert_screenshot_record(
        file_path=str(target_path),
        upload_time=upload_time,
        screenshot_type=screenshot_type,
        recognition_status=DEFAULT_STATUS,
        db_path=db_path,
    )
    return {
        "id": screenshot_id,
        "file_path": str(target_path),
        "upload_time": upload_time,
        "screenshot_type": screenshot_type,
        "recognition_status": DEFAULT_STATUS,
    }


def save_screenshot_record(
    file_path: str,
    screenshot_type: str,
    db_path: str | Path | None = None,
) -> int:
    init_db(db_path)
    ensure_screenshot_dir()
    return insert_screenshot_record(
        file_path=file_path,
        upload_time=datetime.now().isoformat(timespec="seconds"),
        screenshot_type=screenshot_type,
        recognition_status=DEFAULT_STATUS,
        db_path=db_path,
    )
