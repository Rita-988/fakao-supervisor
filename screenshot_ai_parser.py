from __future__ import annotations


EMPTY_RECOGNITION_FIELDS = {
    "recognized_date": None,
    "subject": "",
    "study_minutes": None,
    "reading_pages": None,
    "questions_done": None,
    "correct_count": None,
    "wrong_count": None,
    "accuracy": None,
    "wrong_review_count": None,
    "notes": "V1暂未启用AI识别，请人工确认填写。",
}


def parse_screenshot(image_path: str) -> dict:
    return {
        "image_path": image_path,
        "message": "V1暂未启用AI识别，请人工确认填写。",
        "fields": EMPTY_RECOGNITION_FIELDS.copy(),
    }
