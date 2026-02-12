#!/bin/bash
# 部署到 GitHub Pages

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "📦 部署 Newsloom 到 GitHub Pages..."

# 检查是否有更改
if [ -z "$(git status --porcelain reports/)" ]; then
    echo "⚠️  没有新报告需要部署"
    exit 0
fi

# 添加报告
git add reports/

# 提交
DATE=$(date +%Y-%m-%d)
git commit -m "chore: 生成 $DATE 日报 [skip ci]"

# 推送到 main
git push origin main

# 部署到 gh-pages 分支
echo "🚀 部署到 gh-pages 分支..."

# 创建临时目录
TMP_DIR=$(mktemp -d)
cp -r reports/* "$TMP_DIR/"

# 切换到 gh-pages 分支
git checkout gh-pages 2>/dev/null || git checkout -b gh-pages

# 复制文件
cp -r "$TMP_DIR"/* .

# 创建 index.html 重定向到最新报告
cat > index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0; url=./latest.html">
    <title>Newsloom - Redirecting...</title>
</head>
<body>
    <p>Redirecting to latest report...</p>
    <p>If not redirected, <a href="./latest.html">click here</a>.</p>
</body>
</html>
EOF

# 提交并推送
git add .
git commit -m "chore: 部署 $DATE 报告"
git push origin gh-pages

# 切回 main 分支
git checkout main

# 清理
rm -rf "$TMP_DIR"

echo "✅ 部署完成！"
echo "📊 访问报告: https://zhangjunmengyang.github.io/Newsloom/"
