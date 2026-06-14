from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import streamlit as st
from PIL import Image

from database import (
    confirm_screenshot,
    delete_screenshot,
    get_dashboard_summary,
    get_pending_screenshots,
    get_study_records,
    init_db,
    soft_delete_study_record,
    update_screenshot_manual_fields,
    update_screenshot_record,
    update_study_record,
)
from screenshot_ai_parser import parse_screenshot
from screenshot_manager import is_allowed_image, save_uploaded_screenshot


APP_TITLE = "法考每日督学"
APP_ICON_PATH = Path(__file__).resolve().parent / "static" / "apple-touch-icon.png"
SCREENSHOT_TYPES = ["做题记录", "听课历史", "错题记录", "首页统计", "其他"]
COMPLETION_STATUSES = ["待补充", "未完成", "部分完成", "已完成"]


def inject_pwa_tags() -> None:
    st.markdown(
        """
        <link rel="manifest" href="/app/static/manifest.json">
        <link rel="apple-touch-icon" href="/app/static/apple-touch-icon.png">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-title" content="法考督学">
        <meta name="apple-mobile-web-app-status-bar-style" content="default">
        <meta name="theme-color" content="#1677ff">
        """,
        unsafe_allow_html=True,
    )


def apply_mobile_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
            max-width: 1180px;
        }
        div[data-testid="stImage"] img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
        }
        div[data-testid="stExpander"] {
            border-radius: 8px;
        }
        div[data-testid="stMetric"] {
            background: #fafafa;
            border: 1px solid #eeeeee;
            border-radius: 8px;
            padding: 0.75rem;
        }
        .stDataFrame, div[data-testid="stTable"] {
            overflow-x: auto;
        }
        @media (max-width: 760px) {
            .block-container {
                padding-left: 0.85rem;
                padding-right: 0.85rem;
                padding-top: 0.75rem;
            }
            h1 {
                font-size: 1.55rem !important;
                line-height: 1.25 !important;
            }
            h2 {
                font-size: 1.25rem !important;
            }
            h3 {
                font-size: 1.05rem !important;
            }
            div[data-testid="column"] {
                width: 100% !important;
                flex: 1 1 100% !important;
                margin-bottom: 0.35rem;
            }
            div.stButton > button,
            div[data-testid="stFormSubmitButton"] > button {
                width: 100%;
                min-height: 2.75rem;
                white-space: normal;
            }
            textarea {
                min-height: 6rem !important;
            }
            label, p, li {
                font-size: 0.98rem !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def parse_date_value(value: str | None) -> date:
    if not value:
        return date.today()
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return date.today()


def row_value(record, key: str, default=""):
    return record[key] if key in record.keys() and record[key] is not None else default


def page_upload() -> None:
    st.header("截图上传")
    st.caption("截图是唯一入口。系统只保存和整理你上传的法考 App 学习截图。")

    screenshot_type = st.selectbox("截图类型", SCREENSHOT_TYPES)
    uploaded_files = st.file_uploader(
        "选择 PNG / JPG / JPEG / WEBP 截图",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
    )

    if not uploaded_files:
        st.info("请选择 1 张或多张截图。手机端可以直接从相册选择截图。")
        return

    st.write(f"已选择 {len(uploaded_files)} 张截图")
    if st.button("保存截图", type="primary"):
        saved_count = 0
        for uploaded_file in uploaded_files:
            if not is_allowed_image(uploaded_file.name):
                st.error(f"{uploaded_file.name} 不是支持的图片格式。")
                continue
            result = save_uploaded_screenshot(
                uploaded_file,
                uploaded_file.name,
                screenshot_type,
            )
            parse_result = parse_screenshot(result["file_path"])
            update_screenshot_record(
                result["id"],
                recognition_status="parsed",
                ai_result=parse_result.get("message", ""),
                notes=parse_result.get("fields", {}).get("notes", ""),
            )
            saved_count += 1
            st.success(f"已保存：{Path(result['file_path']).name}")
        if saved_count:
            st.info("截图已进入待确认列表，请人工核对并修正截图内容。")


def save_manual_fields(record_id: int, form_prefix: str) -> None:
    update_screenshot_manual_fields(
        record_id,
        recognized_date=st.session_state[f"{form_prefix}_date"].isoformat(),
        subject=st.session_state[f"{form_prefix}_subject"].strip(),
        study_content=st.session_state[f"{form_prefix}_content"].strip(),
        study_minutes=int(st.session_state[f"{form_prefix}_minutes"]),
        completion_status=st.session_state[f"{form_prefix}_completion"],
        notes=st.session_state[f"{form_prefix}_notes"].strip(),
    )


def render_pending_record(record) -> None:
    record_id = int(record["id"])
    title = (
        f"#{record_id} {row_value(record, 'screenshot_type')} | "
        f"{row_value(record, 'recognition_status')} | {row_value(record, 'upload_time')}"
    )
    with st.expander(title, expanded=False):
        file_path = Path(row_value(record, "file_path"))
        left, right = st.columns([1, 1])
        with left:
            if file_path.exists():
                st.image(str(file_path), caption=str(file_path), use_container_width=True)
            else:
                st.warning(f"截图文件不存在：{file_path}")
        with right:
            ai_text = row_value(record, "ai_result") or parse_screenshot(str(file_path)).get("message", "")
            st.write("上传时间：", row_value(record, "upload_time"))
            st.write("当前状态：", row_value(record, "recognition_status"))
            st.write("占位解析结果：", ai_text)
            st.write("图片路径：", str(file_path))

        form_prefix = f"screenshot_{record_id}"
        with st.form(f"manual_form_{record_id}"):
            st.date_input(
                "学习日期",
                value=parse_date_value(row_value(record, "recognized_date", "")),
                key=f"{form_prefix}_date",
            )
            st.text_input("科目", value=row_value(record, "subject"), key=f"{form_prefix}_subject")
            st.text_area(
                "学习内容",
                value=row_value(record, "study_content"),
                key=f"{form_prefix}_content",
                height=100,
            )
            st.number_input(
                "学习时长/分钟",
                min_value=0,
                step=5,
                value=int(row_value(record, "study_minutes", 0) or 0),
                key=f"{form_prefix}_minutes",
            )
            completion_value = row_value(record, "completion_status", "待补充")
            completion_index = (
                COMPLETION_STATUSES.index(completion_value)
                if completion_value in COMPLETION_STATUSES
                else 0
            )
            st.selectbox(
                "完成状态",
                COMPLETION_STATUSES,
                index=completion_index,
                key=f"{form_prefix}_completion",
            )
            st.text_area("备注", value=row_value(record, "notes"), key=f"{form_prefix}_notes", height=90)

            save_clicked = st.form_submit_button("保存修改")
            confirm_clicked = st.form_submit_button("确认为有效学习记录")
            delete_clicked = st.form_submit_button("删除该截图记录")

        if save_clicked:
            save_manual_fields(record_id, form_prefix)
            st.success("已保存修改。")
            st.rerun()
        if confirm_clicked:
            save_manual_fields(record_id, form_prefix)
            try:
                study_record_id = confirm_screenshot(record_id)
            except ValueError as exc:
                st.error(str(exc))
            else:
                st.success(f"已确认，并生成/更新正式学习记录 #{study_record_id}。")
                st.rerun()
        if delete_clicked:
            result = delete_screenshot(record_id, delete_file=True)
            if result.get("linked_study_record"):
                st.warning(
                    f"该截图已生成正式学习记录 #{result['linked_study_record']}，"
                    "本次只删除截图记录，不删除正式学习记录。"
                )
            elif result.get("file_error"):
                st.warning(f"记录已标记删除，但图片文件删除失败：{result['file_error']}")
            else:
                st.success("已删除该截图记录。")
            st.rerun()


def page_pending() -> None:
    st.header("待确认截图")
    st.caption("人工只负责核对和修正截图内容，确认后才会生成正式学习记录。")

    records = get_pending_screenshots()
    if not records:
        st.success("当前没有待确认截图。")
        return

    st.write(f"待处理截图：{len(records)} 张")
    for record in records:
        render_pending_record(record)


def render_study_record(record) -> None:
    record_id = int(record["id"])
    title = f"#{record_id} {record['study_date']} | {record['subject'] or '未填写科目'}"
    with st.expander(title, expanded=False):
        form_prefix = f"study_{record_id}"
        with st.form(f"study_form_{record_id}"):
            st.date_input(
                "学习日期",
                value=parse_date_value(row_value(record, "study_date", "")),
                key=f"{form_prefix}_date",
            )
            st.text_input("科目", value=row_value(record, "subject"), key=f"{form_prefix}_subject")
            st.text_area(
                "学习内容",
                value=row_value(record, "content"),
                key=f"{form_prefix}_content",
                height=100,
            )
            st.number_input(
                "学习时长/分钟",
                min_value=1,
                step=5,
                value=max(1, int(row_value(record, "duration_minutes", 1) or 1)),
                key=f"{form_prefix}_duration",
            )
            completion_value = row_value(record, "completion_status", "待补充")
            completion_index = (
                COMPLETION_STATUSES.index(completion_value)
                if completion_value in COMPLETION_STATUSES
                else 0
            )
            st.selectbox(
                "完成状态",
                COMPLETION_STATUSES,
                index=completion_index,
                key=f"{form_prefix}_completion",
            )
            st.text_area("备注", value=row_value(record, "notes"), key=f"{form_prefix}_notes", height=80)
            st.write("来源类型：", row_value(record, "source_type"))
            st.write("来源截图 id：", row_value(record, "source_id"))

            save_clicked = st.form_submit_button("保存正式记录")
            delete_clicked = st.form_submit_button("软删除正式记录")

        if save_clicked:
            try:
                update_study_record(
                    record_id,
                    study_date=st.session_state[f"{form_prefix}_date"].isoformat(),
                    subject=st.session_state[f"{form_prefix}_subject"].strip(),
                    content=st.session_state[f"{form_prefix}_content"].strip(),
                    duration_minutes=int(st.session_state[f"{form_prefix}_duration"]),
                    completion_status=st.session_state[f"{form_prefix}_completion"],
                    notes=st.session_state[f"{form_prefix}_notes"].strip(),
                )
            except ValueError as exc:
                st.error(str(exc))
            else:
                st.success("正式学习记录已保存。")
                st.rerun()
        if delete_clicked:
            soft_delete_study_record(record_id)
            st.success("正式学习记录已软删除。")
            st.rerun()


def page_study_records() -> None:
    st.header("正式学习记录")
    st.caption("这里只能查看、编辑、软删除已由截图确认生成的正式学习记录。")

    records = get_study_records()
    if not records:
        st.info("当前还没有正式学习记录。")
        return

    st.write(f"正式学习记录：{len(records)} 条")
    for record in records:
        render_study_record(record)


def render_mobile_list(title: str, rows: list[dict], key_name: str, value_name: str, empty_text: str) -> None:
    st.subheader(title)
    if not rows:
        st.info(empty_text)
        return
    for row in rows:
        left, right = st.columns([2, 1])
        left.write(str(row[key_name]))
        right.write(f"{row[value_name]} 分钟")


def page_dashboard() -> None:
    st.header("学习概览 Dashboard")
    st.caption("仅统计已确认的截图来源正式学习记录，不统计其他来源，不做图表。")

    summary = get_dashboard_summary()
    c1, c2 = st.columns(2)
    c1.metric("今日学习总时长", f"{summary['today_total_minutes']} 分钟")
    c2.metric("今日学习记录数量", summary["today_record_count"])

    c3, c4 = st.columns(2)
    c3.metric("本周学习总时长", f"{summary['week_total_minutes']} 分钟")
    c4.metric("本周学习记录数量", summary["week_record_count"])

    c5, c6 = st.columns(2)
    c5.metric("累计学习总时长", f"{summary['all_total_minutes']} 分钟")
    c6.metric("累计学习记录数量", summary["all_record_count"])

    render_mobile_list(
        "最近 7 天每日学习时长",
        summary["last_7_days"],
        "study_date",
        "total_minutes",
        "暂无最近 7 天学习记录。",
    )
    render_mobile_list(
        "各科目累计学习时长",
        summary["subject_totals"],
        "subject",
        "total_minutes",
        "暂无科目学习记录。",
    )


def main() -> None:
    page_icon = Image.open(APP_ICON_PATH) if APP_ICON_PATH.exists() else "📚"
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=page_icon,
        layout="wide",
        initial_sidebar_state="auto",
    )
    inject_pwa_tags()
    apply_mobile_styles()
    init_db()
    st.title(APP_TITLE)
    st.caption("截图是唯一入口；系统不做题库、不生成题目、不判断答案。")

    with st.sidebar:
        page = st.radio("页面", ["截图上传", "待确认截图", "正式学习记录", "学习概览 Dashboard"])

    if page == "截图上传":
        page_upload()
    elif page == "待确认截图":
        page_pending()
    elif page == "正式学习记录":
        page_study_records()
    else:
        page_dashboard()


if __name__ == "__main__":
    main()
