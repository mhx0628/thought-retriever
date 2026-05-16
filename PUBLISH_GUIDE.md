# Thought-Retriever 发布完整指南

## 平台账户

| 平台 | 用户名 | 仓库地址 |
|------|--------|----------|
| GitHub | `mhx0628` | https://github.com/mhx0628/thought-retriever |
| Gitee | `ma-hongxing-1` | https://gitee.com/ma-hongxing-1/thought-retriever |
| HuggingFace | `star0628` | https://huggingface.co/spaces/star0628/thought-retriever |
| 邮箱 | `mhx1@qq.com` | — |

## 前置准备

### 1. 确保 Git 可用

```bash
D:\Program Files\Git\bin\git.exe --version
```

### 2. 确保各平台远程仓库已创建（公开 Public）

**GitHub**:
1. 打开 https://github.com/new
2. Repository name: `thought-retriever`
3. 选择 **Public**
4. **不要**勾选 "Add a README file"
5. 点击 Create repository

**Gitee**:
1. 打开 https://gitee.com/projects/new
2. 仓库名称: `thought-retriever`
3. 选择 **公开**
4. **不要**勾选 "初始化仓库"
5. 点击 创建

**HuggingFace**:
1. 打开 https://huggingface.co/new-space
2. Space Name: `thought-retriever`
3. License: `apache-2.0`
4. Space SDK: `Static`
5. 选择 **Public**
6. 点击 Create Space

## 一键发布

创建好上述仓库后，双击运行:

```
e:\kaiyuan\Thought-Retriever\publish.bat
```

## 手动发布步骤

如果批处理脚本失败，可以手动执行:

### Step 1: 初始化 Git

```bash
cd /d e:\kaiyuan\Thought-Retriever
git init
git config user.name "mhx0628"
git config user.email "mhx1@qq.com"
```

### Step 2: 提交代码

```bash
git add -A
git commit -m "Initial release: Thought-Retriever v1.0.0"
```

### Step 3: 推送到 GitHub

```bash
git remote add github https://github.com/mhx0628/thought-retriever.git
git push -u github main --force
```

### Step 4: 推送到 Gitee

```bash
git remote add gitee https://gitee.com/ma-hongxing-1/thought-retriever.git
git push -u gitee main --force
```

### Step 5: 推送到 HuggingFace

```bash
git remote add hf https://huggingface.co/spaces/star0628/thought-retriever
git push hf main --force
```

## 验证

发布后检查以下 URL 是否可以正常访问:

- [GitHub](https://github.com/mhx0628/thought-retriever)
- [Gitee](https://gitee.com/ma-hongxing-1/thought-retriever)
- [HuggingFace](https://huggingface.co/spaces/star0628/thought-retriever)

## 论文版权说明

论文 `2604.12231v1.pdf` 托管在 arXiv 平台。arXiv 的论文分发政策允许非商业目的下重新分发 PDF 文件，前提是必须保留作者署名和原始来源。

本仓库中包含的论文 PDF（位于 `paper/` 目录下）严格遵守以下准则:
1. 保留论文原始文件完整性（未作任何修改）
2. 明确标注作者来源（UIUC/MIT/CMU）
3. 提供 arXiv 原始链接
4. 不用于商业目的

如果论文作者或版权方提出异议，我们将立即移除。

## 许可证

- **项目代码**: Apache License 2.0
- **论文 PDF**: 版权归原作者和 TMLR 所有