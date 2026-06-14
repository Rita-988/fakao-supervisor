# 法考每日督学 Streamlit Cloud 部署说明

本说明用于把当前 Streamlit 版本部署到 Streamlit Community Cloud。第一版目标是手机可用、流程简单、风险可控；不改成 Vercel，不改成 Next.js，不做登录和多用户系统。

## 当前项目状态

- Streamlit 入口文件：`app.py`
- 数据库位置：`data/fakao_supervisor.db`
- 截图上传目录：`uploads/screenshots/`
- 当前保存方式：SQLite + 本地文件目录
- 云端第一版用途：个人轻量测试和手机访问

## 重要数据提醒

Streamlit Community Cloud 的本地文件存储不适合长期永久保存数据。重新部署、重启、代码更新后，本地保存的数据库、上传截图或临时文件可能丢失。

第一版请不要放重要隐私数据。不要把本地历史数据库、历史截图、客户资料、RFQ 资料、邮箱密码、API Key、`.env`、`.streamlit/secrets.toml` 提交到 GitHub。

如果要长期保存法考记录和截图，下一步建议升级到 Supabase 数据库 + 云存储。

## 本地部署前检查

先运行：

```text
check_streamlit_cloud_ready.bat
```

它会检查：

- `app.py`
- `requirements.txt`
- `.streamlit/config.toml`
- Windows 绝对路径
- `localhost / 127.0.0.1` 引用
- `.env / secrets.toml` 风险
- `static/` 图标和 `manifest.json`
- `.gitignore`
- `self_test.py`

## Streamlit Community Cloud 部署步骤

1. 确认本地运行正常。
2. 运行 `check_streamlit_cloud_ready.bat`。
3. 确认没有敏感资料准备提交。
4. 把项目推送到 GitHub。
5. 打开 Streamlit Community Cloud。
6. 连接 GitHub。
7. 选择仓库。
8. Main file path 填：`app.py`。
9. 点击 Deploy。
10. 部署成功后，复制 Streamlit Cloud 给出的公网网址。
11. 用 iPhone Chrome 打开公网网址测试。
12. 测试截图上传。
13. 测试待确认截图。
14. 测试确认后生成正式学习记录。
15. 再用 Safari 打开同一个公网网址测试。

第一次部署只用于测试，不要放重要隐私资料。

## iPhone Chrome 使用方式

1. 打开 iPhone Chrome。
2. 输入 Streamlit Community Cloud 部署后的公网网址。
3. 测试截图上传。
4. 从相册选择截图。
5. 提交截图记录。
6. 到“待确认截图”里填写和确认。
7. 查看“正式学习记录”和“学习概览 Dashboard”。

如果 Chrome 可以正常使用，第一版就先用 Chrome 作为主力入口。

## Safari 正确打开方式

Safari 打开后如果显示 Google 搜索页，通常不是 Safari 坏了，而是网址输入到了搜索框或没有输入完整网址。

正确方式：

1. 打开 Safari。
2. 点击 Safari 顶部或底部地址栏。
3. 删除原来的内容。
4. 输入完整的 Streamlit Cloud 公网网址，例如：`https://xxxx.streamlit.app`。
5. 点击“前往”。
6. 部署到 Streamlit Cloud 后，不需要输入 `:8501`。

如果是本地测试，才需要类似：

```text
http://192.168.100.101:8501/
```

本地地址必须有 `http://` 和 `:8501`，否则 Safari 可能当成搜索或访问错误端口。

## 手机添加到主屏幕

1. 用 iPhone Safari 打开 Streamlit Cloud 的公网网址。
2. 不要在 Google 搜索框里搜索，要在 Safari 地址栏输入完整网址。
3. 页面打开后，点击底部分享按钮。
4. 选择“添加到主屏幕”。
5. 名称填写：法考每日督学。
6. 点击添加。
7. 以后手机桌面上会出现图标，一键打开。

必须用 Safari 添加到主屏幕。微信内置浏览器或部分第三方浏览器可能没有这个选项。

Safari 添加主屏幕是可选项，不作为第一版上线阻塞项。如果 Safari 暂时不好用，先用 Chrome 使用工具。

## PWA / 图标限制

本项目已增加轻量图标文件：

- `static/icon-192.png`
- `static/icon-512.png`
- `static/apple-touch-icon.png`
- `static/manifest.json`

Streamlit 对 PWA 的支持不如 Next.js 完整。这里的目标不是做真正原生 App，而是尽量让 iPhone 添加到主屏幕后显示更好的名称和图标。

如果图标没有立即更新，可以删除旧主屏幕图标后重新添加一次。

## 本地版和云端版

本地版仍然可以使用：

```text
start_streamlit_lan.bat
```

云端部署主要依赖：

- `app.py`
- `requirements.txt`
- `.streamlit/config.toml`
- `database.py`
- `screenshot_manager.py`
- `screenshot_ai_parser.py`
- `report_engine.py`
- `reminder_engine.py`
- `static/`

不要提交本地正式数据库和历史截图。

## 后续长期保存方案

如果要长期保存学习记录和截图，建议下一步升级：

- Supabase Postgres 保存学习记录
- Supabase Storage 保存截图
- Streamlit secrets 保存 Supabase URL 和 Key
- 保留截图确认后生成正式记录的原则

第一版先不做登录、多用户、复杂权限。
