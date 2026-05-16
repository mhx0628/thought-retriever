@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ========================================
:: Thought-Retriever 一键发布到三个平台
:: GitHub + Gitee + HuggingFace
:: ========================================

title Thought-Retriever 一键发布工具

:: ===== 配置 =====
set GIT="D:\Program Files\Git\bin\git.exe"
if not exist %GIT% set GIT=git

set GIT_USER=mhx0628
set GIT_EMAIL=mhx1@qq.com
set REPO_NAME=thought-retriever

set GITHUB_REMOTE=https://github.com/mhx0628/%REPO_NAME%.git
set GITEE_REMOTE=https://gitee.com/ma-hongxing-1/%REPO_NAME%.git
set HF_REMOTE=https://huggingface.co/spaces/star0628/%REPO_NAME%

cd /d "e:\kaiyuan\Thought-Retriever"

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
%GIT% commit -m "Initial release: Thought-Retriever v1.0.0"
echo   [OK]
echo.

:: ===== Step 4: 推送到 GitHub =====
echo [4/6] 推送到 GitHub...
%GIT% remote remove github 2>nul
%GIT% remote add github %GITHUB_REMOTE%
%GIT% push -u github main --force
if %errorlevel%==0 (
    echo   [OK] GitHub 推送成功!
    echo   https://github.com/mhx0628/thought-retriever
) else (
    echo   [失败] GitHub 推送失败，请检查网络或仓库权限
)
echo.

:: ===== Step 5: 推送到 Gitee =====
echo [5/6] 推送到 Gitee...
%GIT% remote remove gitee 2>nul
%GIT% remote add gitee %GITEE_REMOTE%
%GIT% push -u gitee main --force
if %errorlevel%==0 (
    echo   [OK] Gitee 推送成功!
    echo   https://gitee.com/ma-hongxing-1/thought-retriever
) else (
    echo   [失败] Gitee 推送失败，请检查网络或仓库权限
)
echo.

:: ===== Step 6: 推送到 HuggingFace =====
echo [6/6] 推送到 HuggingFace...
%GIT% remote remove hf 2>nul
%GIT% remote add hf %HF_REMOTE%
%GIT% push -u hf main --force
if %errorlevel%==0 (
    echo   [OK] HuggingFace 推送成功!
    echo   https://huggingface.co/spaces/star0628/thought-retriever
) else (
    echo   [失败] HuggingFace 推送失败
    echo   请先确认 Space 已创建: https://huggingface.co/new-space
    echo   Space Name: thought-retriever
    echo   License: apache-2.0
    echo   SDK: Static
)
echo.

:: ===== 完成 =====
echo ========================================
echo   发布完成！
echo ========================================
echo   GitHub:      https://github.com/mhx0628/thought-retriever
echo   Gitee:       https://gitee.com/ma-hongxing-1/thought-retriever
echo   HuggingFace: https://huggingface.co/spaces/star0628/thought-retriever
echo   Paper:       https://arxiv.org/abs/2604.12231
echo ========================================

pause