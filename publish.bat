@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ========================================
:: Thought-Retriever 一键发布脚本
:: GitHub + Gitee + HuggingFace
:: 
:: 使用方式：双击运行本文件
:: 首次运行会提示输入各平台访问令牌
:: ========================================

title Thought-Retriever 一键发布工具

:: ===== Git 路径 =====
set GIT="D:\Program Files\Git\bin\git.exe"
if not exist %GIT% set GIT=git

:: ===== 配置 =====
set GIT_USER=mhx0628
set GIT_EMAIL=mhx1@qq.com
set REPO_NAME=thought-retriever
set PROJECT_DIR=e:\kaiyuan\Thought-Retriever

set GITHUB_USER=mhx0628
set GITEE_USER=ma-hongxing-1
set HF_USER=star0628

cd /d "%PROJECT_DIR%"

echo ========================================
echo   Thought-Retriever 一键发布
echo   目标: GitHub + Gitee + HuggingFace
echo ========================================
echo.

:: ===== Step 1: 初始化 Git =====
echo [1/6] 初始化 Git 仓库...
%GIT% init 2>nul
%GIT% config user.name "%GIT_USER%"
%GIT% config user.email "%GIT_EMAIL%"
echo   [OK]
echo.

:: ===== Step 2: 添加文件 =====
echo [2/6] 添加文件...
%GIT% add -A
echo   [OK]
echo.

:: ===== Step 3: 提交 =====
echo [3/6] 提交代码...
%GIT% rev-parse HEAD >nul 2>&1
if %errorlevel% neq 0 (
    %GIT% commit -m "Initial release: Thought-Retriever v1.0.0"
    echo   [OK] 已提交
) else (
    echo   [OK] 已有提交记录，跳过
)
echo.

:: ===== Step 4: 推送到 GitHub =====
echo [4/6] 推送到 GitHub...
echo   请输入 GitHub Personal Access Token
echo   获取方式: https://github.com/settings/tokens
echo   权限要求: 勾选 repo (全部)
echo.
set /p GITHUB_TOKEN="GitHub Token: "

%GIT% remote remove github 2>nul
%GIT% remote add github https://%GITHUB_USER%:%GITHUB_TOKEN%@github.com/%GITHUB_USER%/%REPO_NAME%.git
%GIT% push -u github main --force
if %errorlevel%==0 (
    echo   [OK] GitHub 推送成功!
) else (
    echo   [失败] GitHub 推送失败
    echo   可能原因: Token 无效或网络问题
)
echo.

:: ===== Step 5: 推送到 Gitee =====
echo [5/6] 推送到 Gitee...
echo   请输入 Gitee 密码（或私人令牌）
echo   获取方式: https://gitee.com/profile/personal_access_tokens
echo.
set /p GITEE_PASS="Gitee 密码/Token: "

%GIT% remote remove gitee 2>nul
%GIT% remote add gitee https://%GITEE_USER%:%GITEE_PASS%@gitee.com/%GITEE_USER%/%REPO_NAME%.git
%GIT% push -u gitee main --force
if %errorlevel%==0 (
    echo   [OK] Gitee 推送成功!
) else (
    echo   [失败] Gitee 推送失败
)
echo.

:: ===== Step 6: 推送到 HuggingFace =====
echo [6/6] 推送到 HuggingFace...
echo   请输入 HuggingFace Token
echo   获取方式: https://huggingface.co/settings/tokens
echo   权限要求: 勾选 write repos
echo.
set /p HF_TOKEN="HuggingFace Token: "

%GIT% remote remove hf 2>nul
%GIT% remote add hf https://%HF_USER%:%HF_TOKEN%@huggingface.co/spaces/%HF_USER%/%REPO_NAME%
%GIT% push -u hf main --force
if %errorlevel%==0 (
    echo   [OK] HuggingFace 推送成功!
) else (
    echo   [失败] HuggingFace 推送失败
    echo   请确认 Space 已创建: https://huggingface.co/new-space
)
echo.

:: ===== 完成 =====
echo ========================================
echo   发布完成！
echo ========================================
echo   GitHub:      https://github.com/%GITHUB_USER%/%REPO_NAME%
echo   Gitee:       https://gitee.com/%GITEE_USER%/%REPO_NAME%
echo   HuggingFace: https://huggingface.co/spaces/%HF_USER%/%REPO_NAME%
echo   Paper:       https://arxiv.org/abs/2604.12231
echo ========================================

:: 清除环境变量中的敏感信息
set GITHUB_TOKEN=
set GITEE_PASS=
set HF_TOKEN=

pause