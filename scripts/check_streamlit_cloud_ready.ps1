$Host.UI.RawUI.WindowTitle = "Streamlit Cloud 部署检查"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot

function Write-Check($ok, $message) {
    if ($ok) {
        Write-Host "[OK] $message"
    } else {
        Write-Host "[注意] $message"
    }
}

function Test-GitIgnoreContains($pattern) {
    if (-not (Test-Path -LiteralPath ".gitignore")) {
        return $false
    }
    $content = Get-Content -Raw -Encoding UTF8 -LiteralPath ".gitignore"
    return $content -match [regex]::Escape($pattern)
}

Write-Host ""
Write-Host "===== Streamlit Community Cloud 部署检查 ====="
Write-Host "项目目录：$ProjectRoot"
Write-Host ""

Write-Check (Test-Path -LiteralPath "app.py") "app.py 存在"
Write-Check (Test-Path -LiteralPath "requirements.txt") "requirements.txt 存在"
Write-Check (Test-Path -LiteralPath ".streamlit/config.toml") ".streamlit/config.toml 存在"
Write-Check (Test-Path -LiteralPath "README_DEPLOY.md") "README_DEPLOY.md 存在"

Write-Host ""
Write-Host "【部署文件范围】"
$deployPaths = @(
    "app.py",
    "database.py",
    "screenshot_manager.py",
    "screenshot_ai_parser.py",
    "report_engine.py",
    "reminder_engine.py",
    "self_test.py",
    "requirements.txt",
    "README.md",
    "README_DEPLOY.md",
    ".gitignore",
    ".streamlit/config.toml",
    "static/manifest.json"
)
$deployFiles = foreach ($path in $deployPaths) {
    if (Test-Path -LiteralPath $path) {
        Get-Item -LiteralPath $path
    }
}
$staticFiles = Get-ChildItem -LiteralPath "static" -File -ErrorAction SilentlyContinue
$searchFiles = @($deployFiles + $staticFiles) | Select-Object -Unique
Write-Host "本脚本只检查法考 Streamlit 部署必需文件，不扫描外贸/RFQ/历史备份目录。"
Write-Host "这些无关目录已建议加入 .gitignore，不要提交到法考云端仓库。"

Write-Host ""
Write-Host "【Windows 绝对路径检查】"
$windowsRefs = $searchFiles | Select-String -Pattern 'C:\\Users\\|C:\\' -ErrorAction SilentlyContinue
if ($windowsRefs) {
    $windowsRefs | Select-Object Path, LineNumber, Line | Format-Table -Wrap -AutoSize
    Write-Host "请确认以上路径不是云端运行必需路径。"
} else {
    Write-Host "[OK] 未发现明显 Windows 绝对路径。"
}

Write-Host ""
Write-Host "【localhost / 127.0.0.1 检查】"
$localRefs = $searchFiles | Select-String -Pattern 'http://localhost','http://127\.0\.0\.1','browser\.serverAddress','browser\.serverPort' -ErrorAction SilentlyContinue
if ($localRefs) {
    $localRefs | Select-Object Path, LineNumber, Line | Format-Table -Wrap -AutoSize
    Write-Host "README 或诊断脚本中的提示文字可以保留；app.py 或前端请求里写死 localhost 才需要修复。"
} else {
    Write-Host "[OK] 未发现会影响云端浏览的 localhost 写死项。"
}

Write-Host ""
Write-Host "【敏感文件检查】"
Write-Check (-not (Test-Path -LiteralPath ".env")) ".env 不存在或未放在项目根目录"
Write-Check (-not (Test-Path -LiteralPath ".streamlit/secrets.toml")) ".streamlit/secrets.toml 不存在或不要提交"
Write-Check (Test-GitIgnoreContains ".env") ".gitignore 包含 .env"
Write-Check (Test-GitIgnoreContains ".streamlit/secrets.toml") ".gitignore 包含 .streamlit/secrets.toml"
Write-Check (Test-GitIgnoreContains "*.db") ".gitignore 包含 *.db"
Write-Check (Test-GitIgnoreContains "data/") ".gitignore 包含 data/"
Write-Check (Test-GitIgnoreContains "uploads/") ".gitignore 包含 uploads/"

Write-Host ""
Write-Host "【静态图标检查】"
Write-Check (Test-Path -LiteralPath "static/icon-192.png") "static/icon-192.png 存在"
Write-Check (Test-Path -LiteralPath "static/icon-512.png") "static/icon-512.png 存在"
Write-Check (Test-Path -LiteralPath "static/apple-touch-icon.png") "static/apple-touch-icon.png 存在"
Write-Check (Test-Path -LiteralPath "static/manifest.json") "static/manifest.json 存在"

Write-Host ""
Write-Host "【requirements.txt】"
Get-Content -LiteralPath "requirements.txt" -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "  $_" }

Write-Host ""
if (Test-Path -LiteralPath "self_test.py") {
    Write-Host "正在运行 python self_test.py ..."
    python self_test.py
} else {
    Write-Host "未发现 self_test.py，跳过自测。"
}

Write-Host ""
Write-Host "下一步：确认 .gitignore 生效，不提交 data/、uploads/、*.db、.env、secrets.toml，然后推送到 GitHub 并在 Streamlit Community Cloud 选择 app.py 部署。"
Write-Host ""
Read-Host "按 Enter 键关闭窗口"
