# Thought-Retriever 一键发布脚本
# 推送到 GitHub、Gitee 和 HuggingFace 三个开源平台

$ErrorActionPreference = "Stop"
$projectDir = "e:\kaiyuan\Thought-Retriever"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Thought-Retriever 开源发布工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 用户信息
$gitUser = "mhx0628"
$gitEmail = "mhx1@qq.com"
$githubUser = "mhx0628"
$giteeUser = "ma-hongxing-1"
$huggingfaceUser = "star0628"
$repoName = "thought-retriever"

# ========================================
# Step 1: 初始化 Git 仓库
# ========================================
Write-Host "[1/5] 初始化本地 Git 仓库..." -ForegroundColor Yellow
Set-Location $projectDir

$gitExe = "D:\Program Files\Git\bin\git.exe"
if (-not (Test-Path $gitExe)) {
    $gitExe = "git"
}

# 初始化（如果尚未初始化）
if (-not (Test-Path ".git")) {
    & $gitExe init
    & $gitExe config user.name $gitUser
    & $gitExe config user.email $gitEmail
    Write-Host "  [OK] Git 仓库已初始化" -ForegroundColor Green
} else {
    Write-Host "  [OK] Git 仓库已存在" -ForegroundColor Green
}

# ========================================
# Step 2: 添加所有文件并提交
# ========================================
Write-Host "[2/5] 添加文件并提交..." -ForegroundColor Yellow
& $gitExe add -A
& $gitExe status --short

$commitMsg = "Initial release: Thought-Retriever v1.0.0 - Self-evolving thought memory for LLM agents"
& $gitExe commit -m $commitMsg
Write-Host "  [OK] 代码已提交" -ForegroundColor Green

# ========================================
# Step 3: 推送到 GitHub
# ========================================
Write-Host "[3/5] 推送到 GitHub (用户: $githubUser)..." -ForegroundColor Yellow
$githubRemote = "https://github.com/$githubUser/$repoName.git"

# 检查远程仓库是否已存在
$existingRemotes = & $gitExe remote
if ($existingRemotes -contains "github") {
    & $gitExe remote remove github
}

try {
    & $gitExe remote add github $githubRemote
    & $gitExe push -u github main --force 2>&1
    Write-Host "  [OK] 已推送到 GitHub" -ForegroundColor Green
} catch {
    Write-Host "  [WARNING] GitHub 推送失败，请确认仓库已创建: $githubRemote" -ForegroundColor Red
    Write-Host "  请先手动在 https://github.com/new 创建仓库 '$repoName'" -ForegroundColor Yellow
}

# ========================================
# Step 4: 推送到 Gitee
# ========================================
Write-Host "[4/5] 推送到 Gitee (用户: $giteeUser)..." -ForegroundColor Yellow
$giteeRemote = "https://gitee.com/$giteeUser/$repoName.git"

if ($existingRemotes -contains "gitee") {
    & $gitExe remote remove gitee
}

try {
    & $gitExe remote add gitee $giteeRemote
    & $gitExe push -u gitee main --force 2>&1
    Write-Host "  [OK] 已推送到 Gitee" -ForegroundColor Green
} catch {
    Write-Host "  [WARNING] Gitee 推送失败，请确认仓库已创建: $giteeRemote" -ForegroundColor Red
    Write-Host "  请先手动在 https://gitee.com/projects/new 创建仓库 '$repoName'" -ForegroundColor Yellow
}

# ========================================
# Step 5: HuggingFace 上传说明
# ========================================
Write-Host "[5/5] HuggingFace Space 上传说明 (用户: $huggingfaceUser)..." -ForegroundColor Yellow
Write-Host "  HuggingFace Space 需要在网页端创建，然后通过 Git 推送。" -ForegroundColor White
Write-Host "  请执行以下操作:" -ForegroundColor White
Write-Host "  1. 访问 https://huggingface.co/new-space" -ForegroundColor White
Write-Host "  2. Space Name: $repoName" -ForegroundColor White
Write-Host "  3. License: apache-2.0" -ForegroundColor White
Write-Host "  4. SDK: Docker / Static" -ForegroundColor White
Write-Host "  5. 创建后执行:" -ForegroundColor White
Write-Host "     git remote add hf https://huggingface.co/spaces/$huggingfaceUser/$repoName" -ForegroundColor Cyan
Write-Host "     git push hf main" -ForegroundColor Cyan

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  发布完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  GitHub:   https://github.com/$githubUser/$repoName" -ForegroundColor Cyan
Write-Host "  Gitee:    https://gitee.com/$giteeUser/$repoName" -ForegroundColor Cyan
Write-Host "  HuggingFace: https://huggingface.co/spaces/$huggingfaceUser/$repoName" -ForegroundColor Cyan