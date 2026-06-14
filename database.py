from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "fakao_supervisor.db"


SCREENSHOT_COLUMNS: dict[str, str] = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "file_path": "TEXT NOT NULL",
    "upload_time": "TEXT NOT NULL",
    "screenshot_type": "TEXT NOT NULL",
    "recognition_status": "TEXT NOT NULL DEFAULT 'uploaded'",
    "recognized_date": "TEXT",
    "subject": "TEXT",
    "study_minutes": "INTEGER",
    "reading_pages": "INTEGER",
    "questions_done": "INTEGER",
    "correct_count": "INTEGER",
    "wrong_count": "INTEGER",
    "accuracy": "REAL",
    "wrong_review_count": "INTEGER",
    "study_content": "TEXT",
    "completion_status": "TEXT",
    "ai_result": "TEXT",
    "notes": "TEXT",
    "confirmed_at": "TEXT",
    "deleted_at": "TEXT",
}

SCREENSHOT_ADD_COLUMN_SQL: dict[str, str] = {
    key: value.replace(" NOT NULL", "").replace(" PRIMARY KEY AUTOINCREMENT", "")
    for key, value in SCREENSHOT_COLUMNS.items()
    if key != "id"
}

STUDY_RECORD_COLUMNS: dict[str, str] = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "source_type": "TEXT NOT NULL",
    "source_id": "INTEGER",
    "study_date": "TEXT NOT NULL",
    "subject": "TEXT",
    "content": "TEXT",
    "duration_minutes": "INTEGER NOT NULL",
    "completion_status": "TEXT",
    "notes": "TEXT",
    "created_at": "TEXT NOT NULL",
    "updated_at": "TEXT NOT NULL",
    "is_deleted": "INTEGER NOT NULL DEFAULT 0",
}

STUDY_RECORD_ADD_COLUMN_SQL: dict[str, str] = {
    key: value.replace(" NOT NULL", "").replace(" PRIMARY KEY AUTOINCREMENT", "")
    for key, value in STUDY_RECORD_COLUMNS.items()
    if key != "id"
}

PENDING_SCREENSHOT_STATUSES = (
    "uploaded",
    "parsed",
    "待识别",
    "待确认",
    "识别失败",
)


def ensure_data_dir() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    ensure_data_dir()
    path = Path(db_path) if db_path else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str | Path | None = None) -> None:
    with get_connection(db_path) as conn:
        ensure_screenshots_table(conn)
        ensure_study_records_table(conn)


def _ensure_table_columns(
    conn: sqlite3.Connection,
    table_name: str,
    columns: dict[str, str],
    add_column_sql: dict[str, str],
    unique_sql: str = "",
) -> None:
    column_sql = ",\n            ".join(
        f"{name} {definition}" for name, definition in columns.items()
    )
    suffix = f",\n            {unique_sql}" if unique_sql else ""
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {column_sql}{suffix}
        )
        """
    )
    existing = {
        row["name"]
        for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    if "id" not in existing:
        legacy_name = f"{table_name}_legacy_{datetime.now():%Y%m%d_%H%M%S}"
        conn.execute(f"ALTER TABLE {table_name} RENAME TO {legacy_name}")
        conn.execute(
            f"""
            CREATE TABLE {table_name} (
                {column_sql}{suffix}
            )
            """
        )
        copy_columns = [name for name in columns if name != "id" and name in existing]
        if copy_columns:
            conn.execute(
                f"""
                INSERT INTO {table_name} ({', '.join(copy_columns)})
                SELECT {', '.join(copy_columns)} FROM {legacy_name}
                """
            )
        conn.commit()
        existing = {
            row["name"]
            for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        }

    for name in columns:
        if name != "id" and name not in existing:
            conn.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {name} {add_column_sql[name]}"
            )
    conn.commit()


def ensure_screenshots_table(conn: sqlite3.Connection) -> None:
    _ensure_table_columns(
        conn,
        "screenshots",
        SCREENSHOT_COLUMNS,
        SCREENSHOT_ADD_COLUMN_SQL,
    )


def ensure_study_records_table(conn: sqlite3.Connection) -> None:
    _ensure_table_columns(
        conn,
        "study_records",
        STUDY_RECORD_COLUMNS,
        STUDY_RECORD_ADD_COLUMN_SQL,
        unique_sql="UNIQUE(source_type, source_id)",
    )


def insert_screenshot_record(
    file_path: str,
    screenshot_type: str,
    upload_time: str,
    recognition_status: str = "uploaded",
    db_path: str | Path | None = None,
    **fields: Any,
) -> int:
    payload = {
        "file_path": file_path,
        "upload_time": upload_time,
        "screenshot_type": screenshot_type,
        "recognition_status": recognition_status,
        **fields,
    }
    valid_payload = {
        key: value
        for key, value in payload.items()
        if key in SCREENSHOT_COLUMNS and key != "id"
    }
    columns = list(valid_payload)
    placeholders = ", ".join("?" for _ in columns)
    with get_connection(db_path) as conn:
        ensure_screenshots_table(conn)
        cursor = conn.execute(
            f"INSERT INTO screenshots ({', '.join(columns)}) VALUES ({placeholders})",
            [valid_payload[column] for column in columns],
        )
        conn.commit()
        return int(cursor.lastrowid)


def get_screenshot_record(
    screenshot_id: int,
    db_path: str | Path | None = None,
) -> sqlite3.Row | None:
    with get_connection(db_path) as conn:
        ensure_screenshots_table(conn)
        return conn.execute(
            "SELECT * FROM screenshots WHERE id = ?",
            (screenshot_id,),
        ).fetchone()


def get_screenshot_by_id(
    screenshot_id: int,
    db_path: str | Path | None = None,
) -> sqlite3.Row | None:
    return get_screenshot_record(screenshot_id, db_path=db_path)


def list_screenshot_records(
    statuses: list[str] | tuple[str, ...] | None = None,
    db_path: str | Path | None = None,
) -> list[sqlite3.Row]:
    with get_connection(db_path) as conn:
        ensure_screenshots_table(conn)
        if statuses:
            placeholders = ", ".join("?" for _ in statuses)
            return conn.execute(
                f"""
                SELECT * FROM screenshots
                WHERE recognition_status IN ({placeholders})
                ORDER BY upload_time DESC, id DESC
                """,
                list(statuses),
            ).fetchall()
        return conn.execute(
            "SELECT * FROM screenshots ORDER BY upload_time DESC, id DESC"
        ).fetchall()


def get_pending_screenshots(
    db_path: str | Path | None = None,
) -> list[sqlite3.Row]:
    return list_screenshot_records(PENDING_SCREENSHOT_STATUSES, db_path=db_path)


def update_screenshot_record(
    screenshot_id: int,
    db_path: str | Path | None = None,
    **fields: Any,
) -> None:
    valid_fields = {
        key: value
        for key, value in fields.items()
        if key in SCREENSHOT_COLUMNS and key != "id"
    }
    if not valid_fields:
        return
    assignments = ", ".join(f"{key} = ?" for key in valid_fields)
    values = list(valid_fields.values()) + [screenshot_id]
    with get_connection(db_path) as conn:
        ensure_screenshots_table(conn)
        conn.execute(f"UPDATE screenshots SET {assignments} WHERE id = ?", values)
        conn.commit()


def update_screenshot_manual_fields(
    screenshot_id: int,
    recognized_date: str | None = None,
    subject: str | None = None,
    study_content: str | None = None,
    study_minutes: int | None = None,
    completion_status: str | None = None,
    notes: str | None = None,
    db_path: str | Path | None = None,
) -> None:
    update_screenshot_record(
        screenshot_id,
        db_path=db_path,
        recognized_date=recognized_date,
        subject=subject,
        study_content=study_content,
        study_minutes=study_minutes,
        completion_status=completion_status,
        notes=notes,
        recognition_status="parsed",
    )


def delete_screenshot_record(
    screenshot_id: int,
    db_path: str | Path | None = None,
) -> None:
    with get_connection(db_path) as conn:
        ensure_screenshots_table(conn)
        conn.execute("DELETE FROM screenshots WHERE id = ?", (screenshot_id,))
        conn.commit()


def _valid_study_date(value: str | None) -> str:
    if not value:
        return date.today().isoformat()
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("学习日期格式必须为 YYYY-MM-DD。") from exc
    return value


def _valid_duration(value: Any) -> int:
    try:
        duration = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("学习时长必须是正整数分钟。") from exc
    if duration <= 0:
        raise ValueError("学习时长必须大于 0 分钟。")
    return duration


def get_study_record_by_source(
    source_type: str,
    source_id: int,
    include_deleted: bool = False,
    db_path: str | Path | None = None,
) -> sqlite3.Row | None:
    with get_connection(db_path) as conn:
        ensure_study_records_table(conn)
        query = "SELECT * FROM study_records WHERE source_type = ? AND source_id = ?"
        params: list[Any] = [source_type, source_id]
        if not include_deleted:
            query += " AND is_deleted = 0"
        return conn.execute(query, params).fetchone()


def create_or_update_study_record_from_screenshot(
    screenshot_id: int,
    db_path: str | Path | None = None,
) -> int:
    screenshot = get_screenshot_by_id(screenshot_id, db_path=db_path)
    if screenshot is None:
        raise ValueError("截图记录不存在。")

    duration = _valid_duration(screenshot["study_minutes"])
    study_date = _valid_study_date(screenshot["recognized_date"])
    now = datetime.now().isoformat(timespec="seconds")
    payload = {
        "source_type": "screenshot",
        "source_id": screenshot_id,
        "study_date": study_date,
        "subject": screenshot["subject"] or "",
        "content": screenshot["study_content"] or "",
        "duration_minutes": duration,
        "completion_status": screenshot["completion_status"] or "待补充",
        "notes": screenshot["notes"] or "",
        "updated_at": now,
        "is_deleted": 0,
    }
    existing = get_study_record_by_source(
        "screenshot",
        screenshot_id,
        include_deleted=True,
        db_path=db_path,
    )
    with get_connection(db_path) as conn:
        ensure_study_records_table(conn)
        if existing:
            conn.execute(
                """
                UPDATE study_records
                SET study_date = ?, subject = ?, content = ?, duration_minutes = ?,
                    completion_status = ?, notes = ?, updated_at = ?, is_deleted = 0
                WHERE id = ?
                """,
                (
                    payload["study_date"],
                    payload["subject"],
                    payload["content"],
                    payload["duration_minutes"],
                    payload["completion_status"],
                    payload["notes"],
                    payload["updated_at"],
                    existing["id"],
                ),
            )
            record_id = int(existing["id"])
        else:
            payload["created_at"] = now
            columns = list(payload)
            placeholders = ", ".join("?" for _ in columns)
            cursor = conn.execute(
                f"""
                INSERT INTO study_records ({', '.join(columns)})
                VALUES ({placeholders})
                """,
                [payload[column] for column in columns],
            )
            record_id = int(cursor.lastrowid)
        conn.commit()

    update_screenshot_record(
        screenshot_id,
        db_path=db_path,
        recognition_status="confirmed",
        confirmed_at=now,
    )
    return record_id


def confirm_screenshot(
    screenshot_id: int,
    db_path: str | Path | None = None,
) -> int:
    return create_or_update_study_record_from_screenshot(
        screenshot_id,
        db_path=db_path,
    )


def get_study_records(
    include_deleted: bool = False,
    source_type: str = "screenshot",
    db_path: str | Path | None = None,
) -> list[sqlite3.Row]:
    with get_connection(db_path) as conn:
        ensure_study_records_table(conn)
        query = "SELECT * FROM study_records WHERE source_type = ?"
        params: list[Any] = [source_type]
        if not include_deleted:
            query += " AND is_deleted = 0"
        query += " ORDER BY study_date DESC, id DESC"
        return conn.execute(query, params).fetchall()


def get_dashboard_summary(
    today: date | None = None,
    db_path: str | Path | None = None,
) -> dict[str, Any]:
    current_day = today or date.today()
    week_start = current_day - timedelta(days=current_day.weekday())
    last_7_days = [current_day - timedelta(days=offset) for offset in range(6, -1, -1)]
    base_where = "source_type = 'screenshot' AND is_deleted = 0"

    with get_connection(db_path) as conn:
        ensure_study_records_table(conn)
        today_row = conn.execute(
            f"""
            SELECT COUNT(*) AS record_count, COALESCE(SUM(duration_minutes), 0) AS total_minutes
            FROM study_records
            WHERE {base_where} AND study_date = ?
            """,
            (current_day.isoformat(),),
        ).fetchone()
        week_row = conn.execute(
            f"""
            SELECT COUNT(*) AS record_count, COALESCE(SUM(duration_minutes), 0) AS total_minutes
            FROM study_records
            WHERE {base_where} AND study_date >= ? AND study_date <= ?
            """,
            (week_start.isoformat(), current_day.isoformat()),
        ).fetchone()
        total_row = conn.execute(
            f"""
            SELECT COUNT(*) AS record_count, COALESCE(SUM(duration_minutes), 0) AS total_minutes
            FROM study_records
            WHERE {base_where}
            """
        ).fetchone()
        daily_rows = conn.execute(
            f"""
            SELECT study_date, COALESCE(SUM(duration_minutes), 0) AS total_minutes
            FROM study_records
            WHERE {base_where} AND study_date >= ? AND study_date <= ?
            GROUP BY study_date
            """,
            (last_7_days[0].isoformat(), current_day.isoformat()),
        ).fetchall()
        subject_rows = conn.execute(
            f"""
            SELECT COALESCE(NULLIF(subject, ''), '未填写科目') AS subject,
                   COALESCE(SUM(duration_minutes), 0) AS total_minutes
            FROM study_records
            WHERE {base_where}
            GROUP BY COALESCE(NULLIF(subject, ''), '未填写科目')
            ORDER BY total_minutes DESC, subject ASC
            """
        ).fetchall()

    daily_map = {row["study_date"]: int(row["total_minutes"] or 0) for row in daily_rows}
    return {
        "today_total_minutes": int(today_row["total_minutes"] or 0),
        "today_record_count": int(today_row["record_count"] or 0),
        "week_total_minutes": int(week_row["total_minutes"] or 0),
        "week_record_count": int(week_row["record_count"] or 0),
        "all_total_minutes": int(total_row["total_minutes"] or 0),
        "all_record_count": int(total_row["record_count"] or 0),
        "last_7_days": [
            {"study_date": day.isoformat(), "total_minutes": daily_map.get(day.isoformat(), 0)}
            for day in last_7_days
        ],
        "subject_totals": [
            {"subject": row["subject"], "total_minutes": int(row["total_minutes"] or 0)}
            for row in subject_rows
        ],
    }


def update_study_record(
    record_id: int,
    db_path: str | Path | None = None,
    **fields: Any,
) -> None:
    allowed = {
        "study_date",
        "subject",
        "content",
        "duration_minutes",
        "completion_status",
        "notes",
    }
    valid_fields = {key: value for key, value in fields.items() if key in allowed}
    if "study_date" in valid_fields:
        valid_fields["study_date"] = _valid_study_date(valid_fields["study_date"])
    if "duration_minutes" in valid_fields:
        valid_fields["duration_minutes"] = _valid_duration(
            valid_fields["duration_minutes"]
        )
    valid_fields["updated_at"] = datetime.now().isoformat(timespec="seconds")
    assignments = ", ".join(f"{key} = ?" for key in valid_fields)
    values = list(valid_fields.values()) + [record_id]
    with get_connection(db_path) as conn:
        ensure_study_records_table(conn)
        conn.execute(f"UPDATE study_records SET {assignments} WHERE id = ?", values)
        conn.commit()


def soft_delete_study_record(
    record_id: int,
    db_path: str | Path | None = None,
) -> None:
    with get_connection(db_path) as conn:
        ensure_study_records_table(conn)
        conn.execute(
            """
            UPDATE study_records
            SET is_deleted = 1, updated_at = ?
            WHERE id = ?
            """,
            (datetime.now().isoformat(timespec="seconds"), record_id),
        )
        conn.commit()


def delete_screenshot(
    screenshot_id: int,
    delete_file: bool = True,
    db_path: str | Path | None = None,
) -> dict[str, Any]:
    record = get_screenshot_record(screenshot_id, db_path=db_path)
    result: dict[str, Any] = {
        "deleted_record": False,
        "deleted_file": False,
        "file_error": "",
        "linked_study_record": None,
    }
    if record is None:
        return result

    linked = get_study_record_by_source(
        "screenshot",
        screenshot_id,
        include_deleted=False,
        db_path=db_path,
    )
    if linked:
        result["linked_study_record"] = int(linked["id"])

    file_path = Path(record["file_path"]) if record["file_path"] else None
    update_screenshot_record(
        screenshot_id,
        db_path=db_path,
        recognition_status="deleted",
        deleted_at=datetime.now().isoformat(timespec="seconds"),
    )
    result["deleted_record"] = True

    if delete_file and file_path and file_path.exists():
        try:
            file_path.unlink()
            result["deleted_file"] = True
        except OSError as exc:
            result["file_error"] = str(exc)
    return result


def cleanup_test_screenshots(
    marker: str,
    db_path: str | Path | None = None,
) -> dict[str, Any]:
    cleaned_ids: list[int] = []
    file_errors: list[str] = []
    with get_connection(db_path) as conn:
        ensure_screenshots_table(conn)
        rows = conn.execute(
            "SELECT id FROM screenshots WHERE notes = ? OR ai_result = ?",
            (marker, marker),
        ).fetchall()
    for row in rows:
        linked = get_study_record_by_source(
            "screenshot",
            int(row["id"]),
            include_deleted=True,
            db_path=db_path,
        )
        if linked:
            soft_delete_study_record(int(linked["id"]), db_path=db_path)
        result = delete_screenshot(int(row["id"]), delete_file=True, db_path=db_path)
        delete_screenshot_record(int(row["id"]), db_path=db_path)
        cleaned_ids.append(int(row["id"]))
        if result.get("file_error"):
            file_errors.append(str(result["file_error"]))
    return {
        "cleaned_ids": cleaned_ids,
        "file_errors": file_errors,
    }


def cleanup_test_study_records(
    marker: str,
    db_path: str | Path | None = None,
) -> list[int]:
    cleaned_ids: list[int] = []
    with get_connection(db_path) as conn:
        ensure_study_records_table(conn)
        rows = conn.execute(
            "SELECT id FROM study_records WHERE notes = ?",
            (marker,),
        ).fetchall()
        for row in rows:
            conn.execute("DELETE FROM study_records WHERE id = ?", (int(row["id"]),))
            cleaned_ids.append(int(row["id"]))
        conn.commit()
    return cleaned_ids
